# Multi-lead results (`full_physics_synth_wind`)

Region: `east_china_sea_shelf` · cube: `physics_multidrive` · physics=`True` · sparse=`none` · maskview=`False`

Event threshold: `195.09` µmol/kg (`percentile_p10`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.5, '3': 0.15000000000000002}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 8.265 | 0.000 | 0.600 | 0.429 |
| 1 | climatology | 5.298 | 0.589 | 0.671 | 0.505 |
| 1 | lstm_anomaly | 5.303 | 0.588 | 0.670 | 0.504 |
| 1 | st_transformer | 3.871 | 0.781 | 0.742 | 0.590 |
| 1 | hybrid_clim_st | 3.871 | 0.781 | 0.742 | 0.590 |
| 2 | persistence | 14.815 | 0.000 | 0.357 | 0.217 |
| 2 | climatology | 5.228 | 0.875 | 0.719 | 0.561 |
| 2 | lstm_anomaly | 5.855 | 0.844 | 0.702 | 0.540 |
| 2 | st_transformer | 5.152 | 0.879 | 0.739 | 0.586 |
| 2 | hybrid_clim_st | 4.914 | 0.890 | 0.746 | 0.595 |
| 3 | persistence | 20.319 | 0.000 | 0.235 | 0.133 |
| 3 | climatology | 5.206 | 0.934 | 0.700 | 0.539 |
| 3 | lstm_anomaly | 7.455 | 0.865 | 0.615 | 0.444 |
| 3 | st_transformer | 6.723 | 0.891 | 0.637 | 0.467 |
| 3 | hybrid_clim_st | 5.188 | 0.935 | 0.708 | 0.548 |
