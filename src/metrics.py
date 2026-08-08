"""Forecast and hypoxia-event metrics (stubs for week 3+)."""

from __future__ import annotations

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


def skill_vs_persistence(
    y_true: np.ndarray, y_pred: np.ndarray, y_persist: np.ndarray
) -> float:
    """1 - MSE_model / MSE_persistence (higher is better)."""
    mse_m = np.nanmean((y_pred - y_true) ** 2)
    mse_p = np.nanmean((y_persist - y_true) ** 2)
    if mse_p <= 0 or not np.isfinite(mse_p):
        return float("nan")
    return float(1.0 - mse_m / mse_p)


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
