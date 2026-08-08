#!/usr/bin/env python
"""Survey BGC-Argo O2 coverage across candidate regions and freeze the best."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import TABLES, ensure_dirs, load_regions, save_active_region
from src.argo_survey import (
    fetch_bgc_profiles,
    score_region,
    summarize_profiles,
    write_survey_report,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--freeze", action="store_true", help="Write configs/region.yaml")
    parser.add_argument(
        "--offline-demo",
        action="store_true",
        help="Skip API; assign heuristic demo scores (for offline smoke).",
    )
    args = parser.parse_args()
    ensure_dirs()
    regions = load_regions()["candidates"]
    results = {}
    for key, region in regions.items():
        region = {**region, "id": key}
        print(f"[survey] {key} ...")
        if args.offline_demo:
            # Prefer ECS shelf in offline mode to match research plan default
            demo_n = {
                "east_china_sea_shelf": 180,
                "yellow_sea": 40,
                "northern_south_china_sea": 120,
                "kuroshio_extension": 260,
            }[key]
            summary = {
                "n_profiles": demo_n,
                "n_oxygen_like": demo_n,
                "n_platforms": max(3, demo_n // 20),
                "year_counts": {y: demo_n // 10 for y in range(2014, 2024)},
                "month_counts": {m: demo_n // 12 for m in range(1, 13)},
                "lon_range": [region["lon_min"], region["lon_max"]],
                "lat_range": [region["lat_min"], region["lat_max"]],
                "offline_demo": True,
            }
        else:
            try:
                profiles = fetch_bgc_profiles(region, start=args.start, end=args.end)
                summary = summarize_profiles(profiles)
            except Exception as e:
                print(f"  ! API failed: {e}")
                summary = {
                    "n_profiles": 0,
                    "n_oxygen_like": 0,
                    "n_platforms": 0,
                    "year_counts": {},
                    "month_counts": {},
                    "error": str(e),
                }
        sc = score_region(summary)
        results[key] = {"summary": summary, "score": sc, "region": region}
        print(
            f"  profiles={summary['n_profiles']} o2~{summary['n_oxygen_like']} "
            f"platforms={summary['n_platforms']} score={sc:.1f}"
        )

    report = write_survey_report(results, TABLES / "argo_coverage_survey.md")
    print(f"[survey] wrote {report}")

    ranked = sorted(results.items(), key=lambda kv: kv[1]["score"], reverse=True)
    if args.freeze and ranked:
        by_key = {k: v["score"] for k, v in results.items()}
        # Default freeze: East China Sea shelf when it has usable coverage —
        # hypoxia / fishery narrative beats raw Argo density (Kuroshio).
        ecs = by_key.get("east_china_sea_shelf", 0)
        if ecs >= 50:
            best_key = "east_china_sea_shelf"
            note = "Frozen for hypoxia narrative; denser regions kept as sensitivity sites."
        else:
            best_key = ranked[0][0]
            note = "ECS coverage too low; froze highest-score region."
        best = results[best_key]
        active = {
            **best["region"],
            "id": best_key,
            "leads_days": [30, 60, 90],
            "hypoxia_threshold_umol_kg": 60.0,
            "frozen_from_survey": True,
            "survey_score": best["score"],
            "note": note,
            "sensitivity_regions": [
                k for k, _ in ranked if k != best_key
            ][:2],
        }
        save_active_region(active)
        print(f"[survey] froze region -> {best_key}")


if __name__ == "__main__":
    main()
