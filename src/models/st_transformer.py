"""Lightweight spatiotemporal Transformer for monthly DO cubes."""
from __future__ import annotations

import torch
import torch.nn as nn


class STTransformerForecast(nn.Module):
    """Encode history with temporal Transformer on per-grid tokens, decode to field.

    Input x: (B, H, Z, Y, X)
    Output: (B, Z, Y, X) for a single lead.
    """

    def __init__(
        self,
        n_depth: int,
        hidden: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        max_history: int = 24,
    ):
        super().__init__()
        self.n_depth = n_depth
        self.hidden = hidden
        self.in_proj = nn.Linear(n_depth, hidden)
        layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=n_heads,
            dim_feedforward=hidden * 4,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.time_embed = nn.Parameter(torch.randn(1, max_history, 1, hidden) * 0.02)
        self.out_proj = nn.Linear(hidden, n_depth)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: B,H,Z,Y,X -> B,H,Y*X,Z
        b, h, z, y, w = x.shape
        tokens = x.permute(0, 1, 3, 4, 2).reshape(b, h, y * w, z)
        tok = self.in_proj(tokens)  # B,H,N,C
        tok = tok + self.time_embed[:, :h]
        # merge batch and space: (B*N, H, C)
        n = y * w
        tok = tok.permute(0, 2, 1, 3).reshape(b * n, h, self.hidden)
        enc = self.encoder(tok)[:, -1]  # B*N, C
        out = self.out_proj(enc).reshape(b, y, w, z).permute(0, 3, 1, 2)
        return out
