"""Sparse-observation masks inspired by Mask-View (point / block / station)."""
from __future__ import annotations

import numpy as np


def apply_mask(x: np.ndarray, mask: np.ndarray, fill: float = 0.0) -> np.ndarray:
    """x: (..., Z,Y,X); mask broadcastable, 1=keep."""
    out = x.copy()
    m = mask
    while m.ndim < out.ndim:
        m = np.expand_dims(m, 0)
    m = np.broadcast_to(m, out.shape)
    out = np.where(m > 0, out, fill)
    return out.astype(np.float32)


def sample_point_mask(
    shape_zyx: tuple[int, int, int],
    keep_ratio: float,
    rng: np.random.Generator,
) -> np.ndarray:
    z, y, x = shape_zyx
    m = (rng.random((z, y, x)) < keep_ratio).astype(np.float32)
    # ensure at least one keep
    if m.sum() == 0:
        m[0, 0, 0] = 1.0
    return m


def sample_block_mask(
    shape_zyx: tuple[int, int, int],
    keep_ratio: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Keep a contiguous lat-lon block (same for all depths)."""
    z, y, x = shape_zyx
    # approximate keep via block area
    area = max(1, int(round(y * x * keep_ratio)))
    bh = max(1, int(round(np.sqrt(area * y / max(x, 1)))))
    bw = max(1, int(round(area / bh)))
    bh, bw = min(bh, y), min(bw, x)
    i0 = int(rng.integers(0, max(1, y - bh + 1)))
    j0 = int(rng.integers(0, max(1, x - bw + 1)))
    m = np.zeros((z, y, x), dtype=np.float32)
    m[:, i0 : i0 + bh, j0 : j0 + bw] = 1.0
    return m


def sample_station_mask(
    shape_zyx: tuple[int, int, int],
    n_stations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Keep full-depth columns at random lat-lon 'stations' (Argo-like)."""
    z, y, x = shape_zyx
    m = np.zeros((z, y, x), dtype=np.float32)
    n_stations = max(1, min(n_stations, y * x))
    flat = rng.choice(y * x, size=n_stations, replace=False)
    for f in flat:
        i, j = divmod(int(f), x)
        m[:, i, j] = 1.0
    return m


def make_batch_masks(
    batch_x: np.ndarray,
    pattern: str,
    keep_ratio: float = 0.25,
    n_stations: int = 8,
    seed: int = 0,
) -> np.ndarray:
    """Return masks shaped (N,1,Z,Y,X) for history cubes (N,H,Z,Y,X)."""
    rng = np.random.default_rng(seed)
    n, h, z, y, x = batch_x.shape
    masks = np.ones((n, 1, z, y, x), dtype=np.float32)
    for i in range(n):
        if pattern == "point":
            m = sample_point_mask((z, y, x), keep_ratio, rng)
        elif pattern == "block":
            m = sample_block_mask((z, y, x), keep_ratio, rng)
        elif pattern == "station":
            m = sample_station_mask((z, y, x), n_stations, rng)
        else:
            raise ValueError(pattern)
        masks[i, 0] = m
    return masks
