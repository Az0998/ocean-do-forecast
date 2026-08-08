#!/usr/bin/env python
"""Train spatiotemporal Transformer on DO anomalies with optional physics loss."""
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
    N_HEADS,
    N_LAYERS,
    SEED,
    TABLES,
    ensure_dirs,
    load_active_region,
)
from src.gobai_data import load_or_build_cube
from src.metrics import binary_event_scores, skill_vs_persistence
from src.models.baselines import evaluate_regression, persistence_predict
from src.models.st_transformer import STTransformerForecast
from src.normalize import (
    apply_clim,
    denormalize_anom,
    fit_norm_from_train,
    history_to_norm_anom,
    normalize_anom,
    to_anomaly,
)
from src.physics import physics_residual_loss
from src.samples import build_forecast_arrays, split_arrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--no-physics", action="store_true")
    args = parser.parse_args()
    if args.quick:
        args.epochs = min(args.epochs, 8)

    np.random.seed(SEED)
    torch.manual_seed(SEED)
    ensure_dirs()
    region = load_active_region()
    ds = load_or_build_cube(region, prefer_demo=args.demo)
    fa = build_forecast_arrays(ds)
    splits = split_arrays(fa)
    train, val, test = splits["train"], splits["val"], splits["test"]
    mask_np = splits["meta"]["mask"]
    device = DEVICE if torch.cuda.is_available() and DEVICE == "cuda" else "cpu"

    stats = fit_norm_from_train(train["y"][:, 0], train["times"])
    x_tr = history_to_norm_anom(train["x"], train["hist_times"], stats, train["x"].shape[1])
    x_va = history_to_norm_anom(val["x"], val["hist_times"], stats, val["x"].shape[1])
    x_te = history_to_norm_anom(test["x"], test["hist_times"], stats, test["x"].shape[1])
    y_tr = normalize_anom(to_anomaly(train["y"][:, 0], train["times"], stats.clim), stats)
    y_va = normalize_anom(to_anomaly(val["y"][:, 0], val["times"], stats.clim), stats)

    n_depth = x_tr.shape[2]
    model = STTransformerForecast(
        n_depth=n_depth, hidden=HIDDEN, n_heads=N_HEADS, n_layers=N_LAYERS
    ).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(x_tr), torch.from_numpy(y_tr)),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )
    mask_t = torch.from_numpy(mask_np).to(device)

    best_state, best_val = None, float("inf")
    for ep in range(1, args.epochs + 1):
        model.train()
        total, n = 0.0, 0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            pred = model(x)
            if args.no_physics:
                loss = torch.mean((pred - y) ** 2)
            else:
                loss = physics_residual_loss(pred, y, mask_t, lambda_smooth=0.01)
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
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        if ep == 1 or ep % 5 == 0:
            print(f"[st] ep {ep}: train={total/max(n,1):.4f} val={vloss:.4f}")

    if best_state:
        model.load_state_dict(best_state)
    CKPT.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), CKPT / "st_transformer_lead1.pt")

    model.eval()
    with torch.no_grad():
        pred_norm = model(torch.from_numpy(x_te).to(device)).cpu().numpy()
    y_test = test["y"][:, 0]
    persist = persistence_predict(test["x"])
    pred = denormalize_anom(pred_norm, stats) + apply_clim(y_test, test["times"], stats.clim)
    reg = evaluate_regression(y_test, pred, mask_np)
    skill = skill_vs_persistence(y_test, pred, persist)
    ev = binary_event_scores(y_test, pred, HYPOXIA_UMOL_KG)
    row = {
        "model": "st_transformer_anomaly",
        "physics": not args.no_physics,
        **reg,
        "skill_vs_persist": skill,
        "hypoxia_f1": ev["f1"],
        "hypoxia_csi": ev["csi"],
        "region": region.get("id"),
        "cube_source": ds.attrs.get("source"),
    }
    TABLES.mkdir(parents=True, exist_ok=True)
    out = TABLES / "st_transformer.json"
    out.write_text(json.dumps(row, indent=2), encoding="utf-8")
    summary = TABLES / "st_transformer.md"
    summary.write_text(
        "\n".join(
            [
                "# ST-Transformer (lead=1 month)",
                "",
                f"Region: `{row['region']}` · cube: `{row['cube_source']}` · physics={row['physics']}",
                "",
                f"- RMSE: {row['rmse']:.3f}",
                f"- MAE: {row['mae']:.3f}",
                f"- Skill vs persistence: {row['skill_vs_persist']:.3f}",
                f"- Hypoxia F1 / CSI: {row['hypoxia_f1']:.3f} / {row['hypoxia_csi']:.3f}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(
        f"[st] test rmse={reg['rmse']:.3f} mae={reg['mae']:.3f} "
        f"skill={skill:.3f} hypoxia_f1={ev['f1']:.3f}"
    )
    print(f"[st] wrote {out}")


if __name__ == "__main__":
    main()
