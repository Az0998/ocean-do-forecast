#!/usr/bin/env python
"""Download monthly 10 m wind / 2 m temperature via Open-Meteo archive API.

ERA5-backed, no CDS token. Uses multi-location year batches for speed.
Prefer --match-oxygen-grid so forcings align with the forecast cube.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import xarray as xr

from config import PROCESSED, RAW, ensure_dirs, load_active_region

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def _fetch_batch(lats: list[float], lons: list[float], year: int) -> list[dict]:
    q = urlencode(
        {
            "latitude": ",".join(f"{x:.3f}" for x in lats),
            "longitude": ",".join(f"{x:.3f}" for x in lons),
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "daily": "wind_speed_10m_mean,wind_direction_10m_dominant,temperature_2m_mean",
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }
    )
    url = f"{ARCHIVE}?{q}"
    req = Request(url, headers={"User-Agent": "ocean-do-forecast/0.2"})
    with urlopen(req, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, dict):
        return [data]
    return list(data)


def _daily_to_monthly(payload: dict) -> pd.DataFrame:
    daily = payload.get("daily") or {}
    if not daily.get("time"):
        return pd.DataFrame()
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(daily["time"]),
            "wind_speed": daily.get("wind_speed_10m_mean"),
            "wind_dir": daily.get("wind_direction_10m_dominant"),
            "t2m": daily.get("temperature_2m_mean"),
        }
    ).set_index("time")
    rad = np.deg2rad(df["wind_dir"].astype(float))
    speed = df["wind_speed"].astype(float)
    df["u10"] = -speed * np.sin(rad)
    df["v10"] = -speed * np.cos(rad)
    return df.resample("MS").mean(numeric_only=True)


def _synth_fields(times, lats, lons):
    u = np.zeros((len(times), len(lats), len(lons)), dtype=np.float32)
    v = np.zeros_like(u)
    t2m = np.zeros_like(u)
    months = times.month.values
    for i, m in enumerate(months):
        summer = 0.5 * (1 + np.cos(2 * np.pi * (m - 7) / 12))
        u[i] = 2.0 + 3.0 * summer
        v[i] = -1.5 + 4.0 * summer
        t2m[i] = 18.0 + 10.0 * np.cos(2 * np.pi * (m - 8) / 12)
    return u, v, t2m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2004-01-01", help="Output cube start")
    parser.add_argument("--end", default="2022-12-31", help="Output cube end")
    parser.add_argument(
        "--fetch-start",
        default=None,
        help="First year/date to fetch from API (default: --start). Earlier months filled by clim.",
    )
    parser.add_argument(
        "--fetch-end",
        default=None,
        help="Last year/date to fetch from API (default: --end).",
    )
    parser.add_argument("--step", type=float, default=1.0)
    parser.add_argument("--match-oxygen-grid", action="store_true")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--pause", type=float, default=0.4)
    parser.add_argument("--offline-synth", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output NetCDF path (default: data/processed/openmeteo_wind_region.nc)",
    )
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()

    oxy_path = PROCESSED / "regional_oxygen_cube.nc"
    if args.match_oxygen_grid and oxy_path.exists():
        ods = xr.open_dataset(oxy_path)
        lats = np.asarray(ods["lat"].values, dtype=float)
        lons = np.asarray(ods["lon"].values, dtype=float)
        print(f"[om] matching oxygen grid: {len(lats)}x{len(lons)}", flush=True)
    else:
        lats = np.arange(region["lat_min"] + args.step / 2, region["lat_max"], args.step)
        lons = np.arange(region["lon_min"] + args.step / 2, region["lon_max"], args.step)

    times = pd.date_range(args.start[:7], args.end[:7], freq="MS")
    u = np.full((len(times), len(lats), len(lons)), np.nan, dtype=np.float32)
    v = np.full_like(u, np.nan)
    t2m = np.full_like(u, np.nan)

    if args.offline_synth:
        u, v, t2m = _synth_fields(times, lats, lons)
        source = "openmeteo_offline_synth"
    else:
        source = "open_meteo_era5_archive"
        cache_dir = RAW / "openmeteo" / "batches"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # flatten grid points
        points = [(yi, xi, float(lats[yi]), float(lons[xi])) for yi in range(len(lats)) for xi in range(len(lons))]
        fetch_start = args.fetch_start or args.start
        fetch_end = args.fetch_end or args.end
        y0, y1 = int(str(fetch_start)[:4]), int(str(fetch_end)[:4])
        print(f"[om] fetching years {y0}-{y1}; output span {args.start[:7]}..{args.end[:7]}", flush=True)
        # accumulate daily-monthly series per point
        series = {(yi, xi): [] for yi, xi, _, _ in points}

        for year in range(y0, y1 + 1):
            year_ok = True
            for b0 in range(0, len(points), args.batch_size):
                batch = points[b0 : b0 + args.batch_size]
                key = f"y{year}_n{len(points)}_b{b0}_{len(batch)}.json"
                cpath = cache_dir / key
                if cpath.exists() and cpath.stat().st_size > 200:
                    payloads = json.loads(cpath.read_text(encoding="utf-8"))
                else:
                    blats = [p[2] for p in batch]
                    blons = [p[3] for p in batch]
                    payloads = None
                    for attempt in range(10):
                        try:
                            payloads = _fetch_batch(blats, blons, year)
                            cpath.write_text(json.dumps(payloads), encoding="utf-8")
                            time.sleep(args.pause)
                            break
                        except HTTPError as exc:
                            wait = 60.0 * (attempt + 1) if exc.code == 429 else min(
                                args.pause * (3**attempt), 90.0
                            )
                            wait = min(wait, 300.0)
                            print(
                                f"[om] retry year={year} batch={b0} (HTTP {exc.code}); sleep {wait:.1f}s",
                                flush=True,
                            )
                            time.sleep(wait)
                        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                            wait = min(args.pause * (3**attempt), 90.0)
                            print(
                                f"[om] retry year={year} batch={b0} ({exc}); sleep {wait:.1f}s",
                                flush=True,
                            )
                            time.sleep(wait)
                    if payloads is None:
                        print(f"[om] give up year={year} batch={b0}", flush=True)
                        year_ok = False
                        continue
                if len(payloads) != len(batch):
                    print(
                        f"[om] warn year={year} batch={b0}: got {len(payloads)} != {len(batch)}",
                        flush=True,
                    )
                for p, payload in zip(batch, payloads):
                    yi, xi, _, _ = p
                    df = _daily_to_monthly(payload)
                    if not df.empty:
                        series[(yi, xi)].append(df)
            print(f"[om] year {year} done ok={year_ok}", flush=True)
            # cool down between years to reduce 429s
            time.sleep(max(args.pause, 2.0))

        n_ok = 0
        for (yi, xi), frames in series.items():
            if not frames:
                continue
            df = pd.concat(frames).sort_index()
            df = df[~df.index.duplicated(keep="last")].reindex(times)
            u[:, yi, xi] = df["u10"].to_numpy(dtype=np.float32)
            v[:, yi, xi] = df["v10"].to_numpy(dtype=np.float32)
            t2m[:, yi, xi] = df["t2m"].to_numpy(dtype=np.float32)
            n_ok += 1

        coverage = float(np.isfinite(u).mean())
        print(f"[om] finite coverage={coverage:.3f} points_ok={n_ok}/{len(points)}", flush=True)
        if n_ok == 0 or coverage < 0.2:
            print("[om] insufficient real data; writing offline synth fallback", flush=True)
            u, v, t2m = _synth_fields(times, lats, lons)
            source = "openmeteo_offline_synth"

    # Backfill missing months/years with month-of-year climatology from available data
    months = times.month.values
    for arr in (u, v, t2m):
        if np.isfinite(arr).all():
            continue
        for m in range(1, 13):
            idx = np.where(months == m)[0]
            if not len(idx):
                continue
            with np.errstate(all="ignore"):
                clim = np.nanmean(arr[idx], axis=0)
            if not np.isfinite(clim).any():
                continue
            for i in idx:
                bad = ~np.isfinite(arr[i])
                if bad.any():
                    arr[i][bad] = clim[bad]
        still = ~np.isfinite(arr)
        if still.any():
            with np.errstate(all="ignore"):
                fill = np.nanmean(arr)
            arr[still] = 0.0 if not np.isfinite(fill) else float(fill)

    wind = np.sqrt(u**2 + v**2).astype(np.float32)
    ds = xr.Dataset(
        {
            "u10": (("time", "lat", "lon"), u),
            "v10": (("time", "lat", "lon"), v),
            "wind_speed": (("time", "lat", "lon"), wind),
            "t2m": (("time", "lat", "lon"), t2m),
        },
        coords={
            "time": times,
            "lat": lats.astype(np.float32),
            "lon": lons.astype(np.float32),
        },
        attrs={
            "source": source,
            "region_id": region.get("id"),
            "api": ARCHIVE,
            "fetch_start": str(args.fetch_start or args.start),
            "fetch_end": str(args.fetch_end or args.end),
            "note": "Open-Meteo archive is ERA5-backed; monthly means from daily. "
            "Months outside the fetch window are filled with month-of-year climatology.",
        },
    )
    dest = Path(args.output) if args.output else (PROCESSED / "openmeteo_wind_region.nc")
    dest.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(dest)
    print(f"[om] wrote {dest} source={source} shape={dict(ds.sizes)}")
    print(
        f"[om] wind_speed mean={float(np.nanmean(wind)):.2f} "
        f"std={float(np.nanstd(wind)):.2f} t2m mean={float(np.nanmean(t2m)):.2f}"
    )


if __name__ == "__main__":
    main()
