# Multi-lead results (`full_physics_phys_yangtze_estuary`)

Region: `yangtze_estuary` · cube: `physics_multidrive` · physics=`True` · sparse=`none` · maskview=`False`

Event threshold: `201.32` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 0.9500000000000001, '2': 0.6000000000000001, '3': 0.1}`

| Lead (mo) | Model | RMSE | Anom RMSE | Skill vs persist | Skill vs clim | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 8.046 | 8.046 | 0.000 | -1.743 | 0.575 | 0.403 |
| 1 | climatology | 4.858 | 4.858 | 0.635 | 0.000 | 0.403 | 0.253 |
| 1 | lstm_anomaly | 4.872 | 4.872 | 0.633 | -0.006 | 0.403 | 0.252 |
| 1 | st_transformer | 3.742 | 3.742 | 0.784 | 0.407 | 0.629 | 0.458 |
| 1 | hybrid_clim_st | 3.736 | 3.736 | 0.784 | 0.409 | 0.643 | 0.474 |
| 2 | persistence | 14.582 | 14.582 | 0.000 | -8.113 | 0.240 | 0.136 |
| 2 | climatology | 4.831 | 4.831 | 0.890 | 0.000 | 0.459 | 0.298 |
| 2 | lstm_anomaly | 5.055 | 5.055 | 0.880 | -0.095 | 0.529 | 0.359 |
| 2 | st_transformer | 5.007 | 5.007 | 0.882 | -0.074 | 0.716 | 0.558 |
| 2 | hybrid_clim_st | 4.651 | 4.651 | 0.898 | 0.073 | 0.671 | 0.505 |
| 3 | persistence | 20.132 | 20.132 | 0.000 | -16.620 | 0.084 | 0.044 |
| 3 | climatology | 4.796 | 4.796 | 0.943 | 0.000 | 0.509 | 0.341 |
| 3 | lstm_anomaly | 6.477 | 6.477 | 0.896 | -0.824 | 0.479 | 0.315 |
| 3 | st_transformer | 7.332 | 7.332 | 0.867 | -1.337 | 0.636 | 0.467 |
| 3 | hybrid_clim_st | 4.775 | 4.775 | 0.944 | 0.009 | 0.593 | 0.422 |

## Seasonal skill (lead = 1 month)

| Season | Model | N | RMSE | Anom RMSE | SkillP | SkillC | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| JJAS | climatology | 8 | 4.707 | 4.707 | 0.618 | 0.000 | 0.000 |
| DJF | climatology | 5 | 4.895 | 4.895 | 0.366 | 0.000 | 0.389 |
| annual | climatology | 22 | 4.858 | 4.858 | 0.635 | 0.000 | 0.403 |
| JJAS | st_transformer | 8 | 3.868 | 3.868 | 0.742 | 0.325 | 0.000 |
| DJF | st_transformer | 5 | 3.771 | 3.771 | 0.624 | 0.406 | 0.610 |
| annual | st_transformer | 22 | 3.742 | 3.742 | 0.784 | 0.407 | 0.629 |
| JJAS | hybrid_clim_st | 8 | 3.841 | 3.841 | 0.746 | 0.334 | 0.000 |
| DJF | hybrid_clim_st | 5 | 3.768 | 3.768 | 0.624 | 0.407 | 0.634 |
| annual | hybrid_clim_st | 22 | 3.736 | 3.736 | 0.784 | 0.409 | 0.643 |
