# Cover letter draft — AIES / Ocean Modelling

**Subject:** Submission — Spatiotemporal forecasting of dissolved oxygen on the East China Sea shelf under sparse observations

Dear Editor,

We submit a manuscript on **multi-month dissolved oxygen (DO) forecasting** for the East China Sea shelf. Unlike recent ML products that **reconstruct** monthly oxygen maps from sparse observations (e.g., GOBAI-O2), we target **1–3 month leads** that are more relevant to hypoxia risk awareness.

**Why this journal.** The work centers on an AI method (spatiotemporal Transformer + validation-tuned climatology hybrid + Mask-View sparse training) with Earth-system evaluation (lead skill, low-oxygen events, depth profiles, Argo/section sparsity, multi-region sensitivity) and a fully reproducible pipeline that runs without proprietary BGC reanalyses—using WOA T/S, OISST, and ERA5-backed winds as free physical drivers.

**Main findings (method-development cube; physics drivers optional).**
1. At 1-month lead, the Transformer reduces RMSE versus persistence and climatology and improves low-O₂ event F1.
2. At 2–3 month leads, seasonal climatology dominates; a hybrid clim–ST blend recovers near-climatology RMSE while retaining short-lead anomaly skill.
3. Under station-sparse and section-extrapolation inputs, the task remains a **full-field forecast**, not dense reconstruction; one-month skill degrades but stays above persistence.
4. Multi-region checks (Yellow Sea, Yangtze plume) and Mask-View pattern banks stress-test transfer of the sparse-obs narrative.

Code, project site, and intermediate products are public; a DOI will be minted upon acceptance. We confirm the manuscript is original and not under review elsewhere.

Sincerely,  
Senjie Zhang (张森捷) and co-authors

**Suggested reviewers (placeholders):**  
1. Ocean biogeochemical ML / Argo-O2 specialist  
2. Coastal hypoxia forecasting specialist  
3. Spatiotemporal Earth-system AI specialist  
