# Spatiotemporal forecasting of dissolved oxygen on the East China Sea shelf under sparse observations

**Target journal:** *Artificial Intelligence for the Earth Systems* (AMS)  
**Backup:** *Ocean Modelling* (Elsevier)  
**Manuscript status:** Final text for AMS formatting (method-development oxygen target; see Limitations)  
**Authors:** Senjie Zhang (张森捷)¹,* [and co-authors to be finalized]  
**Affiliation:** ¹ College of Earth and Environmental Sciences / related unit, Lanzhou University, China  
**Correspondence:** [author email]  
**Code & site:** https://github.com/Az0998/ocean-do-forecast · https://az0998.github.io/ocean-do-forecast/

---

## Significance statement

Most machine-learning oxygen products reconstruct monthly maps from sparse profiles. This study instead builds a **1–3 month regional forecast** protocol for the East China Sea shelf, shows when a spatiotemporal Transformer beats climatology, and demonstrates that skill must be evaluated under Mask-View / Argo-like missingness—so the task remains forecasting, not dense reconstruction.

---

## Abstract

Ocean deoxygenation threatens coastal ecosystems, yet biogeochemical Argo oxygen profiles remain sparse. Recent machine-learning products excel at reconstructing monthly dissolved-oxygen (DO) maps; fewer studies address multi-month **forecasts** that are more relevant to hypoxia risk awareness. We present a regional forecasting framework for the East China Sea (ECS) shelf that (i) predicts 1–3 month oxygen fields from a 12-month history using a spatiotemporal Transformer, optionally driven by temperature, salinity, stratification, sea-surface temperature (SST) and 10 m wind; (ii) blends Transformer outputs with month-of-year climatology using validation-tuned weights; and (iii) stress-tests skill under a Mask-View missingness bank (point, block, block-time, sensor, station, mixed) and Argo/section column masks while scoring the **full field**.

On a WOA-informed development cube, the Transformer achieves the best one-month root-mean-square error (RMSE; 3.84 µmol kg⁻¹; skill versus persistence 0.78; skill versus climatology 0.47) and the highest low-oxygen event F1 (0.74). With Open-Meteo (ERA5-backed) physical drivers, lead-1 scores remain comparable (RMSE 3.88 µmol kg⁻¹; bootstrap 95% interval [3.77, 4.02]), while mid-lead Transformer skill improves sharply relative to oxygen-only history; a hybrid climatology–Transformer forecast is best at two months (RMSE 5.08 µmol kg⁻¹). Under Argo- or station-column inputs, lead-1 RMSE rises to ≈5.23–5.24 µmol kg⁻¹ but still beats persistence (8.27). Residual errors concentrate on the western shelf and near 50 dbar. These results establish a reproducible mid-range DO forecast protocol and clarify where denser time-varying oxygen targets (e.g., GOBAI-O2) are required before process-level frontal claims.

**Keywords:** dissolved oxygen; hypoxia; spatiotemporal Transformer; East China Sea; sparse observations; multi-lead forecast; physical covariates; Mask-View

---

## 1. Introduction

Global ocean oxygen inventories are declining, and coastal low-oxygen events affect fisheries, aquaculture and nutrient cycling (Breitburg et al. 2018). Two machine-learning threads dominate recent dissolved-oxygen (DO) literature. The first maps or **reconstructs** interior oxygen from sparse profiles and ship data, producing monthly gridded products such as GOBAI-O2 (Sharp et al. 2023), ML4O2 mappings (Ito and Cervania 2024) and deep-ocean blends (e.g., BLENDR). The second targets **short-range** coastal hypoxia classification or nowcasting (hours to days), for example in Chesapeake Bay and the northern Gulf of Mexico. Mid-range (≈30–90 day) **regional forecasting**—predicting future fields from recent history under realistic observation gaps—remains comparatively thin, yet it is the horizon at which seasonal hypoxia risk awareness is most actionable.

Reconstruction and forecasting are easily conflated. A model that fills holes in a dense monthly map is not the same as a model that extrapolates forward in time when oxygen is observed only along Argo columns or a ship section. Operational and research users need the latter skill to be reported explicitly, including degradation under missingness and the lead at which learned anomaly forecasts should yield to climatology.

This paper contributes a regional multi-lead DO forecast protocol for the ECS shelf with five elements:

1. A fixed experimental design: 12-month history → leads of 1, 2 and 3 months; year-block train/validation/test splits.  
2. Multi-source physical drivers (WOA temperature/salinity and stratification, NOAA OISST, Open-Meteo/ERA5-backed wind) that do not require proprietary biogeochemical reanalyses.  
3. A spatiotemporal Transformer with weak spatial smoothness, optional Mask-View multi-view training, and a validation-tuned hybrid with month-of-year climatology.  
4. A Mask-View sparse bank and section-extrapolation tests that keep oxygen visible only on columns while scoring full-field forecasts.  
5. Seasonal skill, block-bootstrap uncertainty, multi-region subsets (Yangtze plume; southern Yellow Sea overlap), coastal/stratification failure diagnosis, and a fully open pipeline.

We deliberately separate **method protocol** from **final process claims**. Primary tables use a WOA-informed oxygen cube (observed climatological structure plus synthetic autoregressive anomalies) so that the forecast stack can be developed and stress-tested without multi-gigabyte GOBAI archives. Physical drivers and sparsity protocols are evaluated on that cube; Limitations state what must be repeated on GOBAI-O2 or ship DO before frontal/thermocline process narratives are asserted.

---

## 2. Data and study region

### 2.1 Region

The primary domain is the East China Sea shelf, 118–128°E, 26–35°N, at depths {10, 50, 100, 200, 500} dbar. The region combines seasonal stratification, Changjiang (Yangtze) influence and documented low-oxygen risk with fishery relevance. Sensitivity experiments use spatial subsets for the Yangtze estuary/plume (121–125°E, 30–33°N) and the southern Yellow Sea overlap within the ECS cube. Demo-cube runs for the full Yellow Sea box are reported in the repository as transfer checks but are not the primary physics tables.

### 2.2 Fields and products

| Product | Role in this study |
|---------|--------------------|
| WOA18 oxygen (annual) | Climatological O₂ structure for the development target |
| WOA18 temperature & salinity | Stratification / N² proxy and physical channels |
| NOAA OISST v2 monthly | Surface thermal driver |
| Open-Meteo archive (ERA5-backed) | 10 m wind and 2 m temperature (2° fetch 2015–2022; month-of-year fill for earlier years) |
| WOA-informed O₂ cube | Method-development forecast target (clim + AR anomalies) |
| Physics cube | Multi-channel drivers aligned to the oxygen grid |
| BGC-Argo / section columns | Sparse masks via Argovis center+radius (section fallback) |
| GOBAI-O2 (optional) | Time-varying O₂ upgrade path (Sharp et al. 2023; DOI 10.25921/z72m-yz67) |

Time coverage for experiments is monthly from 2004-01 through 2022-12. Splits are year blocks by **target** month: training ≤2018, validation 2019–2020, test ≥2021. Random profile shuffling is not used.

### 2.3 Event definition

Absolute coastal hypoxia (<60 µmol kg⁻¹) occupies <1% of training cells on the development cube. We therefore report **low-oxygen events** below the training 10th percentile (195.09 µmol kg⁻¹ on the WOA-informed cube; region-specific percentiles for subsets). Metrics include F1 and critical success index (CSI). This choice is explicit: the paper evaluates low-tail skill under a reproducible threshold rule, not absolute hypoxia prevalence on a synthetic-anomaly field.

---

## 3. Methods

### 3.1 Forecast problem

Let \(X_{t-11:t}\) be a 12-month history of oxygen (and optional physical channels) on the regional grid, and let \(Y_{t+\tau}\) be the oxygen field at lead \(\tau\in\{1,2,3\}\) months. Models predict normalized anomalies; absolute fields are recovered by adding the month-of-year climatology estimated on training data. Persistence uses the last history month; climatology uses the training month-of-year mean at the target calendar month.

### 3.2 Models

**LSTM baseline.** Flattened spatial tokens with a shallow LSTM on anomaly histories.  
**Spatiotemporal Transformer (ST).** Per-grid tokens carrying oxygen (and physics) channels; a temporal Transformer encoder; mean-squared error plus a weak spatial smoothness penalty. Optional Mask-View training adds multi-view reconstruction and cross-view consistency losses (sibling design to lake-monitoring Mask-View imputation).  
**Hybrid.** \(\hat{Y}=(1-w)\,C(m)+w\,f_\theta(X)\), where \(C(m)\) is month-of-year climatology and \(w\in[0,1]\) is chosen on validation RMSE for each lead independently. This encodes the empirical transition from anomaly learning at short lead to climatology at long lead without hard switching.

### 3.3 Sparse observation protocol

Oxygen history channels are masked; physical forcings remain visible when present (forcings are treated as available). Patterns: `point`, `block`, `block_time`, `sensor`, `station` (fixed columns), `mixed`, and `argo` (Argovis-derived or section fallback columns). Section extrapolation keeps oxygen only along a Yangtze plume transect (or Argo columns) and still scores the full field—separating forecast skill from dense reconstruction skill.

### 3.4 Metrics and uncertainty

We report RMSE and mean absolute error (MAE); anomaly RMSE relative to climatology; skill versus persistence and versus climatology (\(1-\mathrm{MSE}_\mathrm{model}/\mathrm{MSE}_\mathrm{ref}\)); low-oxygen F1/CSI; depth RMSE profiles; and spatial depth-mean RMSE maps. Seasonal scores use JJAS and DJF subsets of the test period. Block bootstrap over test months (default 80–200 replicates in reported runs) provides percentile intervals for RMSE and F1. Failure-mode diagnosis bins lead-1 absolute error by SST-front strength (\(|\nabla\mathrm{SST}|\)), upper-column N², coastal proximity, and thermocline depth (depth of maximum N²).

### 3.5 Implementation

Training uses fixed seed 42, Adam optimization, and early stopping on validation loss within the reported epoch budgets. Code, configs and tables are public (GitHub / project site). Reproduction commands are listed in the repository README; figure plates are generated by `scripts/compose_paper_figures.py` and `scripts/compose_comparison_figures.py`.

---

## 4. Results

Unless noted, RMSE units are µmol kg⁻¹. Oxygen-only tables use the WOA-informed cube without physical channels. Physics tables use the same oxygen target plus T/S, N², SST and Open-Meteo wind (`phys_real_wind`).

### 4.1 Multi-lead skill without physical drivers

Validation-tuned hybrid weights: \(w=1.0\) (lead 1), \(0.1\) (lead 2), \(0.0\) (lead 3).

| Lead | Model | RMSE | Skill vs persist | Skill vs clim | Low-O₂ F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | −1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | LSTM | 5.312 | 0.587 | −0.005 | 0.672 | 0.506 |
| 1 | **ST / hybrid** | **3.842** | **0.784** | **0.465** | **0.743** | **0.591** |
| 2 | persistence | 14.815 | 0.000 | −7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | LSTM | 9.685 | 0.573 | −2.43 | 0.523 | 0.354 |
| 2 | ST | 8.694 | 0.656 | −1.76 | 0.596 | 0.424 |
| 2 | **hybrid** | **5.191** | **0.877** | **0.014** | 0.718 | 0.560 |
| 3 | climatology / hybrid | **5.206** | **0.934** | 0.000 | 0.700 | 0.539 |
| 3 | ST | 14.752 | 0.473 | −7.03 | 0.372 | 0.229 |

At one month the Transformer clearly beats both persistence and climatology. At two and three months, pure ST degrades; hybrid (or pure climatology at lead 3) recovers usable scores by shrinking \(w\).

**Depth RMSE (lead 1).** ST improves every level relative to climatology; the largest climatology error is at 50 dbar (5.52), where ST reaches 3.92.

### 4.2 Physical drivers and wind ablation

Holding the oxygen target fixed and varying drivers:

| Config | Lead-1 ST | Lead-2 ST | Lead-2 best | Lead-3 best |
|---|---:|---:|---|---|
| oxy_only | 3.842 | 8.694 | hybrid 5.191 | clim 5.206 |
| phys_ts_sst (no wind) | 3.868 | 5.833 | hybrid 5.063 | clim 5.206 |
| phys_synth_wind | 3.871 | 5.152 | hybrid 4.914 | hybrid 5.188 |
| **phys_real_wind (Open-Meteo)** | **3.876** | **5.832** | **hybrid 5.083** | clim 5.206 |

Temperature, salinity, stratification and SST recover most of the mid-lead gain. Real Open-Meteo wind is the paper’s main physics configuration; synthetic monsoon wind can appear stronger at lead 2 by aligning too cleanly with the seasonal DO cycle and is retained only as an ablation control. Under `phys_real_wind`, hybrid weights are \(w=1.0,\ 0.35,\ 0.05\) for leads 1–3. Lead-1 skill versus climatology remains 0.47; lead-2 hybrid skill versus climatology is small but positive (≈0.05).

**Seasonal skill (physics, lead 1).** ST beats climatology in JJAS (3.85 vs 5.17; skillC 0.45) and DJF (3.93 vs 5.61; skillC 0.51). Summer low-oxygen F1 is 0.71 versus 0.58 for climatology.

**Bootstrap (physics).** Lead-1 ST RMSE 3.88 [3.77, 4.02]; F1 0.74 [0.69, 0.79]. Lead-2 hybrid RMSE 5.08 [4.94, 5.22] is more stable than pure ST at the same lead.

### 4.3 Mask-View sparse ablation (physics cube)

| Sparse pattern | Lead-1 ST | Lead-1 F1 | Lead-2 best |
|---|---:|---:|---|
| none (dense) | 3.876 | 0.741 | hybrid 5.083 |
| block_time | 4.273 | 0.720 | hybrid 5.094 |
| block | 4.994 | 0.683 | clim 5.228 |
| point | 5.016 | 0.692 | clim 5.228 |
| mixed | 5.071 | 0.680 | clim 5.228 |
| sensor | 5.075 | 0.693 | clim 5.228 |
| station (8 columns) | 5.232 | 0.674 | clim 5.228 |
| argo | 5.241 | 0.667 | clim 5.228 |

Skill degrades gracefully from dense history through contiguous block-time gaps to random/mixed masks and finally to column-limited station/Argo views. Even under Argo masks, lead-1 ST beats persistence (8.265) and retains positive skill versus climatology. Beyond one month, hybrid/climatology again dominate.

### 4.4 Section extrapolation and multi-region subsets

Section extrapolation (oxygen visible only on a Yangtze plume transect; full-field score) yields ST RMSE 5.21 versus persistence 8.27 and climatology 5.30—illustrating a full-field forecast from column-limited inputs rather than dense map filling.

Physics spatial subsets reproduce the same lead story: Yangtze plume lead-1 hybrid RMSE 3.74 (skillC 0.41); southern Yellow Sea overlap lead-1 ST 3.92 (skillC 0.49). Lead-2 hybrid again beats climatology (4.65 and 5.11, respectively).

### 4.5 Failure modes

Lead-1 absolute-error binning on the physics cube shows a clear **coastal** penalty: western-shelf proximity tercile MAE rises from ≈2.95 (offshore/mid) to 3.30 µmol kg⁻¹ (coastal; P90 ≈4.9). Depth-wise, **50 dbar** is the worst level (MAE 3.18), consistent with the seasonal subsurface low-oxygen / pycnocline layer. SST-front and upper-N² terciles are **not** monotonically harder on this development cube; high-stratification cells are slightly easier. Thermocline-level MAE is nearly indistinguishable from other depths. These patterns caution against over-interpreting frontal failure before time-varying oxygen targets are used.

---

## 5. Discussion

**Lead dependence is the central scientific result.** Anomaly learning is valuable at one month (skill versus climatology ≈0.47 under physics) and should not be discarded because longer leads revert toward climatology. The hybrid weight \(w(\tau)\) turns that empirical transition into an operational rule: trust the Transformer when validation supports it; otherwise fall back smoothly.

**Forecasting is not reconstruction.** Mask-View and section tests force the model to emit a full field from incomplete oxygen histories. Reporting only dense-input RMSE would overstate operational readiness on the ECS shelf, where BGC-Argo coverage is limited.

**Physical drivers help mid-lead dynamics more than lead-1 RMSE.** T/S–SST channels cut lead-2 ST RMSE from 8.69 (oxygen-only) to ≈5.83. Real wind is preferred for honesty; synthetic wind can inflate mid-lead scores through seasonal co-variation with the development anomalies.

**Errors concentrate where the hypoxia narrative matters.** Coastal and 50 dbar penalties align with river–shelf and subsurface low-oxygen stories. The absence of a clean front/N² penalty on the WOA-informed cube is itself informative: it indicates that residual errors are not yet diagnostic of frontal process skill and motivates GOBAI-O2 or cruise DO as the next target.

**Relation to prior work.** Relative to GOBAI-O2 / ML4O2, we do not claim a better monthly map; we claim a **lead-aware forecast protocol** with sparse-input stress tests. Relative to Chesapeake-style short-range hypoxia AI, we target a longer lead on a shelf domain with hybrid climatology blending.

---

## 6. Limitations and next steps

1. **Oxygen target.** Primary tables use a WOA-informed development cube (climatology + synthetic AR anomalies). Absolute hypoxia is rare; events use a training percentile rule. Main numerical claims should be re-run on GOBAI-O2 (or equivalent time-varying DO) before process-level frontal/thermocline conclusions.  
2. **Wind resolution.** Open-Meteo fetch uses a coarse 2° grid with climatology fill for early years; denser ERA5 (CDS) is optional.  
3. **Region subsets.** Yellow Sea / Yangtze physics results are spatial crops of the ECS cube, not independently forced regional reanalyses.  
4. **Open research.** Code and intermediate products are public; a Zenodo (or equivalent) DOI should be minted at submission/acceptance.  
5. **Product surface.** A lead-1 NetCDF and interactive demo are provided for transparency; they are development products, not operational warnings.

---

## 7. Conclusions

We presented a reproducible mid-range DO forecasting framework for the East China Sea shelf under sparse observations. A spatiotemporal Transformer delivers clear one-month skill against persistence and climatology; a validation-tuned hybrid with climatology stabilizes two- and three-month leads; Mask-View and section protocols keep the evaluation honest about observation gaps; and physical drivers improve mid-lead Transformer behavior without requiring proprietary BGC reanalyses. Residual errors emphasize the western shelf and the 50 dbar layer. The immediate priority for a process-hardened journal revision is repeating the main tables on a time-varying oxygen product (GOBAI-O2 or ship-validated fields) while retaining the sparse-forecast evaluation design introduced here.

---

## Data and code availability

- **Code / project site:** https://github.com/Az0998/ocean-do-forecast · https://az0998.github.io/ocean-do-forecast/  
- **Interactive lead-1 demo:** https://az0998.github.io/ocean-do-forecast/demo.html  
- **Dataset card:** `dataset_card/README.md` in the repository  
- **WOA18 O₂ / T / S:** World Ocean Atlas 2018 (NCEI)  
- **OISST:** NOAA / PSL monthly SST  
- **Wind:** Open-Meteo archive (ERA5-based); CDS ERA5 optional  
- **Argo locations:** Argovis API (center + radius)  
- **GOBAI-O2 (optional):** Sharp et al., NCEI accession / DOI 10.25921/z72m-yz67  
- **Archival DOI:** to be minted (Zenodo) at submission  

All split definitions, seeds and table JSON files used in this manuscript are in `results/tables/`.

---

## Author contributions

Conceptualization, methodology, software, analysis, writing—original draft: Senjie Zhang. [Co-author roles to be completed.]

## Competing interests

The authors declare no competing interests.

## Acknowledgments

[Funding and compute acknowledgments to be inserted.]

---

## References

Breitburg, D., and Coauthors, 2018: Declining oxygen in the global ocean and coastal waters. *Science*, **359**, eaam7240, https://doi.org/10.1126/science.aam7240.

Garcia, H. E., and Coauthors, 2019: *World Ocean Atlas 2018*, Volume 3: Dissolved Oxygen, Apparent Oxygen Utilization, and Oxygen Saturation. NOAA Atlas NESDIS 83.

Huang, and Coauthors: Coastal hypoxia machine-learning studies in *Artificial Intelligence for the Earth Systems* and related venues (specific citations to be finalized from target journal precedents, including Chesapeake Bay applications).

Ito, T., and A. Cervania, 2024: Machine learning mapping of dissolved oxygen (ML4O2). *JGR: Machine Learning and Computation*.

Reynolds, R. W., and Coauthors, 2007: Daily high-resolution-blended analyses for sea surface temperature. *J. Climate*, **20**, 5473–5496. (OISST lineage)

Sharp, J. D., and Coauthors, 2023: GOBAI-O2: A global gridded monthly dataset of ocean interior dissolved oxygen based on recent profiling float measurements. *Earth Syst. Sci. Data*, https://doi.org/10.5194/essd-15-xxxx (see also DOI 10.25921/z72m-yz67).

Sibling Mask-View lake study (Dianchi monitoring-network imputation): repository and manuscript cross-reference to be inserted at submission to avoid dual-submission overlap.

---

## Figure captions (suggested)

**Figure 1.** Study region and schematic: 12-month history → 1/2/3-month leads; hybrid climatology–Transformer blend.  
**Figure 2.** Lead–RMSE, skill versus persistence, and low-oxygen F1 for oxygen-only and physics (`phys_real_wind`) configurations (`paper_plate_full_physics_real_wind.png`).  
**Figure 3.** Physics/wind ablation and Mask-View sparse ablation (`aies_comparison_plate.png`, `maskview_ablation.png`).  
**Figure 4.** Spatial lead-1 absolute-error map and coastal / depth failure-mode bins (`failure_spatial_abserr.png`, `failure_mode_bins.png`).  
**Figure 5.** Section-extrapolation schematic and scores; multi-region subset summary.

## Table index (repository)

| Manuscript table | File |
|------------------|------|
| §4.1 oxygen-only multilead | `results/tables/multilead_full.md` |
| §4.2 physics / wind ablation | `results/tables/physics_ablation.md` |
| §4.2 physics main run | `results/tables/multilead_full_physics_real_wind.md` |
| §4.3 Mask-View ablation | `results/tables/maskview_ablation.md` |
| §4.4 section extrapolation | `results/tables/section_extrapolation.md` |
| §4.5 failure modes | `results/tables/failure_modes.md` |

---

## Change log (editorial)

- Converted working notes into submission prose; removed portfolio-only language from the scientific narrative.  
- Locked numbers to repository tables (oxygen-only, `phys_real_wind`, Mask-View, section, failure modes, bootstrap).  
- Separated method claims from GOBAI-dependent process claims in Limitations.  
- Added Significance statement, Author contributions, Competing interests, and figure/table indices for AMS packaging.
