#!/usr/bin/env python
"""Physics-cube multi-region sensitivity via spatial subsets of the ECS cube.

Unlike demo-only `run_region_sensitivity.py`, this keeps WOA/OISST/Open-Meteo
drivers and evaluates Yangtze plume / Yellow Sea overlap on the same protocol.
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

from config import (
    ACTIVE_REGION_YAML,
    PROCESSED,
    TABLES,
    ensure_dirs,
    load_regions,
    save_active_region,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--regions",
        nargs="+",
        default=["yangtze_estuary", "yellow_sea"],
    )
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    ensure_dirs()

    backup_yaml = (
        ACTIVE_REGION_YAML.read_text(encoding="utf-8") if ACTIVE_REGION_YAML.exists() else None
    )
    main_phys = PROCESSED / "regional_physics_cube.nc"
    phys_backup = PROCESSED / "regional_physics_cube.__ecs_backup__.nc"
    if not main_phys.exists():
        raise SystemExit("Missing regional_physics_cube.nc — run build_physics_cube.py first")
    shutil.copy2(main_phys, phys_backup)

    candidates = load_regions()["candidates"]
    summary = {}
    try:
        for rid in args.regions:
            if rid not in candidates:
                print(f"[phys-sens] skip unknown {rid}")
                continue
            reg = dict(candidates[rid])
            reg["id"] = rid
            reg["note"] = "physics subset sensitivity"
            save_active_region(reg)

            print(f"\n===== physics sensitivity: {rid} =====")
            subprocess.check_call(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "subset_physics_region.py"),
                    "--region",
                    rid,
                    "--source",
                    str(phys_backup),
                ],
                cwd=str(ROOT),
            )
            side = PROCESSED / f"regional_physics_cube_{rid}.nc"
            shutil.copy2(side, main_phys)

            cmd = [
                sys.executable,
                str(ROOT / "run_multilead.py"),
                "--physics",
                "--epochs",
                str(args.epochs),
                "--tag",
                f"phys_{rid}",
                "--bootstrap",
                "0",
            ]
            if args.quick:
                cmd.append("--quick")
            subprocess.check_call(cmd, cwd=str(ROOT))
            out = TABLES / f"multilead_full_physics_phys_{rid}.md"
            if out.exists():
                summary[rid] = str(out)
    finally:
        if backup_yaml is not None:
            ACTIVE_REGION_YAML.write_text(backup_yaml, encoding="utf-8")
            print("[phys-sens] restored region.yaml")
        if phys_backup.exists():
            shutil.copy2(phys_backup, main_phys)
            print("[phys-sens] restored ECS physics cube")

    idx = TABLES / "physics_region_sensitivity_index.json"
    idx.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[phys-sens] index -> {idx}")


if __name__ == "__main__":
    main()
