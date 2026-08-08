# Cover letter draft — AIES / Ocean Modelling

**Subject:** Submission — Spatiotemporal forecasting of dissolved oxygen on the East China Sea shelf under sparse observations

Dear Editor,

We submit a manuscript on **multi-month dissolved oxygen (DO) forecasting** for the East China Sea shelf. Unlike recent ML products that **reconstruct** monthly oxygen maps from sparse observations (e.g., GOBAI-O2), we target **1–3 month leads** that are more relevant to hypoxia risk awareness.

**Why this journal.** The work centers on an AI method (spatiotemporal Transformer + validation-tuned climatology hybrid) with Earth-system evaluation (lead skill, low-oxygen events, depth profiles, Argo-like sparsity stress tests) and a fully reproducible pipeline.

**Main findings (method-development cube pending GOBAI replacement).**
1. At 1-month lead, the Transformer reduces RMSE versus persistence and climatology and improves low-O2 event F1.
2. At 2–3 month leads, seasonal climatology dominates; a hybrid clim–ST blend recovers near-climatology RMSE while retaining short-lead anomaly skill.
3. Under station-sparse inputs, one-month skill degrades but remains above persistence.

Code and intermediate products will be archived with a DOI upon acceptance. We confirm the manuscript is original and not under review elsewhere.

Sincerely,  
[Authors]

**Suggested reviewers (placeholders):**  
1. Ocean biogeochemical ML / Argo-O2 specialist  
2. Coastal hypoxia forecasting specialist  
3. Spatiotemporal Earth-system AI specialist  
