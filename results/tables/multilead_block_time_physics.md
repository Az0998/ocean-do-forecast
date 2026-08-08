# Multi-lead results (`block_time_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`block_time` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.30000000000000004, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.306 | 5.306 | 0.588 | -0.003 | 0.665 | 0.499 |
| 1 | st_transformer | 4.273 | 4.273 | 0.733 | 0.349 | 0.720 | 0.563 |
| 1 | hybrid_clim_st | 4.273 | 4.273 | 0.733 | 0.349 | 0.720 | 0.563 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.943 | 5.943 | 0.839 | -0.292 | 0.705 | 0.544 |
| 2 | st_transformer | 5.858 | 5.858 | 0.844 | -0.255 | 0.698 | 0.536 |
| 2 | hybrid_clim_st | 5.094 | 5.094 | 0.882 | 0.050 | 0.740 | 0.588 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.206 | 7.206 | 0.874 | -0.916 | 0.637 | 0.467 |
| 3 | st_transformer | 9.885 | 9.885 | 0.763 | -2.605 | 0.529 | 0.360 |
| 3 | hybrid_clim_st | 5.225 | 5.225 | 0.934 | -0.007 | 0.702 | 0.541 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 4.105 | 4.105 | 0.765 | 0.369 | 0.630 |
| DJF | st_transformer | 5 | 4.291 | 4.291 | 0.522 | 0.414 | 0.668 |
| annual | st_transformer | 22 | 4.273 | 4.273 | 0.733 | 0.349 | 0.720 |
| JJAS | hybrid_clim_st | 8 | 4.105 | 4.105 | 0.765 | 0.369 | 0.630 |
| DJF | hybrid_clim_st | 5 | 4.291 | 4.291 | 0.522 | 0.414 | 0.668 |
| annual | hybrid_clim_st | 22 | 4.273 | 4.273 | 0.733 | 0.349 | 0.720 |
