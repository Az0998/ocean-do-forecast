#!/usr/bin/env python
"""Section / sparse-column extrapolation evaluation.

Keeps oxygen only along a ship section (or Argo stations) in the input history,
then scores full-field forecast skill — narrative: forecast ≠ dense reconstruction.
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

from config import DEVICE, EPOCHS, PROCESSED, SEED, TABLES, ensure_dirs, load_active_region
from src.gobai_data import load_or_build_cube
from src.metrics import skill_vs_persistence
from src.models.baselines import climatology_predict, evaluate_regression, persistence_predict
from src.normalize import (
    apply_clim,
    denormalize_anom,
    fit_norm_from_train,
    history_to_norm_anom,
    normalize_anom,
    to_anomaly,
)
from src.samples import build_forecast_arrays, split_arrays
from src.sparse_mask import load_argo_station_cells
from src.train_utils import predict_st, train_st_anom


def section_mask(n_oxygen, lat, lon, path: Path):
    z, y, x = n_oxygen, len(lat), len(lon)
    m = np.zeros((z, y, x), dtype=np.float32)
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    pts = payload.get("section") or payload.get("stations") or []
    if not pts:
        # fallback diagonal
        n = min(y, x, 8)
        for k in range(n):
            m[:, int(k * y / n), int(k * x / n)] = 1.0
        return m
    for p in pts:
        i = int(np.argmin(np.abs(lat - float(p["lat"]))))
        j = int(np.argmin(np.abs(lon - float(p["lon"]))))
        m[:, i, j] = 1.0
    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lead-index", type=int, default=0)
    args = parser.parse_args()
    if args.quick:
        args.epochs = min(args.epochs, 6)

    ensure_dirs()
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    region = load_active_region()
    device = "cpu"
    ds = load_or_build_cube(region, prefer_demo=True)
    fa = build_forecast_arrays(ds, use_physics=False)
    splits = split_arrays(fa)
    n_oxygen = int(splits["meta"]["n_oxygen"])
    mask = splits["meta"]["mask"]
    lat, lon = ds["lat"].values, ds["lon"].values
    sm = section_mask(n_oxygen, lat, lon, PROCESSED / "argo_stations.json")

    stats = fit_norm_from_train(splits["train"]["y"][:, 0], splits["train"]["times"])
    li = args.lead_index

    def prep(split):
        x = split["x"].copy()
        # zero oxygen off-section
        x[:, :, :n_oxygen] = x[:, :, :n_oxygen] * sm[None, None]
        x_n = history_to_norm_anom(
            x, split["hist_times"], stats, x.shape[1], n_oxygen=n_oxygen
        )
        y = split["y"][:, li]
        y_n = normalize_anom(to_anomaly(y, split["times"], stats.clim), stats)
        return x_n, y_n, y, split["times"], split["x"][:, :, :n_oxygen]

    x_tr, y_tr_n, y_tr, t_tr, x_tr_raw = prep(splits["train"])
    x_va, y_va_n, y_va, t_va, x_va_raw = prep(splits["val"])
    x_te, y_te_n, y_te, t_te, x_te_raw = prep(splits["test"])

    persist = persistence_predict(x_te_raw)
    clim = climatology_predict(y_tr, t_tr, t_te)
    st = train_st_anom(
        x_tr, y_tr_n, x_va, y_va_n, mask, device, args.epochs, n_oxygen=n_oxygen
    )
    pred = denormalize_anom(predict_st(st, x_te, device), stats) + apply_clim(
        y_te, t_te, stats.clim
    )

    rows = []
    for name, p in [("persistence", persist), ("climatology", clim), ("st_section", pred)]:
        reg = evaluate_regression(y_te, p, mask)
        rows.append(
            {
                "model": name,
                **reg,
                "skill_vs_persist": skill_vs_persistence(y_te, p, persist),
                "n_section_cells": int(sm[0].sum()),
            }
        )
        print(name, reg)

    out = {
        "region": region.get("id"),
        "task": "section_extrapolation",
        "narrative": "Inputs visible only on section/Argo columns; targets are full-field forecasts.",
        "metrics": rows,
    }
    path = TABLES / "section_extrapolation.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    md = TABLES / "section_extrapolation.md"
    lines = [
        "# Section extrapolation (forecast ≠ reconstruction)",
        "",
        "Oxygen history is masked to a ship section / Argo columns; models still forecast the full field.",
        "",
        "| Model | RMSE | Skill |",
        "|---|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['model']} | {r['rmse']:.3f} | {r['skill_vs_persist']:.3f} |")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[section] wrote {md}")


if __name__ == "__main__":
    main()
