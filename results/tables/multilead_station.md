# Multi-lead results (`station`)

Region: `east_china_sea_shelf` · cube: `woa_informed` · sparse=`station`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.0, '3': 0.0}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.300 | 0.589 | 0.673 | 0.507 |
| 1 | st_transformer | 5.215 | 0.602 | 0.675 | 0.510 |
| 1 | hybrid_clim_st | 5.215 | 0.602 | 0.675 | 0.510 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 9.041 | 0.628 | 0.555 | 0.384 |
| 2 | st_transformer | 8.993 | 0.632 | 0.562 | 0.391 |
| 2 | hybrid_clim_st | 5.228 | 0.875 | 0.719 | 0.561 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 14.825 | 0.468 | 0.358 | 0.218 |
| 3 | st_transformer | 14.797 | 0.470 | 0.355 | 0.216 |
| 3 | hybrid_clim_st | 5.206 | 0.934 | 0.700 | 0.539 |

## Depth RMSE (lead=1)

| Depth (dbar) | climatology | lstm_anomaly | st_transformer | hybrid_clim_st |
|---:|---:|---:|---:|---:|
| 10 | 5.126 | 5.118 | 5.043 | 5.043 |
| 50 | 5.522 | 5.533 | 5.404 | 5.404 |
| 100 | 5.290 | 5.300 | 5.223 | 5.223 |
| 200 | 5.299 | 5.298 | 5.260 | 5.260 |
| 500 | 5.243 | 5.244 | 5.139 | 5.139 |
