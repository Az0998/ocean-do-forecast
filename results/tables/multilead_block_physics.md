# Multi-lead results (`block_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`block` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.1, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.310 | 5.310 | 0.587 | -0.005 | 0.672 | 0.506 |
| 1 | st_transformer | 4.994 | 4.994 | 0.635 | 0.111 | 0.683 | 0.518 |
| 1 | hybrid_clim_st | 4.994 | 4.994 | 0.635 | 0.111 | 0.683 | 0.518 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.914 | 5.914 | 0.841 | -0.280 | 0.701 | 0.539 |
| 2 | st_transformer | 6.268 | 6.268 | 0.821 | -0.437 | 0.702 | 0.541 |
| 2 | hybrid_clim_st | 5.229 | 5.229 | 0.875 | -0.001 | 0.728 | 0.573 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.431 | 7.431 | 0.866 | -1.038 | 0.606 | 0.434 |
| 3 | st_transformer | 9.954 | 9.954 | 0.760 | -2.656 | 0.530 | 0.361 |
| 3 | hybrid_clim_st | 5.238 | 5.238 | 0.934 | -0.012 | 0.701 | 0.540 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 4.913 | 4.913 | 0.664 | 0.097 | 0.630 |
| DJF | st_transformer | 5 | 5.246 | 5.246 | 0.285 | 0.124 | 0.584 |
| annual | st_transformer | 22 | 4.994 | 4.994 | 0.635 | 0.111 | 0.683 |
| JJAS | hybrid_clim_st | 8 | 4.913 | 4.913 | 0.664 | 0.097 | 0.630 |
| DJF | hybrid_clim_st | 5 | 5.246 | 5.246 | 0.285 | 0.124 | 0.584 |
| annual | hybrid_clim_st | 22 | 4.994 | 4.994 | 0.635 | 0.111 | 0.683 |
