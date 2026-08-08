#!/usr/bin/env python
"""Multi-region sensitivity without permanently clobbering the ECS oxygen cube.

Writes `regional_oxygen_cube_<region>.nc`, temporarily swaps it in for
`run_multilead.py --demo`, then restores any pre-existing ECS cube.
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

from config import ACTIVE_REGION_YAML, PROCESSED, TABLES, ensure_dirs, load_regions, save_active_region
from src.gobai_data import build_demo_cube, save_cube


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--regions",
        nargs="+",
        default=["yellow_sea", "yangtze_estuary"],
    )
    parser.add_argument("--epochs", type=int, default=6)
    args = parser.parse_args()
    ensure_dirs()

    backup_yaml = ACTIVE_REGION_YAML.read_text(encoding="utf-8") if ACTIVE_REGION_YAML.exists() else None
    main_cube = PROCESSED / "regional_oxygen_cube.nc"
    ecs_backup = PROCESSED / "regional_oxygen_cube.__ecs_backup__.nc"
    if main_cube.exists():
        shutil.copy2(main_cube, ecs_backup)

    candidates = load_regions()["candidates"]
    summary = {}
    try:
        for rid in args.regions:
            if rid not in candidates:
                print(f"[sens] skip unknown region {rid}")
                continue
            reg = dict(candidates[rid])
            reg["id"] = rid
            reg["note"] = "temporary sensitivity freeze"
            save_active_region(reg)
            print(f"\n===== sensitivity region: {rid} =====")

            side = PROCESSED / f"regional_oxygen_cube_{rid}.nc"
            save_cube(build_demo_cube(reg), side)
            shutil.copy2(side, main_cube)

            cmd = [
                sys.executable,
                str(ROOT / "run_multilead.py"),
                "--demo",
                "--quick",
                "--epochs",
                str(args.epochs),
                "--tag",
                rid,
            ]
            subprocess.check_call(cmd, cwd=str(ROOT))
            out = TABLES / f"multilead_full_{rid}.md"
            if out.exists():
                summary[rid] = str(out)
    finally:
        if backup_yaml is not None:
            ACTIVE_REGION_YAML.write_text(backup_yaml, encoding="utf-8")
            print("[sens] restored active region.yaml")
        if ecs_backup.exists():
            shutil.copy2(ecs_backup, main_cube)
            print(f"[sens] restored oxygen cube from {ecs_backup.name}")

    out = TABLES / "region_sensitivity_index.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[sens] index -> {out}")


if __name__ == "__main__":
    main()
