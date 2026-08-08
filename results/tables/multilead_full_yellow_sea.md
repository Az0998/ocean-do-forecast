# Multi-lead results (`full_yellow_sea`)

Region: `yellow_sea` · cube: `demo` · physics=`False` · sparse=`none` · maskview=`False`

Event threshold: `60.00` µmol/kg (`absolute_hypoxia`)

Hybrid blend weights (val-tuned ST weight): `{'1': 1.0, '2': 0.15000000000000002, '3': 0.0}`

| Lead (mo) | Model | RMSE | Skill vs persist | Hypoxia F1 | CSI |
|---:|---|---:|---:|---:|---:|
| 1 | persistence | 7.153 | 0.000 | 0.882 | 0.789 |
| 1 | climatology | 4.627 | 0.581 | 0.960 | 0.924 |
| 1 | lstm_anomaly | 4.627 | 0.581 | 0.972 | 0.946 |
| 1 | st_transformer | 3.044 | 0.819 | 0.986 | 0.973 |
| 1 | hybrid_clim_st | 3.044 | 0.819 | 0.986 | 0.973 |
| 2 | persistence | 13.030 | 0.000 | 0.788 | 0.650 |
| 2 | climatology | 4.634 | 0.874 | 0.960 | 0.924 |
| 2 | lstm_anomaly | 8.061 | 0.617 | 0.873 | 0.774 |
| 2 | st_transformer | 7.600 | 0.660 | 0.879 | 0.784 |
| 2 | hybrid_clim_st | 4.527 | 0.879 | 0.962 | 0.926 |
| 3 | persistence | 17.983 | 0.000 | 0.696 | 0.534 |
| 3 | climatology | 4.626 | 0.934 | 0.960 | 0.924 |
| 3 | lstm_anomaly | 13.426 | 0.443 | 0.760 | 0.613 |
| 3 | st_transformer | 13.218 | 0.460 | 0.774 | 0.631 |
| 3 | hybrid_clim_st | 4.626 | 0.934 | 0.960 | 0.924 |
