#!/usr/bin/env python
"""Where does the lead-1 ST-vs-climatology tax appear?

Lake 10/20/30% is a hide rate on observed cells. Ocean `keep_ratio=0.25` is not
that quantity: spatial masks are constant in time, and `station` ignore
keep_ratio (keep = n_stations * Z / n_water). This scan therefore has two axes:

  point keep_ratio in {0.10, 0.20, 0.25, 0.30, 0.50}  — MCAR-like voxel keep
  station n_stations in {4, 8, 16, 24}               — column geometry
    (keep ≈ 0.044, 0.089, 0.178, 0.267 on this 450-voxel water mask)

Sensor is omitted: Z=5 so 10/20/25% all keep 1 layer (effective 0.20).
Same Mask-View seeds as run_multilead.py. ST: 8-epoch ablation recipe, no LSTM.
Paired month-block bootstrap of Δ = clim RMSE − ST RMSE.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from config import (
    DEVICE,
    LEADS_MONTHS,
    PROCESSED,
    SEED,
    TABLES,
    ensure_dirs,
    load_active_region,
)
from src.gobai_data import load_or_build_cube
from src.metrics import rmse
from src.models.baselines import (
    climatology_predict,
    evaluate_regression,
    fill_with_climatology,
    last_observed_persist,
)
from src.normalize import (
    apply_clim,
    denormalize_anom,
    fit_norm_from_train,
    fit_phys_channel_stats,
)
from src.samples import build_forecast_arrays, split_arrays
from src.sparse_mask import apply_mask, make_batch_masks
from src.train_utils import predict_st, train_st_anom

from run_multilead import _oxygen_history, prepare_lead, set_seed

EPOCHS = 8
N_BOOT = 200
LEAD = 1
# (pattern, keep_ratio, n_stations) — keep_ratio unused for station/none
SCANS = (
    ("none", 1.00, 8),
    ("point", 0.10, 8),
    ("point", 0.20, 8),
    ("point", 0.25, 8),
    ("point", 0.30, 8),
    ("point", 0.50, 8),
    ("station", 0.25, 4),
    ("station", 0.25, 8),
    ("station", 0.25, 16),
    ("station", 0.25, 24),
)


def oxygen_keep(x_raw, pattern, keep_ratio, n_stations, seed, n_oxygen, lat, lon, argo_path):
    n, h, _c, y, x = x_raw.shape
    z = n_oxygen
    if pattern == "none":
        return np.ones((n, h, z, y, x), dtype=np.float32)
    m = make_batch_masks(
        x_raw,
        pattern,
        keep_ratio,
        n_stations,
        seed=seed,
        n_oxygen=n_oxygen,
        lat=lat,
        lon=lon,
        argo_stations_path=argo_path,
    )
    return np.broadcast_to(m, (n, h, z, y, x)).copy()


def keep_frac_water(keep: np.ndarray, water: np.ndarray) -> float:
    w = water > 0.5
    k = keep[:, :, w]
    return float(k.mean()) if k.size else float("nan")


def _mask_water(y, pred, water):
    m = water > 0
    while m.ndim < y.ndim:
        m = m[None, ...]
    m = np.broadcast_to(m, y.shape)
    return np.where(m, y, np.nan), np.where(m, pred, np.nan)


def paired_delta(y, pred_st, pred_clim, water, n_boot, seed):
    y, pred_st = _mask_water(y, pred_st, water)
    y, pred_clim = _mask_water(y, pred_clim, water)
    rng = np.random.default_rng(seed)
    n = y.shape[0]
    d_delta = []
    n_st_better = 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        rs = rmse(y[idx], pred_st[idx])
        rc = rmse(y[idx], pred_clim[idx])
        d_delta.append(rc - rs)
        if rs < rc:
            n_st_better += 1
    arr = np.asarray(d_delta, dtype=float)
    return {
        "delta_clim_minus_st_p05": float(np.percentile(arr, 5)),
        "delta_clim_minus_st_p50": float(np.percentile(arr, 50)),
        "delta_clim_minus_st_p95": float(np.percentile(arr, 95)),
        "frac_boot_st_better": float(n_st_better / n_boot),
        "st_significantly_better": bool(np.percentile(arr, 5) > 0),
        "n_boot": int(n_boot),
    }


def main() -> None:
    ensure_dirs()
    set_seed()
    region = load_active_region()
    device = DEVICE if __import__("torch").cuda.is_available() and DEVICE == "cuda" else "cpu"
    ds = load_or_build_cube(region, prefer_demo=False, prefer_physics=True)
    fa = build_forecast_arrays(ds, leads=LEADS_MONTHS, use_physics=True)
    splits = split_arrays(fa)
    water = splits["meta"]["mask"]
    n_oxygen = int(splits["meta"]["n_oxygen"])
    lat = ds["lat"].values
    lon = ds["lon"].values
    argo_path = PROCESSED / "argo_stations.json"
    stats = fit_norm_from_train(splits["train"]["y"][:, 0], splits["train"]["times"])
    pmean, pstd = fit_phys_channel_stats(splits["train"]["x"], n_oxygen)
    stats.phys_mean = pmean
    stats.phys_std = pstd
    li = LEADS_MONTHS.index(LEAD)
    n_water = int((water > 0.5).sum())
    rows = []

    for pattern, keep_ratio, n_stations in SCANS:
        print(
            f"\n===== {pattern} keep_ratio={keep_ratio} n_stations={n_stations} ====="
        )
        data = prepare_lead(splits, li, stats, n_oxygen)
        x_tr, y_tr_n, y_tr, t_tr, x_tr_raw = data["train"]
        x_va, y_va_n, y_va, t_va, x_va_raw = data["val"]
        x_te, y_te_n, y_te, t_te, x_te_raw = data["test"]
        if pattern != "none":
            m_tr = make_batch_masks(
                x_tr, pattern, keep_ratio, n_stations, seed=SEED + LEAD,
                n_oxygen=n_oxygen, lat=lat, lon=lon, argo_stations_path=argo_path,
            )
            m_va = make_batch_masks(
                x_va, pattern, keep_ratio, n_stations, seed=SEED + 100 + LEAD,
                n_oxygen=n_oxygen, lat=lat, lon=lon, argo_stations_path=argo_path,
            )
            m_te = make_batch_masks(
                x_te, pattern, keep_ratio, n_stations, seed=SEED + 200 + LEAD,
                n_oxygen=n_oxygen, lat=lat, lon=lon, argo_stations_path=argo_path,
            )
            x_tr = apply_mask(x_tr, m_tr)
            x_va = apply_mask(x_va, m_va)
            x_te = apply_mask(x_te, m_te)

        clim = climatology_predict(y_tr, t_tr, t_te)
        keep = oxygen_keep(
            x_te_raw, pattern, keep_ratio, n_stations,
            SEED + 200 + LEAD, n_oxygen, lat, lon, argo_path,
        )
        kf = keep_frac_water(keep, water)
        locf = fill_with_climatology(
            last_observed_persist(_oxygen_history(x_te_raw, n_oxygen), keep), clim
        )
        st = train_st_anom(
            x_tr, y_tr_n, x_va, y_va_n, water, device, EPOCHS, n_oxygen=n_oxygen
        )
        pred_st = denormalize_anom(predict_st(st, x_te, device), stats) + apply_clim(
            y_te, t_te, stats.clim
        )
        st_pt = evaluate_regression(y_te, pred_st, water)["rmse"]
        clim_pt = evaluate_regression(y_te, clim, water)["rmse"]
        locf_pt = evaluate_regression(y_te, locf, water)["rmse"]
        boot = paired_delta(y_te, pred_st, clim, water, N_BOOT, SEED + 17)
        winner = "st_transformer"
        if locf_pt < st_pt and locf_pt < clim_pt:
            winner = "persist_locf"
        elif clim_pt <= st_pt:
            winner = "climatology"
        rec = {
            "pattern": pattern,
            "keep_ratio": keep_ratio,
            "n_stations": int(n_stations),
            "keep_frac": round(kf, 4),
            "n_water_voxels": n_water,
            "lead": LEAD,
            "epochs": EPOCHS,
            "n_test": int(y_te.shape[0]),
            "st_rmse": float(f"{st_pt:.3f}"),
            "clim_rmse": float(f"{clim_pt:.3f}"),
            "persist_locf_rmse": float(f"{locf_pt:.3f}"),
            "point_delta_clim_minus_st": float(f"{clim_pt - st_pt:.3f}"),
            "winner": winner,
            **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in boot.items()},
        }
        rows.append(rec)
        print(
            f"  keep={kf:.3f}  ST={st_pt:.3f}  clim={clim_pt:.3f}  locf={locf_pt:.3f}  "
            f"delta={clim_pt-st_pt:.3f} "
            f"CI[{boot['delta_clim_minus_st_p05']:.3f},{boot['delta_clim_minus_st_p95']:.3f}]  "
            f"sig={boot['st_significantly_better']}  winner={winner}"
        )

    TABLES.mkdir(parents=True, exist_ok=True)
    out_json = TABLES / "keep_ratio_scan.json"
    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    out_csv = TABLES / "keep_ratio_scan.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    lines = [
        "# Lead-1 keep scan: ST vs climatology",
        "",
        f"n_test=22; {N_BOOT} paired month resamples; ST retrained {EPOCHS} epochs.",
        "point axis = voxel keep (lake 10/20/30% analog). "
        "station axis = column count (keep_ratio unused).",
        "delta = clim RMSE - ST RMSE.",
        "",
        "| Pattern | keep_ratio | n_stations | keep_frac | ST | locf | clim | delta | delta 5-95% | ST sig. | winner |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['pattern']} | {r['keep_ratio']:.2f} | {r['n_stations']} | "
            f"{r['keep_frac']:.3f} | {r['st_rmse']:.3f} | {r['persist_locf_rmse']:.3f} | "
            f"{r['clim_rmse']:.3f} | {r['point_delta_clim_minus_st']:.3f} | "
            f"[{r['delta_clim_minus_st_p05']:.3f}, {r['delta_clim_minus_st_p95']:.3f}] | "
            f"{r['st_significantly_better']} | {r['winner']} |"
        )
    out_md = TABLES / "keep_ratio_scan.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", out_json)
    print("Wrote", out_csv)
    print("Wrote", out_md)


if __name__ == "__main__":
    main()
