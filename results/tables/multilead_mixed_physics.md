# Multi-lead results (`mixed_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`mixed` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.1, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.299 | 5.299 | 0.589 | -0.001 | 0.673 | 0.507 |
| 1 | st_transformer | 5.071 | 5.071 | 0.624 | 0.084 | 0.680 | 0.515 |
| 1 | hybrid_clim_st | 5.071 | 5.071 | 0.624 | 0.084 | 0.680 | 0.515 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 6.098 | 6.098 | 0.831 | -0.360 | 0.682 | 0.517 |
| 2 | st_transformer | 6.259 | 6.259 | 0.822 | -0.433 | 0.688 | 0.525 |
| 2 | hybrid_clim_st | 5.233 | 5.233 | 0.875 | -0.002 | 0.731 | 0.576 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.265 | 7.265 | 0.872 | -0.947 | 0.619 | 0.448 |
| 3 | st_transformer | 9.934 | 9.934 | 0.761 | -2.641 | 0.533 | 0.363 |
| 3 | hybrid_clim_st | 5.239 | 5.239 | 0.934 | -0.013 | 0.702 | 0.540 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 4.942 | 4.942 | 0.660 | 0.086 | 0.620 |
| DJF | st_transformer | 5 | 5.372 | 5.372 | 0.250 | 0.082 | 0.589 |
| annual | st_transformer | 22 | 5.071 | 5.071 | 0.624 | 0.084 | 0.680 |
| JJAS | hybrid_clim_st | 8 | 4.942 | 4.942 | 0.660 | 0.086 | 0.620 |
| DJF | hybrid_clim_st | 5 | 5.372 | 5.372 | 0.250 | 0.082 | 0.589 |
| annual | hybrid_clim_st | 22 | 5.071 | 5.071 | 0.624 | 0.084 | 0.680 |
