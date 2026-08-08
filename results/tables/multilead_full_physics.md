# Multi-lead results (`full_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`none` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.4, '3': 0.1}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.304 | 0.588 | 0.670 | 0.503 |
| 1 | st_transformer | 3.873 | 0.780 | 0.742 | 0.589 |
| 1 | hybrid_clim_st | 3.873 | 0.780 | 0.742 | 0.589 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 6.018 | 0.835 | 0.698 | 0.536 |
| 2 | st_transformer | 5.687 | 0.853 | 0.710 | 0.551 |
| 2 | hybrid_clim_st | 5.043 | 0.884 | 0.740 | 0.587 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.570 | 0.861 | 0.631 | 0.461 |
| 3 | st_transformer | 9.123 | 0.798 | 0.546 | 0.376 |
| 3 | hybrid_clim_st | 5.237 | 0.934 | 0.704 | 0.544 |
