# Lead-1 keep scan: ST vs climatology

n_test=22; 200 paired month resamples; ST retrained 8 epochs.
point axis = voxel keep (lake 10/20/30% analog). station axis = column count (keep_ratio unused).
delta = clim RMSE - ST RMSE.

| Pattern | keep_ratio | n_stations | keep_frac | ST | locf | clim | delta | delta 5-95% | ST sig. | winner |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| none | 1.00 | 8 | 1.000 | 3.871 | 8.265 | 5.298 | 1.426 | [1.344, 1.537] | True | st_transformer |
| point | 0.10 | 8 | 0.101 | 5.214 | 5.680 | 5.298 | 0.084 | [0.071, 0.098] | True | st_transformer |
| point | 0.20 | 8 | 0.199 | 5.069 | 6.013 | 5.298 | 0.228 | [0.197, 0.267] | True | st_transformer |
| point | 0.25 | 8 | 0.249 | 5.012 | 6.176 | 5.298 | 0.286 | [0.260, 0.321] | True | st_transformer |
| point | 0.30 | 8 | 0.295 | 4.956 | 6.350 | 5.298 | 0.342 | [0.306, 0.394] | True | st_transformer |
| point | 0.50 | 8 | 0.498 | 4.655 | 6.962 | 5.298 | 0.643 | [0.585, 0.718] | True | st_transformer |
| station | 0.25 | 4 | 0.044 | 5.284 | 5.461 | 5.298 | 0.013 | [0.006, 0.022] | True | st_transformer |
| station | 0.25 | 8 | 0.089 | 5.233 | 5.599 | 5.298 | 0.064 | [0.054, 0.075] | True | st_transformer |
| station | 0.25 | 16 | 0.178 | 5.129 | 5.988 | 5.298 | 0.169 | [0.155, 0.184] | True | st_transformer |
| station | 0.25 | 24 | 0.267 | 4.963 | 6.255 | 5.298 | 0.335 | [0.304, 0.369] | True | st_transformer |
