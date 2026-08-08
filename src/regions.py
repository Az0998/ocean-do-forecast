"""Region helpers."""
from __future__ import annotations

from typing import Any


def bbox(region: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        float(region["lon_min"]),
        float(region["lon_max"]),
        float(region["lat_min"]),
        float(region["lat_max"]),
    )


def contains(lon: float, lat: float, region: dict[str, Any]) -> bool:
    return (
        region["lon_min"] <= lon <= region["lon_max"]
        and region["lat_min"] <= lat <= region["lat_max"]
    )
