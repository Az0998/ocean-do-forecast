# Multi-lead results (`full_physics_real_wind`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`none` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.35000000000000003, '3': 0.05}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.311 | 0.587 | 0.665 | 0.498 |
| 1 | st_transformer | 3.876 | 0.780 | 0.741 | 0.588 |
| 1 | hybrid_clim_st | 3.876 | 0.780 | 0.741 | 0.588 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 6.060 | 0.833 | 0.696 | 0.534 |
| 2 | st_transformer | 5.832 | 0.845 | 0.701 | 0.540 |
| 2 | hybrid_clim_st | 5.083 | 0.882 | 0.742 | 0.590 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.537 | 0.862 | 0.629 | 0.458 |
| 3 | st_transformer | 9.810 | 0.767 | 0.537 | 0.367 |
| 3 | hybrid_clim_st | 5.222 | 0.934 | 0.703 | 0.542 |
