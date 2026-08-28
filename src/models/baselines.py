"""Non-learned and shallow baselines for monthly DO forecast."""
from __future__ import annotations

import numpy as np


def persistence_predict(x: np.ndarray) -> np.ndarray:
    """Last history month as prediction. x: (N,H,Z,Y,X) -> (N,Z,Y,X)."""
    return x[:, -1].copy()


def last_observed_persist(oxy: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """LOCF along history. oxy/keep: (N,H,Z,Y,X) -> (N,Z,Y,X), NaN if never seen.

    Operational analog of lake LOCF: only uses oxygen that survived the mask.
    """
    observed = keep > 0.5
    v = np.where(observed, oxy, np.nan).astype(np.float64)
    n, h, z, y, x = v.shape
    flat = np.ascontiguousarray(v.transpose(0, 2, 3, 4, 1).reshape(-1, h))
    valid = np.isfinite(flat)
    idx = np.where(valid, np.arange(h, dtype=np.int64), 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    rows = np.arange(flat.shape[0])[:, None]
    filled = flat[rows, idx]
    never = ~valid.any(axis=1)
    filled[never] = np.nan
    last = filled[:, -1].reshape(n, z, y, x)
    return last.astype(np.float32)


def time_linear_persist(oxy: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """Per-voxel linear interpolation in time, then last month.

    Analog of lake Linear (per station–variable). No spatial or depth borrowing.
    Unobserved series stay NaN. np.interp holds endpoints (no seasonal clim mix).
    """
    n, h, z, y, x = oxy.shape
    t = np.arange(h, dtype=np.float64)
    o = np.ascontiguousarray(oxy.reshape(n, h, -1))
    k = np.ascontiguousarray(keep.reshape(n, h, -1) > 0.5)
    n_vox = o.shape[2]
    last = np.full((n, n_vox), np.nan, dtype=np.float64)
    for i in range(n):
        for j in range(n_vox):
            obs = k[i, :, j]
            n_obs = int(obs.sum())
            if n_obs == 0:
                continue
            vals = o[i, obs, j]
            if n_obs == 1:
                last[i, j] = vals[0]
                continue
            last[i, j] = np.interp(float(h - 1), t[obs], vals)
    return last.reshape(n, z, y, x).astype(np.float32)


def fill_with_climatology(pred: np.ndarray, clim: np.ndarray) -> np.ndarray:
    """Where the simple method saw no oxygen, fall back to month-of-year climatology."""
    out = np.where(np.isfinite(pred), pred, clim)
    return out.astype(np.float32)


def spatial_linear_persist(oxy: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """LOCF per column, then horizontal linear interpolation at each depth.

    Analog of filling missing *stations* (lake Linear cannot do this). Depths
    with fewer than 3 observed columns stay NaN.
    """
    from scipy.interpolate import griddata

    locf = last_observed_persist(oxy, keep).astype(np.float64)
    n, z, y, x = locf.shape
    yy, xx = np.mgrid[0:y, 0:x]
    out = locf.copy()
    for i in range(n):
        for zi in range(z):
            field = locf[i, zi]
            obs = np.isfinite(field)
            if int(obs.sum()) < 3:
                continue
            pts = np.column_stack([yy[obs], xx[obs]])
            vals = field[obs]
            lin = griddata(pts, vals, (yy, xx), method="linear")
            near = griddata(pts, vals, (yy, xx), method="nearest")
            filled = np.where(np.isfinite(lin), lin, near)
            out[i, zi] = filled
    return out.astype(np.float32)


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
