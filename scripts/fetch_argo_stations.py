#!/usr/bin/env python
"""Fetch BGC-Argo profile locations (Argovis center+radius) and save station mask cells.

Also supports a synthetic section (Yangtze plume transect) for extrapolation demos.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import PROCESSED, ensure_dirs, load_active_region

ARGOVIS = "https://argovis-api.colorado.edu"


def _get(url: str, timeout: int = 90):
    req = Request(url, headers={"User-Agent": "ocean-do-forecast/0.2"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_profiles(region: dict, start: str, end: str, radius_km: float = 700.0):
    lon_c = 0.5 * (float(region["lon_min"]) + float(region["lon_max"]))
    lat_c = 0.5 * (float(region["lat_min"]) + float(region["lat_max"]))
    stations = []
    seen = set()
    y0, y1 = int(start[:4]), int(end[:4])
    for y in range(y0, y1 + 1):
        s = f"{y}-01-01T00:00:00.000Z" if y > y0 else f"{start[:10]}T00:00:00.000Z"
        e = f"{y}-12-31T23:59:59.000Z" if y < y1 else f"{end[:10]}T23:59:59.000Z"
        q = urlencode(
            {
                "center": f"{lon_c},{lat_c}",
                "radius": str(int(radius_km)),
                "startDate": s,
                "endDate": e,
            }
        )
        url = f"{ARGOVIS}/argo?{q}"
        try:
            data = _get(url)
        except Exception as exc:
            print(f"[argo] {y} failed: {exc}", flush=True)
            continue
        if not isinstance(data, list):
            continue
        for p in data:
            geo = p.get("geolocation") or {}
            coords = geo.get("coordinates") or [None, None]
            lon, lat = coords[0], coords[1]
            if lon is None or lat is None:
                continue
            lon, lat = float(lon), float(lat)
            if not (
                region["lon_min"] <= lon <= region["lon_max"]
                and region["lat_min"] <= lat <= region["lat_max"]
            ):
                continue
            pid = str(p.get("_id") or f"{lon:.3f},{lat:.3f},{p.get('timestamp')}")
            if pid in seen:
                continue
            seen.add(pid)
            stations.append(
                {
                    "id": pid,
                    "lon": lon,
                    "lat": lat,
                    "platform": p.get("platform_id") or p.get("platform"),
                    "timestamp": p.get("timestamp") or p.get("date"),
                }
            )
        print(f"[argo] {y}: cumulative stations/profiles={len(stations)}", flush=True)
        time.sleep(0.35)
    return stations


def yangtze_section(region: dict, n: int = 12):
    """Synthetic ship section from near Changjiang mouth offshore (for extrapolation)."""
    # ~122E,31.5N eastward
    lons = [122.0 + 0.4 * i for i in range(n)]
    lats = [31.5 - 0.05 * i for i in range(n)]
    out = []
    for i, (lo, la) in enumerate(zip(lons, lats)):
        if region["lon_min"] <= lo <= region["lon_max"] and region["lat_min"] <= la <= region["lat_max"]:
            out.append({"id": f"section_{i}", "lon": lo, "lat": la, "kind": "ship_section"})
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end", default="2022-12-31")
    parser.add_argument("--radius-km", type=float, default=700.0)
    parser.add_argument("--offline-section", action="store_true")
    parser.add_argument("--include-section", action="store_true", default=True)
    args = parser.parse_args()
    ensure_dirs()
    region = load_active_region()

    stations = []
    if args.offline_section:
        stations = yangtze_section(region)
        source = "offline_yangtze_section"
    else:
        try:
            stations = fetch_profiles(region, args.start, args.end, args.radius_km)
            source = "argovis_center_radius"
        except Exception as exc:
            print(f"[argo] fetch failed ({exc}); using section fallback", flush=True)
            stations = yangtze_section(region)
            source = "offline_yangtze_section"

    section = yangtze_section(region) if args.include_section else []
    payload = {
        "region_id": region.get("id"),
        "source": source,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "n_stations": len(stations),
        "stations": stations,
        "section": section,
        "note": "Used for --sparse argo masks and section-extrapolation narratives.",
    }
    dest = PROCESSED / "argo_stations.json"
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[argo] wrote {dest} n={len(stations)} section={len(section)}")


if __name__ == "__main__":
    main()
