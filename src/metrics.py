"""Forecast and hypoxia-event metrics for multi-lead DO evaluation."""

from __future__ import annotations

from typing import Callable

import numpy as np


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not mask.any():
        return float("nan")
    err = y_pred[mask] - y_true[mask]
    return float(np.sqrt(np.mean(err**2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs(y_pred[mask] - y_true[mask])))


def skill_vs_reference(
    y_true: np.ndarray, y_pred: np.ndarray, y_ref: np.ndarray
) -> float:
    """1 - MSE_model / MSE_reference (higher is better)."""
    mse_m = np.nanmean((y_pred - y_true) ** 2)
    mse_r = np.nanmean((y_ref - y_true) ** 2)
    if mse_r <= 0 or not np.isfinite(mse_r):
        return float("nan")
    return float(1.0 - mse_m / mse_r)


def skill_vs_persistence(
    y_true: np.ndarray, y_pred: np.ndarray, y_persist: np.ndarray
) -> float:
    """1 - MSE_model / MSE_persistence (higher is better)."""
    return skill_vs_reference(y_true, y_pred, y_persist)


def anomaly_rmse(
    y_true: np.ndarray, y_pred: np.ndarray, y_clim: np.ndarray
) -> float:
    """RMSE on anomalies relative to the same climatology field."""
    return rmse(y_true - y_clim, y_pred - y_clim)


def binary_event_scores(
    y_true: np.ndarray, y_pred: np.ndarray, threshold: float
) -> dict[str, float]:
    """CSI / F1 for hypoxia-like events where value < threshold."""
    yt = np.asarray(y_true) < threshold
    yp = np.asarray(y_pred) < threshold
    tp = int(np.sum(yt & yp))
    fp = int(np.sum(~yt & yp))
    fn = int(np.sum(yt & ~yp))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    csi = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "csi": csi,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "threshold": float(threshold),
    }


def choose_event_threshold(
    train_y: np.ndarray,
    absolute: float = 60.0,
    percentile: float = 10.0,
    min_rate: float = 0.01,
) -> tuple[float, str]:
    """Prefer absolute hypoxia threshold; else low-O2 percentile."""
    rate = float(np.mean(train_y < absolute))
    if rate >= min_rate:
        return float(absolute), "absolute_hypoxia"
    thr = float(np.nanpercentile(train_y, percentile))
    return thr, f"percentile_p{percentile:g}"


# Summer hypoxia season vs winter for ECS shelf narratives
SEASON_MONTHS = {
    "JJAS": (6, 7, 8, 9),
    "DJF": (12, 1, 2),
    "MAM": (3, 4, 5),
    "annual": tuple(range(1, 13)),
}


def month_mask(times: np.ndarray, months: tuple[int, ...]) -> np.ndarray:
    import pandas as pd

    m = pd.DatetimeIndex(times).month.to_numpy()
    return np.isin(m, months)


def seasonal_scores(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_persist: np.ndarray,
    y_clim: np.ndarray,
    times: np.ndarray,
    threshold: float,
    seasons: dict[str, tuple[int, ...]] | None = None,
) -> dict[str, dict[str, float]]:
    """Per-season RMSE / anomaly RMSE / skill / event scores."""
    seasons = seasons or SEASON_MONTHS
    out: dict[str, dict[str, float]] = {}
    for name, months in seasons.items():
        sel = month_mask(times, months)
        if not np.any(sel):
            continue
        yt, yp = y_true[sel], y_pred[sel]
        yp_persist, yc = y_persist[sel], y_clim[sel]
        ev = binary_event_scores(yt, yp, threshold)
        out[name] = {
            "n": int(sel.sum()),
            "rmse": rmse(yt, yp),
            "anom_rmse": anomaly_rmse(yt, yp, yc),
            "skill_vs_persist": skill_vs_persistence(yt, yp, yp_persist),
            "skill_vs_clim": skill_vs_reference(yt, yp, yc),
            "hypoxia_f1": ev["f1"],
            "hypoxia_csi": ev["csi"],
            "event_rate_true": float(np.mean(yt < threshold)),
        }
    return out


def bootstrap_metric(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    n_boot: int = 200,
    seed: int = 42,
    block_axis: int = 0,
) -> dict[str, float]:
    """Block bootstrap over the leading (sample/time) axis."""
    rng = np.random.default_rng(seed)
    n = y_true.shape[block_axis]
    if n < 2:
        val = metric_fn(y_true, y_pred)
        return {"mean": val, "p05": val, "p50": val, "p95": val, "n": float(n)}
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yt = np.take(y_true, idx, axis=block_axis)
        yp = np.take(y_pred, idx, axis=block_axis)
        vals.append(metric_fn(yt, yp))
    arr = np.asarray(vals, dtype=float)
    return {
        "mean": float(np.nanmean(arr)),
        "p05": float(np.nanpercentile(arr, 5)),
        "p50": float(np.nanpercentile(arr, 50)),
        "p95": float(np.nanpercentile(arr, 95)),
        "n": float(n),
    }
