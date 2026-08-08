"""Climatology anomalies + z-score for stable training."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class NormStats:
    clim: dict[int, np.ndarray]  # month -> (Z,Y,X) oxygen clim
    mean: np.ndarray  # (Z,Y,X) oxygen anomaly mean
    std: np.ndarray
    # optional physics channel stats on raw history channels beyond oxygen
    phys_mean: np.ndarray | None = None  # (C_phys, Y, X)
    phys_std: np.ndarray | None = None


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


def fit_phys_channel_stats(x_train: np.ndarray, n_oxygen: int) -> tuple[np.ndarray, np.ndarray]:
    """x_train: (N,H,C,Y,X). Stats over N,H for channels after oxygen."""
    phys = x_train[:, :, n_oxygen:, :, :]
    if phys.shape[2] == 0:
        return np.zeros((0, 1, 1), dtype=np.float32), np.ones((0, 1, 1), dtype=np.float32)
    mean = np.nanmean(phys, axis=(0, 1)).astype(np.float32)
    std = np.nanstd(phys, axis=(0, 1)).astype(np.float32)
    std = np.where(std < 1e-6, 1.0, std)
    return mean, std


def normalize_anom(anom: np.ndarray, stats: NormStats) -> np.ndarray:
    return (anom - stats.mean) / stats.std


def denormalize_anom(normed: np.ndarray, stats: NormStats) -> np.ndarray:
    return normed * stats.std + stats.mean


def history_to_norm_anom(
    x: np.ndarray,
    times_last: np.ndarray,
    stats: NormStats,
    history: int,
    n_oxygen: int | None = None,
) -> np.ndarray:
    """Convert history cube (N,H,C,Y,X) to normalized features.

    Oxygen channels: month-of-year anomaly + z-score.
    Extra physics channels: z-score with phys_mean/std (or identity if absent).
    """
    n, h, c, y, w = x.shape
    n_oxygen = n_oxygen if n_oxygen is not None else min(c, stats.mean.shape[0])
    out = np.empty_like(x)
    for i in range(n):
        end = pd.Timestamp(times_last[i])
        for k in range(h):
            t = end - pd.DateOffset(months=(h - 1 - k))
            month = t.month
            clim = stats.clim.get(month)
            if clim is None:
                clim = stats.mean * 0
            oxy = x[i, k, :n_oxygen]
            anom = oxy - clim
            out[i, k, :n_oxygen] = (anom - stats.mean) / stats.std
            if c > n_oxygen:
                phys = x[i, k, n_oxygen:]
                if stats.phys_mean is not None and stats.phys_std is not None:
                    out[i, k, n_oxygen:] = (phys - stats.phys_mean) / stats.phys_std
                else:
                    out[i, k, n_oxygen:] = phys
    return out.astype(np.float32)
