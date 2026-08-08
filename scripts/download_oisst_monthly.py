#!/usr/bin/env python
"""Download NOAA OISST v2 monthly SST (PSL) and subset to the active region."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import xarray as xr

from config import PROCESSED, RAW, ensure_dirs, load_active_region
from src.download_util import download

OISST_URL = "https://downloads.psl.noaa.gov/Datasets/noaa.oisst.v2/sst.mnmean.nc"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--start", default="2004-01")
    parser.add_argument("--end", default="2022-12")
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    raw = RAW / "oisst" / "sst.mnmean.nc"
    if not args.skip_download:
        download(OISST_URL, raw, min_bytes=10_000_000)

    ds = xr.open_dataset(raw)
    lon0 = float(region["lon_min"]) % 360
    lon1 = float(region["lon_max"]) % 360
    lat0, lat1 = float(region["lat_min"]), float(region["lat_max"])
    lat_asc = bool(ds["lat"][0] < ds["lat"][-1])
    lat_slice = slice(lat0, lat1) if lat_asc else slice(lat1, lat0)
    sub = ds.sel(lon=slice(lon0, lon1), lat=lat_slice, time=slice(args.start, args.end))
    out = sub[["sst"]]
    lon = np.asarray(out["lon"].values, dtype=float)
    if lon.min() >= 0:
        out = out.assign_coords(lon=((lon + 180.0) % 360.0) - 180.0).sortby("lon")
    out.attrs.update(
        {
            "source": "noaa_oisst_v2_monthly",
            "region_id": region.get("id"),
            "url": OISST_URL,
        }
    )
    dest = PROCESSED / "oisst_monthly_region.nc"
    out.to_netcdf(dest)
    print(f"[oisst] wrote {dest} shape={dict(out.sizes)}")


if __name__ == "__main__":
    main()
