# Spatiotemporal forecasting of dissolved oxygen on the East China Sea shelf under sparse observations

**Working draft.** Main quantitative tables currently use a **WOA-informed** cube (WOA18 regional climatology + synthetic AR anomalies). Replace with GOBAI-O2 regional fields before journal submission.

**Target venues:** *Artificial Intelligence for the Earth Systems* (AMS) → *Ocean Modelling*.

---

## Abstract

Ocean deoxygenation threatens coastal ecosystems, yet biogeochemical Argo oxygen profiles remain sparse. Most recent machine-learning products reconstruct monthly oxygen maps; fewer studies address multi-month **forecasts**. We present a regional forecasting framework for the East China Sea shelf that (i) predicts 1–3 month oxygen anomalies with a spatiotemporal Transformer, (ii) blends predictions with climatology using validation-tuned weights, and (iii) stress-tests skill under Argo-like station sparsity. On a WOA-informed development cube, the Transformer achieves the best one-month RMSE (3.84 µmol kg⁻¹; skill vs persistence 0.78) and highest low-O₂ event F1 (0.74). At two- and three-month leads, a hybrid climatology–Transformer forecast matches or beats pure learning models by shrinking the learned weight toward climatology. These results clarify lead-dependent predictability and motivate GOBAI-based final experiments.

**Keywords:** dissolved oxygen; hypoxia; spatiotemporal Transformer; East China Sea; sparse observations; multi-lead forecast

---

## 1. Introduction

Global ocean oxygen inventories are declining, and coastal low-oxygen events affect fisheries and aquaculture. Two ML threads dominate recent literature: (1) **mapping/reconstruction** of interior O₂ from sparse profiles (GOBAI-O2, ML4O2, BLENDR), and (2) **short-range coastal hypoxia classification** (e.g., Chesapeake Bay, northern Gulf of Mexico). Mid-range (≈30–90 day) regional DO forecasting remains comparatively thin.

This paper contributes:
1. A regional multi-lead DO forecast protocol (history 12 months → leads 1/2/3 months).
2. A spatiotemporal Transformer with physics-inspired smoothness, plus hybrid climatology blending.
3. Sparse-observation stress tests (station/point/block) and event scores with adaptive thresholds.
4. An open reproducible pipeline.

## 2. Data and study region

### 2.1 Region
East China Sea shelf, 118–128°E, 26–35°N, depths {10, 50, 100, 200, 500} dbar. Sensitivity candidates: Kuroshio Extension, northern South China Sea.

### 2.2 Fields
| Product | Role | Status |
|---------|------|--------|
| WOA18 oxygen annual | Real climatological structure | ✅ regional subset |
| WOA-informed cube | Method development target | ✅ clim + AR anomalies |
| GOBAI-O2 | Final forecast target | ⬜ user import |

Year-block splits: train ≤2018, validation 2019–2020, test ≥2021.

### 2.3 Event definition
If absolute hypoxia (<60 µmol kg⁻¹) is rarer than 1% of training cells, we report **low-O₂ events** below the training 10th percentile (here 195.09 µmol kg⁻¹ on the WOA-informed cube).

## 3. Methods

**Problem.** Given \(X_{t-11:t}\), predict \(Y_{t+\tau}\), \(\tau\in\{1,2,3\}\).

**Baselines.** Persistence; month-of-year climatology; LSTM on flattened anomaly tokens.

**ST-Transformer.** Depth tokens per grid cell; temporal Transformer encoder; loss = MSE + weak spatial smoothness.

**Hybrid.** \(\hat Y=(1-w)C(m)+w f_\theta(X)\), with \(w\) tuned on validation RMSE per lead.

**Sparse stress.** Point / block / station masks on inputs.

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

ST improves every depth level at one-month lead.

### 4.3 Sparse station stress (8 columns)

On the same WOA-informed cube with station masks, lead-1 ST RMSE rises from 3.84 to 5.22 (still better than persistence 8.27); leads 2–3 again collapse to climatology via hybrid \(w=0\).

### 4.4 Figures
Composite plate: `results/figures/paper_plate_full.png`.

## 5. Discussion

1. **Lead dependence is the story:** anomaly learning helps at 1 month; climatology dominates beyond.
2. Hybrid blending operationalizes that transition without ad-hoc switching.
3. Event metrics must use region-appropriate thresholds on well-oxygenated shelves.
4. Final claims require GOBAI (or equivalent time-varying) targets and independent shipboard checks.

## 6. Data and code availability

- Code: `ocean-do-forecast` repository.
- WOA18 oxygen: NCEI WOA18.
- GOBAI-O2 (planned): Sharp et al., DOI 10.25921/z72m-yz67.
- Upon acceptance: Zenodo DOI for code + regional intermediates.

## References (seed)

1. Sharp et al. (2023), *ESSD* — GOBAI-O2.  
2. Ito & Cervania (2024), *JGR: Machine Learning and Computation*.  
3. Garcia et al., World Ocean Atlas 2018 Oxygen.  
4. Coastal hypoxia AI studies in AIES / *Scientific Reports* (Chesapeake; northern Gulf of Mexico).
