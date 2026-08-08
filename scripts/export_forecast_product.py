#!/usr/bin/env python
"""Export a lightweight operational forecast NetCDF + JSON sidecar.

Trains a quick ST model on the physics cube and writes the next lead-1 field
relative to the last available time in the cube.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import torch
import xarray as xr

from config import DEVICE, PROCESSED, RESULTS, SEED, TABLES, ensure_dirs, load_active_region
from src.gobai_data import load_or_build_cube
from src.normalize import (
    apply_clim,
    denormalize_anom,
    fit_norm_from_train,
    fit_phys_channel_stats,
    history_to_norm_anom,
    normalize_anom,
    to_anomaly,
)
from src.samples import build_forecast_arrays, split_arrays
from src.train_utils import predict_st, train_st_anom


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--physics", action="store_true", default=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    if args.quick:
        args.epochs = min(args.epochs, 6)

    ensure_dirs()
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    region = load_active_region()
    device = DEVICE if torch.cuda.is_available() and DEVICE == "cuda" else "cpu"
    ds = load_or_build_cube(region, prefer_demo=False, prefer_physics=True)
    use_physics = "temp" in ds
    fa = build_forecast_arrays(ds, leads=[1], use_physics=use_physics)
    splits = split_arrays(fa)
    n_oxygen = int(splits["meta"]["n_oxygen"])
    mask = splits["meta"]["mask"]

    stats = fit_norm_from_train(splits["train"]["y"][:, 0], splits["train"]["times"])
    if use_physics:
        stats.phys_mean, stats.phys_std = fit_phys_channel_stats(
            splits["train"]["x"], n_oxygen
        )

    x_tr = history_to_norm_anom(
        splits["train"]["x"],
        splits["train"]["hist_times"],
        stats,
        fa.x.shape[1],
        n_oxygen,
    )
    y_tr = normalize_anom(
        to_anomaly(splits["train"]["y"][:, 0], splits["train"]["times"], stats.clim),
        stats,
    )
    x_va = history_to_norm_anom(
        splits["val"]["x"], splits["val"]["hist_times"], stats, fa.x.shape[1], n_oxygen
    )
    y_va = normalize_anom(
        to_anomaly(splits["val"]["y"][:, 0], splits["val"]["times"], stats.clim), stats
    )

    print(f"[product] train ST epochs={args.epochs} device={device}")
    model = train_st_anom(
        x_tr, y_tr, x_va, y_va, mask, device, args.epochs, n_oxygen=n_oxygen
    )

    # Use the last sample in the full series as "now"
    x_all = history_to_norm_anom(fa.x, fa.hist_times, stats, fa.x.shape[1], n_oxygen)
    pred_anom = denormalize_anom(predict_st(model, x_all[-1:], device), stats)
    last_time = pd.Timestamp(fa.times[-1])
    valid_time = last_time + pd.DateOffset(months=1)
    clim_field = apply_clim(
        np.zeros_like(pred_anom), np.array([valid_time.to_datetime64()]), stats.clim
    )
    pred = pred_anom + clim_field

    # Holdout test RMSE for the sidecar
    x_te = history_to_norm_anom(
        splits["test"]["x"], splits["test"]["hist_times"], stats, fa.x.shape[1], n_oxygen
    )
    y_te = splits["test"]["y"][:, 0]
    t_te = splits["test"]["times"]
    pred_te = denormalize_anom(predict_st(model, x_te, device), stats) + apply_clim(
        y_te, t_te, stats.clim
    )
    test_rmse = float(np.sqrt(np.nanmean((pred_te - y_te) ** 2)))

    out_dir = RESULTS / "products"
    out_dir.mkdir(parents=True, exist_ok=True)
    field = pred[0]
    product = xr.Dataset(
        {
            "oxygen_forecast": (("depth", "lat", "lon"), field.astype(np.float32)),
            "oxygen_clim": (("depth", "lat", "lon"), clim_field[0].astype(np.float32)),
            "oxygen_anom": (("depth", "lat", "lon"), pred_anom[0].astype(np.float32)),
        },
        coords={
            "time": [valid_time.to_datetime64()],
            "depth": ds["depth"].values,
            "lat": ds["lat"].values,
            "lon": ds["lon"].values,
        },
        attrs={
            "title": "Ocean-DO-Forecast lead-1 product",
            "region_id": region.get("id"),
            "init_time": str(last_time.date()),
            "valid_time": str(valid_time.date()),
            "lead_months": 1,
            "model": "st_transformer",
            "physics": int(bool(use_physics)),
            "test_rmse_holdout": float(test_rmse),
            "units": "umol kg-1",
            "disclaimer": "Development product on WOA-informed oxygen cube; not an operational warning.",
        },
    )
    nc_path = out_dir / "forecast_lead1_latest.nc"
    product.to_netcdf(nc_path)

    side = {
        "region": region.get("id"),
        "init_time": str(last_time.date()),
        "valid_time": str(valid_time.date()),
        "lead_months": 1,
        "physics": use_physics,
        "test_rmse_holdout": test_rmse,
        "pred_mean": float(np.nanmean(field)),
        "clim_mean": float(np.nanmean(clim_field)),
        "path": str(nc_path.relative_to(ROOT)).replace("\\", "/"),
    }
    json_path = TABLES / "forecast_product.json"
    json_path.write_text(json.dumps(side, indent=2), encoding="utf-8")
    print(f"[product] wrote {nc_path}")
    print(f"[product] wrote {json_path}")
    print(f"[product] holdout RMSE={test_rmse:.3f} valid={valid_time.date()}")


if __name__ == "__main__":
    main()
