#!/usr/bin/env python
"""Paired bootstrap: does lead-1 ST still beat climatology under Mask-View?

Locked ablation numbers used --bootstrap 0. The station/argo margin vs clim is
~0.06 µmol kg⁻¹ on n≈22 test months. This script retrains ST (same 8-epoch
quick recipe, no LSTM) and bootstraps RMSE and the paired difference
(clim RMSE − ST RMSE). If that CI includes 0, “ST still wins lead-1” is not
supported under column-limited history.
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
from src.sparse_mask import apply_block_time_to_batch, apply_mask, make_batch_masks, sample_block_time_mask
from src.train_utils import predict_st, train_st_anom

from run_multilead import _oxygen_history, prepare_lead, set_seed

KEEP_RATIO = 0.25
N_STATIONS = 8
EPOCHS = 8
N_BOOT = 200
PATTERNS = ("none", "point", "station", "argo")
LEAD = 1


def oxygen_keep(x_raw, pattern, seed, n_oxygen, lat, lon, argo_path):
    n, h, _c, y, x = x_raw.shape
    z = n_oxygen
    if pattern == "none":
        return np.ones((n, h, z, y, x), dtype=np.float32)
    if pattern == "block_time":
        rng = np.random.default_rng(seed)
        keep = np.empty((n, h, z, y, x), dtype=np.float32)
        for i in range(n):
            keep[i] = sample_block_time_mask((h, z, y, x), KEEP_RATIO, rng)
        return keep
    m = make_batch_masks(
        x_raw,
        pattern,
        KEEP_RATIO,
        N_STATIONS,
        seed=seed,
        n_oxygen=n_oxygen,
        lat=lat,
        lon=lon,
        argo_stations_path=argo_path,
    )
    return np.broadcast_to(m, (n, h, z, y, x)).copy()


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
    d_st, d_clim, d_delta = [], [], []
    n_st_better = 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        rs = rmse(y[idx], pred_st[idx])
        rc = rmse(y[idx], pred_clim[idx])
        d_st.append(rs)
        d_clim.append(rc)
        d_delta.append(rc - rs)
        if rs < rc:
            n_st_better += 1
    arr = np.asarray(d_delta, dtype=float)
    return {
        "st_rmse_p05": float(np.percentile(d_st, 5)),
        "st_rmse_p50": float(np.percentile(d_st, 50)),
        "st_rmse_p95": float(np.percentile(d_st, 95)),
        "clim_rmse_p05": float(np.percentile(d_clim, 5)),
        "clim_rmse_p50": float(np.percentile(d_clim, 50)),
        "clim_rmse_p95": float(np.percentile(d_clim, 95)),
        "delta_clim_minus_st_p05": float(np.percentile(arr, 5)),
        "delta_clim_minus_st_p50": float(np.percentile(arr, 50)),
        "delta_clim_minus_st_p95": float(np.percentile(arr, 95)),
        "frac_boot_st_better": float(n_st_better / n_boot),
        "ci_excludes_zero": bool(np.percentile(arr, 5) > 0 or np.percentile(arr, 95) < 0),
        "st_significantly_better": bool(np.percentile(arr, 5) > 0),
        "n_test": int(n),
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
    rows = []

    for pattern in PATTERNS:
        print(f"\n===== bootstrap sparse={pattern} lead={LEAD} =====")
        data = prepare_lead(splits, li, stats, n_oxygen)
        x_tr, y_tr_n, y_tr, t_tr, x_tr_raw = data["train"]
        x_va, y_va_n, y_va, t_va, x_va_raw = data["val"]
        x_te, y_te_n, y_te, t_te, x_te_raw = data["test"]
        if pattern == "block_time":
            x_tr = apply_block_time_to_batch(x_tr, KEEP_RATIO, n_oxygen, SEED + LEAD)
            x_va = apply_block_time_to_batch(x_va, KEEP_RATIO, n_oxygen, SEED + 100 + LEAD)
            x_te = apply_block_time_to_batch(x_te, KEEP_RATIO, n_oxygen, SEED + 200 + LEAD)
        elif pattern != "none":
            m_tr = make_batch_masks(
                x_tr, pattern, KEEP_RATIO, N_STATIONS, seed=SEED + LEAD,
                n_oxygen=n_oxygen, lat=lat, lon=lon, argo_stations_path=argo_path,
            )
            m_va = make_batch_masks(
                x_va, pattern, KEEP_RATIO, N_STATIONS, seed=SEED + 100 + LEAD,
                n_oxygen=n_oxygen, lat=lat, lon=lon, argo_stations_path=argo_path,
            )
            m_te = make_batch_masks(
                x_te, pattern, KEEP_RATIO, N_STATIONS, seed=SEED + 200 + LEAD,
                n_oxygen=n_oxygen, lat=lat, lon=lon, argo_stations_path=argo_path,
            )
            x_tr = apply_mask(x_tr, m_tr)
            x_va = apply_mask(x_va, m_va)
            x_te = apply_mask(x_te, m_te)

        clim = climatology_predict(y_tr, t_tr, t_te)
        keep = oxygen_keep(
            x_te_raw, pattern, SEED + 200 + LEAD, n_oxygen, lat, lon, argo_path
        )
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
        rec = {
            "pattern": pattern,
            "lead": LEAD,
            "epochs": EPOCHS,
            "n_test": int(y_te.shape[0]),
            "st_rmse": float(f"{st_pt:.3f}"),
            "clim_rmse": float(f"{clim_pt:.3f}"),
            "persist_locf_rmse": float(f"{locf_pt:.3f}"),
            "point_delta_clim_minus_st": float(f"{clim_pt - st_pt:.3f}"),
            **{k: (round(v, 3) if isinstance(v, float) else v) for k, v in boot.items()},
        }
        rows.append(rec)
        print(
            f"  ST={st_pt:.3f} [{boot['st_rmse_p05']:.3f},{boot['st_rmse_p95']:.3f}]  "
            f"clim={clim_pt:.3f}  delta={clim_pt-st_pt:.3f} "
            f"CI[{boot['delta_clim_minus_st_p05']:.3f},{boot['delta_clim_minus_st_p95']:.3f}]  "
            f"P(ST<clim)={boot['frac_boot_st_better']:.2f}  "
            f"sig={boot['st_significantly_better']}"
        )

    TABLES.mkdir(parents=True, exist_ok=True)
    out_json = TABLES / "st_clim_bootstrap.json"
    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    out_csv = TABLES / "st_clim_bootstrap.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    lines = [
        "# Lead-1 ST vs climatology, paired bootstrap over test months",
        "",
        f"n_test=22 months; {N_BOOT} resamples; ST retrained {EPOCHS} epochs (ablation recipe).",
        "delta = clim RMSE - ST RMSE; positive means ST better. "
        "st_significantly_better if the 5th percentile of delta is > 0.",
        "",
        "| Pattern | ST | ST 5-95% | clim | persist_locf | delta | delta 5-95% | P(ST<clim) | ST sig. better |",
        "|---|---:|---|---:|---:|---:|---|---:|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['pattern']} | {r['st_rmse']:.3f} | "
            f"[{r['st_rmse_p05']:.3f}, {r['st_rmse_p95']:.3f}] | {r['clim_rmse']:.3f} | "
            f"{r['persist_locf_rmse']:.3f} | {r['point_delta_clim_minus_st']:.3f} | "
            f"[{r['delta_clim_minus_st_p05']:.3f}, {r['delta_clim_minus_st_p95']:.3f}] | "
            f"{r['frac_boot_st_better']:.2f} | {r['st_significantly_better']} |"
        )
    out_md = TABLES / "st_clim_bootstrap.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", out_json)
    print("Wrote", out_csv)
    print("Wrote", out_md)


if __name__ == "__main__":
    main()
