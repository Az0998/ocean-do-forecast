#!/usr/bin/env python
"""Run persistence / climatology / LSTM baselines on regional oxygen cube."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config import (
    BATCH_SIZE,
    CKPT,
    DEVICE,
    EPOCHS,
    HIDDEN,
    HYPOXIA_UMOL_KG,
    LR,
    SEED,
    TABLES,
    ensure_dirs,
    load_active_region,
)
from src.gobai_data import load_or_build_cube
from src.metrics import binary_event_scores, skill_vs_persistence
from src.models.baselines import (
    climatology_predict,
    evaluate_regression,
    persistence_predict,
)
from src.models.lstm import LSTMForecast
from src.normalize import (
    apply_clim,
    denormalize_anom,
    fit_norm_from_train,
    history_to_norm_anom,
    normalize_anom,
    to_anomaly,
)
from src.samples import build_forecast_arrays, flatten_space, split_arrays


def set_seed(seed: int = SEED):
    np.random.seed(seed)
    torch.manual_seed(seed)


def train_lstm(
    x_tr, y_tr, x_va, y_va, feature_dim: int, device: str, epochs: int
) -> LSTMForecast:
    model = LSTMForecast(feature_dim, hidden=HIDDEN).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(x_tr), torch.from_numpy(y_tr)),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )
    best, best_val = None, float("inf")
    for ep in range(1, epochs + 1):
        model.train()
        total, n = 0.0, 0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            pred = model(x)
            loss = torch.mean((pred - y) ** 2)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss.detach()) * x.size(0)
            n += x.size(0)
        model.eval()
        with torch.no_grad():
            vp = model(torch.from_numpy(x_va).to(device))
            vloss = float(torch.mean((vp - torch.from_numpy(y_va).to(device)) ** 2))
        if vloss < best_val:
            best_val = vloss
            best = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        if ep == 1 or ep % 5 == 0:
            print(f"  LSTM ep {ep}: train_mse={total/max(n,1):.4f} val_mse={vloss:.4f}")
    if best:
        model.load_state_dict(best)
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Force demo cube")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    if args.quick:
        args.epochs = min(args.epochs, 8)
    set_seed()
    ensure_dirs()
    region = load_active_region()
    print(f"[baselines] region={region.get('id', region.get('name'))}")
    ds = load_or_build_cube(region, prefer_demo=args.demo)
    print(f"[baselines] cube source={ds.attrs.get('source')} sizes={dict(ds.sizes)}")
    fa = build_forecast_arrays(ds)
    splits = split_arrays(fa)
    mask = splits["meta"]["mask"]
    train, val, test = splits["train"], splits["val"], splits["test"]
    print(
        f"[baselines] samples train/val/test = "
        f"{len(train['x'])}/{len(val['x'])}/{len(test['x'])}"
    )
    if len(test["x"]) == 0:
        raise SystemExit("Empty test split — widen years or check TRAIN/VAL_END")

    y_test = test["y"][:, 0]
    persist = persistence_predict(test["x"])
    clim = climatology_predict(train["y"][:, 0], train["times"], test["times"])

    rows = []
    for name, pred in [("persistence", persist), ("climatology", clim)]:
        reg = evaluate_regression(y_test, pred, mask)
        skill = skill_vs_persistence(y_test, pred, persist)
        ev = binary_event_scores(y_test, pred, HYPOXIA_UMOL_KG)
        rows.append(
            {
                "model": name,
                **reg,
                "skill_vs_persist": skill,
                "hypoxia_f1": ev["f1"],
                "hypoxia_csi": ev["csi"],
            }
        )
        print(f"  {name}: rmse={reg['rmse']:.3f} mae={reg['mae']:.3f} f1={ev['f1']:.3f}")

    # LSTM on normalized anomalies (lead=1)
    stats = fit_norm_from_train(train["y"][:, 0], train["times"])
    x_tr = history_to_norm_anom(train["x"], train["hist_times"], stats, train["x"].shape[1])
    x_va = history_to_norm_anom(val["x"], val["hist_times"], stats, val["x"].shape[1])
    x_te = history_to_norm_anom(test["x"], test["hist_times"], stats, test["x"].shape[1])
    y_tr = normalize_anom(to_anomaly(train["y"][:, 0], train["times"], stats.clim), stats)
    y_va = normalize_anom(to_anomaly(val["y"][:, 0], val["times"], stats.clim), stats)

    device = DEVICE if torch.cuda.is_available() and DEVICE == "cuda" else "cpu"
    x_tr_f = flatten_space(torch.from_numpy(x_tr)).numpy()
    x_va_f = flatten_space(torch.from_numpy(x_va)).numpy()
    x_te_f = flatten_space(torch.from_numpy(x_te)).numpy()
    y_tr_f = y_tr.reshape(len(y_tr), -1)
    y_va_f = y_va.reshape(len(y_va), -1)
    feat = x_tr_f.shape[-1]
    print(f"[baselines] training LSTM on {device} feature_dim={feat} (anomaly z-score)")
    model = train_lstm(x_tr_f, y_tr_f, x_va_f, y_va_f, feat, device, args.epochs)
    CKPT.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "stats_mean": stats.mean, "stats_std": stats.std}, CKPT / "lstm_lead1.pt")
    model.eval()
    with torch.no_grad():
        pred_norm = model(torch.from_numpy(x_te_f).to(device)).cpu().numpy().reshape(y_test.shape)
    pred_anom = denormalize_anom(pred_norm, stats)
    pred = pred_anom + apply_clim(y_test, test["times"], stats.clim)
    reg = evaluate_regression(y_test, pred, mask)
    skill = skill_vs_persistence(y_test, pred, persist)
    ev = binary_event_scores(y_test, pred, HYPOXIA_UMOL_KG)
    rows.append(
        {
            "model": "lstm_anomaly",
            **reg,
            "skill_vs_persist": skill,
            "hypoxia_f1": ev["f1"],
            "hypoxia_csi": ev["csi"],
        }
    )
    print(f"  lstm_anomaly: rmse={reg['rmse']:.3f} mae={reg['mae']:.3f} f1={ev['f1']:.3f}")

    TABLES.mkdir(parents=True, exist_ok=True)
    out_json = TABLES / "baselines.json"
    out_md = TABLES / "baselines.md"
    payload = {
        "region": region.get("id"),
        "cube_source": ds.attrs.get("source"),
        "lead_months": fa.leads[0],
        "metrics": rows,
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Baseline results (lead=1 month)",
        "",
        f"Region: `{region.get('id')}` · cube: `{ds.attrs.get('source')}`",
        "",
        "| Model | RMSE | MAE | Skill vs persist | Hypoxia F1 | CSI |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['model']} | {r['rmse']:.3f} | {r['mae']:.3f} | "
            f"{r['skill_vs_persist']:.3f} | {r['hypoxia_f1']:.3f} | {r['hypoxia_csi']:.3f} |"
        )
    if ds.attrs.get("source") == "demo":
        lines += [
            "",
            "> Demo cube: climatology is intentionally strong; use GOBAI for paper claims.",
        ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[baselines] wrote {out_md}")


if __name__ == "__main__":
    main()
