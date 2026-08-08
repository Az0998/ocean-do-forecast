# Failure-mode diagnosis (lead-1 ST, physics cube)

Region: `east_china_sea_shelf` · test MAE = `3.094` µmol kg⁻¹

| Driver | Bin | N cells | MAE | P90 |
|---|---|---:|---:|---:|
| front_|gradSST| | low | 719 | 3.146 | 4.502 |
| front_|gradSST| | mid | 722 | 3.097 | 4.509 |
| front_|gradSST| | high | 719 | 3.040 | 4.333 |
| stratification_N2 | low | 719 | 3.147 | 4.633 |
| stratification_N2 | mid | 722 | 3.181 | 4.593 |
| stratification_N2 | high | 719 | 2.955 | 4.174 |
| coastal_proximity | low | 648 | 2.968 | 4.228 |
| coastal_proximity | mid | 648 | 2.947 | 4.114 |
| coastal_proximity | high | 864 | 3.299 | 4.890 |
| thermocline_depth_level | at_max_N2 | 2160 | 3.114 | 6.338 |
| thermocline_depth_level | other_depths | 8640 | 3.089 | 6.368 |

## Depth MAE

| Depth (dbar) | MAE |
|---:|---:|
| 10 | 3.097 |
| 50 | 3.179 |
| 100 | 3.032 |
| 200 | 3.085 |
| 500 | 3.078 |

## Interpretation notes

- **Coastal proximity** is the clearest failure mode here (MAE 3.30 vs ≈2.95 offshore/mid).
- Depth maximum at **50 dbar** aligns with the seasonal subsurface low-O₂ / pycnocline layer.
- SST-front and N² terciles are **not** monotonic on the WOA-informed cube — do not over-claim frontal failure until GOBAI/ship DO targets are used.
- Thermocline-level MAE ≈ other depths on this development field; revisit with time-varying oxygen.
