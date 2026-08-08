#!/usr/bin/env python
"""AIES-oriented physics / wind ablation table.

Configs:
  A) oxy_only           — oxygen channels only
  B) phys_ts_sst        — T/S/N2 + OISST, wind zeroed
  C) phys_synth_wind    — + offline monsoon wind
  D) phys_real_wind     — + NCEP monthly (default) or Open-Meteo if present

Open-Meteo is preferred when the API is not rate-limited; otherwise NCEP/NCAR
monthly surface winds from PSL provide a reproducible real-atmosphere driver.
CDS ERA5 remains optional via scripts/download_era5_cds.py.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import xarray as xr

from config import PROCESSED, TABLES, ensure_dirs


def _run(cmd: list[str]):
    print("[ablation]", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT))


def _wind_source(path: Path) -> str:
    try:
        return str(xr.open_dataset(path).attrs.get("source", "unknown"))
    except Exception:
        return "missing"


def _ensure_winds(skip_download: bool, prefer_openmeteo: bool):
    synth = PROCESSED / "openmeteo_wind_region_synth.nc"
    real = PROCESSED / "openmeteo_wind_region.nc"
    ncep = PROCESSED / "ncep_wind_region.nc"

    if not synth.exists():
        _run(
            [
                sys.executable,
                str(ROOT / "scripts" / "download_openmeteo_wind.py"),
                "--match-oxygen-grid",
                "--offline-synth",
                "--output",
                str(synth),
            ]
        )

    src = _wind_source(real) if real.exists() else "missing"
    # Prefer an existing real Open-Meteo cube; do not clobber it with NCEP.
    if src.startswith("open_meteo") and "synth" not in src:
        print(f"[ablation] using existing Open-Meteo wind ({src})", flush=True)
        return real, synth, ncep, src

    if prefer_openmeteo and not skip_download:
        try:
            _run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "download_openmeteo_wind.py"),
                    "--step",
                    "2.0",
                    "--batch-size",
                    "20",
                    "--pause",
                    "4.0",
                    "--fetch-start",
                    "2015-01-01",
                    "--fetch-end",
                    "2022-12-31",
                    "--output",
                    str(real),
                ]
            )
            src = _wind_source(real)
            if src.startswith("open_meteo") and "synth" not in src:
                return real, synth, ncep, src
        except subprocess.CalledProcessError:
            print("[ablation] Open-Meteo fetch failed", flush=True)

    # Fallback: NCEP (optional; may be slow)
    if (not ncep.exists()) and (not skip_download):
        _run([sys.executable, str(ROOT / "scripts" / "download_ncep_wind.py")])
    if ncep.exists() and (("synth" in src) or (src == "missing") or (not real.exists())):
        shutil.copy2(ncep, real)
        src = _wind_source(real)
        print(f"[ablation] using NCEP wind as real driver ({src})", flush=True)
    else:
        print(f"[ablation] real wind source={src}", flush=True)
    return real, synth, ncep, src


def _build_physics(drop_wind: bool = False, wind_nc: Path | None = None, tag: str = ""):
    wind_path = PROCESSED / "openmeteo_wind_region.nc"
    bak = PROCESSED / "openmeteo_wind_region.__ablation_bak__.nc"
    replaced = False
    if wind_nc is not None and wind_nc.exists():
        same = wind_nc.resolve() == wind_path.resolve()
        if not same:
            if wind_path.exists():
                shutil.copy2(wind_path, bak)
            shutil.copy2(wind_nc, wind_path)
            replaced = True
    try:
        _run([sys.executable, str(ROOT / "scripts" / "build_physics_cube.py")])
        cube = PROCESSED / "regional_physics_cube.nc"
        if drop_wind and cube.exists():
            with xr.open_dataset(cube) as ds:
                ds = ds.load()
            for v in ("wind_speed", "u10", "v10", "t2m"):
                if v in ds:
                    ds[v] = xr.zeros_like(ds[v])
            ds.attrs["wind_source"] = "ablated_zero"
            ds.attrs["ablation_tag"] = tag
            tmp = PROCESSED / "regional_physics_cube.tmp.nc"
            ds.to_netcdf(tmp)
            shutil.move(str(tmp), str(cube))
    finally:
        if replaced and bak.exists():
            shutil.copy2(bak, wind_path)
            bak.unlink(missing_ok=True)


def _read_metrics(tag: str, physics: bool) -> dict:
    p = (
        TABLES / f"multilead_full_physics_{tag}.json"
        if physics
        else TABLES / f"multilead_full_{tag}.json"
    )
    if not p.exists():
        raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))


def _best_rows(payload: dict) -> dict:
    best, st = {}, {}
    for r in payload.get("metrics", []):
        lead = int(r["lead_months"])
        if r["model"] == "st_transformer":
            st[lead] = r
        if r["model"] == "persistence":
            continue
        cur = best.get(lead)
        if cur is None or r["rmse"] < cur["rmse"]:
            best[lead] = r
    return {"best": best, "st": st, "blend": payload.get("blend_weights", {})}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument(
        "--prefer-openmeteo",
        action="store_true",
        help="Attempt Open-Meteo before falling back to NCEP",
    )
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()
    ensure_dirs()

    real_wind, synth_wind, ncep_wind, real_src = _ensure_winds(
        args.skip_download, args.prefer_openmeteo
    )

    configs = [
        ("oxy_only", {"physics": False, "tag": "oxy_only"}),
        ("phys_ts_sst", {"physics": True, "drop_wind": True, "tag": "ts_sst"}),
        (
            "phys_synth_wind",
            {"physics": True, "wind_nc": synth_wind, "tag": "synth_wind"},
        ),
        (
            "phys_real_wind",
            {"physics": True, "wind_nc": real_wind, "tag": "real_wind"},
        ),
    ]
    if args.only:
        configs = [c for c in configs if c[0] in args.only]

    summary = {}
    for name, cfg in configs:
        print(f"\n===== ablation: {name} =====", flush=True)
        tag = cfg["tag"]
        if cfg.get("physics"):
            _build_physics(
                drop_wind=bool(cfg.get("drop_wind")),
                wind_nc=cfg.get("wind_nc"),
                tag=tag,
            )
            cmd = [
                sys.executable,
                str(ROOT / "run_multilead.py"),
                "--physics",
                "--quick",
                "--epochs",
                str(args.epochs),
                "--tag",
                tag,
            ]
        else:
            cmd = [
                sys.executable,
                str(ROOT / "run_multilead.py"),
                "--quick",
                "--epochs",
                str(args.epochs),
                "--tag",
                tag,
            ]
        _run(cmd)
        payload = _read_metrics(tag, physics=bool(cfg.get("physics")))
        summary[name] = {
            "cube_source": payload.get("cube_source"),
            "physics": payload.get("physics"),
            "parsed": _best_rows(payload),
            "metrics_file": str(
                TABLES
                / (
                    f"multilead_full_physics_{tag}.json"
                    if cfg.get("physics")
                    else f"multilead_full_{tag}.json"
                )
            ),
        }

    lines = [
        "# Physics / wind ablation (AIES)",
        "",
        f"Real wind driver in this run: `{real_src}`",
        "",
        "Target oxygen field fixed (WOA-informed). Only drivers change.",
        "",
        "| Config | Lead-1 ST RMSE | Lead-2 ST RMSE | Lead-2 best | Lead-3 best |",
        "|---|---:|---:|---|---|",
    ]
    rows_json = []
    for name, _ in configs:
        if name not in summary:
            continue
        st = summary[name]["parsed"]["st"]
        best = summary[name]["parsed"]["best"]
        st1 = st.get(1, {}).get("rmse", float("nan"))
        st2 = st.get(2, {}).get("rmse", float("nan"))
        b2 = best.get(2, {})
        b3 = best.get(3, {})
        lines.append(
            f"| `{name}` | {st1:.3f} | {st2:.3f} | "
            f"{b2.get('model','?')} {b2.get('rmse', float('nan')):.3f} | "
            f"{b3.get('model','?')} {b3.get('rmse', float('nan')):.3f} |"
        )
        rows_json.append(
            {
                "config": name,
                "st_rmse": {str(k): v.get("rmse") for k, v in st.items()},
                "best": {
                    str(k): {"model": v.get("model"), "rmse": v.get("rmse")}
                    for k, v in best.items()
                },
            }
        )
    lines += [
        "",
        "## Notes",
        "",
        "- `oxy_only`: oxygen history only.",
        "- `phys_ts_sst`: WOA T/S→N² + OISST; wind/t2m zeroed.",
        "- `phys_synth_wind`: offline monsoon synthetic wind.",
        "- `phys_real_wind`: NCEP/NCAR monthly surface winds (PSL), or Open-Meteo/ERA5-backed if successfully fetched.",
        "- CDS ERA5: `py -3.12 scripts/download_era5_cds.py` after placing `~/.cdsapirc`.",
        "- Open-Meteo retry: `py -3.12 scripts/download_openmeteo_wind.py --step 2.0 --pause 3`.",
        "",
        f"- Synth file: `{synth_wind}`",
        f"- Real/default wind file: `{real_wind}`",
        f"- NCEP file: `{ncep_wind}`",
        "",
    ]
    md = TABLES / "physics_ablation.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (TABLES / "physics_ablation.json").write_text(
        json.dumps(
            {"real_wind_source": real_src, "rows": rows_json, "summary": summary},
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"\n[ablation] wrote {md}")
    try:
        print("\n".join(lines))
    except UnicodeEncodeError:
        print(md.read_text(encoding="utf-8").encode("ascii", "replace").decode("ascii"))


if __name__ == "__main__":
    main()
