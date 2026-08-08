# Dataset card — Ocean-DO-Forecast

## Modes

| Mode | Path | Use |
|------|------|-----|
| **demo** | `build_demo_cube.py` → `regional_oxygen_cube.nc` | Synthetic smoke tests |
| **woa_informed** | WOA18 O₂ clim + synthetic anomalies | Semi-real method development (default O₂ target) |
| **physics_multidrive** | `regional_physics_cube.nc` | O₂ + T/S/N² + SST + wind channels |
| **woa18_annual** | `woa18_oxygen_region.nc` / `woa18_ts_region.nc` | Real clim structure |
| **gobai** (optional) | `data/raw/gobai/*.nc` | Time-varying O₂ if locally available |

## Physical drivers (no GOBAI / no CMEMS login)

| Variable | Source | Script |
|----------|--------|--------|
| Temperature / salinity | WOA18 annual (NCEI) | `scripts/download_woa_ts.py` |
| Stratification N² | Linear EOS from T–S | `src/stratification.py` |
| SST | NOAA OISST v2 monthly (PSL) | `scripts/download_oisst_monthly.py` |
| 10 m wind / t2m | Open-Meteo ERA5 archive (or `--offline-synth`) | `scripts/download_openmeteo_wind.py` |
| Merge | Same grid as oxygen cube | `scripts/build_physics_cube.py` |

Optional upgrades (token required later): CDS ERA5 grids, CMEMS GLORYS via `copernicusmarine`.

## Sparse observation assets

| Asset | Path | Script |
|-------|------|--------|
| Argo / section columns | `data/processed/argo_stations.json` | `scripts/fetch_argo_stations.py` |
| Mask-View patterns | point, block, block_time, sensor, station, mixed, argo | `src/sparse_mask.py` |

## Splits

- Train: ≤ 2018-12  
- Val: 2019-01 … 2020-12  
- Test: ≥ 2021-01  

Time-block split by target month (no random profile shuffle).

## Regions

Frozen active region: `configs/region.yaml` (default East China Sea shelf).  
Candidates: `configs/regions.yaml` (Yellow Sea, Yangtze estuary, …).  
Sensitivity runner: `scripts/run_region_sensitivity.py`.

## Citations

- Garcia et al., World Ocean Atlas 2018.  
- Reynolds / NOAA OISST.  
- Open-Meteo (ERA5-based archive).  
- Argovis (Argo profile API).  
- Sharp et al. (2023) GOBAI-O2 — optional only.
