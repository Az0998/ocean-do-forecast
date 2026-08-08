"""GOBAI-O2 regional cube I/O + demo cube generator.

If a real GOBAI NetCDF is present under data/raw/gobai/, we subset it.
Otherwise `build_demo_cube` creates a physically-plausible monthly DO field
for pipeline development (clearly flagged as demo).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from config import DEPTH_LEVELS_DBAR, PROCESSED, RAW


def gobai_dir() -> Path:
    return RAW / "gobai"


def find_gobai_files() -> list[Path]:
    d = gobai_dir()
    if not d.exists():
        return []
    files = sorted(d.rglob("*.nc"))
    return files


def _pick_oxygen_name(ds: xr.Dataset) -> str:
    for cand in ("oxygen", "o2", "dissolved_oxygen", "O2", "oxy"):
        if cand in ds:
            return cand
    # fallback: first data var with oxygen-ish attrs
    for name, da in ds.data_vars.items():
        long_name = str(da.attrs.get("long_name", "")).lower()
        if "oxygen" in long_name or "o2" in name.lower():
            return name
    raise KeyError(f"No oxygen variable in {list(ds.data_vars)}")


def load_regional_cube(
    region: dict[str, Any],
    depths: list[float] | None = None,
) -> xr.Dataset:
    files = find_gobai_files()
    if not files:
        raise FileNotFoundError(
            f"No GOBAI NetCDF under {gobai_dir()}. "
            "Run scripts/download_gobai.py or scripts/build_demo_cube.py"
        )
    ds = xr.open_mfdataset([str(f) for f in files], combine="by_coords")
    o2_name = _pick_oxygen_name(ds)
    # normalize coordinate names
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
    if rename:
        ds = ds.rename(rename)
    lon0, lon1 = region["lon_min"], region["lon_max"]
    lat0, lat1 = region["lat_min"], region["lat_max"]
    ds = ds.sel(lon=slice(lon0, lon1), lat=slice(lat0, lat1))
    if "depth" in ds.dims and depths:
        ds = ds.sel(depth=depths, method="nearest")
    out = ds[[o2_name]].rename({o2_name: "oxygen"})
    out.attrs["source"] = "gobai"
    out.attrs["source_files"] = [str(f) for f in files]
    return out.load()


def build_demo_cube(
    region: dict[str, Any],
    start: str = "2004-01",
    end: str = "2022-12",
    depths: list[float] | None = None,
    seed: int = 42,
) -> xr.Dataset:
    """Synthetic monthly DO cube with seasonal cycle, depth decay, coastal hypoxia.

    Units: µmol/kg. For pipeline smoke tests only — not for publication claims.
    """
    depths = depths or DEPTH_LEVELS_DBAR
    rng = np.random.default_rng(seed)
    lons = np.arange(region["lon_min"] + 0.5, region["lon_max"], 1.0)
    lats = np.arange(region["lat_min"] + 0.5, region["lat_max"], 1.0)
    times = xr.date_range(start, end, freq="MS")
    lon_g, lat_g = np.meshgrid(lons, lats, indexing="xy")
    # coastal proximity proxy: distance to western boundary (shelf)
    coastal = np.exp(-((lon_g - region["lon_min"]) / 3.0) ** 2)

    T, Z, Y, X = len(times), len(depths), len(lats), len(lons)
    oxygen = np.zeros((T, Z, Y, X), dtype=np.float32)
    # AR(1) anomaly field — gives forecast models something beyond pure climatology
    anom = np.zeros((Z, Y, X), dtype=np.float32)
    month = times.month
    for ti, m in enumerate(month):
        season = 15.0 * np.sin(2 * np.pi * (m - 3) / 12.0)  # summer lower O2
        innov = rng.normal(0, 4.0, size=(Z, Y, X)).astype(np.float32)
        # coastal-biased innovation (hypoxia event persistence)
        innov = innov - 8.0 * coastal[None, :, :] * (rng.random() < 0.08)
        anom = 0.75 * anom + innov
        for zi, d in enumerate(depths):
            depth_decay = 220.0 * np.exp(-d / 180.0) + 40.0
            lat_term = 10.0 * ((lat_g - lat_g.mean()) / 5.0)
            hypoxia = -55.0 * coastal * np.exp(-d / 80.0) * max(
                0.0, np.sin(2 * np.pi * (m - 6) / 12.0)
            )
            trend = -0.15 * (times[ti].year - 2004)
            field = (
                depth_decay
                + season
                + lat_term
                + hypoxia
                + trend
                + anom[zi] * np.exp(-d / 250.0)
            )
            oxygen[ti, zi] = np.clip(field, 5.0, 350.0)

    ds = xr.Dataset(
        {
            "oxygen": (
                ("time", "depth", "lat", "lon"),
                oxygen,
                {"units": "umol/kg", "long_name": "dissolved oxygen (demo)"},
            )
        },
        coords={
            "time": times,
            "depth": ("depth", np.array(depths, dtype=np.float32), {"units": "dbar"}),
            "lat": ("lat", lats.astype(np.float32)),
            "lon": ("lon", lons.astype(np.float32)),
        },
        attrs={
            "source": "demo",
            "warning": "Synthetic field for pipeline development only",
            "region": region.get("name", region.get("id", "unknown")),
        },
    )
    return ds


def save_cube(ds: xr.Dataset, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(path)
    return path


def load_or_build_cube(
    region: dict[str, Any],
    prefer_demo: bool = False,
    cube_path: Path | None = None,
    prefer_physics: bool = False,
) -> xr.Dataset:
    """Load regional cube.

    Priority:
      1) GOBAI (unless prefer_demo)
      2) regional_physics_cube.nc if prefer_physics
      3) existing oxygen cube path
      4) build demo
    """
    cube_path = cube_path or (PROCESSED / "regional_oxygen_cube.nc")
    if not prefer_demo:
        try:
            return load_regional_cube(region)
        except FileNotFoundError:
            pass
    if prefer_physics:
        phys = PROCESSED / "regional_physics_cube.nc"
        if phys.exists():
            return xr.open_dataset(phys).load()
    if cube_path.exists():
        return xr.open_dataset(cube_path).load()
    ds = build_demo_cube(region)
    save_cube(ds, cube_path)
    return ds
