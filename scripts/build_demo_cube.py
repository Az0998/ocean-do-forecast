#!/usr/bin/env python
"""Build synthetic regional oxygen cube for pipeline development."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import PROCESSED, ensure_dirs, load_active_region
from src.gobai_data import build_demo_cube, save_cube


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2004-01")
    parser.add_argument("--end", default="2022-12")
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()
    ds = build_demo_cube(region, start=args.start, end=args.end)
    path = PROCESSED / "regional_oxygen_cube.nc"
    save_cube(ds, path)
    print(f"[demo] saved {path}")
    print(ds)


if __name__ == "__main__":
    main()
