# Spatiotemporal forecasting of dissolved oxygen on the East China Sea shelf under sparse observations

**Working draft for *Artificial Intelligence for the Earth Systems* (AMS), with *Ocean Modelling* as backup.**

**Development status.** Primary tables currently use a **WOA-informed** oxygen cube (WOA18 regional climatology + synthetic AR anomalies). Multi-source **physical drivers** (WOA T/S → stratification, NOAA OISST, Open-Meteo/ERA5-backed wind) are wired through `regional_physics_cube.nc`. GOBAI-O2 remains optional if a local copy becomes available; it is **not required** to run the forecast narrative.

---

## Abstract

Ocean deoxygenation threatens coastal ecosystems, yet biogeochemical Argo oxygen profiles remain sparse. Most recent machine-learning products reconstruct monthly oxygen maps; fewer studies address multi-month **forecasts**. We present a regional forecasting framework for the East China Sea shelf that (i) predicts 1–3 month oxygen anomalies with a spatiotemporal Transformer driven by optional temperature, salinity, stratification, SST and wind channels, (ii) blends predictions with climatology using validation-tuned weights, and (iii) stress-tests skill under Mask-View-style missingness (point, block, block-time, sensor, station, mixed) and real Argo/section column masks. On a WOA-informed development cube, the Transformer achieves the best one-month RMSE (3.84 µmol kg⁻¹; skill vs persistence 0.78) and highest low-O₂ event F1 (0.74). At two- and three-month leads, a hybrid climatology–Transformer forecast matches or beats pure learning models by shrinking the learned weight toward climatology. Section-extrapolation experiments keep oxygen visible only along sparse columns while scoring full-field forecasts, sharpening the distinction between **forecasting** and dense **reconstruction**.

**Keywords:** dissolved oxygen; hypoxia; spatiotemporal Transformer; East China Sea; sparse observations; multi-lead forecast; physical covariates; Mask-View

---

## 1. Introduction

Global ocean oxygen inventories are declining, and coastal low-oxygen events affect fisheries and aquaculture. Two ML threads dominate recent literature: (1) **mapping/reconstruction** of interior O₂ from sparse profiles (GOBAI-O2, ML4O2, BLENDR), and (2) **short-range coastal hypoxia classification** (e.g., Chesapeake Bay, northern Gulf of Mexico). Mid-range (≈30–90 day) regional DO forecasting remains comparatively thin.

This paper contributes:
1. A regional multi-lead DO forecast protocol (history 12 months → leads 1/2/3 months).
2. Multi-source physical drivers (T/S/N², SST, 10 m wind) as free substitutes when global BGC reanalyses are inaccessible.
3. A spatiotemporal Transformer with physics-inspired smoothness, hybrid climatology blending, and Mask-View multi-view training.
4. Sparse-observation and section-extrapolation tests that evaluate full-field forecasts from column-limited inputs.
5. Multi-region sensitivity (Yellow Sea, Yangtze estuary/plume) plus an open reproducible pipeline.

## 2. Data and study region

### 2.1 Region
Primary: East China Sea shelf, 118–128°E, 26–35°N, depths {10, 50, 100, 200, 500} dbar.  
Sensitivity: Yellow Sea; Yangtze estuary/plume (121–125°E, 30–33°N).

### 2.2 Fields
| Product | Role | Status |
|---------|------|--------|
| WOA18 oxygen annual | Real climatological O₂ structure | ✅ regional subset |
| WOA18 T/S annual | Stratification / N² proxy | ✅ download + subset |
| NOAA OISST v2 monthly | Surface thermal driver | ✅ PSL NetCDF |
| Open-Meteo archive (ERA5-backed) | 10 m wind, 2 m temperature | ✅ API or offline monsoon synth |
| WOA-informed O₂ cube | Method development target | ✅ clim + AR anomalies |
| Physics cube | Multi-channel drivers + O₂ | ✅ `regional_physics_cube.nc` |
| BGC-Argo locations | Sparse column masks | ✅ Argovis center+radius / section fallback |
| GOBAI-O2 | Optional time-varying O₂ | ⬜ local import only |

Year-block splits: train ≤2018, validation 2019–2020, test ≥2021.

### 2.3 Event definition
If absolute hypoxia (<60 µmol kg⁻¹) is rarer than 1% of training cells, we report **low-O₂ events** below the training 10th percentile (here 195.09 µmol kg⁻¹ on the WOA-informed cube).

## 3. Methods

**Problem.** Given history \(X_{t-11:t}\) (oxygen ± physical channels), predict oxygen \(Y_{t+\tau}\), \(\tau\in\{1,2,3\}\).

**Baselines.** Persistence; month-of-year climatology; LSTM on flattened anomaly tokens.

**ST-Transformer.** Per-grid tokens with channel features (oxygen depths and optional physics); temporal Transformer encoder; loss = MSE + weak spatial smoothness. Optional Mask-View multi-view reconstruction + cross-view consistency.

**Hybrid.** \(\hat Y=(1-w)C(m)+w f_\theta(X)\), with \(w\) tuned on validation RMSE per lead.

**Sparse stress (Mask-View bank).** point / block / block_time / sensor / station / mixed / argo.

**Section extrapolation.** Keep oxygen only on a ship section (Yangtze plume transect) or Argo columns; score full-field forecasts.

**Metrics.** RMSE, skill vs persistence, event F1/CSI, depth RMSE, spatial RMSE.

## 4. Results (WOA-informed development cube)

### 4.1 Multi-lead scores (`sparse=none`)

Hybrid blend weights (val-tuned ST weight): lead1 \(w=1.0\), lead2 \(w=0.1\), lead3 \(w=0.0\).

| Lead (mo) | Model | RMSE | Skill vs persist | Low-O₂ F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.312 | 0.587 | 0.672 | 0.506 |
| 1 | **st_transformer** | **3.842** | **0.784** | **0.743** | **0.591** |
| 1 | hybrid_clim_st | 3.842 | 0.784 | 0.743 | 0.591 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 9.685 | 0.573 | 0.523 | 0.354 |
| 2 | st_transformer | 8.694 | 0.656 | 0.596 | 0.424 |
| 2 | **hybrid_clim_st** | **5.191** | **0.877** | 0.718 | 0.560 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | **climatology / hybrid** | **5.206** | **0.934** | 0.700 | 0.539 |
| 3 | lstm_anomaly | 14.827 | 0.468 | 0.358 | 0.218 |
| 3 | st_transformer | 14.752 | 0.473 | 0.372 | 0.229 |

### 4.2 Depth RMSE (lead = 1 month)

| Depth (dbar) | climatology | lstm | ST / hybrid |
|---:|---:|---:|---:|
| 10 | 5.126 | 5.146 | 3.853 |
| 50 | 5.522 | 5.524 | 3.921 |
| 100 | 5.290 | 5.282 | 3.747 |
| 200 | 5.299 | 5.326 | 3.881 |
| 500 | 5.243 | 5.272 | 3.807 |

### 4.3 Sparse station stress (8 columns)

Lead-1 ST RMSE rises from 3.84 to 5.22 (still better than persistence 8.27); leads 2–3 again collapse to climatology via hybrid \(w=0\).

### 4.4 Physics drivers, Mask-View, section extrapolation, multi-region

**Physics / wind ablation** (same WOA-informed O₂ target; see `results/tables/physics_ablation.md`):

| Config | Lead-1 ST | Lead-2 ST | Lead-2 best |
|---|---:|---:|---|
| oxy_only | 3.84 | 8.69 | hybrid 5.19 |
| phys_ts_sst (no wind) | 3.87 | 5.83 | hybrid 5.06 |
| phys_synth_wind | 3.87 | 5.15 | hybrid 4.91 |
| **phys_real_wind (Open-Meteo/ERA5)** | 3.88 | **5.83** | **hybrid 5.08** |

T/S + SST alone recover most of the mid-lead gain versus oxygen-only history. Real Open-Meteo (ERA5-backed) wind replaces the offline monsoon driver for the paper’s main physics run; synthetic wind can look stronger at lead 2 by aligning too cleanly with the seasonal DO cycle and is reported only as an ablation control. CDS ERA5 remains optional when credentials are available.

**Argo/section sparsity.** With Argo-column masks, lead-1 ST RMSE ≈ 5.22 (still beats persistence). Section-extrapolation (oxygen visible only on a Yangtze plume transect) yields ST RMSE 5.21 vs persistence 8.26 — a full-field forecast from column-limited inputs.

**Mask-View mixed + multiview** under physics: lead-1 ST RMSE 5.06; leads 2–3 again hybrid/climatology.

**Multi-region (demo cubes).** Yellow Sea lead-1 ST 3.04; Yangtze estuary lead-1 ST 2.88 — same lead-dependent hybrid story.

```bash
py -3.12 run_multilead.py --physics --quick
py -3.12 run_multilead.py --physics --maskview --sparse mixed --quick
py -3.12 run_multilead.py --sparse argo --quick
py -3.12 scripts/eval_section_extrapolation.py --quick
py -3.12 scripts/run_region_sensitivity.py
```

### 4.5 Figures
Composite plate: `results/figures/paper_plate_full.png`. Forecast demo map: `results/figures/forecast_demo_mae.png`.

## 5. Discussion

1. **Lead dependence is the story:** anomaly learning helps at 1 month; climatology dominates beyond.
2. Hybrid blending operationalizes that transition without ad-hoc switching.
3. Physical covariates supply stratification and wind context when BGC reanalyses are unavailable; they do not replace a time-varying oxygen target for final journal claims.
4. Mask-View patterns and section masks enforce an operational sparse-obs view: the model must **forecast the field**, not only interpolate dense maps.
5. Multi-region sensitivity checks whether shelf hypoxia narratives transfer to the Yellow Sea and Yangtze plume.

## 6. Data and code availability

- Code / project site: https://github.com/Az0998/ocean-do-forecast · https://az0998.github.io/ocean-do-forecast/
- WOA18 O₂/T/S: NCEI World Ocean Atlas 2018.
- OISST: NOAA / PSL monthly SST.
- Wind: Open-Meteo archive (ERA5-based) or documented monsoon synthetic fallback.
- Argo locations: Argovis API (center+radius).
- GOBAI-O2 (optional): Sharp et al., DOI 10.25921/z72m-yz67.
- Dataset card: `dataset_card/README.md`.

## References (seed)

1. Sharp et al. (2023), *ESSD* — GOBAI-O2.  
2. Ito & Cervania (2024), *JGR: Machine Learning and Computation*.  
3. Garcia et al., World Ocean Atlas 2018.  
4. Huang et al. / related coastal hypoxia AI studies in AIES and *Scientific Reports*.  
5. Mask-View spatiotemporal imputation for block-missing monitoring networks (sibling Dianchi study).
