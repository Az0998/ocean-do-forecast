"""Lightweight spatiotemporal Transformer for monthly DO cubes."""
from __future__ import annotations

import torch
import torch.nn as nn


class STTransformerForecast(nn.Module):
    """Encode history with temporal Transformer on per-grid tokens, decode oxygen field.

    Input x: (B, H, C, Y, X)  — C may be oxygen depths only, or oxygen+physics channels
    Output: (B, Z, Y, X) for a single lead (Z = n_oxygen).
    """

    def __init__(
        self,
        n_in: int,
        n_oxygen: int | None = None,
        hidden: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        max_history: int = 24,
    ):
        super().__init__()
        self.n_in = n_in
        self.n_oxygen = n_oxygen if n_oxygen is not None else n_in
        self.hidden = hidden
        self.in_proj = nn.Linear(n_in, hidden)
        layer = nn.TransformerEncoderLayer(
            d_model=hidden,
            nhead=n_heads,
            dim_feedforward=hidden * 4,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.time_embed = nn.Parameter(torch.randn(1, max_history, 1, hidden) * 0.02)
        self.out_proj = nn.Linear(hidden, self.n_oxygen)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: B,H,C,Y,X -> B,H,Y*X,C
        b, h, c, y, w = x.shape
        tokens = x.permute(0, 1, 3, 4, 2).reshape(b, h, y * w, c)
        tok = self.in_proj(tokens)
        tok = tok + self.time_embed[:, :h]
        n = y * w
        tok = tok.permute(0, 2, 1, 3).reshape(b * n, h, self.hidden)
        enc = self.encoder(tok)[:, -1]
        out = self.out_proj(enc).reshape(b, y, w, self.n_oxygen).permute(0, 3, 1, 2)
        return out
