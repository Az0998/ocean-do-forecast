# Multi-lead results (`mixed_physics_maskview`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`mixed` · maskview=`True`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.1, '3': 0.05}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.311 | 0.587 | 0.667 | 0.500 |
| 1 | st_transformer | 5.062 | 0.625 | 0.684 | 0.520 |
| 1 | hybrid_clim_st | 5.062 | 0.625 | 0.684 | 0.520 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.813 | 0.846 | 0.702 | 0.541 |
| 2 | st_transformer | 6.123 | 0.829 | 0.698 | 0.536 |
| 2 | hybrid_clim_st | 5.226 | 0.876 | 0.726 | 0.569 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.359 | 0.869 | 0.630 | 0.460 |
| 3 | st_transformer | 9.178 | 0.796 | 0.551 | 0.381 |
| 3 | hybrid_clim_st | 5.227 | 0.934 | 0.702 | 0.541 |
