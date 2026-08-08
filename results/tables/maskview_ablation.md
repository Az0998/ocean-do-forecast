# Mask-View sparse ablation (physics cube)

Oxygen history + T/S/N²/SST/Open-Meteo wind. Only the observation mask changes.

| Sparse | Lead-1 ST | Lead-1 best | Lead-1 F1 | Lead-2 ST | Lead-2 best |
|---|---:|---|---:|---:|---|
| none | 3.876 | st_transformer 3.876 | 0.741 | 5.832 | hybrid_clim_st 5.083 |
| point | 5.016 | st_transformer 5.016 | 0.692 | 6.248 | climatology 5.228 |
| block | 4.994 | st_transformer 4.994 | 0.683 | 6.268 | climatology 5.228 |
| block_time | 4.273 | st_transformer 4.273 | 0.720 | 5.858 | hybrid_clim_st 5.094 |
| sensor | 5.075 | st_transformer 5.075 | 0.693 | 6.252 | climatology 5.228 |
| station | 5.232 | st_transformer 5.232 | 0.674 | 6.320 | climatology 5.228 |
| mixed | 5.071 | st_transformer 5.071 | 0.680 | 6.259 | climatology 5.228 |
| argo | 5.241 | st_transformer 5.241 | 0.667 | 6.309 | climatology 5.228 |

## Notes

- `none`: dense oxygen history (upper bound).
- `argo` / `station`: column-limited operational view.
- `block` / `block_time`: contiguous missingness (Mask-View stress).
- Hybrid blend weights shrink toward climatology at longer leads.
