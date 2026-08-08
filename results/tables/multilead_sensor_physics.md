# Multi-lead results (`sensor_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`sensor` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 0.9500000000000001, '2': 0.1, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.305 | 5.305 | 0.588 | -0.003 | 0.671 | 0.504 |
| 1 | st_transformer | 5.075 | 5.075 | 0.623 | 0.082 | 0.693 | 0.530 |
| 1 | hybrid_clim_st | 5.076 | 5.076 | 0.623 | 0.082 | 0.694 | 0.532 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.998 | 5.998 | 0.836 | -0.316 | 0.690 | 0.526 |
| 2 | st_transformer | 6.252 | 6.252 | 0.822 | -0.430 | 0.692 | 0.528 |
| 2 | hybrid_clim_st | 5.232 | 5.232 | 0.875 | -0.002 | 0.730 | 0.575 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.718 | 7.718 | 0.856 | -1.198 | 0.629 | 0.459 |
| 3 | st_transformer | 10.002 | 10.002 | 0.758 | -2.691 | 0.526 | 0.357 |
| 3 | hybrid_clim_st | 5.240 | 5.240 | 0.933 | -0.013 | 0.701 | 0.539 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 4.975 | 4.975 | 0.655 | 0.074 | 0.650 |
| DJF | st_transformer | 5 | 5.309 | 5.309 | 0.268 | 0.103 | 0.594 |
| annual | st_transformer | 22 | 5.075 | 5.075 | 0.623 | 0.082 | 0.693 |
| JJAS | hybrid_clim_st | 8 | 4.973 | 4.973 | 0.656 | 0.075 | 0.650 |
| DJF | hybrid_clim_st | 5 | 5.313 | 5.313 | 0.267 | 0.102 | 0.598 |
| annual | hybrid_clim_st | 22 | 5.076 | 5.076 | 0.623 | 0.082 | 0.694 |
