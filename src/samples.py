"""Build supervised lead-time forecast samples from monthly oxygen / physics cubes."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
import xarray as xr

from config import HISTORY_MONTHS, LEADS_MONTHS, TRAIN_END, VAL_END


@dataclass
class ForecastArrays:
    """x: (N, H, C, Y, X), y: (N, L, Z, Y, X) oxygen targets, meta times.

    Channel layout when physics enabled:
      [oxygen depths (Z) | temp (Z) | salt (Z) | n2 (Z) | sst | wind | t2m]
    Without physics, C == Z (oxygen only).
    """

    x: np.ndarray
    y: np.ndarray
    times: np.ndarray
    hist_times: np.ndarray
    leads: list[int]
    mask: np.ndarray  # (Z,Y,X) ocean mask for oxygen
    n_oxygen: int
    channel_names: list[str]


def _time_split_labels(times: pd.DatetimeIndex) -> np.ndarray:
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


def _fill_nan(arr: np.ndarray) -> np.ndarray:
    with np.errstate(all="ignore"):
        fill = np.nanmean(arr, axis=0)
    fill = np.where(np.isfinite(fill), fill, 0.0).astype(np.float32)
    nan = ~np.isfinite(arr)
    if nan.any():
        arr = arr.copy()
        arr[nan] = np.broadcast_to(fill, arr.shape)[nan]
    return arr.astype(np.float32)


def _stack_physics_channels(ds: xr.Dataset) -> tuple[np.ndarray, list[str], int]:
    """Return field (T,C,Y,X), names, n_oxygen."""
    oxy = ds["oxygen"].transpose("time", "depth", "lat", "lon").values.astype(np.float32)
    t, z, y, x = oxy.shape
    names = [f"oxygen_z{i}" for i in range(z)]
    chunks = [oxy]

    def add_vol(name: str, key: str):
        nonlocal names
        if key not in ds:
            return
        vol = ds[key].transpose("time", "depth", "lat", "lon").values.astype(np.float32)
        chunks.append(vol)
        names.extend([f"{name}_z{i}" for i in range(z)])

    def add_surf(name: str, key: str):
        nonlocal names
        if key not in ds:
            return
        s = ds[key].transpose("time", "lat", "lon").values.astype(np.float32)
        chunks.append(s[:, None, :, :])
        names.append(name)

    add_vol("temp", "temp")
    add_vol("salt", "salt")
    add_vol("n2", "n2")
    add_surf("sst", "sst")
    add_surf("wind", "wind_speed")
    add_surf("t2m", "t2m")

    field = np.concatenate(chunks, axis=1)  # T,C,Y,X
    return field, names, z


def build_forecast_arrays(
    ds: xr.Dataset,
    history: int = HISTORY_MONTHS,
    leads: list[int] | None = None,
    use_physics: bool = False,
) -> ForecastArrays:
    leads = leads or LEADS_MONTHS
    oxy = ds["oxygen"].transpose("time", "depth", "lat", "lon")
    oxy_data = oxy.values.astype(np.float32)
    times = pd.to_datetime(oxy["time"].values)
    if use_physics and any(k in ds for k in ("temp", "salt", "sst", "wind_speed")):
        field, channel_names, n_oxygen = _stack_physics_channels(ds)
    else:
        field = oxy_data  # T,Z,Y,X
        n_oxygen = oxy_data.shape[1]
        channel_names = [f"oxygen_z{i}" for i in range(n_oxygen)]

    field = _fill_nan(field)
    oxy_data = _fill_nan(oxy_data)
    T, C, Y, X = field.shape
    Z = n_oxygen
    max_lead = max(leads)
    xs, ys, t_list, h_list = [], [], [], []
    for t in range(history - 1, T - max_lead):
        x = field[t - history + 1 : t + 1]
        y = np.stack([oxy_data[t + lead] for lead in leads], axis=0)
        if not np.isfinite(x).any() or not np.isfinite(y).any():
            continue
        xs.append(x)
        ys.append(y)
        t_list.append(times[t + leads[0]])
        h_list.append(times[t])
    x_arr = np.stack(xs).astype(np.float32)
    y_arr = np.stack(ys).astype(np.float32)
    mask = np.isfinite(oxy.values).any(axis=0).astype(np.float32)  # Z,Y,X
    return ForecastArrays(
        x=x_arr,
        y=y_arr,
        times=np.array(t_list),
        hist_times=np.array(h_list),
        leads=list(leads),
        mask=mask,
        n_oxygen=Z,
        channel_names=channel_names,
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
    out["meta"] = {
        "leads": fa.leads,
        "mask": fa.mask,
        "n_oxygen": fa.n_oxygen,
        "channel_names": fa.channel_names,
    }
    return out


class OxygenForecastDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray, lead_index: int = 0):
        self.x = torch.from_numpy(x)
        self.y = torch.from_numpy(y[:, lead_index])

    def __len__(self) -> int:
        return self.x.shape[0]

    def __getitem__(self, i: int):
        return self.x[i], self.y[i]


def flatten_space(x: torch.Tensor) -> torch.Tensor:
    """(B,H,C,Y,X) -> (B,H,F)."""
    return x.reshape(*x.shape[:-3], -1)
