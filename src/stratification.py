"""Simple density / stratification proxies from T–S (no gsw required)."""
from __future__ import annotations

import numpy as np


def sigma0_linear(temp_c: np.ndarray, salt: np.ndarray) -> np.ndarray:
    """Linear EOS density anomaly proxy (kg/m³)."""
    return (
        1025.0
        - 0.2 * (temp_c.astype(np.float64) - 10.0)
        + 0.8 * (salt.astype(np.float64) - 35.0)
    ).astype(np.float32)


def buoyancy_freq_sq(
    temp_c: np.ndarray,
    salt: np.ndarray,
    depth_dbar: np.ndarray,
) -> np.ndarray:
    """Approximate N² on depth interfaces, then map back to level centers.

    temp/salt: (..., Z, Y, X) with Z matching depth_dbar ascending.
    Returns N² (s^-2) same shape, edge-padded.
    """
    rho = sigma0_linear(temp_c, salt)
    z = np.asarray(depth_dbar, dtype=np.float64)
    # depth increases downward; stable if denser below
    drho = np.diff(rho, axis=-3)
    dz = np.diff(z)
    dz = np.maximum(dz, 1.0)
    # broadcast dz onto (..., Z-1, Y, X)
    shape = [1] * drho.ndim
    shape[-3] = dz.shape[0]
    dz_b = dz.reshape(shape)
    g = 9.81
    n2_int = (g / 1025.0) * (drho / dz_b)
    # map interfaces -> levels
    n2 = np.empty_like(rho, dtype=np.float32)
    n2[..., 0, :, :] = n2_int[..., 0, :, :]
    n2[..., -1, :, :] = n2_int[..., -1, :, :]
    if n2.shape[-3] > 2:
        n2[..., 1:-1, :, :] = 0.5 * (n2_int[..., :-1, :, :] + n2_int[..., 1:, :, :])
    return n2.astype(np.float32)


def stratification_index(n2: np.ndarray) -> np.ndarray:
    """Surface-minus-deep density proxy via mean upper N² (..., Y, X)."""
    # mean over upper half of water column
    z = n2.shape[-3]
    k = max(1, z // 2)
    return np.nanmean(n2[..., :k, :, :], axis=-3).astype(np.float32)
