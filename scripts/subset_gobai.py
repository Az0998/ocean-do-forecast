#!/usr/bin/env python
"""Subset a full GOBAI-O2 NetCDF to the active region and save a regional cube."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import xarray as xr

from config import DEPTH_LEVELS_DBAR, PROCESSED, ensure_dirs, load_active_region
from src.gobai_data import _pick_oxygen_name, gobai_dir, save_cube


def _normalize_coords(ds: xr.Dataset) -> xr.Dataset:
    rename = {}
    for a, b in [
        ("longitude", "lon"),
        ("latitude", "lat"),
        ("Longitude", "lon"),
        ("Latitude", "lat"),
        ("pressure", "depth"),
        ("pres", "depth"),
        ("lev", "depth"),
        ("z", "depth"),
    ]:
        if a in ds.coords or a in ds.dims:
            rename[a] = b
    return ds.rename(rename) if rename else ds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="GOBAI NetCDF path (default: first *.nc under data/raw/gobai/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output regional cube (default: data/processed/regional_oxygen_cube.nc)",
    )
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    inp = args.input
    if inp is None:
        files = sorted(gobai_dir().rglob("*.nc"))
        if not files:
            raise SystemExit(
                f"No GOBAI file found. Place NetCDF in {gobai_dir()} "
                "or pass --input"
            )
        inp = files[0]
    print(f"[subset] reading {inp}")
    ds = xr.open_dataset(inp)
    ds = _normalize_coords(ds)
    o2 = _pick_oxygen_name(ds)
    lon0, lon1 = region["lon_min"], region["lon_max"]
    lat0, lat1 = region["lat_min"], region["lat_max"]
    # handle descending lat
    lat_coord = ds["lat"]
    if float(lat_coord[0]) > float(lat_coord[-1]):
        sub = ds.sel(lon=slice(lon0, lon1), lat=slice(lat1, lat0))
    else:
        sub = ds.sel(lon=slice(lon0, lon1), lat=slice(lat0, lat1))
    if "depth" in sub.dims:
        depths = np.array(DEPTH_LEVELS_DBAR, dtype=float)
        sub = sub.sel(depth=depths, method="nearest")
    out_ds = sub[[o2]].rename({o2: "oxygen"})
    out_ds.attrs.update(
        {
            "source": "gobai",
            "region_id": region.get("id"),
            "source_file": str(inp),
            "doi": "10.25921/z72m-yz67",
        }
    )
    out = args.output or (PROCESSED / "regional_oxygen_cube.nc")
    save_cube(out_ds.load(), out)
    print(f"[subset] wrote {out}")
    print(out_ds)


if __name__ == "__main__":
    main()
