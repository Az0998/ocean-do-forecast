"""Climatology anomalies + z-score for stable training."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class NormStats:
    clim: dict[int, np.ndarray]  # month -> (Z,Y,X)
    mean: np.ndarray  # (Z,Y,X)
    std: np.ndarray


def month_climatology(fields: np.ndarray, times: np.ndarray) -> dict[int, np.ndarray]:
    months = pd.DatetimeIndex(times).month
    clim = {}
    for m in range(1, 13):
        idx = np.where(months == m)[0]
        if len(idx):
            clim[m] = np.nanmean(fields[idx], axis=0).astype(np.float32)
    return clim


def apply_clim(fields: np.ndarray, times: np.ndarray, clim: dict[int, np.ndarray]) -> np.ndarray:
    months = pd.DatetimeIndex(times).month
    out = np.empty_like(fields)
    fallback = np.nanmean(np.stack(list(clim.values())), axis=0) if clim else 0.0
    for i, m in enumerate(months):
        out[i] = clim.get(int(m), fallback)
    return out


def to_anomaly(fields: np.ndarray, times: np.ndarray, clim: dict[int, np.ndarray]) -> np.ndarray:
    return fields - apply_clim(fields, times, clim)


def fit_norm_from_train(y_train: np.ndarray, times_train: np.ndarray) -> NormStats:
    clim = month_climatology(y_train, times_train)
    anom = to_anomaly(y_train, times_train, clim)
    mean = np.nanmean(anom, axis=0).astype(np.float32)
    std = np.nanstd(anom, axis=0).astype(np.float32)
    std = np.where(std < 1e-3, 1.0, std)
    return NormStats(clim=clim, mean=mean, std=std)


def normalize_anom(anom: np.ndarray, stats: NormStats) -> np.ndarray:
    return (anom - stats.mean) / stats.std


def denormalize_anom(normed: np.ndarray, stats: NormStats) -> np.ndarray:
    return normed * stats.std + stats.mean


def history_to_norm_anom(
    x: np.ndarray, times_last: np.ndarray, stats: NormStats, history: int
) -> np.ndarray:
    """Convert history cube (N,H,Z,Y,X) to normalized anomalies using month of each step."""
    n, h = x.shape[:2]
    out = np.empty_like(x)
    # reconstruct timestamps for each history step from target-associated last month
    # times_last here is the last history month time (same as sample time index t)
    for i in range(n):
        end = pd.Timestamp(times_last[i])
        for k in range(h):
            t = end - pd.DateOffset(months=(h - 1 - k))
            month = t.month
            clim = stats.clim.get(month)
            if clim is None:
                clim = stats.mean * 0  # unlikely
            anom = x[i, k] - clim
            out[i, k] = (anom - stats.mean) / stats.std
    return out.astype(np.float32)
