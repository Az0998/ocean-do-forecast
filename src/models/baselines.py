"""Non-learned and shallow baselines for monthly DO forecast."""
from __future__ import annotations

import numpy as np


def persistence_predict(x: np.ndarray) -> np.ndarray:
    """Last history month as prediction. x: (N,H,Z,Y,X) -> (N,Z,Y,X)."""
    return x[:, -1].copy()


def climatology_predict(
    train_y: np.ndarray,
    train_times: np.ndarray,
    target_times: np.ndarray,
) -> np.ndarray:
    """Month-of-year climatology from training targets. y lead0: (N,Z,Y,X)."""
    import pandas as pd

    months = pd.DatetimeIndex(train_times).month
    out = np.zeros((len(target_times),) + train_y.shape[1:], dtype=np.float32)
    clim = {}
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        if len(idx):
            clim[m] = np.nanmean(train_y[idx], axis=0)
    global_mean = np.nanmean(train_y, axis=0)
    t_months = pd.DatetimeIndex(target_times).month
    for i, m in enumerate(t_months):
        out[i] = clim.get(int(m), global_mean)
    return out


def evaluate_regression(
    y_true: np.ndarray, y_pred: np.ndarray, mask: np.ndarray | None = None
) -> dict[str, float]:
    from src.metrics import mae, rmse

    yt, yp = y_true, y_pred
    if mask is not None:
        m = mask > 0
        # broadcast mask over batch
        while m.ndim < yt.ndim:
            m = m[None, ...]
        m = np.broadcast_to(m, yt.shape)
        yt = np.where(m, yt, np.nan)
        yp = np.where(m, yp, np.nan)
    return {"rmse": rmse(yt, yp), "mae": mae(yt, yp)}
