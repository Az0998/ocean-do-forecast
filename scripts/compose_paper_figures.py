#!/usr/bin/env python
"""Compose a 2x2 paper figure plate from existing multilead PNGs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from config import FIGS, ensure_dirs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="full", help="full | station | ...")
    args = parser.parse_args()
    ensure_dirs()
    tag = args.tag
    panels = [
        (FIGS / f"lead_rmse_{tag}.png", "(a) Lead–RMSE"),
        (FIGS / f"lead_skill_{tag}.png", "(b) Lead–Skill vs persistence"),
        (FIGS / f"lead_hypoxia_f1_{tag}.png", "(c) Low-O2 event F1"),
        (FIGS / f"depth_rmse_lead1_{tag}.png", "(d) Depth RMSE (lead=1)"),
    ]
    missing = [str(p) for p, _ in panels if not p.exists()]
    if missing:
        raise SystemExit("Missing panels:\n" + "\n".join(missing))

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.2), dpi=200)
    for ax, (path, title) in zip(axes.ravel(), panels):
        img = mpimg.imread(path)
        ax.imshow(img)
        ax.set_title(title, fontsize=11, loc="left")
        ax.axis("off")
    fig.suptitle(
        f"East China Sea shelf DO forecast · `{tag}`",
        fontsize=13,
        y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIGS / f"paper_plate_{tag}.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"[figures] wrote {out}")


if __name__ == "__main__":
    main()
