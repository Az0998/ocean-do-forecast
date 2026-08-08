"""Ocean-DO-Forecast configuration."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
TABLES = RESULTS / "tables"
CKPT = ROOT / "checkpoints"
CONFIGS = ROOT / "configs"

REGIONS_YAML = CONFIGS / "regions.yaml"
ACTIVE_REGION_YAML = CONFIGS / "region.yaml"

SEED = 42
BATCH_SIZE = 32
EPOCHS = 20
LR = 1e-3
HIDDEN = 64
N_LAYERS = 2
N_HEADS = 4
DEVICE = "cuda"

# Monthly forecast defaults (GOBAI-native cadence)
HISTORY_MONTHS = 12
LEADS_MONTHS = [1, 2, 3]  # ~30/60/90 days
DEPTH_LEVELS_DBAR = [10.0, 50.0, 100.0, 200.0, 500.0]

TRAIN_END = "2018-12"
VAL_END = "2020-12"
# test: after VAL_END

HYPOXIA_UMOL_KG = 60.0  # absolute coastal hypoxia threshold when applicable
# If absolute events are too rare (<min_rate of train cells), fall back to
# low-oxygen percentile events for skill reporting.
LOW_O2_PERCENTILE = 10.0
LOW_O2_MIN_EVENT_RATE = 0.01


def ensure_dirs() -> None:
    for p in (RAW, PROCESSED, FIGS, TABLES, CKPT):
        p.mkdir(parents=True, exist_ok=True)


def load_regions() -> dict:
    with open(REGIONS_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_active_region() -> dict:
    with open(ACTIVE_REGION_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_active_region(region: dict) -> None:
    ACTIVE_REGION_YAML.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTIVE_REGION_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(region, f, allow_unicode=True, sort_keys=False)
