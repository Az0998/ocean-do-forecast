# Multi-lead results (`full_physics_ts_sst`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`none` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.35000000000000003, '3': 0.05}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.336 | 0.583 | 0.671 | 0.505 |
| 1 | st_transformer | 3.868 | 0.781 | 0.743 | 0.591 |
| 1 | hybrid_clim_st | 3.868 | 0.781 | 0.743 | 0.591 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.970 | 0.838 | 0.687 | 0.523 |
| 2 | st_transformer | 5.833 | 0.845 | 0.702 | 0.541 |
| 2 | hybrid_clim_st | 5.063 | 0.883 | 0.739 | 0.586 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.346 | 0.869 | 0.637 | 0.467 |
| 3 | st_transformer | 10.229 | 0.747 | 0.508 | 0.341 |
| 3 | hybrid_clim_st | 5.221 | 0.934 | 0.702 | 0.541 |
