"""LSTM baseline over flattened spatial field."""
from __future__ import annotations

import torch
import torch.nn as nn


class LSTMForecast(nn.Module):
    def __init__(self, feature_dim: int, hidden: int = 64, n_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=feature_dim,
            hidden_size=hidden,
            num_layers=n_layers,
            batch_first=True,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, feature_dim),
        )
        self.feature_dim = feature_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, H, F)
        out, _ = self.lstm(x)
        pred = self.head(out[:, -1])
        return pred
