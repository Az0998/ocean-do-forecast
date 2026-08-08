"""Simple physical constraints / residuals for DO."""
from __future__ import annotations

import torch
import torch.nn.functional as F


def nonneg_oxygen(pred: torch.Tensor) -> torch.Tensor:
    return F.relu(pred)


def solubility_proxy(temp_c: torch.Tensor) -> torch.Tensor:
    """Very rough O2 solubility proxy (µmol/kg scale) from temperature.

    Not Garcia-Gordon; used only as a soft residual feature.
    """
    return 300.0 - 5.0 * temp_c


def physics_residual_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor | None = None,
    lambda_smooth: float = 0.01,
) -> torch.Tensor:
    """MSE + weak spatial smoothness (encourages coherent fields)."""
    err = (pred - target) ** 2
    if mask is not None:
        m = mask
        while m.ndim < err.ndim:
            m = m.unsqueeze(0)
        err = err * m
        denom = m.sum().clamp_min(1.0)
        mse = err.sum() / denom
    else:
        mse = err.mean()
    # spatial Laplacian-ish on last two dims
    if pred.ndim >= 3:
        dh = pred[..., 1:, :] - pred[..., :-1, :]
        dw = pred[..., :, 1:] - pred[..., :, :-1]
        smooth = dh.pow(2).mean() + dw.pow(2).mean()
    else:
        smooth = pred.new_zeros(())
    return mse + lambda_smooth * smooth
