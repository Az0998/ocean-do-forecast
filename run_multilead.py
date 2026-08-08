#!/usr/bin/env python
"""Multi-lead evaluation: persistence / clim / LSTM / ST / hybrid (+ sparse / physics)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config import (
    DEVICE,
    EPOCHS,
    FIGS,
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
from src.hybrid import blend, depth_rmse_profile, tune_blend_weight
from src.metrics import binary_event_scores, choose_event_threshold, skill_vs_persistence
from src.models.baselines import (
    climatology_predict,
    evaluate_regression,
    persistence_predict,
)
from src.normalize import (
    apply_clim,
    denormalize_anom,
    fit_norm_from_train,
    fit_phys_channel_stats,
    history_to_norm_anom,
    normalize_anom,
    to_anomaly,
)
from src.samples import build_forecast_arrays, split_arrays
from src.sparse_mask import (
    MASK_PATTERNS,
    apply_block_time_to_batch,
    apply_mask,
    make_batch_masks,
)
from src.train_utils import predict_lstm, predict_st, train_lstm_anom, train_st_anom
from src.viz import depth_mean_rmse, plot_depth_rmse, plot_lead_skill, plot_spatial_rmse


def set_seed(seed: int = SEED):
    np.random.seed(seed)
    torch.manual_seed(seed)


def prepare_lead(splits, lead_index: int, stats, n_oxygen: int):
    def pack(split):
        y = split["y"][:, lead_index]
        x_n = history_to_norm_anom(
            split["x"],
            split["hist_times"],
            stats,
            split["x"].shape[1],
            n_oxygen=n_oxygen,
        )
        y_n = normalize_anom(to_anomaly(y, split["times"], stats.clim), stats)
        return x_n, y_n, y, split["times"], split["x"]

    return {k: pack(splits[k]) for k in ("train", "val", "test")}


def _oxygen_history(x_raw: np.ndarray, n_oxygen: int) -> np.ndarray:
    """Slice oxygen channels for persistence baseline."""
    return x_raw[:, :, :n_oxygen]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument(
        "--sparse",
        choices=[p for p in MASK_PATTERNS],
        default="none",
    )
    parser.add_argument("--keep-ratio", type=float, default=0.25)
    parser.add_argument("--stations", type=int, default=8)
    parser.add_argument(
        "--physics",
        action="store_true",
        help="Use regional_physics_cube (T/S/N2/SST/wind) as multi-channel drivers",
    )
    parser.add_argument(
        "--maskview",
        action="store_true",
        help="Train ST with Mask-View multi-view reconstruction + consistency",
    )
    parser.add_argument("--tag", default="", help="Optional results filename tag suffix")
    args = parser.parse_args()
    if args.quick:
        args.epochs = min(args.epochs, 8)

    set_seed()
    ensure_dirs()
    region = load_active_region()
    device = DEVICE if torch.cuda.is_available() and DEVICE == "cuda" else "cpu"
    ds = load_or_build_cube(
        region, prefer_demo=args.demo, prefer_physics=args.physics
    )
    use_physics = args.physics and any(
        k in ds for k in ("temp", "salt", "sst", "wind_speed")
    )
    fa = build_forecast_arrays(ds, leads=LEADS_MONTHS, use_physics=use_physics)
    splits = split_arrays(fa)
    mask = splits["meta"]["mask"]
    n_oxygen = int(splits["meta"]["n_oxygen"])
    leads = fa.leads
    depths = ds["depth"].values
    lat = ds["lat"].values
    lon = ds["lon"].values
    print(
        f"[multilead] region={region.get('id')} source={ds.attrs.get('source')} "
        f"physics={use_physics} channels={fa.x.shape[2]} leads={leads} "
        f"sparse={args.sparse} maskview={args.maskview} device={device}"
    )

    stats = fit_norm_from_train(splits["train"]["y"][:, 0], splits["train"]["times"])
    if use_physics:
        pmean, pstd = fit_phys_channel_stats(splits["train"]["x"], n_oxygen)
        stats.phys_mean = pmean
        stats.phys_std = pstd

    event_thr, event_mode = choose_event_threshold(
        splits["train"]["y"][:, 0],
        absolute=HYPOXIA_UMOL_KG,
        percentile=LOW_O2_PERCENTILE,
        min_rate=LOW_O2_MIN_EVENT_RATE,
    )
    print(f"[multilead] event threshold={event_thr:.2f} ({event_mode})")

    model_names = [
        "persistence",
        "climatology",
        "lstm_anomaly",
        "st_transformer",
        "hybrid_clim_st",
    ]
    rows = []
    skill_series = {k: [] for k in model_names}
    rmse_series = {k: [] for k in model_names}
    f1_series = {k: [] for k in model_names}
    blend_weights = {}
    depth_profiles_lead1 = {}
    st_maps = {}
    argo_path = PROCESSED / "argo_stations.json"

    for li, lead in enumerate(leads):
        data = prepare_lead(splits, li, stats, n_oxygen)
        x_tr, y_tr_n, y_tr, t_tr, x_tr_raw = data["train"]
        x_va, y_va_n, y_va, t_va, x_va_raw = data["val"]
        x_te, y_te_n, y_te, t_te, x_te_raw = data["test"]

        if args.sparse == "block_time":
            x_tr = apply_block_time_to_batch(x_tr, args.keep_ratio, n_oxygen, SEED + lead)
            x_va = apply_block_time_to_batch(
                x_va, args.keep_ratio, n_oxygen, SEED + 100 + lead
            )
            x_te = apply_block_time_to_batch(
                x_te, args.keep_ratio, n_oxygen, SEED + 200 + lead
            )
        elif args.sparse != "none":
            m_tr = make_batch_masks(
                x_tr,
                args.sparse,
                args.keep_ratio,
                args.stations,
                seed=SEED + lead,
                n_oxygen=n_oxygen,
                lat=lat,
                lon=lon,
                argo_stations_path=argo_path,
            )
            m_va = make_batch_masks(
                x_va,
                args.sparse,
                args.keep_ratio,
                args.stations,
                seed=SEED + 100 + lead,
                n_oxygen=n_oxygen,
                lat=lat,
                lon=lon,
                argo_stations_path=argo_path,
            )
            m_te = make_batch_masks(
                x_te,
                args.sparse,
                args.keep_ratio,
                args.stations,
                seed=SEED + 200 + lead,
                n_oxygen=n_oxygen,
                lat=lat,
                lon=lon,
                argo_stations_path=argo_path,
            )
            x_tr = apply_mask(x_tr, m_tr)
            x_va = apply_mask(x_va, m_va)
            x_te = apply_mask(x_te, m_te)

        persist = persistence_predict(_oxygen_history(x_te_raw, n_oxygen))
        persist_va = persistence_predict(_oxygen_history(x_va_raw, n_oxygen))
        clim = climatology_predict(y_tr, t_tr, t_te)
        clim_va = climatology_predict(y_tr, t_tr, t_va)

        print(f"\n[multilead] lead={lead}m training ...")
        lstm = train_lstm_anom(x_tr, y_tr_n, x_va, y_va_n, device, args.epochs)
        st = train_st_anom(
            x_tr,
            y_tr_n,
            x_va,
            y_va_n,
            mask,
            device,
            args.epochs,
            n_oxygen=n_oxygen,
            multiview=args.maskview,
        )

        pred_lstm = denormalize_anom(
            predict_lstm(lstm, x_te, device, y_te.shape), stats
        ) + apply_clim(y_te, t_te, stats.clim)
        pred_st = denormalize_anom(predict_st(st, x_te, device), stats) + apply_clim(
            y_te, t_te, stats.clim
        )
        pred_st_va = denormalize_anom(predict_st(st, x_va, device), stats) + apply_clim(
            y_va, t_va, stats.clim
        )
        w = tune_blend_weight(y_va, clim_va, pred_st_va)
        pred_hyb = blend(clim, pred_st, w)
        blend_weights[str(lead)] = w
        print(f"  hybrid blend weight w(ST)={w:.2f}  (val-tuned)")

        preds = {
            "persistence": persist,
            "climatology": clim,
            "lstm_anomaly": pred_lstm,
            "st_transformer": pred_st,
            "hybrid_clim_st": pred_hyb,
        }
        for name, pred in preds.items():
            reg = evaluate_regression(y_te, pred, mask)
            skill = skill_vs_persistence(y_te, pred, persist)
            ev = binary_event_scores(y_te, pred, event_thr)
            row = {
                "lead_months": lead,
                "model": name,
                "sparse": args.sparse,
                "physics": use_physics,
                "maskview": args.maskview,
                "blend_w_st": w if name == "hybrid_clim_st" else None,
                "event_threshold": event_thr,
                "event_mode": event_mode,
                **reg,
                "skill_vs_persist": skill,
                "hypoxia_f1": ev["f1"],
                "hypoxia_csi": ev["csi"],
            }
            rows.append(row)
            skill_series[name].append(skill)
            rmse_series[name].append(reg["rmse"])
            f1_series[name].append(ev["f1"])
            print(
                f"  {name:16s} rmse={reg['rmse']:.3f} skill={skill:.3f} f1={ev['f1']:.3f}"
            )

        st_maps[lead] = depth_mean_rmse(y_te, pred_hyb if w < 1 else pred_st)
        if lead == 1:
            for name, pred in preds.items():
                if name == "persistence":
                    continue
                depth_profiles_lead1[name] = depth_rmse_profile(y_te, pred, depths)

    tag = args.sparse if args.sparse != "none" else "full"
    if use_physics:
        tag = f"{tag}_physics"
    if args.maskview:
        tag = f"{tag}_maskview"
    if args.tag:
        tag = f"{tag}_{args.tag}"

    payload = {
        "region": region.get("id"),
        "cube_source": ds.attrs.get("source"),
        "physics": use_physics,
        "maskview": args.maskview,
        "channels": fa.channel_names,
        "sparse": args.sparse,
        "keep_ratio": args.keep_ratio,
        "epochs": args.epochs,
        "blend_weights": blend_weights,
        "metrics": rows,
        "depth_rmse_lead1": depth_profiles_lead1,
    }
    json_path = TABLES / f"multilead_{tag}.json"
    md_path = TABLES / f"multilead_{tag}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# Multi-lead results (`{tag}`)",
        "",
        f"Region: `{region.get('id')}` · cube: `{ds.attrs.get('source')}` · "
        f"physics=`{use_physics}` · sparse=`{args.sparse}` · maskview=`{args.maskview}`",
        "",
        f"Event threshold: `{event_thr:.2f}` µmol/kg (`{event_mode}`)",
        "",
        f"Hybrid blend weights (val-tuned ST weight): `{blend_weights}`",
        "",
        "| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['lead_months']} | {r['model']} | {r['rmse']:.3f} | "
            f"{r['skill_vs_persist']:.3f} | {r['hypoxia_f1']:.3f} | {r['hypoxia_csi']:.3f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    plot_lead_skill(
        leads,
        rmse_series,
        "RMSE (µmol/kg)",
        f"Lead–RMSE · {region.get('id')} · {tag}",
        FIGS / f"lead_rmse_{tag}.png",
    )
    plot_lead_skill(
        leads,
        skill_series,
        "Skill vs persistence",
        f"Lead–Skill · {region.get('id')} · {tag}",
        FIGS / f"lead_skill_{tag}.png",
    )
    plot_lead_skill(
        leads,
        f1_series,
        "Hypoxia F1",
        f"Lead–Hypoxia F1 · {region.get('id')} · {tag}",
        FIGS / f"lead_hypoxia_f1_{tag}.png",
    )
    if 1 in st_maps:
        plot_spatial_rmse(
            st_maps[1],
            lat,
            lon,
            f"Hybrid/ST depth-mean RMSE · lead=1m · {tag}",
            FIGS / f"spatial_rmse_st_lead1_{tag}.png",
        )
    if depth_profiles_lead1:
        plot_depth_rmse(
            depth_profiles_lead1,
            f"Depth RMSE · lead=1m · {tag}",
            FIGS / f"depth_rmse_lead1_{tag}.png",
        )

    print(f"\n[multilead] wrote {md_path}")
    print(f"[multilead] figures in {FIGS}")


if __name__ == "__main__":
    main()
