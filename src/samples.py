"""Build supervised lead-time forecast samples from a monthly oxygen cube."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
import xarray as xr

from config import HISTORY_MONTHS, LEADS_MONTHS, TRAIN_END, VAL_END


@dataclass
class ForecastArrays:
    """x: (N, H, Z, Y, X), y: (N, L, Z, Y, X), meta times."""

    x: np.ndarray
    y: np.ndarray
    times: np.ndarray  # target month for lead=1
    hist_times: np.ndarray  # last month in the history window
    leads: list[int]
    mask: np.ndarray  # ocean mask (Z,Y,X) or (Y,X)


def _time_split_labels(times: pd.DatetimeIndex) -> np.ndarray:
    """Return 0=train, 1=val, 2=test for each sample indexed by target time."""
    labels = np.zeros(len(times), dtype=np.int64)
    train_end = pd.Period(TRAIN_END, freq="M").to_timestamp()
    val_end = pd.Period(VAL_END, freq="M").to_timestamp()
    for i, t in enumerate(times):
        ts = pd.Timestamp(t)
        if ts <= train_end:
            labels[i] = 0
        elif ts <= val_end:
            labels[i] = 1
        else:
            labels[i] = 2
    return labels


def build_forecast_arrays(
    ds: xr.Dataset,
    history: int = HISTORY_MONTHS,
    leads: list[int] | None = None,
) -> ForecastArrays:
    leads = leads or LEADS_MONTHS
    oxy = ds["oxygen"].transpose("time", "depth", "lat", "lon")
    data = oxy.values.astype(np.float32)
    times = pd.to_datetime(oxy["time"].values)
    T, Z, Y, X = data.shape
    max_lead = max(leads)
    xs, ys, t_list, h_list = [], [], [], []
    for t in range(history - 1, T - max_lead):
        x = data[t - history + 1 : t + 1]
        y = np.stack([data[t + lead] for lead in leads], axis=0)
        if not np.isfinite(x).any() or not np.isfinite(y).any():
            continue
        xs.append(x)
        ys.append(y)
        t_list.append(times[t + leads[0]])
        h_list.append(times[t])
    x_arr = np.stack(xs).astype(np.float32)
    y_arr = np.stack(ys).astype(np.float32)
    # fill nan with per-depth mean for model stability; keep mask
    mask = np.isfinite(data).any(axis=0)  # Z,Y,X
    fill = np.nanmean(data, axis=0)
    fill = np.where(np.isfinite(fill), fill, 0.0).astype(np.float32)
    for arr in (x_arr, y_arr):
        nan = ~np.isfinite(arr)
        if nan.any():
            arr[nan] = np.broadcast_to(fill, arr.shape)[nan]
    return ForecastArrays(
        x=x_arr,
        y=y_arr,
        times=np.array(t_list),
        hist_times=np.array(h_list),
        leads=list(leads),
        mask=mask.astype(np.float32),
    )


def split_arrays(fa: ForecastArrays) -> dict[str, dict[str, np.ndarray]]:
    labels = _time_split_labels(pd.DatetimeIndex(fa.times))
    out = {}
    for name, lab in [("train", 0), ("val", 1), ("test", 2)]:
        idx = np.where(labels == lab)[0]
        out[name] = {
            "x": fa.x[idx],
            "y": fa.y[idx],
            "times": fa.times[idx],
            "hist_times": fa.hist_times[idx],
        }
    out["meta"] = {"leads": fa.leads, "mask": fa.mask}
    return out


class OxygenForecastDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray, lead_index: int = 0):
        self.x = torch.from_numpy(x)
        self.y = torch.from_numpy(y[:, lead_index])

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, i: int):
        # flatten spatial for LSTM path: (H, Z*Y*X)
        x = self.x[i]
        y = self.y[i]
        return x, y


def flatten_space(x: torch.Tensor) -> torch.Tensor:
    """(B,H,Z,Y,X) -> (B,H,F) or (H,Z,Y,X)->(H,F)."""
    return x.reshape(*x.shape[:-3], -1)
