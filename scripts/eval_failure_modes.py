#!/usr/bin/env python
"""Diagnose where the forecast fails: fronts, strong stratification, coastal shelf.

Trains a quick ST model on the physics cube, scores lead-1 absolute error on the
test set, and bins errors by:
  - horizontal front strength (|∇SST| / |∇O₂_clim|)
  - stratification (upper-column N²)
  - coastal proximity (distance to western shelf edge)

Writes `results/tables/failure_modes.md` + figures for the manuscript discussion.
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

from config import DEVICE, FIGS, SEED, TABLES, ensure_dirs, load_active_region
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
from src.stratification import stratification_index
from src.train_utils import predict_st, train_st_anom
from src.viz import plot_spatial_rmse


def _grad_mag(field: np.ndarray, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """field (..., Y, X) -> horizontal gradient magnitude on degrees grid."""
    dlat = np.gradient(lat)
    dlon = np.gradient(lon)
    # mean spacing
    dy = float(np.mean(np.abs(dlat))) if len(dlat) else 1.0
    dx = float(np.mean(np.abs(dlon))) if len(dlon) else 1.0
    gy, gx = np.gradient(field, dy, dx, axis=(-2, -1))
    return np.sqrt(gx**2 + gy**2).astype(np.float32)


def _tercile_labels(x: np.ndarray) -> tuple[np.ndarray, list[str]]:
    flat = x[np.isfinite(x)]
    if flat.size < 9:
        return np.zeros_like(x, dtype=int), ["all"]
    q1, q2 = np.nanpercentile(flat, [33.3, 66.7])
    lab = np.zeros(x.shape, dtype=int)
    lab[x >= q1] = 1
    lab[x >= q2] = 2
    return lab, ["low", "mid", "high"]


def main():
    parser = argparse.ArgumentParser()
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
    use_physics = "temp" in ds and "n2" in ds
    if not use_physics:
        raise SystemExit("Need regional_physics_cube.nc with temp/n2 for failure modes")

    fa = build_forecast_arrays(ds, leads=[1], use_physics=True)
    splits = split_arrays(fa)
    n_oxygen = int(splits["meta"]["n_oxygen"])
    mask = splits["meta"]["mask"]
    lat = ds["lat"].values.astype(float)
    lon = ds["lon"].values.astype(float)
    depths = ds["depth"].values.astype(float)

    stats = fit_norm_from_train(splits["train"]["y"][:, 0], splits["train"]["times"])
    stats.phys_mean, stats.phys_std = fit_phys_channel_stats(
        splits["train"]["x"], n_oxygen
    )

    x_tr = history_to_norm_anom(
        splits["train"]["x"], splits["train"]["hist_times"], stats, fa.x.shape[1], n_oxygen
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
    x_te = history_to_norm_anom(
        splits["test"]["x"], splits["test"]["hist_times"], stats, fa.x.shape[1], n_oxygen
    )
    y_te = splits["test"]["y"][:, 0]
    t_te = splits["test"]["times"]

    print(f"[fail] train ST epochs={args.epochs} device={device}")
    model = train_st_anom(
        x_tr, y_tr, x_va, y_va, mask, device, args.epochs, n_oxygen=n_oxygen
    )
    pred = denormalize_anom(predict_st(model, x_te, device), stats) + apply_clim(
        y_te, t_te, stats.clim
    )
    err = np.abs(pred - y_te)  # (N,Z,Y,X)

    # Physical diagnostics on test times from raw cube
    times = ds["time"].values
    # map each test target time to cube index
    t_idx = []
    for t in t_te:
        t_idx.append(int(np.argmin(np.abs(times.astype("datetime64[ns]") - np.datetime64(t)))))
    t_idx = np.asarray(t_idx)

    sst = ds["sst"].values[t_idx]  # (N,Y,X)
    n2 = ds["n2"].values[t_idx]  # (N,Z,Y,X)
    strat = stratification_index(n2)  # (N,Y,X)
    front = _grad_mag(sst, lat, lon)  # (N,Y,X)
    # coastal distance proxy: lon - lon_min
    lon_g = lon[None, None, :] - float(region["lon_min"])
    coastal = np.broadcast_to(np.exp(-((lon_g) / 3.0) ** 2), front.shape).astype(np.float32)

    # depth-mean absolute error
    err_xy = np.nanmean(err, axis=1)  # (N,Y,X)
    spatial = np.nanmean(err_xy, axis=0)
    plot_spatial_rmse(
        spatial,
        lat,
        lon,
        "Lead-1 |error| depth-mean · failure map",
        FIGS / "failure_spatial_abserr.png",
        cmap="magma",
    )

    def bin_report(name: str, driver: np.ndarray) -> list[dict]:
        # broadcast driver to err_xy if needed
        d = driver
        while d.ndim < err_xy.ndim:
            d = d[None, ...]
        labs, names = _tercile_labels(d)
        rows = []
        for i, lab_name in enumerate(names):
            sel = labs == i if len(names) > 1 else np.ones_like(labs, dtype=bool)
            vals = err_xy[sel]
            if vals.size == 0:
                continue
            rows.append(
                {
                    "driver": name,
                    "bin": lab_name,
                    "n_cells": int(vals.size),
                    "mae": float(np.nanmean(vals)),
                    "p90": float(np.nanpercentile(vals, 90)),
                }
            )
        return rows

    rows = []
    rows += bin_report("front_|gradSST|", front)
    rows += bin_report("stratification_N2", strat)
    rows += bin_report("coastal_proximity", coastal)

    # Depth profile of MAE
    depth_mae = [
        {"depth_dbar": float(d), "mae": float(np.nanmean(err[:, zi]))}
        for zi, d in enumerate(depths)
    ]

    # Thermocline proxy: depth of max N2
    n2_mean = np.nanmean(n2, axis=0)  # (Z,Y,X)
    z_thermo = depths[np.nanargmax(n2_mean, axis=0)]  # (Y,X)
    # error near thermocline depth vs elsewhere
    zi_near = np.argmin(np.abs(depths[:, None, None] - z_thermo[None, :, :]), axis=0)
    near_vals = []
    far_vals = []
    for n in range(err.shape[0]):
        for iy in range(err.shape[2]):
            for ix in range(err.shape[3]):
                z0 = int(zi_near[iy, ix])
                near_vals.append(err[n, z0, iy, ix])
                far = [err[n, z, iy, ix] for z in range(err.shape[1]) if z != z0]
                far_vals.extend(far)
    thermo_row = {
        "driver": "thermocline_depth_level",
        "bin": "at_max_N2",
        "n_cells": len(near_vals),
        "mae": float(np.nanmean(near_vals)),
        "p90": float(np.nanpercentile(near_vals, 90)),
    }
    other_row = {
        "driver": "thermocline_depth_level",
        "bin": "other_depths",
        "n_cells": len(far_vals),
        "mae": float(np.nanmean(far_vals)),
        "p90": float(np.nanpercentile(far_vals, 90)),
    }
    rows.extend([thermo_row, other_row])

    payload = {
        "region": region.get("id"),
        "epochs": args.epochs,
        "test_mae": float(np.nanmean(err)),
        "bins": rows,
        "depth_mae": depth_mae,
        "notes": [
            "front: horizontal |∇SST| terciles",
            "stratification: upper-column N² terciles",
            "coastal: exp(-Δlon/3°) proximity to western boundary",
            "thermocline: MAE at depth of max N² vs other depths",
        ],
    }
    json_path = TABLES / "failure_modes.json"
    md_path = TABLES / "failure_modes.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Failure-mode diagnosis (lead-1 ST, physics cube)",
        "",
        f"Region: `{region.get('id')}` · test MAE = `{payload['test_mae']:.3f}` µmol kg⁻¹",
        "",
        "| Driver | Bin | N cells | MAE | P90 |",
        "|---|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['driver']} | {r['bin']} | {r['n_cells']} | {r['mae']:.3f} | {r['p90']:.3f} |"
        )
    lines += [
        "",
        "## Depth MAE",
        "",
        "| Depth (dbar) | MAE |",
        "|---:|---:|",
    ]
    for d in depth_mae:
        lines.append(f"| {d['depth_dbar']:.0f} | {d['mae']:.3f} |")
    lines += [
        "",
        "## Interpretation notes",
        "",
        "- Higher MAE in **high front** / **high stratification** bins implicates unresolved frontal and pycnocline processes.",
        "- Elevated **coastal** MAE matches river–shelf hypoxia gradients that are hard to learn from sparse columns.",
        "- Thermocline-level MAE vs other depths tests whether vertical structure errors concentrate at the pycnocline.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # Bar figure
    import matplotlib.pyplot as plt

    focus = [r for r in rows if r["driver"] in ("front_|gradSST|", "stratification_N2", "coastal_proximity")]
    if focus:
        labels = [f"{r['driver'].split('_')[0]}:{r['bin']}" for r in focus]
        vals = [r["mae"] for r in focus]
        fig, ax = plt.subplots(figsize=(8.5, 3.6), dpi=160)
        ax.bar(range(len(labels)), vals, color="#0f5f78")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
        ax.set_ylabel("Lead-1 MAE (µmol kg⁻¹)")
        ax.set_title("Error by physical regime (terciles)")
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(FIGS / "failure_mode_bins.png")
        plt.close(fig)

    print(f"[fail] wrote {md_path}")
    print(f"[fail] figures in {FIGS}")


if __name__ == "__main__":
    main()
