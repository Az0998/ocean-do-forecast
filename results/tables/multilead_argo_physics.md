# Multi-lead results (`argo_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`argo` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.05, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.300 | 5.300 | 0.589 | -0.001 | 0.672 | 0.506 |
| 1 | st_transformer | 5.241 | 5.241 | 0.598 | 0.021 | 0.667 | 0.500 |
| 1 | hybrid_clim_st | 5.241 | 5.241 | 0.598 | 0.021 | 0.667 | 0.500 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.833 | 5.833 | 0.845 | -0.245 | 0.701 | 0.539 |
| 2 | st_transformer | 6.309 | 6.309 | 0.819 | -0.457 | 0.685 | 0.521 |
| 2 | hybrid_clim_st | 5.232 | 5.232 | 0.875 | -0.002 | 0.719 | 0.562 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.770 | 7.770 | 0.854 | -1.227 | 0.617 | 0.447 |
| 3 | st_transformer | 9.928 | 9.928 | 0.761 | -2.637 | 0.534 | 0.365 |
| 3 | hybrid_clim_st | 5.241 | 5.241 | 0.933 | -0.014 | 0.701 | 0.540 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 5.108 | 5.108 | 0.637 | 0.024 | 0.601 |
| DJF | st_transformer | 5 | 5.543 | 5.543 | 0.202 | 0.022 | 0.572 |
| annual | st_transformer | 22 | 5.241 | 5.241 | 0.598 | 0.021 | 0.667 |
| JJAS | hybrid_clim_st | 8 | 5.108 | 5.108 | 0.637 | 0.024 | 0.601 |
| DJF | hybrid_clim_st | 5 | 5.543 | 5.543 | 0.202 | 0.022 | 0.572 |
| annual | hybrid_clim_st | 22 | 5.241 | 5.241 | 0.598 | 0.021 | 0.667 |
