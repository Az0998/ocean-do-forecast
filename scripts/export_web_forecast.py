#!/usr/bin/env python
"""Export lead-1 forecast fields as JSON for the GitHub Pages demo viewer.

Reads `results/products/forecast_lead1_latest.nc` (or rebuilds via export_forecast_product)
and writes `docs/data/forecast_demo.json` + a preview PNG under `docs/assets/`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import xarray as xr

from config import FIGS, PROCESSED, RESULTS, TABLES, ensure_dirs


def _to_list(a: np.ndarray) -> list:
    return np.round(np.asarray(a, dtype=float), 3).tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nc",
        type=Path,
        default=RESULTS / "products" / "forecast_lead1_latest.nc",
    )
    parser.add_argument("--rebuild", action="store_true", help="Run export_forecast_product first")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    ensure_dirs()

    if args.rebuild or not args.nc.exists():
        import subprocess

        cmd = [sys.executable, str(ROOT / "scripts" / "export_forecast_product.py")]
        if args.quick:
            cmd.append("--quick")
        subprocess.check_call(cmd, cwd=str(ROOT))

    ds = xr.open_dataset(args.nc)
    depths = ds["depth"].values.astype(float)
    lat = ds["lat"].values.astype(float)
    lon = ds["lon"].values.astype(float)
    oxy = ds["oxygen_forecast"].values.astype(float)
    clim = ds["oxygen_clim"].values.astype(float)
    anom = ds["oxygen_anom"].values.astype(float)

    # Surface-ish and mid levels for the web viewer
    depth_idxs = []
    for target in (10.0, 50.0, 100.0):
        depth_idxs.append(int(np.argmin(np.abs(depths - target))))
    depth_idxs = sorted(set(depth_idxs))

    levels = []
    for zi in depth_idxs:
        levels.append(
            {
                "depth_dbar": float(depths[zi]),
                "oxygen": _to_list(oxy[zi]),
                "clim": _to_list(clim[zi]),
                "anom": _to_list(anom[zi]),
            }
        )

    meta_path = TABLES / "forecast_product.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    payload = {
        "title": "East China Sea shelf · lead-1 DO forecast",
        "region_id": str(ds.attrs.get("region_id", meta.get("region", "east_china_sea_shelf"))),
        "init_time": str(ds.attrs.get("init_time", meta.get("init_time", ""))),
        "valid_time": str(ds.attrs.get("valid_time", meta.get("valid_time", ""))),
        "lead_months": int(ds.attrs.get("lead_months", 1)),
        "units": "µmol kg⁻¹",
        "disclaimer": str(
            ds.attrs.get(
                "disclaimer",
                "Development product on WOA-informed oxygen cube; not an operational warning.",
            )
        ),
        "test_rmse_holdout": float(
            ds.attrs.get("test_rmse_holdout", meta.get("test_rmse_holdout", float("nan")))
        ),
        "lat": _to_list(lat),
        "lon": _to_list(lon),
        "levels": levels,
        "stats": {
            "oxy_min": float(np.nanmin(oxy)),
            "oxy_max": float(np.nanmax(oxy)),
            "anom_min": float(np.nanmin(anom)),
            "anom_max": float(np.nanmax(anom)),
            "pred_mean": float(np.nanmean(oxy)),
        },
    }

    out_dir = ROOT / "docs" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "forecast_demo.json"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Preview PNG for static fallback
    import matplotlib.pyplot as plt

    zi0 = depth_idxs[0]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), dpi=160)
    im0 = axes[0].pcolormesh(lon, lat, oxy[zi0], shading="auto", cmap="viridis")
    axes[0].set_title(f"O₂ forecast · {depths[zi0]:.0f} dbar")
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04, label="µmol kg⁻¹")
    im1 = axes[1].pcolormesh(lon, lat, anom[zi0], shading="auto", cmap="RdBu_r")
    axes[1].set_title(f"Anomaly vs clim · {depths[zi0]:.0f} dbar")
    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04, label="µmol kg⁻¹")
    for ax in axes:
        ax.set_xlabel("Lon")
        ax.set_ylabel("Lat")
    fig.suptitle(
        f"Lead-1 product · init {payload['init_time']} → valid {payload['valid_time']}",
        fontsize=11,
    )
    fig.tight_layout()
    assets = ROOT / "docs" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    png = assets / "forecast_product_preview.png"
    fig.savefig(png)
    plt.close(fig)
    # also keep under results/figures
    FIGS.mkdir(parents=True, exist_ok=True)
    fig_png = FIGS / "forecast_product_preview.png"
    # rewrite quickly
    import shutil

    shutil.copy2(png, fig_png)

    print(f"[web] wrote {out_json}")
    print(f"[web] wrote {png}")


if __name__ == "__main__":
    main()
