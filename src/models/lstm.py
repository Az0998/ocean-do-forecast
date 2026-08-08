"""LSTM baseline over flattened spatial field."""
from __future__ import annotations

import torch
import torch.nn as nn


class LSTMForecast(nn.Module):
    def __init__(
        self,
        in_dim: int,
        out_dim: int | None = None,
        hidden: int = 64,
        n_layers: int = 2,
    ):
        super().__init__()
        out_dim = out_dim if out_dim is not None else in_dim
        self.lstm = nn.LSTM(
            input_size=in_dim,
            hidden_size=hidden,
            num_layers=n_layers,
            batch_first=True,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )
        self.in_dim = in_dim
        self.out_dim = out_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, H, F_in)
        out, _ = self.lstm(x)
        return self.head(out[:, -1])
