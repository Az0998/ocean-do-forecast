# Multi-lead results (`full_physics_phys_yellow_sea`)

Region: `yellow_sea` · cube: `physics_multidrive` · physics=`True` · sparse=`none` · maskview=`False`

Event threshold: `199.43` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.4, '3': 0.05}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.362 | 8.362 | 0.000 | -1.347 | 0.593 | 0.421 |
| 1 | climatology | 5.459 | 5.459 | 0.574 | 0.000 | 0.562 | 0.391 |
| 1 | lstm_anomaly | 5.472 | 5.472 | 0.572 | -0.005 | 0.563 | 0.392 |
| 1 | st_transformer | 3.915 | 3.915 | 0.781 | 0.486 | 0.710 | 0.551 |
| 1 | hybrid_clim_st | 3.915 | 3.915 | 0.781 | 0.486 | 0.710 | 0.551 |
| 2 | persistence | 15.158 | 15.158 | 0.000 | -7.013 | 0.254 | 0.146 |
| 2 | climatology | 5.355 | 5.355 | 0.875 | 0.000 | 0.674 | 0.508 |
| 2 | lstm_anomaly | 5.766 | 5.766 | 0.855 | -0.159 | 0.636 | 0.467 |
| 2 | st_transformer | 5.640 | 5.640 | 0.862 | -0.109 | 0.723 | 0.567 |
| 2 | hybrid_clim_st | 5.108 | 5.108 | 0.886 | 0.090 | 0.703 | 0.543 |
| 3 | persistence | 20.873 | 20.873 | 0.000 | -14.532 | 0.099 | 0.052 |
| 3 | climatology | 5.296 | 5.296 | 0.936 | 0.000 | 0.662 | 0.495 |
| 3 | lstm_anomaly | 7.206 | 7.206 | 0.881 | -0.851 | 0.663 | 0.496 |
| 3 | st_transformer | 9.985 | 9.985 | 0.771 | -2.554 | 0.574 | 0.403 |
| 3 | hybrid_clim_st | 5.304 | 5.304 | 0.935 | -0.003 | 0.671 | 0.505 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 5.405 | 5.405 | 0.578 | 0.000 | 0.571 |
| DJF | climatology | 5 | 5.463 | 5.463 | 0.230 | 0.000 | 0.271 |
| annual | climatology | 22 | 5.459 | 5.459 | 0.574 | 0.000 | 0.562 |
| JJAS | st_transformer | 8 | 3.917 | 3.917 | 0.778 | 0.475 | 0.556 |
| DJF | st_transformer | 5 | 3.843 | 3.843 | 0.619 | 0.505 | 0.569 |
| annual | st_transformer | 22 | 3.915 | 3.915 | 0.781 | 0.486 | 0.710 |
| JJAS | hybrid_clim_st | 8 | 3.917 | 3.917 | 0.778 | 0.475 | 0.556 |
| DJF | hybrid_clim_st | 5 | 3.843 | 3.843 | 0.619 | 0.505 | 0.569 |
| annual | hybrid_clim_st | 22 | 3.915 | 3.915 | 0.781 | 0.486 | 0.710 |
