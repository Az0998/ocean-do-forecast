#!/usr/bin/env python
"""Spatially subset the ECS physics cube onto an overlapping candidate region.

Useful for Yangtze plume / southern Yellow Sea sensitivity without re-downloading
Open-Meteo / OISST / WOA. Writes `regional_physics_cube_<region_id>.nc`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import xarray as xr

from config import PROCESSED, ensure_dirs, load_regions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True, help="candidate id in regions.yaml")
    parser.add_argument(
        "--source",
        type=Path,
        default=PROCESSED / "regional_physics_cube.nc",
    )
    args = parser.parse_args()
    ensure_dirs()
    candidates = load_regions()["candidates"]
    if args.region not in candidates:
        raise SystemExit(f"Unknown region {args.region}")
    if not args.source.exists():
        raise SystemExit(f"Missing physics cube: {args.source}")

    reg = candidates[args.region]
    ds = xr.open_dataset(args.source)
    sub = ds.sel(
        lon=slice(reg["lon_min"], reg["lon_max"]),
        lat=slice(reg["lat_min"], reg["lat_max"]),
    )
    if sub.sizes.get("lat", 0) < 2 or sub.sizes.get("lon", 0) < 2:
        raise SystemExit(
            f"Subset too small for {args.region}: lat={sub.sizes.get('lat')} "
            f"lon={sub.sizes.get('lon')} — region may not overlap ECS cube."
        )
    # Depth clip by region max if requested
    dmax = float(reg.get("depth_max_m", 1e9))
    sub = sub.sel(depth=sub.depth.where(sub.depth <= dmax, drop=True))
    sub = sub.assign_attrs(
        {
            **ds.attrs,
            "region_id": args.region,
            "parent_cube": str(args.source.name),
            "note": f"Spatial subset of ECS physics cube for {args.region}",
        }
    )
    dest = PROCESSED / f"regional_physics_cube_{args.region}.nc"
    sub.to_netcdf(dest)
    print(
        f"[subset] {args.region}: time={sub.sizes['time']} depth={sub.sizes['depth']} "
        f"lat={sub.sizes['lat']} lon={sub.sizes['lon']} -> {dest}"
    )


if __name__ == "__main__":
    main()
