#!/usr/bin/env python
"""Compose AIES comparison figures from ablation JSON tables."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from config import FIGS, TABLES, ensure_dirs


def _physics_panel(ax):
    path = TABLES / "physics_ablation.json"
    if not path.exists():
        ax.set_axis_off()
        ax.set_title("physics_ablation.json missing")
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["rows"] if isinstance(payload, dict) and "rows" in payload else payload
    labels = [r.get("config") or r.get("name") or "?" for r in rows]
    st1, st2 = [], []
    for r in rows:
        if "st_rmse" in r:
            st1.append(float(r["st_rmse"].get("1", np.nan)))
            st2.append(float(r["st_rmse"].get("2", np.nan)))
        else:
            st1.append(float(r.get("lead1_st_rmse", r.get("lead1_st", np.nan))))
            st2.append(float(r.get("lead2_st_rmse", r.get("lead2_st", np.nan))))
    x = np.arange(len(labels))
    w = 0.36
    ax.bar(x - w / 2, st1, w, label="Lead-1 ST", color="#0f5f78")
    ax.bar(x + w / 2, st2, w, label="Lead-2 ST", color="#b45309")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("RMSE (µmol kg⁻¹)")
    ax.set_title("(a) Physics / wind ablation")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.25)


def _maskview_panel(ax):
    path = TABLES / "maskview_ablation.json"
    if not path.exists():
        ax.set_axis_off()
        ax.set_title("maskview_ablation.json missing")
        return
    rows = json.loads(path.read_text(encoding="utf-8"))
    labels = [r["sparse"] for r in rows]
    vals = [r["lead1_st_rmse"] for r in rows]
    ax.bar(range(len(labels)), vals, color="#2f6f4e")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Lead-1 ST RMSE")
    ax.set_title("(b) Mask-View sparse stress")
    ax.grid(axis="y", alpha=0.25)


def _seasonal_panel(ax):
    # Prefer physics real-wind multilead JSON
    candidates = [
        TABLES / "multilead_full_physics_real_wind.json",
        TABLES / "multilead_full_physics.json",
    ]
    payload = None
    for p in candidates:
        if p.exists():
            payload = json.loads(p.read_text(encoding="utf-8"))
            break
    if not payload or "seasonal" not in payload:
        ax.set_axis_off()
        ax.set_title("seasonal metrics missing — re-run multilead")
        return
    seasons = ("DJF", "MAM", "JJAS", "annual")
    models = ("climatology", "st_transformer", "hybrid_clim_st")
    width = 0.25
    x = np.arange(len(seasons))
    for i, model in enumerate(models):
        vals = []
        for season in seasons:
            hit = next(
                (
                    s
                    for s in payload["seasonal"]
                    if s["lead_months"] == 1
                    and s["model"] == model
                    and s["season"] == season
                ),
                None,
            )
            vals.append(hit["rmse"] if hit else np.nan)
        ax.bar(x + (i - 1) * width, vals, width, label=model)
    ax.set_xticks(x)
    ax.set_xticklabels(seasons)
    ax.set_ylabel("Lead-1 RMSE")
    ax.set_title("(c) Seasonal skill (physics run)")
    ax.legend(fontsize=7)
    ax.grid(axis="y", alpha=0.25)


def main():
    ensure_dirs()
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), dpi=200)
    _physics_panel(axes[0])
    _maskview_panel(axes[1])
    _seasonal_panel(axes[2])
    fig.suptitle(
        "East China Sea shelf DO forecast · AIES evidence plate",
        fontsize=12,
        y=1.02,
    )
    fig.tight_layout()
    out = FIGS / "aies_comparison_plate.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[compose] wrote {out}")


if __name__ == "__main__":
    main()
