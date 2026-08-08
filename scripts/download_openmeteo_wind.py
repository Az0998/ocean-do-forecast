#!/usr/bin/env python
"""Download monthly 10 m wind / 2 m temperature via Open-Meteo archive API.

Builds a coarse regional forcing cube (no CDS token required). ERA5-backed.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import xarray as xr

from config import PROCESSED, RAW, ensure_dirs, load_active_region

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def _fetch_point(lat: float, lon: float, start: str, end: str) -> dict:
    q = urlencode(
        {
            "latitude": f"{lat:.3f}",
            "longitude": f"{lon:.3f}",
            "start_date": start,
            "end_date": end,
            "daily": "wind_speed_10m_mean,wind_direction_10m_dominant,temperature_2m_mean",
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }
    )
    url = f"{ARCHIVE}?{q}"
    req = Request(url, headers={"User-Agent": "ocean-do-forecast/0.2"})
    with urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


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
    # u/v from speed/dir
    rad = np.deg2rad(df["wind_dir"].astype(float))
    df["u10"] = -df["wind_speed"].astype(float) * np.sin(rad)
    df["v10"] = -df["wind_speed"].astype(float) * np.cos(rad)
    return df.resample("MS").mean(numeric_only=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2004-01-01")
    parser.add_argument("--end", default="2022-12-31")
    parser.add_argument("--step", type=float, default=2.0, help="grid step degrees")
    parser.add_argument("--pause", type=float, default=0.35)
    parser.add_argument("--offline-synth", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()

    lats = np.arange(region["lat_min"] + args.step / 2, region["lat_max"], args.step)
    lons = np.arange(region["lon_min"] + args.step / 2, region["lon_max"], args.step)
    times = pd.date_range(args.start[:7], args.end[:7], freq="MS")

    u = np.full((len(times), len(lats), len(lons)), np.nan, dtype=np.float32)
    v = np.full_like(u, np.nan)
    t2m = np.full_like(u, np.nan)

    if args.offline_synth:
        # Monsoon-like seasonal wind: summer SW, winter NE
        months = times.month.values
        for i, m in enumerate(months):
            summer = 0.5 * (1 + np.cos(2 * np.pi * (m - 7) / 12))
            u[i] = 2.0 + 3.0 * summer
            v[i] = -1.5 + 4.0 * summer
            t2m[i] = 18.0 + 10.0 * np.cos(2 * np.pi * (m - 8) / 12)
        source = "openmeteo_offline_synth"
    else:
        source = "open_meteo_era5_archive"
        cache = RAW / "openmeteo" / "points"
        cache.mkdir(parents=True, exist_ok=True)
        for yi, lat in enumerate(lats):
            for xi, lon in enumerate(lons):
                cpath = cache / f"lat{lat:.2f}_lon{lon:.2f}.json"
                if cpath.exists():
                    payload = json.loads(cpath.read_text(encoding="utf-8"))
                else:
                    try:
                        payload = _fetch_point(float(lat), float(lon), args.start, args.end)
                        cpath.write_text(json.dumps(payload), encoding="utf-8")
                        time.sleep(args.pause)
                    except Exception as exc:
                        print(f"[om] fail {lat},{lon}: {exc}", flush=True)
                        continue
                df = _daily_to_monthly(payload)
                if df.empty:
                    continue
                df = df.reindex(times)
                u[:, yi, xi] = df["u10"].to_numpy(dtype=np.float32)
                v[:, yi, xi] = df["v10"].to_numpy(dtype=np.float32)
                t2m[:, yi, xi] = df["t2m"].to_numpy(dtype=np.float32)
                print(f"[om] ok {lat:.2f},{lon:.2f}", flush=True)

        if not np.isfinite(u).any():
            print("[om] no points fetched; falling back to offline synth", flush=True)
            return main_offline_fallback(region, times, lats, lons)

    wind = np.sqrt(u**2 + v**2)
    ds = xr.Dataset(
        {
            "u10": (("time", "lat", "lon"), u),
            "v10": (("time", "lat", "lon"), v),
            "wind_speed": (("time", "lat", "lon"), wind.astype(np.float32)),
            "t2m": (("time", "lat", "lon"), t2m),
        },
        coords={"time": times, "lat": lats, "lon": lons},
        attrs={"source": source, "region_id": region.get("id")},
    )
    dest = PROCESSED / "openmeteo_wind_region.nc"
    ds.to_netcdf(dest)
    print(f"[om] wrote {dest} shape={dict(ds.sizes)}")


def main_offline_fallback(region, times, lats, lons):
    import sys as _sys

    _sys.argv = [_sys.argv[0], "--offline-synth"]
    # rebuild with synth on same grid
    months = times.month.values
    u = np.zeros((len(times), len(lats), len(lons)), dtype=np.float32)
    v = np.zeros_like(u)
    t2m = np.zeros_like(u)
    for i, m in enumerate(months):
        summer = 0.5 * (1 + np.cos(2 * np.pi * (m - 7) / 12))
        u[i] = 2.0 + 3.0 * summer
        v[i] = -1.5 + 4.0 * summer
        t2m[i] = 18.0 + 10.0 * np.cos(2 * np.pi * (m - 8) / 12)
    wind = np.sqrt(u**2 + v**2)
    ds = xr.Dataset(
        {
            "u10": (("time", "lat", "lon"), u),
            "v10": (("time", "lat", "lon"), v),
            "wind_speed": (("time", "lat", "lon"), wind),
            "t2m": (("time", "lat", "lon"), t2m),
        },
        coords={"time": times, "lat": lats, "lon": lons},
        attrs={"source": "openmeteo_offline_synth", "region_id": region.get("id")},
    )
    dest = PROCESSED / "openmeteo_wind_region.nc"
    ds.to_netcdf(dest)
    print(f"[om] wrote synth {dest}")


if __name__ == "__main__":
    main()
