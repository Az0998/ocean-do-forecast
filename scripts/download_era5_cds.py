#!/usr/bin/env python
"""Optional ERA5 download via CDS API (requires ~/.cdsapirc + accepted licences).

Dataset: reanalysis-era5-single-levels-monthly-means
Vars: 10m u/v, 2m temperature, SST
Area: active region (N/W/S/E)

If cdsapi or credentials are missing, exits with setup instructions (no crash loop).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import PROCESSED, RAW, ensure_dirs, load_active_region


SETUP = """
CDS / ERA5 setup (one-time):
  1) Create account at https://cds.climate.copernicus.eu/
  2) Accept licences for ERA5 monthly means
  3) Create %USERPROFILE%\\.cdsapirc with:
       url: https://cds.climate.copernicus.eu/api
       key: <UID>:<APIKEY>
  4) pip install cdsapi
  5) py -3.12 scripts/download_era5_cds.py

Until then, use Open-Meteo (ERA5-backed, no token):
  py -3.12 scripts/download_openmeteo_wind.py --match-oxygen-grid
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2004")
    parser.add_argument("--end", default="2022")
    args = parser.parse_args()
    ensure_dirs()
    cdsapirc = Path.home() / ".cdsapirc"
    try:
        import cdsapi
    except ImportError:
        print("[era5] cdsapi not installed.")
        print(SETUP)
        raise SystemExit(2)
    if not cdsapirc.exists():
        print(f"[era5] missing {cdsapirc}")
        print(SETUP)
        raise SystemExit(2)

    region = load_active_region()
    out_dir = RAW / "era5"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"era5_monthly_{region.get('id')}_{args.start}_{args.end}.nc"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"[era5] exists: {dest}")
    else:
        c = cdsapi.Client()
        years = [str(y) for y in range(int(args.start), int(args.end) + 1)]
        months = [f"{m:02d}" for m in range(1, 13)]
        print(f"[era5] requesting monthly means -> {dest}")
        c.retrieve(
            "reanalysis-era5-single-levels-monthly-means",
            {
                "product_type": "monthly_averaged_reanalysis",
                "variable": [
                    "10m_u_component_of_wind",
                    "10m_v_component_of_wind",
                    "2m_temperature",
                    "sea_surface_temperature",
                ],
                "year": years,
                "month": months,
                "time": "00:00",
                "area": [
                    float(region["lat_max"]),
                    float(region["lon_min"]),
                    float(region["lat_min"]),
                    float(region["lon_max"]),
                ],
                "format": "netcdf",
            },
            str(dest),
        )

    import numpy as np
    import xarray as xr

    ds = xr.open_dataset(dest)
    rename = {}
    for a, b in [
        ("longitude", "lon"),
        ("latitude", "lat"),
        ("u10", "u10"),
        ("v10", "v10"),
        ("t2m", "t2m"),
        ("sst", "sst"),
    ]:
        if a in ds and a != b:
            rename[a] = b
    # CDS short names vary
    for cand, std in [
        ("u10", "u10"),
        ("10u", "u10"),
        ("v10", "v10"),
        ("10v", "v10"),
        ("t2m", "t2m"),
        ("2t", "t2m"),
        ("sst", "sst"),
    ]:
        if cand in ds and std not in ds and cand != std:
            rename[cand] = std
    if rename:
        ds = ds.rename(rename)
    if "u10" in ds and "v10" in ds:
        ds["wind_speed"] = np.sqrt(ds["u10"] ** 2 + ds["v10"] ** 2)
    ds.attrs.update({"source": "era5_cds_monthly", "region_id": region.get("id")})
    # also write wind-shaped product for build_physics_cube
    wind_vars = [v for v in ("u10", "v10", "wind_speed", "t2m") if v in ds]
    out = ds[wind_vars]
    processed = PROCESSED / "era5_wind_region.nc"
    out.to_netcdf(processed)
    # optional: override openmeteo path for drop-in use
    dropin = PROCESSED / "openmeteo_wind_region.nc"
    out.to_netcdf(dropin)
    print(f"[era5] wrote {processed} and refreshed {dropin}")


if __name__ == "__main__":
    main()
