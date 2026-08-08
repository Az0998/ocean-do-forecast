#!/usr/bin/env python
"""Download NCEP/NCAR monthly surface winds (PSL) and subset to the active region.

Real atmospheric reanalysis forcing when Open-Meteo is rate-limited and CDS
credentials are unavailable. Writes data/processed/ncep_wind_region.nc and
optionally refreshes openmeteo_wind_region.nc as a drop-in wind cube.
"""
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

UWND = "https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.derived/surface/uwnd.mon.mean.nc"
VWND = "https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.derived/surface/vwnd.mon.mean.nc"
AIR = "https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.derived/surface/air.mon.mean.nc"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--start", default="2004-01")
    parser.add_argument("--end", default="2022-12")
    parser.add_argument(
        "--as-default-wind",
        action="store_true",
        help="Also write processed/openmeteo_wind_region.nc for drop-in use",
    )
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    raw = RAW / "ncep"
    u_path = raw / "uwnd.mon.mean.nc"
    v_path = raw / "vwnd.mon.mean.nc"
    t_path = raw / "air.mon.mean.nc"
    if not args.skip_download:
        download(UWND, u_path, min_bytes=1_000_000)
        download(VWND, v_path, min_bytes=1_000_000)
        download(AIR, t_path, min_bytes=1_000_000)

    u = xr.open_dataset(u_path)
    v = xr.open_dataset(v_path)
    t = xr.open_dataset(t_path)

    def subset(ds, var):
        # lon 0-360, lat often descending
        lon0 = float(region["lon_min"]) % 360
        lon1 = float(region["lon_max"]) % 360
        lat0, lat1 = float(region["lat_min"]), float(region["lat_max"])
        lat_asc = bool(ds["lat"][0] < ds["lat"][-1])
        lat_slice = slice(lat0, lat1) if lat_asc else slice(lat1, lat0)
        # variable name: uwnd / vwnd / air
        name = var if var in ds else list(ds.data_vars)[0]
        da = ds[name].sel(lon=slice(lon0, lon1), lat=lat_slice, time=slice(args.start, args.end))
        # drop level if present
        if "level" in da.dims:
            da = da.isel(level=0)
        return da

    u_da = subset(u, "uwnd")
    v_da = subset(v, "vwnd")
    t_da = subset(t, "air")
    # align
    u_da, v_da = xr.align(u_da, v_da, join="inner")
    t_da = t_da.sel(time=u_da.time, method="nearest")
    t_da = t_da.interp(lat=u_da.lat, lon=u_da.lon)
    # convert lon to -180..180 for ECS
    lon = np.asarray(u_da["lon"].values, dtype=float)
    if lon.min() >= 0:
        new_lon = ((lon + 180.0) % 360.0) - 180.0
        u_da = u_da.assign_coords(lon=new_lon).sortby("lon")
        v_da = v_da.assign_coords(lon=new_lon).sortby("lon")
        t_da = t_da.assign_coords(lon=new_lon).sortby("lon")

    wind = np.sqrt(u_da.values.astype(np.float32) ** 2 + v_da.values.astype(np.float32) ** 2)
    # air is often Kelvin
    tvals = t_da.values.astype(np.float32)
    if np.nanmean(tvals) > 100:
        tvals = tvals - 273.15

    ds = xr.Dataset(
        {
            "u10": (("time", "lat", "lon"), u_da.values.astype(np.float32)),
            "v10": (("time", "lat", "lon"), v_da.values.astype(np.float32)),
            "wind_speed": (("time", "lat", "lon"), wind),
            "t2m": (("time", "lat", "lon"), tvals),
        },
        coords={
            "time": u_da["time"].values,
            "lat": u_da["lat"].values.astype(np.float32),
            "lon": u_da["lon"].values.astype(np.float32),
        },
        attrs={
            "source": "ncep_ncar_monthly_surface",
            "region_id": region.get("id"),
            "url_u": UWND,
            "url_v": VWND,
            "note": "NCEP/NCAR Reanalysis monthly means (PSL). Proxy for ERA5 when CDS/Open-Meteo unavailable.",
        },
    )
    dest = PROCESSED / "ncep_wind_region.nc"
    ds.to_netcdf(dest)
    print(f"[ncep] wrote {dest} shape={dict(ds.sizes)}")
    print(
        f"[ncep] wind mean={float(np.nanmean(wind)):.2f} "
        f"t2m mean={float(np.nanmean(tvals)):.2f}"
    )
    if args.as_default_wind:
        dropin = PROCESSED / "openmeteo_wind_region.nc"
        ds.to_netcdf(dropin)
        print(f"[ncep] also wrote drop-in {dropin}")


if __name__ == "__main__":
    main()
