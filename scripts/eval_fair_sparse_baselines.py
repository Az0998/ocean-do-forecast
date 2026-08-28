#!/usr/bin/env python
"""Fair Mask-View simple baselines: they ingest the *masked* oxygen history.

The published persist/clim numbers are invariant to sparsity because
`run_multilead.py` scored them on unmasked history. Climatology still does
not need recent O2 (valid operational fallback). Persistence and linear
interpolation must see the same mask as the Transformer.

Does not retrain ST. Reapplies the same Mask-View seeds as `run_multilead.py`.

Lake analog: persist_locf ↔ LOCF, linear_time ↔ Linear (no spatial borrow).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from config import (
    HYPOXIA_UMOL_KG,
    LEADS_MONTHS,
    LOW_O2_MIN_EVENT_RATE,
    LOW_O2_PERCENTILE,
    PROCESSED,
    SEED,
    TABLES,
    ensure_dirs,
    load_active_region,
)
from src.gobai_data import load_or_build_cube
from src.metrics import binary_event_scores, choose_event_threshold
from src.models.baselines import (
    climatology_predict,
    evaluate_regression,
    fill_with_climatology,
    last_observed_persist,
    persistence_predict,
    spatial_linear_persist,
    time_linear_persist,
)
from src.samples import build_forecast_arrays, split_arrays
from src.sparse_mask import MASK_PATTERNS, make_batch_masks, sample_block_time_mask

KEEP_RATIO = 0.25
N_STATIONS = 8
LEAD_ST_JSON = {
    "none": "multilead_full_physics.json",
    "point": "multilead_point_physics.json",
    "block": "multilead_block_physics.json",
    "block_time": "multilead_block_time_physics.json",
    "sensor": "multilead_sensor_physics.json",
    "station": "multilead_station_physics.json",
    "mixed": "multilead_mixed_physics.json",
    "argo": "multilead_argo_physics.json",
}


def oxygen_history_keep(
    x_raw: np.ndarray,
    pattern: str,
    seed: int,
    n_oxygen: int,
    lat: np.ndarray,
    lon: np.ndarray,
    argo_path: Path,
) -> np.ndarray:
    """(N,H,Z,Y,X) keep mask matching run_multilead.py."""
    n, h, _c, y, x = x_raw.shape
    z = n_oxygen
    if pattern == "none":
        return np.ones((n, h, z, y, x), dtype=np.float32)
    if pattern == "block_time":
        rng = np.random.default_rng(seed)
        keep = np.empty((n, h, z, y, x), dtype=np.float32)
        for i in range(n):
            keep[i] = sample_block_time_mask((h, z, y, x), KEEP_RATIO, rng)
        return keep
    m = make_batch_masks(
        x_raw,
        pattern,
        KEEP_RATIO,
        N_STATIONS,
        seed=seed,
        n_oxygen=n_oxygen,
        lat=lat,
        lon=lon,
        argo_stations_path=argo_path,
    )
    return np.broadcast_to(m, (n, h, z, y, x)).copy()


def keep_stats(keep: np.ndarray, water: np.ndarray) -> dict:
    w = water > 0.5
    k = keep[:, :, w]
    any_t = keep.max(axis=1)[:, w]
    last = keep[:, -1, w]
    return {
        "keep_frac": float(k.mean()) if k.size else float("nan"),
        "last_month_keep_frac": float(last.mean()) if last.size else float("nan"),
        "voxel_any_obs_frac": float(any_t.mean()) if any_t.size else float("nan"),
        "n_test": int(keep.shape[0]),
        "n_water_voxels": int(w.sum()),
    }


def st_lookup() -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    for pat, name in LEAD_ST_JSON.items():
        path = TABLES / name
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for rec in payload.get("metrics", []):
            if rec.get("model") != "st_transformer":
                continue
            out[(pat, int(rec["lead_months"]))] = rec
    return out


def main() -> None:
    ensure_dirs()
    region = load_active_region()
    ds = load_or_build_cube(region, prefer_demo=False, prefer_physics=True)
    if ds.attrs.get("source") == "demo":
        raise SystemExit("Refusing demo cube — need regional_physics_cube.nc")
    fa = build_forecast_arrays(ds, leads=LEADS_MONTHS, use_physics=True)
    splits = split_arrays(fa)
    water = splits["meta"]["mask"]
    n_oxygen = int(splits["meta"]["n_oxygen"])
    lat = ds["lat"].values
    lon = ds["lon"].values
    argo_path = PROCESSED / "argo_stations.json"
    y_tr0 = splits["train"]["y"][:, 0]
    event_thr, event_mode = choose_event_threshold(
        y_tr0,
        absolute=HYPOXIA_UMOL_KG,
        percentile=LOW_O2_PERCENTILE,
        min_rate=LOW_O2_MIN_EVENT_RATE,
    )
    st_map = st_lookup()
    rows: list[dict] = []
    keep_rows: list[dict] = []
    x_te_raw = splits["test"]["x"]
    oxy_hist = x_te_raw[:, :, :n_oxygen]
    t_te = splits["test"]["times"]

    for li, lead in enumerate(LEADS_MONTHS):
        y_te = splits["test"]["y"][:, li]
        t_tr = splits["train"]["times"]
        clim = climatology_predict(splits["train"]["y"][:, li], t_tr, t_te)
        persist_oracle = persistence_predict(oxy_hist)
        seed = SEED + 200 + lead
        for pattern in MASK_PATTERNS:
            keep = oxygen_history_keep(
                x_te_raw, pattern, seed, n_oxygen, lat, lon, argo_path
            )
            stats = keep_stats(keep, water)
            stats.update({"pattern": pattern, "lead": lead})
            keep_rows.append(stats)
            locf = fill_with_climatology(last_observed_persist(oxy_hist, keep), clim)
            linear = fill_with_climatology(time_linear_persist(oxy_hist, keep), clim)
            spatial = fill_with_climatology(spatial_linear_persist(oxy_hist, keep), clim)
            preds = {
                "persist_unmasked": persist_oracle,
                "persist_locf": locf,
                "linear_time": linear,
                "spatial_linear": spatial,
                "climatology": clim,
            }
            for name, pred in preds.items():
                reg = evaluate_regression(y_te, pred, water)
                ev = binary_event_scores(y_te, pred, event_thr)
                rows.append(
                    {
                        "pattern": pattern,
                        "lead": lead,
                        "model": name,
                        "RMSE": round(float(reg["rmse"]), 3),
                        "MAE": round(float(reg["mae"]), 3),
                        "F1": round(ev["f1"], 3),
                        "CSI": round(ev["csi"], 3),
                        "keep_frac": round(stats["keep_frac"], 4),
                        "last_month_keep_frac": round(stats["last_month_keep_frac"], 4),
                        "voxel_any_obs_frac": round(stats["voxel_any_obs_frac"], 4),
                    }
                )
            st_rec = st_map.get((pattern, lead))
            if st_rec is not None:
                rows.append(
                    {
                        "pattern": pattern,
                        "lead": lead,
                        "model": "st_transformer",
                        "RMSE": round(float(st_rec["rmse"]), 3),
                        "MAE": round(float(st_rec["mae"]), 3)
                        if st_rec.get("mae") is not None
                        else "",
                        "F1": round(float(st_rec["hypoxia_f1"]), 3),
                        "CSI": round(float(st_rec["hypoxia_csi"]), 3),
                        "keep_frac": round(stats["keep_frac"], 4),
                        "last_month_keep_frac": round(stats["last_month_keep_frac"], 4),
                        "voxel_any_obs_frac": round(stats["voxel_any_obs_frac"], 4),
                    }
                )

    df = pd.DataFrame(rows)
    keep_df = pd.DataFrame(keep_rows)
    out = TABLES / "fair_sparse_baselines.csv"
    keep_out = TABLES / "maskview_keep_rates.csv"
    df.to_csv(out, index=False)
    keep_df.to_csv(keep_out, index=False)

    d1 = df[df.lead == 1]
    lines = [
        "# Fair sparse baselines (masked oxygen history)",
        "",
        f"Cube `{ds.attrs.get('source')}`; event `{event_mode}` thr={event_thr:.2f}.",
        "persist_unmasked ignores the mask (original number). persist_locf /",
        "linear_time are temporal; spatial_linear fills missing columns horizontally.",
        "Empty voxels fall back to climatology. Static spatial masks make linear_time equal persist_locf.",
        "",
        "| Pattern | keep | persist_unmasked | persist_locf | linear_time | spatial_linear | clim | ST | fair simple best | ST beats fair simple |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for pat in MASK_PATTERNS:
        sub = d1[d1.pattern == pat]

        def g(m: str) -> float:
            hit = sub[sub.model == m]
            return float(hit.RMSE.iloc[0]) if len(hit) else float("nan")

        k = float(sub.keep_frac.iloc[0])
        simple = {
            "persist_locf": g("persist_locf"),
            "linear_time": g("linear_time"),
            "spatial_linear": g("spatial_linear"),
            "climatology": g("climatology"),
        }
        best_s = min(simple, key=simple.get)
        st = g("st_transformer")
        lines.append(
            f"| {pat} | {k:.3f} | {g('persist_unmasked'):.3f} | "
            f"{simple['persist_locf']:.3f} | {simple['linear_time']:.3f} | "
            f"{simple['spatial_linear']:.3f} | {simple['climatology']:.3f} | "
            f"{st:.3f} | {best_s} | {st < simple[best_s]} |"
        )
    md = TABLES / "fair_sparse_baselines.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", out)
    print("Wrote", keep_out)
    print(md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
