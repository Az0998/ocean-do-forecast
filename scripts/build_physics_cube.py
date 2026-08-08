#!/usr/bin/env python
"""Build a multi-source physics+oxygen cube on the regional oxygen grid.

Sources (no GOBAI / no CMEMS login):
  - oxygen: existing regional_oxygen_cube.nc (woa_informed / demo)
  - temp/salt/N2: WOA18 annual T/S (+ mild seasonal modulation)
  - sst: NOAA OISST monthly
  - wind/t2m: Open-Meteo ERA5 archive (or offline synth)

Output: data/processed/regional_physics_cube.nc
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import xarray as xr

from config import PROCESSED, SEED, ensure_dirs, load_active_region
from src.stratification import buoyancy_freq_sq


def _regrid_xy(da: xr.DataArray, lat: np.ndarray, lon: np.ndarray) -> xr.DataArray:
    return da.interp(lat=lat, lon=lon, method="linear")


def _seasonal_modulate(clim_zyx: np.ndarray, times: pd.DatetimeIndex, amp: float, phase: int) -> np.ndarray:
    """clim (Z,Y,X) -> (T,Z,Y,X) with cos seasonality."""
    out = np.empty((len(times),) + clim_zyx.shape, dtype=np.float32)
    for i, t in enumerate(times):
        fac = 1.0 + amp * np.cos(2 * np.pi * (t.month - phase) / 12.0)
        out[i] = clim_zyx * fac
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--oxygen", type=Path, default=PROCESSED / "regional_oxygen_cube.nc")
    parser.add_argument("--start", default="2004-01")
    parser.add_argument("--end", default="2022-12")
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    rng = np.random.default_rng(SEED)

    if not args.oxygen.exists():
        raise SystemExit(f"Missing oxygen cube: {args.oxygen}. Build woa_informed/demo first.")

    oxy_ds = xr.open_dataset(args.oxygen)
    oxy = oxy_ds["oxygen"].transpose("time", "depth", "lat", "lon")
    times = pd.to_datetime(oxy["time"].values)
    # clip to requested window if needed
    times_full = pd.date_range(args.start, args.end, freq="MS")
    oxy = oxy.sel(time=slice(times_full[0], times_full[-1]))
    times = pd.to_datetime(oxy["time"].values)
    lat = oxy["lat"].values.astype(float)
    lon = oxy["lon"].values.astype(float)
    depth = oxy["depth"].values.astype(float)
    T, Z, Y, X = oxy.shape

    # --- T/S from WOA ---
    ts_path = PROCESSED / "woa18_ts_region.nc"
    if ts_path.exists():
        ts = xr.open_dataset(ts_path)
        temp_clim = _regrid_xy(ts["temp"], lat, lon).interp(depth=depth, method="linear").values
        salt_clim = _regrid_xy(ts["salt"], lat, lon).interp(depth=depth, method="linear").values
        temp_clim = np.nan_to_num(temp_clim, nan=np.nanmean(temp_clim))
        salt_clim = np.nan_to_num(salt_clim, nan=np.nanmean(salt_clim))
        temp = _seasonal_modulate(temp_clim.astype(np.float32), times, amp=0.08, phase=8)
        salt = _seasonal_modulate(salt_clim.astype(np.float32), times, amp=0.03, phase=2)
        # small AR noise so models can learn anomalies
        eps_t = rng.normal(0, 0.15, size=temp.shape).astype(np.float32)
        eps_s = rng.normal(0, 0.05, size=salt.shape).astype(np.float32)
        for t in range(1, T):
            eps_t[t] = 0.7 * eps_t[t - 1] + 0.3 * eps_t[t]
            eps_s[t] = 0.7 * eps_s[t - 1] + 0.3 * eps_s[t]
        temp = temp + eps_t
        salt = salt + eps_s
        ts_src = "woa18_ts_seasonal"
    else:
        print("[physics] woa18_ts_region.nc missing — synth T/S from latitude/depth")
        lon_g, lat_g = np.meshgrid(lon, lat, indexing="xy")
        temp_clim = np.zeros((Z, Y, X), dtype=np.float32)
        salt_clim = np.zeros((Z, Y, X), dtype=np.float32)
        for zi, d in enumerate(depth):
            temp_clim[zi] = 22.0 - 0.25 * (lat_g - 26) - 0.02 * d
            salt_clim[zi] = 33.5 + 0.01 * (lon_g - 118) + 0.001 * d
        temp = _seasonal_modulate(temp_clim, times, amp=0.1, phase=8)
        salt = _seasonal_modulate(salt_clim, times, amp=0.04, phase=2)
        ts_src = "synth_ts"

    n2 = buoyancy_freq_sq(temp, salt, depth)

    # --- SST OISST ---
    sst = np.full((T, Y, X), np.nan, dtype=np.float32)
    oisst_path = PROCESSED / "oisst_monthly_region.nc"
    if oisst_path.exists():
        oi = xr.open_dataset(oisst_path)
        sst_da = _regrid_xy(oi["sst"], lat, lon)
        sst_da = sst_da.sel(time=times, method="nearest")
        sst = np.asarray(sst_da.values, dtype=np.float32)
        # fill gaps with surface temp
        bad = ~np.isfinite(sst)
        sst[bad] = temp[:, 0][bad]
        sst_src = "noaa_oisst_v2_monthly"
    else:
        sst = temp[:, 0].copy()
        sst_src = "temp_surface_proxy"

    # --- wind ---
    wind = np.zeros((T, Y, X), dtype=np.float32)
    u10 = np.zeros_like(wind)
    v10 = np.zeros_like(wind)
    t2m = np.zeros_like(wind)
    wind_path = PROCESSED / "openmeteo_wind_region.nc"
    if wind_path.exists():
        wds = xr.open_dataset(wind_path)
        for name, arr in (
            ("wind_speed", wind),
            ("u10", u10),
            ("v10", v10),
            ("t2m", t2m),
        ):
            if name not in wds:
                continue
            da = _regrid_xy(wds[name], lat, lon).sel(time=times, method="nearest")
            vals = np.asarray(da.values, dtype=np.float32)
            arr[:] = vals
        wind_src = str(wds.attrs.get("source", "openmeteo"))
    else:
        months = times.month.values
        for i, m in enumerate(months):
            summer = 0.5 * (1 + np.cos(2 * np.pi * (m - 7) / 12))
            u10[i] = 2.0 + 3.0 * summer
            v10[i] = -1.5 + 4.0 * summer
            wind[i] = np.sqrt(u10[i] ** 2 + v10[i] ** 2)
            t2m[i] = 18.0 + 10.0 * np.cos(2 * np.pi * (m - 8) / 12)
        wind_src = "monsoon_synth"

    ds = xr.Dataset(
        {
            "oxygen": (("time", "depth", "lat", "lon"), oxy.values.astype(np.float32)),
            "temp": (("time", "depth", "lat", "lon"), temp),
            "salt": (("time", "depth", "lat", "lon"), salt),
            "n2": (("time", "depth", "lat", "lon"), n2),
            "sst": (("time", "lat", "lon"), sst),
            "wind_speed": (("time", "lat", "lon"), wind),
            "u10": (("time", "lat", "lon"), u10),
            "v10": (("time", "lat", "lon"), v10),
            "t2m": (("time", "lat", "lon"), t2m),
        },
        coords={"time": times, "depth": depth, "lat": lat, "lon": lon},
        attrs={
            "source": "physics_multidrive",
            "region_id": region.get("id"),
            "oxygen_source": oxy_ds.attrs.get("source"),
            "ts_source": ts_src,
            "sst_source": sst_src,
            "wind_source": wind_src,
            "note": "GLORYS/CMEMS optional later; GODAS/WOA+OISST+Open-Meteo used as free substitutes.",
        },
    )
    dest = PROCESSED / "regional_physics_cube.nc"
    ds.to_netcdf(dest)
    print(f"[physics] wrote {dest}")
    print(f"  sources: oxy={ds.attrs['oxygen_source']} ts={ts_src} sst={sst_src} wind={wind_src}")
    print(f"  shape oxygen={oxy.shape}")


if __name__ == "__main__":
    main()
