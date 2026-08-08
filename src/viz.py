"""Publication-oriented quick figures."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_lead_skill(
    leads: list[int],
    series: dict[str, list[float]],
    ylabel: str,
    title: str,
    out: Path,
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.2, 3.8), dpi=150)
    for name, vals in series.items():
        ax.plot(leads, vals, marker="o", label=name)
    ax.set_xlabel("Lead (months)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(leads)
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_spatial_rmse(
    rmse_map: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    title: str,
    out: Path,
    cmap: str = "viridis",
) -> Path:
    """rmse_map: (Y,X) depth-mean or single level."""
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.5, 4.2), dpi=150)
    im = ax.pcolormesh(lon, lat, rmse_map, shading="auto", cmap=cmap)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("RMSE (µmol/kg)")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_depth_rmse(
    profiles: dict[str, list[dict]],
    title: str,
    out: Path,
) -> Path:
    """profiles[model] = [{depth_dbar, rmse}, ...]"""
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4.8, 5.2), dpi=150)
    for name, rows in profiles.items():
        depths = [r["depth_dbar"] for r in rows]
        rmses = [r["rmse"] for r in rows]
        ax.plot(rmses, depths, marker="o", label=name)
    ax.set_xlabel("RMSE (µmol/kg)")
    ax.set_ylabel("Depth (dbar)")
    ax.set_title(title)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def depth_mean_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """(N,Z,Y,X) -> (Y,X) RMSE."""
    err2 = (y_pred - y_true) ** 2
    return np.sqrt(np.nanmean(err2, axis=(0, 1)))
