"""Lead-aware hybrid: climatology + learned anomaly with val-tuned blend."""
from __future__ import annotations

import numpy as np

from src.metrics import rmse


def blend(clim: np.ndarray, model: np.ndarray, w: float) -> np.ndarray:
    """pred = (1-w)*clim + w*model; w in [0,1]."""
    return (1.0 - w) * clim + w * model


def tune_blend_weight(
    y_val: np.ndarray,
    clim_val: np.ndarray,
    model_val: np.ndarray,
    grid: np.ndarray | None = None,
) -> float:
    """Pick w minimizing RMSE on validation."""
    if grid is None:
        grid = np.linspace(0.0, 1.0, 21)
    best_w, best = 0.0, float("inf")
    for w in grid:
        pred = blend(clim_val, model_val, float(w))
        r = rmse(y_val, pred)
        if r < best:
            best, best_w = r, float(w)
    return best_w


def depth_rmse_profile(
    y_true: np.ndarray, y_pred: np.ndarray, depths: np.ndarray
) -> list[dict]:
    """y: (N,Z,Y,X) -> per-depth RMSE."""
    rows = []
    for zi, d in enumerate(depths):
        rows.append(
            {
                "depth_dbar": float(d),
                "rmse": rmse(y_true[:, zi], y_pred[:, zi]),
            }
        )
    return rows
