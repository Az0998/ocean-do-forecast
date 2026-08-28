# Lead-1 ST vs climatology, paired bootstrap over test months

n_test=22 months; 200 resamples; ST retrained 8 epochs (ablation recipe).
delta = clim RMSE - ST RMSE; positive means ST better.
st_significantly_better if the 5th percentile of delta is > 0.

| Pattern | ST | ST 5-95% | clim | persist_locf | delta | delta 5-95% | P(ST<clim) | ST sig. better |
|---|---:|---|---:|---:|---:|---|---:|---|
| none | 3.871 | [3.763, 4.002] | 5.298 | 8.265 | 1.426 | [1.344, 1.537] | 1.00 | True |
| point | 5.001 | [4.887, 5.144] | 5.298 | 6.176 | 0.296 | [0.264, 0.343] | 1.00 | True |
| station | 5.220 | [5.090, 5.377] | 5.298 | 5.599 | 0.078 | [0.064, 0.093] | 1.00 | True |
| argo | 5.235 | [5.094, 5.408] | 5.298 | 5.538 | 0.062 | [0.051, 0.071] | 1.00 | True |
