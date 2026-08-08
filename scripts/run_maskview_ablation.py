#!/usr/bin/env python
"""Systematic Mask-View sparse ablation under physics drivers.

Runs `run_multilead.py --physics` for each sparsity pattern and writes
`results/tables/maskview_ablation.{md,json}` plus a comparison figure.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import FIGS, TABLES, ensure_dirs

PATTERNS = ("none", "point", "block", "block_time", "sensor", "station", "mixed", "argo")


def _load_metrics(tag: str) -> dict | None:
    path = TABLES / f"multilead_{tag}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _best_for_lead(payload: dict, lead: int) -> tuple[str, float, float]:
    rows = [r for r in payload["metrics"] if r["lead_months"] == lead]
    best = min(rows, key=lambda r: r["rmse"])
    st = next(r for r in rows if r["model"] == "st_transformer")
    return best["model"], float(best["rmse"]), float(st["rmse"])


def _compose_figure(rows: list[dict], out: Path) -> None:
    import matplotlib.pyplot as plt

    labels = [r["sparse"] for r in rows]
    st1 = [r["lead1_st_rmse"] for r in rows]
    best2 = [r["lead2_best_rmse"] for r in rows]
    f1 = [r["lead1_st_f1"] for r in rows]

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.8), dpi=180)
    x = range(len(labels))
    axes[0].bar(x, st1, color="#0f5f78")
    axes[0].set_title("Lead-1 ST RMSE")
    axes[0].set_ylabel("µmol kg⁻¹")
    axes[1].bar(x, best2, color="#b45309")
    axes[1].set_title("Lead-2 best RMSE")
    axes[2].bar(x, f1, color="#2f6f4e")
    axes[2].set_title("Lead-1 ST low-O₂ F1")
    axes[2].set_ylim(0, 1)
    for ax in axes:
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Mask-View sparse ablation · physics cube", fontsize=12)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patterns", nargs="+", default=list(PATTERNS))
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--skip-run", action="store_true", help="Only aggregate existing JSONs")
    parser.add_argument("--keep-ratio", type=float, default=0.25)
    parser.add_argument("--stations", type=int, default=8)
    parser.add_argument("--maskview", action="store_true", help="Also enable multiview loss")
    args = parser.parse_args()
    ensure_dirs()

    summary = []
    for pattern in args.patterns:
        tag = "full_physics" if pattern == "none" else f"{pattern}_physics"
        if args.maskview and pattern != "none":
            tag = f"{tag}_maskview"
        if not args.skip_run:
            cmd = [
                sys.executable,
                str(ROOT / "run_multilead.py"),
                "--physics",
                "--sparse",
                pattern,
                "--keep-ratio",
                str(args.keep_ratio),
                "--stations",
                str(args.stations),
                "--epochs",
                str(args.epochs),
                "--bootstrap",
                "0",
            ]
            if args.quick:
                cmd.append("--quick")
            if args.maskview and pattern != "none":
                cmd.append("--maskview")
            print(f"\n===== Mask-View ablation: sparse={pattern} =====")
            subprocess.check_call(cmd, cwd=str(ROOT))

        # Retag: run_multilead names none -> full_physics
        payload = _load_metrics(tag)
        if payload is None and pattern == "none":
            payload = _load_metrics("full_physics")
        if payload is None:
            print(f"[maskview] missing metrics for {tag}")
            continue
        b1, best1, st1 = _best_for_lead(payload, 1)
        b2, best2, st2 = _best_for_lead(payload, 2)
        st_row = next(
            r
            for r in payload["metrics"]
            if r["lead_months"] == 1 and r["model"] == "st_transformer"
        )
        summary.append(
            {
                "sparse": pattern,
                "tag": tag,
                "lead1_best": b1,
                "lead1_best_rmse": best1,
                "lead1_st_rmse": st1,
                "lead1_st_f1": float(st_row["hypoxia_f1"]),
                "lead2_best": b2,
                "lead2_best_rmse": best2,
                "lead2_st_rmse": st2,
                "blend_weights": payload.get("blend_weights", {}),
            }
        )

    md = [
        "# Mask-View sparse ablation (physics cube)",
        "",
        "Oxygen history + T/S/N²/SST/Open-Meteo wind. Only the observation mask changes.",
        "",
        "| Sparse | Lead-1 ST | Lead-1 best | Lead-1 F1 | Lead-2 ST | Lead-2 best |",
        "|---|---:|---|---:|---:|---|",
    ]
    for r in summary:
        md.append(
            f"| {r['sparse']} | {r['lead1_st_rmse']:.3f} | "
            f"{r['lead1_best']} {r['lead1_best_rmse']:.3f} | {r['lead1_st_f1']:.3f} | "
            f"{r['lead2_st_rmse']:.3f} | {r['lead2_best']} {r['lead2_best_rmse']:.3f} |"
        )
    md += [
        "",
        "## Notes",
        "",
        "- `none`: dense oxygen history (upper bound).",
        "- `argo` / `station`: column-limited operational view.",
        "- `block` / `block_time`: contiguous missingness (Mask-View stress).",
        "- Hybrid blend weights shrink toward climatology at longer leads.",
        "",
    ]
    out_md = TABLES / "maskview_ablation.md"
    out_json = TABLES / "maskview_ablation.json"
    out_md.write_text("\n".join(md), encoding="utf-8")
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    fig = FIGS / "maskview_ablation.png"
    if summary:
        _compose_figure(summary, fig)
    print(f"[maskview] wrote {out_md}")
    print(f"[maskview] wrote {out_json}")
    print(f"[maskview] figure {fig}")


if __name__ == "__main__":
    main()
