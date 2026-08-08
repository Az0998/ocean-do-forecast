#!/usr/bin/env python
"""Tiny forecast demo: train a quick ST model and emit next-lead field stats + PNG.

Usage:
  py -3.12 scripts/forecast_demo.py --quick
  py -3.12 scripts/forecast_demo.py --physics --quick
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from config import DEVICE, FIGS, LEADS_MONTHS, PROCESSED, SEED, TABLES, ensure_dirs, load_active_region
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
from src.viz import plot_spatial_rmse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--physics", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--lead-index", type=int, default=0)
    args = parser.parse_args()
    if args.quick:
        args.epochs = min(args.epochs, 6)

    ensure_dirs()
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    region = load_active_region()
    device = DEVICE if torch.cuda.is_available() and DEVICE == "cuda" else "cpu"
    ds = load_or_build_cube(region, prefer_demo=True, prefer_physics=args.physics)
    use_physics = args.physics and "temp" in ds
    fa = build_forecast_arrays(ds, leads=LEADS_MONTHS, use_physics=use_physics)
    splits = split_arrays(fa)
    n_oxygen = int(splits["meta"]["n_oxygen"])
    mask = splits["meta"]["mask"]

    stats = fit_norm_from_train(splits["train"]["y"][:, 0], splits["train"]["times"])
    if use_physics:
        stats.phys_mean, stats.phys_std = fit_phys_channel_stats(
            splits["train"]["x"], n_oxygen
        )

    li = args.lead_index
    x_tr = history_to_norm_anom(
        splits["train"]["x"], splits["train"]["hist_times"], stats, fa.x.shape[1], n_oxygen
    )
    y_tr = normalize_anom(
        to_anomaly(splits["train"]["y"][:, li], splits["train"]["times"], stats.clim),
        stats,
    )
    x_va = history_to_norm_anom(
        splits["val"]["x"], splits["val"]["hist_times"], stats, fa.x.shape[1], n_oxygen
    )
    y_va = normalize_anom(
        to_anomaly(splits["val"]["y"][:, li], splits["val"]["times"], stats.clim), stats
    )
    x_te = history_to_norm_anom(
        splits["test"]["x"], splits["test"]["hist_times"], stats, fa.x.shape[1], n_oxygen
    )
    y_te = splits["test"]["y"][:, li]
    t_te = splits["test"]["times"]

    print(f"[demo] training ST epochs={args.epochs} physics={use_physics} device={device}")
    model = train_st_anom(
        x_tr, y_tr, x_va, y_va, mask, device, args.epochs, n_oxygen=n_oxygen
    )
    pred = denormalize_anom(predict_st(model, x_te, device), stats) + apply_clim(
        y_te, t_te, stats.clim
    )
    rmse = float(np.sqrt(np.nanmean((pred - y_te) ** 2)))
    out = {
        "region": region.get("id"),
        "lead_months": LEADS_MONTHS[li],
        "physics": use_physics,
        "test_rmse": rmse,
        "pred_mean": float(np.nanmean(pred)),
        "true_mean": float(np.nanmean(y_te)),
        "n_test": int(len(y_te)),
    }
    TABLES.joinpath("forecast_demo.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    # spatial error map for last test sample mean over depth
    err = np.nanmean(np.abs(pred - y_te), axis=(0, 1))
    plot_spatial_rmse(
        err,
        ds["lat"].values,
        ds["lon"].values,
        f"Forecast demo |MAE| · lead={LEADS_MONTHS[li]}m",
        FIGS / "forecast_demo_mae.png",
    )
    print(json.dumps(out, indent=2))
    print(f"[demo] figure -> {FIGS / 'forecast_demo_mae.png'}")


if __name__ == "__main__":
    main()
