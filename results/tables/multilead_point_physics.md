# Multi-lead results (`point_physics`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`point` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.1, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 8.265 | 0.000 | -1.434 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.300 | 5.300 | 0.589 | -0.001 | 0.670 | 0.503 |
| 1 | st_transformer | 5.016 | 5.016 | 0.632 | 0.104 | 0.692 | 0.529 |
| 1 | hybrid_clim_st | 5.016 | 5.016 | 0.632 | 0.104 | 0.692 | 0.529 |
| 2 | persistence | 14.815 | 14.815 | 0.000 | -7.031 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 5.228 | 0.875 | 0.000 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.974 | 5.974 | 0.837 | -0.306 | 0.697 | 0.535 |
| 2 | st_transformer | 6.248 | 6.248 | 0.822 | -0.429 | 0.683 | 0.519 |
| 2 | hybrid_clim_st | 5.229 | 5.229 | 0.875 | -0.000 | 0.732 | 0.578 |
| 3 | persistence | 20.319 | 20.319 | 0.000 | -14.233 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 5.206 | 0.934 | 0.000 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.432 | 7.432 | 0.866 | -1.038 | 0.621 | 0.450 |
| 3 | st_transformer | 9.959 | 9.959 | 0.760 | -2.659 | 0.528 | 0.359 |
| 3 | hybrid_clim_st | 5.238 | 5.238 | 0.934 | -0.012 | 0.702 | 0.541 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.170 | 5.170 | 0.628 | 0.000 | 0.576 |
| DJF | climatology | 5 | 5.606 | 5.606 | 0.184 | 0.000 | 0.573 |
| annual | climatology | 22 | 5.298 | 5.298 | 0.589 | 0.000 | 0.671 |
| JJAS | st_transformer | 8 | 4.924 | 4.924 | 0.662 | 0.093 | 0.634 |
| DJF | st_transformer | 5 | 5.213 | 5.213 | 0.294 | 0.135 | 0.601 |
| annual | st_transformer | 22 | 5.016 | 5.016 | 0.632 | 0.104 | 0.692 |
| JJAS | hybrid_clim_st | 8 | 4.924 | 4.924 | 0.662 | 0.093 | 0.634 |
| DJF | hybrid_clim_st | 5 | 5.213 | 5.213 | 0.294 | 0.135 | 0.601 |
| annual | hybrid_clim_st | 22 | 5.016 | 5.016 | 0.632 | 0.104 | 0.692 |
