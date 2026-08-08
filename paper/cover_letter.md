# Cover letter — AIES

**Subject:** Submission — Spatiotemporal forecasting of dissolved oxygen on the East China Sea shelf under sparse observations

Dear Editor,

We submit a manuscript on **multi-month dissolved oxygen (DO) forecasting** for the East China Sea shelf. Unlike recent machine-learning products that **reconstruct** monthly oxygen maps from sparse observations (e.g., GOBAI-O2), we target **1–3 month leads** with an evaluation protocol that keeps the task a full-field forecast under Mask-View / Argo-like missingness.

**Why AIES.** The work centers on an Earth-system AI method—spatiotemporal Transformer, validation-tuned climatology hybrid, and Mask-View sparse training—with lead skill, low-oxygen events, seasonal scores, bootstrap uncertainty, multi-region subsets, and a fully reproducible open pipeline that runs with free physical drivers (WOA T/S, OISST, Open-Meteo/ERA5-backed wind).

**Main findings.**
1. At one-month lead, the Transformer reduces RMSE versus persistence and climatology (3.84 µmol kg⁻¹; skill vs persistence 0.78) and improves low-oxygen event F1 (0.74) on a WOA-informed development cube.
2. Physical drivers mainly lift mid-lead Transformer skill; a hybrid clim–ST blend is best at two months (RMSE 5.08 with real wind).
3. Under station/Argo column masks, lead-1 skill degrades (RMSE ≈5.23–5.24) but remains above persistence; section extrapolation yields a full-field forecast from transect-limited oxygen.
4. Residual errors concentrate on the western shelf and near 50 dbar; we do **not** over-claim frontal failure pending time-varying oxygen targets (GOBAI-O2).

**Transparency.** Primary tables use a clearly labeled method-development oxygen target; Limitations state what must be repeated on GOBAI-O2. Code, tables and an interactive lead-1 demo are public; a Zenodo DOI will be minted at submission/acceptance. The manuscript is original and not under review elsewhere.

Sincerely,  
Senjie Zhang (张森捷)  
Lanzhou University  
[email]

**Suggested reviewers (to be named):**  
1. Ocean biogeochemical ML / Argo-O2 specialist  
2. Coastal hypoxia forecasting specialist  
3. Spatiotemporal Earth-system AI specialist
