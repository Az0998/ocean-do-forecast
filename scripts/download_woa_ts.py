#!/usr/bin/env python
"""Download WOA18 annual temperature + salinity and subset to the active region."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import xarray as xr

from config import DEPTH_LEVELS_DBAR, PROCESSED, RAW, ensure_dirs, load_active_region
from src.download_util import download

WOA_T = (
    "https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/temperature/"
    "netcdf/decav/1.00/woa18_decav_t00_01.nc"
)
WOA_S = (
    "https://www.ncei.noaa.gov/data/oceans/woa/WOA18/DATA/salinity/"
    "netcdf/decav/1.00/woa18_decav_s00_01.nc"
)


def _subset(ds: xr.Dataset, region: dict, var_in: str, var_out: str) -> xr.Dataset:
    lon_name = "lon" if "lon" in ds.coords else "longitude"
    lat_name = "lat" if "lat" in ds.coords else "latitude"
    depth_name = "depth" if "depth" in ds.coords else "lev"
    lon0, lon1 = region["lon_min"], region["lon_max"]
    lon = ds[lon_name]
    if float(lon.min()) >= 0 and lon0 < 0:
        lon0, lon1 = lon0 % 360, lon1 % 360
    sub = ds.sel(
        {lon_name: slice(lon0, lon1), lat_name: slice(region["lat_min"], region["lat_max"])}
    )
    sub = sub.sel({depth_name: np.array(DEPTH_LEVELS_DBAR, dtype=float)}, method="nearest")
    out = sub[[var_in]].rename(
        {var_in: var_out, lon_name: "lon", lat_name: "lat", depth_name: "depth"}
    )
    if "time" in out.dims and out.sizes.get("time", 1) == 1:
        out = out.squeeze("time", drop=True)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    raw_t = RAW / "woa" / "woa18_decav_t00_01.nc"
    raw_s = RAW / "woa" / "woa18_decav_s00_01.nc"
    if not args.skip_download:
        download(WOA_T, raw_t, min_bytes=10_000_000)
        download(WOA_S, raw_s, min_bytes=10_000_000)

    t = _subset(xr.open_dataset(raw_t, decode_times=False), region, "t_an", "temp")
    s = _subset(xr.open_dataset(raw_s, decode_times=False), region, "s_an", "salt")
    out = xr.merge([t, s])
    out.attrs.update(
        {
            "source": "woa18_annual_ts",
            "region_id": region.get("id"),
            "citation": "World Ocean Atlas 2018 Temperature & Salinity",
        }
    )
    dest = PROCESSED / "woa18_ts_region.nc"
    out.to_netcdf(dest)
    print(f"[woa-ts] wrote {dest}")
    print(out)


if __name__ == "__main__":
    main()
