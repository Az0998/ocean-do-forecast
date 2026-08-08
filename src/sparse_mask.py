"""Sparse-observation masks inspired by Dianchi Mask-View.

Patterns:
  point / block_time / sensor / station / block / mixed / argo
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


MASK_PATTERNS = (
    "none",
    "point",
    "block",
    "block_time",
    "sensor",
    "station",
    "mixed",
    "argo",
)


def apply_mask(x: np.ndarray, mask: np.ndarray, fill: float = 0.0) -> np.ndarray:
    """x: (..., C,Y,X); mask broadcastable on spatial dims, 1=keep.

    If mask is (Z,Y,X) and C > Z, only the first Z (oxygen) channels are masked;
    physics channels stay visible (forcings are assumed available).
    """
    out = x.copy()
    # mask expected (N,1,Z,Y,X) or (Z,Y,X)
    if mask.ndim == out.ndim:
        m = mask
    else:
        m = mask
        while m.ndim < out.ndim:
            m = np.expand_dims(m, 0)
    # Channel-aware: if C != Z, pad mask channels with ones for physics
    if out.ndim >= 3 and m.shape[-3] != out.shape[-3]:
        z = m.shape[-3]
        c = out.shape[-3]
        if c > z:
            pad = np.ones(m.shape[:-3] + (c - z,) + m.shape[-2:], dtype=m.dtype)
            m = np.concatenate([m, pad], axis=-3)
        else:
            m = m[..., :c, :, :]
    m = np.broadcast_to(m, out.shape)
    out = np.where(m > 0, out, fill)
    return out.astype(np.float32)


def sample_point_mask(shape_zyx, keep_ratio, rng):
    z, y, x = shape_zyx
    m = (rng.random((z, y, x)) < keep_ratio).astype(np.float32)
    if m.sum() == 0:
        m[0, 0, 0] = 1.0
    return m


def sample_block_mask(shape_zyx, keep_ratio, rng):
    z, y, x = shape_zyx
    area = max(1, int(round(y * x * keep_ratio)))
    bh = max(1, int(round(np.sqrt(area * y / max(x, 1)))))
    bw = max(1, int(round(area / bh)))
    bh, bw = min(bh, y), min(bw, x)
    i0 = int(rng.integers(0, max(1, y - bh + 1)))
    j0 = int(rng.integers(0, max(1, x - bw + 1)))
    m = np.zeros((z, y, x), dtype=np.float32)
    m[:, i0 : i0 + bh, j0 : j0 + bw] = 1.0
    return m


def sample_block_time_mask(shape_hzyx, keep_ratio, rng):
    """(H,Z,Y,X): zero a contiguous time slab over a spatial block."""
    h, z, y, x = shape_hzyx
    m = np.ones((h, z, y, x), dtype=np.float32)
    spatial = sample_block_mask((z, y, x), max(keep_ratio, 0.2), rng)
    # hide complementary block for a time span
    tlen = max(1, int(round(h * (1.0 - keep_ratio))))
    t0 = int(rng.integers(0, max(1, h - tlen + 1)))
    hide = 1.0 - spatial
    m[t0 : t0 + tlen] = m[t0 : t0 + tlen] * (1.0 - hide)
    return m


def sample_sensor_mask(shape_zyx, keep_ratio, rng):
    """Drop entire depth layers (sensor failure), keep ratio of depths."""
    z, y, x = shape_zyx
    m = np.zeros((z, y, x), dtype=np.float32)
    n_keep = max(1, int(round(z * keep_ratio)))
    keep = rng.choice(z, size=n_keep, replace=False)
    m[keep, :, :] = 1.0
    return m


def sample_station_mask(shape_zyx, n_stations, rng):
    z, y, x = shape_zyx
    m = np.zeros((z, y, x), dtype=np.float32)
    n_stations = max(1, min(n_stations, y * x))
    flat = rng.choice(y * x, size=n_stations, replace=False)
    for f in flat:
        i, j = divmod(int(f), x)
        m[:, i, j] = 1.0
    return m


def sample_mixed_mask(shape_zyx, keep_ratio, n_stations, rng):
    """Station columns plus extra point samples (Mask-View mixed)."""
    m = sample_station_mask(shape_zyx, n_stations, rng)
    extra = sample_point_mask(shape_zyx, keep_ratio * 0.5, rng)
    return np.clip(m + extra, 0, 1).astype(np.float32)


def load_argo_station_cells(
    lat: np.ndarray,
    lon: np.ndarray,
    stations_json: Path,
) -> list[tuple[int, int]]:
    if not stations_json.exists():
        return []
    payload = json.loads(stations_json.read_text(encoding="utf-8"))
    coords = payload.get("stations") or payload.get("profiles") or []
    cells = []
    for c in coords:
        la = float(c.get("lat") or c.get("latitude"))
        lo = float(c.get("lon") or c.get("longitude"))
        i = int(np.argmin(np.abs(lat - la)))
        j = int(np.argmin(np.abs(lon - lo)))
        cells.append((i, j))
    # unique
    return sorted(set(cells))


def sample_argo_mask(shape_zyx, lat, lon, stations_json: Path, rng, n_fallback=8):
    z, y, x = shape_zyx
    cells = load_argo_station_cells(lat, lon, stations_json)
    m = np.zeros((z, y, x), dtype=np.float32)
    if not cells:
        return sample_station_mask(shape_zyx, n_fallback, rng)
    for i, j in cells:
        if 0 <= i < y and 0 <= j < x:
            m[:, i, j] = 1.0
    if m.sum() == 0:
        return sample_station_mask(shape_zyx, n_fallback, rng)
    return m


def make_batch_masks(
    batch_x: np.ndarray,
    pattern: str,
    keep_ratio: float = 0.25,
    n_stations: int = 8,
    seed: int = 0,
    n_oxygen: int | None = None,
    lat: np.ndarray | None = None,
    lon: np.ndarray | None = None,
    argo_stations_path: Path | None = None,
) -> np.ndarray:
    """Return masks shaped (N,1,Z,Y,X) for oxygen channels."""
    rng = np.random.default_rng(seed)
    n, h, c, y, x = batch_x.shape
    z = n_oxygen if n_oxygen is not None else c
    masks = np.ones((n, 1, z, y, x), dtype=np.float32)
    argo_path = argo_stations_path or Path("data/processed/argo_stations.json")

    for i in range(n):
        if pattern == "point":
            m = sample_point_mask((z, y, x), keep_ratio, rng)
        elif pattern == "block":
            m = sample_block_mask((z, y, x), keep_ratio, rng)
        elif pattern == "block_time":
            # collapse time-varying mask to oxygen keep if any time kept
            mt = sample_block_time_mask((h, z, y, x), keep_ratio, rng)
            m = (mt.max(axis=0) > 0).astype(np.float32)
            # also store time mask by zeroing history externally — apply below
            masks[i, 0] = m
            continue
        elif pattern == "sensor":
            m = sample_sensor_mask((z, y, x), keep_ratio, rng)
        elif pattern == "station":
            m = sample_station_mask((z, y, x), n_stations, rng)
        elif pattern == "mixed":
            m = sample_mixed_mask((z, y, x), keep_ratio, n_stations, rng)
        elif pattern == "argo":
            if lat is None or lon is None:
                m = sample_station_mask((z, y, x), n_stations, rng)
            else:
                m = sample_argo_mask((z, y, x), lat, lon, argo_path, rng, n_stations)
        else:
            raise ValueError(pattern)
        masks[i, 0] = m
    return masks


def apply_block_time_to_batch(
    batch_x: np.ndarray,
    keep_ratio: float,
    n_oxygen: int,
    seed: int,
) -> np.ndarray:
    """Apply true (N,H,Z,Y,X) temporal block masks on oxygen channels."""
    rng = np.random.default_rng(seed)
    out = batch_x.copy()
    n, h, c, y, x = batch_x.shape
    z = n_oxygen
    for i in range(n):
        mt = sample_block_time_mask((h, z, y, x), keep_ratio, rng)
        # expand phys channels keep=1
        if c > z:
            pad = np.ones((h, c - z, y, x), dtype=np.float32)
            m = np.concatenate([mt, pad], axis=1)
        else:
            m = mt
        out[i] = np.where(m > 0, out[i], 0.0)
    return out.astype(np.float32)
