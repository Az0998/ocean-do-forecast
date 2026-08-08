# Multi-lead results (`station_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`station` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.05, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.303 | 5.303 | 0.588 | -0.002 | 0.668 | 0.502 |
| 1 | st_transformer | 5.232 | 5.232 | 0.599 | 0.025 | 0.674 | 0.508 |
| 1 | hybrid_clim_st | 5.232 | 5.232 | 0.599 | 0.025 | 0.674 | 0.508 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 6.024 | 6.024 | 0.835 | -0.328 | 0.695 | 0.532 |
| 2 | st_transformer | 6.320 | 6.320 | 0.818 | -0.462 | 0.688 | 0.525 |
| 2 | hybrid_clim_st | 5.233 | 5.233 | 0.875 | -0.002 | 0.720 | 0.563 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 8.373 | 8.373 | 0.830 | -1.587 | 0.557 | 0.386 |
| 3 | st_transformer | 9.944 | 9.944 | 0.761 | -2.648 | 0.531 | 0.361 |
| 3 | hybrid_clim_st | 5.241 | 5.241 | 0.933 | -0.013 | 0.701 | 0.540 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 5.119 | 5.119 | 0.635 | 0.020 | 0.598 |
| DJF | st_transformer | 5 | 5.521 | 5.521 | 0.208 | 0.030 | 0.579 |
| annual | st_transformer | 22 | 5.232 | 5.232 | 0.599 | 0.025 | 0.674 |
| JJAS | hybrid_clim_st | 8 | 5.119 | 5.119 | 0.635 | 0.020 | 0.598 |
| DJF | hybrid_clim_st | 5 | 5.521 | 5.521 | 0.208 | 0.030 | 0.579 |
| annual | hybrid_clim_st | 22 | 5.232 | 5.232 | 0.599 | 0.025 | 0.674 |
