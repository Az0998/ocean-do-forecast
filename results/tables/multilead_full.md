# Multi-lead results (`full`)

Region: `east_china_sea_shelf` · cube: `woa_informed` · sparse=`none`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.1, '3': 0.0}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.312 | 0.587 | 0.672 | 0.506 |
| 1 | st_transformer | 3.842 | 0.784 | 0.743 | 0.591 |
| 1 | hybrid_clim_st | 3.842 | 0.784 | 0.743 | 0.591 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 9.685 | 0.573 | 0.523 | 0.354 |
| 2 | st_transformer | 8.694 | 0.656 | 0.596 | 0.424 |
| 2 | hybrid_clim_st | 5.191 | 0.877 | 0.718 | 0.560 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 14.827 | 0.468 | 0.358 | 0.218 |
| 3 | st_transformer | 14.752 | 0.473 | 0.372 | 0.229 |
| 3 | hybrid_clim_st | 5.206 | 0.934 | 0.700 | 0.539 |

## Depth RMSE (lead=1)

| Depth (dbar) | climatology | lstm_anomaly | st_transformer | hybrid_clim_st |
|---:|---:|---:|---:|---:|
| 10 | 5.126 | 5.146 | 3.853 | 3.853 |
| 50 | 5.522 | 5.524 | 3.921 | 3.921 |
| 100 | 5.290 | 5.282 | 3.747 | 3.747 |
| 200 | 5.299 | 5.326 | 3.881 | 3.881 |
| 500 | 5.243 | 5.272 | 3.807 | 3.807 |
