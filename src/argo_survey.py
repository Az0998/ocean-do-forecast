"""BGC-Argo oxygen coverage survey via Argovis API (center+radius; box is deprecated)."""
from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ARGOVIS = "https://argovis-api.colorado.edu"


def _get_json(url: str, timeout: int = 90) -> Any:
    req = Request(url, headers={"User-Agent": "ocean-do-forecast/0.2"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _year_chunks(start: str, end: str) -> list[tuple[str, str]]:
    y0 = int(start[:4])
    y1 = int(end[:4])
    chunks = []
    for y in range(y0, y1 + 1):
        s = f"{y}-01-01T00:00:00.000Z" if y > y0 else f"{start[:10]}T00:00:00.000Z"
        e = f"{y}-12-31T23:59:59.000Z" if y < y1 else f"{end[:10]}T23:59:59.000Z"
        chunks.append((s, e))
    return chunks


def fetch_bgc_profiles(
    region: dict[str, Any],
    start: str = "2015-01-01",
    end: str | None = None,
    pause_s: float = 0.4,
    radius_km: float = 700.0,
) -> list[dict[str, Any]]:
    """Fetch Argo profiles near a region using center+radius, then clip to the box."""
    end = end or datetime.utcnow().strftime("%Y-%m-%d")
    lon0, lon1 = float(region["lon_min"]), float(region["lon_max"])
    lat0, lat1 = float(region["lat_min"]), float(region["lat_max"])
    lon_c = 0.5 * (lon0 + lon1)
    lat_c = 0.5 * (lat0 + lat1)
    all_profiles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for s, e in _year_chunks(start, end):
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
            data = _get_json(url)
        except Exception as exc:
            raise RuntimeError(f"Argovis failed for {s[:4]}: {exc}") from exc
        if not isinstance(data, list):
            continue
        for p in data:
            geo = p.get("geolocation") or {}
            coords = geo.get("coordinates") or [None, None]
            lon, lat = coords[0], coords[1]
            if lon is None or lat is None:
                continue
            lon, lat = float(lon), float(lat)
            if not (lon0 <= lon <= lon1 and lat0 <= lat <= lat1):
                continue
            pid = str(p.get("_id") or p.get("id") or f"{lon:.3f},{lat:.3f}")
            if pid in seen:
                continue
            seen.add(pid)
            all_profiles.append(p)
        time.sleep(pause_s)
    return all_profiles


def summarize_profiles(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    years: Counter[int] = Counter()
    months: Counter[int] = Counter()
    platforms: set[str] = set()
    lons, lats = [], []
    o2_count = 0
    for p in profiles:
        geoloc = p.get("geolocation") or {}
        coords = geoloc.get("coordinates") or [None, None]
        lon, lat = coords[0], coords[1]
        if lon is not None and lat is not None:
            lons.append(float(lon))
            lats.append(float(lat))
        ts = p.get("timestamp") or p.get("date")
        if ts:
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                years[dt.year] += 1
                months[dt.month] += 1
            except ValueError:
                pass
        plat = p.get("platform_id") or p.get("platform")
        if plat:
            platforms.add(str(plat))
        blob = json.dumps(p).lower()
        if "doxy" in blob or "oxygen" in blob or "bgc" in blob:
            o2_count += 1
    return {
        "n_profiles": len(profiles),
        "n_oxygen_like": o2_count if o2_count else len(profiles),
        "n_platforms": len(platforms),
        "year_counts": dict(sorted(years.items())),
        "month_counts": dict(sorted(months.items())),
        "lon_range": [min(lons), max(lons)] if lons else None,
        "lat_range": [min(lats), max(lats)] if lats else None,
    }


def score_region(summary: dict[str, Any]) -> float:
    n = float(summary.get("n_oxygen_like") or summary.get("n_profiles") or 0)
    months = summary.get("month_counts") or {}
    season_cov = len(months) / 12.0
    plats = float(summary.get("n_platforms") or 0)
    return n * (0.5 + 0.5 * season_cov) * (1.0 + 0.05 * min(plats, 40))


def write_survey_report(results: dict[str, dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Argo coverage survey",
        "",
        "Query mode: Argovis `center` + `radius`, clipped to region box.",
        "",
        "| Region | Profiles | O2-like | Platforms | Score |",
        "|---|---:|---:|---:|---:|",
    ]
    for rid, payload in results.items():
        s = payload.get("summary") or {}
        lines.append(
            f"| {rid} | {s.get('n_profiles', 0)} | {s.get('n_oxygen_like', 0)} | "
            f"{s.get('n_platforms', 0)} | {payload.get('score', 0):.1f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
