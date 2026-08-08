#!/usr/bin/env python
"""Build a semi-real monthly cube: WOA18 regional clim + synthetic AR anomalies.

Stronger than pure demo for method debugging; still NOT a substitute for GOBAI
in the paper's main results. Output flagged source='woa_informed'.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import xarray as xr

from config import PROCESSED, ensure_dirs, load_active_region
from src.gobai_data import save_cube


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2004-01")
    parser.add_argument("--end", default="2022-12")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    woa_path = PROCESSED / "woa18_oxygen_region.nc"
    if not woa_path.exists():
        raise SystemExit(
            f"Missing {woa_path}. Run: py -3.12 scripts/download_woa_oxygen.py"
        )
    woa = xr.open_dataset(woa_path)
    # oxygen: (depth, lat, lon)
    clim = woa["oxygen"].transpose("depth", "lat", "lon").values.astype(np.float32)
    depths = woa["depth"].values
    lats = woa["lat"].values
    lons = woa["lon"].values
    # handle missing
    fill = np.nanmean(clim)
    clim = np.where(np.isfinite(clim), clim, fill)

    times = xr.date_range(args.start, args.end, freq="MS")
    rng = np.random.default_rng(args.seed)
    lon_g, lat_g = np.meshgrid(lons, lats, indexing="xy")
    coastal = np.exp(-((lon_g - float(np.nanmin(lons))) / 3.0) ** 2)

    T, Z, Y, X = len(times), len(depths), len(lats), len(lons)
    oxygen = np.zeros((T, Z, Y, X), dtype=np.float32)
    anom = np.zeros((Z, Y, X), dtype=np.float32)
    for ti, ts in enumerate(times):
        m = int(ts.month)
        # mild seasonal modulation of clim (±8%)
        season = 1.0 + 0.08 * np.sin(2 * np.pi * (m - 3) / 12.0)
        innov = rng.normal(0, 3.5, size=(Z, Y, X)).astype(np.float32)
        innov = innov - 6.0 * coastal[None, :, :] * (rng.random() < 0.08)
        anom = 0.7 * anom + innov
        summer_hyp = -20.0 * coastal * max(0.0, np.sin(2 * np.pi * (m - 6) / 12.0))
        field = clim * season + anom + summer_hyp[None, :, :]
        oxygen[ti] = np.clip(field, 5.0, 400.0)

    ds = xr.Dataset(
        {
            "oxygen": (
                ("time", "depth", "lat", "lon"),
                oxygen,
                {"units": "umol/kg", "long_name": "WOA clim + synthetic anomaly"},
            )
        },
        coords={
            "time": times,
            "depth": ("depth", depths.astype(np.float32), {"units": "dbar"}),
            "lat": ("lat", lats.astype(np.float32)),
            "lon": ("lon", lons.astype(np.float32)),
        },
        attrs={
            "source": "woa_informed",
            "warning": "WOA18 clim + synthetic anomalies; not for final paper claims",
            "region": region.get("id"),
            "woa_file": str(woa_path),
        },
    )
    out = PROCESSED / "regional_oxygen_cube.nc"
    save_cube(ds, out)
    print(f"[woa-informed] wrote {out} source={ds.attrs['source']}")
    print(ds)


if __name__ == "__main__":
    main()
