# Baseline results (lead=1 month)

Region: `east_china_sea_shelf` · cube: `demo`

| Model | RMSE | MAE | Skill vs persist | Hypoxia F1 | CSI |
|---|---:|---:|---:|---:|---:|
| persistence | 7.663 | 6.260 | 0.000 | 0.880 | 0.785 |
| climatology | 3.487 | 2.794 | 0.793 | 0.937 | 0.882 |
| lstm_anomaly | 3.263 | 2.607 | 0.819 | 0.940 | 0.887 |
| st_transformer_anomaly | 3.172 | 2.533 | 0.829 | 0.944 | 0.895 |

> Demo cube: climatology is intentionally strong; use GOBAI for paper claims.
> Smoke run: anomaly z-score training, lead=1 month, epochs=8 (quick).
