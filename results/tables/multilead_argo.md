# Multi-lead results (`argo`)

Region: `east_china_sea_shelf` · cube: `woa_informed` · physics=`False` · sparse=`argo` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.0, '3': 0.0}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.317 | 0.586 | 0.673 | 0.508 |
| 1 | st_transformer | 5.221 | 0.601 | 0.671 | 0.505 |
| 1 | hybrid_clim_st | 5.221 | 0.601 | 0.671 | 0.505 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 9.038 | 0.628 | 0.558 | 0.387 |
| 2 | st_transformer | 8.997 | 0.631 | 0.561 | 0.389 |
| 2 | hybrid_clim_st | 5.228 | 0.875 | 0.719 | 0.561 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 14.826 | 0.468 | 0.358 | 0.218 |
| 3 | st_transformer | 14.804 | 0.469 | 0.352 | 0.214 |
| 3 | hybrid_clim_st | 5.206 | 0.934 | 0.700 | 0.539 |
