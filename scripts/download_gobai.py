#!/usr/bin/env python
"""Download / stage GOBAI-O2 files.

NCEI accession 0259304 packaging changes across versions. This script:
1. Tries known HTTPS directory listings / direct paths
2. If user passes --from-file, copies a local NetCDF into data/raw/gobai/
3. Always prints manual fallback instructions
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import ensure_dirs
from src.gobai_data import gobai_dir

# Probed 2026-08: direct OCADS directory URLs 404; accession download times out.
# Working entry is the NCEI metadata landing page (manual HTTPS download).
LANDING_PAGE = (
    "https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso"
    "?id=gov.noaa.nodc:0259304"
)
# Note: /archive/accession/.../data/0-data/ 301-redirects to OAS jquery path;
# automated listing often times out — prefer manual HTTPS from the landing page.
CANDIDATE_INDEX_URLS = [
    LANDING_PAGE,
    "https://www.ncei.noaa.gov/archive/archive-management-system/OAS/bin/prd/jquery/accession/0259304/5.5/data/0-data/",
    "https://www.ncei.noaa.gov/archive/accession/0259304/5.5/data/0-data/",
]


def try_list(url: str) -> str | None:
    try:
        req = Request(url, headers={"User-Agent": "ocean-do-forecast/0.1"})
        with urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  fail {url}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-file",
        type=Path,
        help="Copy an already-downloaded GOBAI NetCDF into data/raw/gobai/",
    )
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    dest = gobai_dir()
    dest.mkdir(parents=True, exist_ok=True)

    if args.from_file:
        target = dest / args.from_file.name
        shutil.copy2(args.from_file, target)
        print(f"[gobai] copied -> {target}")
        return

    print("[gobai] probing NCEI paths ...")
    found = False
    for url in CANDIDATE_INDEX_URLS:
        html = try_list(url)
        if html and (".nc" in html or "GOBAI" in html.upper()):
            print(f"[gobai] listing looks usable: {url}")
            (dest / "SOURCE_URL.txt").write_text(url + "\n", encoding="utf-8")
            found = True
            if args.probe_only:
                break
            print(
                "[gobai] Auto-download of multi-GB archives is not enabled by default.\n"
                f"  Open: {url}\n"
                f"  Place NetCDF files into: {dest}\n"
                "  Then re-run build samples."
            )
            break
    if not found:
        print(
            "[gobai] Could not auto-list NCEI file directories (404/timeout).\n"
            "Manual steps:\n"
            f"  1. Open {LANDING_PAGE}\n"
            "     (or DOI https://doi.org/10.25921/z72m-yz67)\n"
            "  2. Use the page HTTPS download for latest GOBAI-O2 NetCDF\n"
            f"  3. Copy into {dest}\n"
            "  4. Or for pipeline development: python scripts/build_demo_cube.py\n"
        )


if __name__ == "__main__":
    main()
