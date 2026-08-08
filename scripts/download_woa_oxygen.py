#!/usr/bin/env python
"""Download WOA18 dissolved oxygen and subset to the active region.

Uses the NCEI HTTPS annual field (objectively analyzed, 1°). This is a
climatology — not a forecast target — but provides a real-data ocean mask,
depth structure, and clim baseline for the East China Sea shelf.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import xarray as xr

from config import DEPTH_LEVELS_DBAR, PROCESSED, RAW, ensure_dirs, load_active_region

WOA_ANNUAL = (
    "https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/oxygen/"
    "netcdf/all/1.00/woa18_all_o00_01.nc"
)


def download(url: str, dest: Path, chunk: int = 1 << 20) -> Path:
    import subprocess

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"[woa] exists, skip download: {dest}", flush=True)
        return dest
    print(f"[woa] downloading via curl: {url}", flush=True)
    try:
        subprocess.check_call(
            ["curl", "-L", "--retry", "3", "-C", "-", "-o", str(dest), url]
        )
        return dest
    except Exception as exc:
        print(f"[woa] curl failed ({exc}); falling back to urllib", flush=True)
    req = Request(url, headers={"User-Agent": "ocean-do-forecast/0.1"})
    with urlopen(req, timeout=600) as resp, open(dest, "wb") as f:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        done = 0
        while True:
            buf = resp.read(chunk)
            if not buf:
                break
            f.write(buf)
            done += len(buf)
            if total and done % (8 * chunk) < chunk:
                pct = 100.0 * done / total
                print(f"[woa] {pct:5.1f}% ({done/1e6:.1f}/{total/1e6:.1f} MB)", flush=True)
    return dest


def subset_region(ds: xr.Dataset, region: dict) -> xr.Dataset:
    # WOA uses lat ascending, lon 0-360 or -180-180 depending on file
    lon_name = "lon" if "lon" in ds.coords else "longitude"
    lat_name = "lat" if "lat" in ds.coords else "latitude"
    depth_name = "depth" if "depth" in ds.coords else "lev"
    o2_name = "o_an" if "o_an" in ds else [v for v in ds.data_vars if "o_" in v][0]

    lon = ds[lon_name]
    # convert region to file lon convention
    lon0, lon1 = region["lon_min"], region["lon_max"]
    if float(lon.min()) >= 0 and lon0 < 0:
        lon0, lon1 = lon0 % 360, lon1 % 360
    lat0, lat1 = region["lat_min"], region["lat_max"]
    sub = ds.sel(
        {lon_name: slice(lon0, lon1), lat_name: slice(lat0, lat1)}
    )
    depths = np.array(DEPTH_LEVELS_DBAR, dtype=float)
    sub = sub.sel({depth_name: depths}, method="nearest")
    out = sub[[o2_name]].rename(
        {o2_name: "oxygen", lon_name: "lon", lat_name: "lat", depth_name: "depth"}
    )
    # drop time if singleton climatology
    if "time" in out.dims and out.sizes.get("time", 1) == 1:
        out = out.squeeze("time", drop=True)
    out["oxygen"].attrs["units"] = out["oxygen"].attrs.get("units", "micromole/kg")
    out.attrs.update(
        {
            "source": "woa18_annual",
            "region_id": region.get("id"),
            "citation": "World Ocean Atlas 2018 Oxygen",
            "url": WOA_ANNUAL,
        }
    )
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    raw = RAW / "woa" / "woa18_all_o00_01.nc"
    if not args.skip_download:
        download(WOA_ANNUAL, raw)
    print(f"[woa] opening {raw}")
    ds = xr.open_dataset(raw, decode_times=False)
    out = subset_region(ds, region)
    dest = PROCESSED / "woa18_oxygen_region.nc"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_netcdf(dest)
    print(f"[woa] wrote {dest}")
    print(out)


if __name__ == "__main__":
    main()
