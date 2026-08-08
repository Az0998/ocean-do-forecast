# Multi-lead results (`full_yangtze_estuary`)

Region: `yangtze_estuary` · cube: `demo` · physics=`False` · sparse=`none` · maskview=`False`

Event threshold: `60.00` µmol/kg (`absolute_hypoxia`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.0, '3': 0.0}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 7.888 | 0.000 | 0.867 | 0.765 |
| 1 | climatology | 3.995 | 0.744 | 0.989 | 0.978 |
| 1 | lstm_anomaly | 4.064 | 0.735 | 0.989 | 0.978 |
| 1 | st_transformer | 2.875 | 0.867 | 0.989 | 0.978 |
| 1 | hybrid_clim_st | 2.875 | 0.867 | 0.989 | 0.978 |
| 2 | persistence | 14.245 | 0.000 | 0.733 | 0.579 |
| 2 | climatology | 3.968 | 0.922 | 0.989 | 0.978 |
| 2 | lstm_anomaly | 8.243 | 0.665 | 0.865 | 0.762 |
| 2 | st_transformer | 8.057 | 0.680 | 0.869 | 0.768 |
| 2 | hybrid_clim_st | 3.968 | 0.922 | 0.989 | 0.978 |
| 3 | persistence | 19.439 | 0.000 | 0.600 | 0.429 |
| 3 | climatology | 4.013 | 0.957 | 0.989 | 0.978 |
| 3 | lstm_anomaly | 14.157 | 0.470 | 0.730 | 0.575 |
| 3 | st_transformer | 14.079 | 0.475 | 0.739 | 0.586 |
| 3 | hybrid_clim_st | 4.013 | 0.957 | 0.989 | 0.978 |
