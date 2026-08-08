"""Shared training loops for anomaly-normalized monthly forecasts."""
from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from config import BATCH_SIZE, HIDDEN, LR, N_HEADS, N_LAYERS
from src.models.lstm import LSTMForecast
from src.models.st_transformer import STTransformerForecast
from src.physics import physics_residual_loss
from src.samples import flatten_space


def train_lstm_anom(
    x_tr: np.ndarray,
    y_tr: np.ndarray,
    x_va: np.ndarray,
    y_va: np.ndarray,
    device: str,
    epochs: int,
) -> LSTMForecast:
    x_tr_f = flatten_space(torch.from_numpy(x_tr)).numpy()
    x_va_f = flatten_space(torch.from_numpy(x_va)).numpy()
    y_tr_f = y_tr.reshape(len(y_tr), -1)
    y_va_f = y_va.reshape(len(y_va), -1)
    model = LSTMForecast(x_tr_f.shape[-1], hidden=HIDDEN).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(x_tr_f), torch.from_numpy(y_tr_f)),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )
    best, best_val = None, float("inf")
    for _ in range(epochs):
        model.train()
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            loss = torch.mean((model(x) - y) ** 2)
            opt.zero_grad()
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vp = model(torch.from_numpy(x_va_f).to(device))
            vloss = float(torch.mean((vp - torch.from_numpy(y_va_f).to(device)) ** 2))
        if vloss < best_val:
            best_val = vloss
            best = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    if best:
        model.load_state_dict(best)
    return model


def predict_lstm(model: LSTMForecast, x: np.ndarray, device: str, out_shape) -> np.ndarray:
    x_f = flatten_space(torch.from_numpy(x)).to(device)
    model.eval()
    with torch.no_grad():
        pred = model(x_f).cpu().numpy().reshape(out_shape)
    return pred


def train_st_anom(
    x_tr: np.ndarray,
    y_tr: np.ndarray,
    x_va: np.ndarray,
    y_va: np.ndarray,
    mask: np.ndarray,
    device: str,
    epochs: int,
    use_physics: bool = True,
) -> STTransformerForecast:
    n_depth = x_tr.shape[2]
    model = STTransformerForecast(
        n_depth=n_depth, hidden=HIDDEN, n_heads=N_HEADS, n_layers=N_LAYERS
    ).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(x_tr), torch.from_numpy(y_tr)),
        batch_size=BATCH_SIZE,
        shuffle=True,
    )
    mask_t = torch.from_numpy(mask).to(device)
    best, best_val = None, float("inf")
    for _ in range(epochs):
        model.train()
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            pred = model(x)
            if use_physics:
                loss = physics_residual_loss(pred, y, mask_t, lambda_smooth=0.01)
            else:
                loss = torch.mean((pred - y) ** 2)
            opt.zero_grad()
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            vp = model(torch.from_numpy(x_va).to(device))
            vloss = float(torch.mean((vp - torch.from_numpy(y_va).to(device)) ** 2))
        if vloss < best_val:
            best_val = vloss
            best = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    if best:
        model.load_state_dict(best)
    return model


def predict_st(model: STTransformerForecast, x: np.ndarray, device: str) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return model(torch.from_numpy(x).to(device)).cpu().numpy()
