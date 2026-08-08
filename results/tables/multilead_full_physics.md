# Multi-lead results (`full_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`none` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.35000000000000003, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.311 | 5.311 | 0.587 | -0.005 | 0.665 | 0.498 |
| 1 | st_transformer | 3.876 | 3.876 | 0.780 | 0.465 | 0.741 | 0.588 |
| 1 | hybrid_clim_st | 3.876 | 3.876 | 0.780 | 0.465 | 0.741 | 0.588 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 6.060 | 6.060 | 0.833 | -0.344 | 0.696 | 0.534 |
| 2 | st_transformer | 5.832 | 5.832 | 0.845 | -0.245 | 0.701 | 0.540 |
| 2 | hybrid_clim_st | 5.083 | 5.083 | 0.882 | 0.054 | 0.742 | 0.590 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.537 | 7.537 | 0.862 | -1.096 | 0.629 | 0.458 |
| 3 | st_transformer | 9.810 | 9.810 | 0.767 | -2.551 | 0.537 | 0.367 |
| 3 | hybrid_clim_st | 5.222 | 5.222 | 0.934 | -0.006 | 0.703 | 0.542 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 3.848 | 3.848 | 0.794 | 0.446 | 0.711 |
| DJF | st_transformer | 5 | 3.928 | 3.928 | 0.599 | 0.509 | 0.670 |
| annual | st_transformer | 22 | 3.876 | 3.876 | 0.780 | 0.465 | 0.741 |
| JJAS | hybrid_clim_st | 8 | 3.848 | 3.848 | 0.794 | 0.446 | 0.711 |
| DJF | hybrid_clim_st | 5 | 3.928 | 3.928 | 0.599 | 0.509 | 0.670 |
| annual | hybrid_clim_st | 22 | 3.876 | 3.876 | 0.780 | 0.465 | 0.741 |
