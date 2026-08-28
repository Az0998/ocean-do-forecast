# Fair sparse baselines (masked oxygen history)

Cube `physics_multidrive`; event `percentile_p10` thr=195.09.
persist_unmasked ignores the mask (original number). persist_locf /
linear_time are temporal; spatial_linear fills missing columns horizontally.
Empty voxels fall back to climatology. Static spatial masks make linear_time ≡ persist_locf.

| Pattern | keep | persist_unmasked | persist_locf | linear_time | spatial_linear | clim | ST | fair simple best | ST beats fair simple |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| none | 1.000 | 8.265 | 8.265 | 8.265 | 8.265 | 5.298 | 3.876 | climatology | True |
| point | 0.249 | 8.265 | 6.176 | 6.176 | 12.697 | 5.298 | 5.016 | climatology | True |
| block | 0.267 | 8.265 | 6.105 | 6.105 | 13.728 | 5.298 | 4.994 | climatology | True |
| block_time | 0.450 | 8.265 | 10.049 | 10.049 | 10.049 | 5.298 | 4.273 | climatology | True |
| sensor | 0.200 | 8.265 | 5.990 | 5.990 | 5.990 | 5.298 | 5.075 | climatology | True |
| station | 0.089 | 8.265 | 5.599 | 5.599 | 14.168 | 5.298 | 5.232 | climatology | True |
| mixed | 0.205 | 8.265 | 6.006 | 6.006 | 12.773 | 5.298 | 5.071 | climatology | True |
| argo | 0.078 | 8.265 | 5.538 | 5.538 | 15.150 | 5.298 | 5.241 | climatology | True |
