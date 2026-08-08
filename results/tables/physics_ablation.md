# Physics / wind ablation (AIES)

Real wind driver: Open-Meteo archive (ERA5-backed), 2 deg grid, fetched 2015-2022 with month-of-year climatology fill for 2004-2014.

Target oxygen field fixed (WOA-informed). Only drivers change.

| Config | Lead-1 ST RMSE | Lead-2 ST RMSE | Lead-2 best | Lead-3 best |
|---|---:|---:|---|---|
| oxy_only | 3.842 | 8.694 | hybrid_clim_st 5.191 | climatology 5.206 |
| phys_ts_sst | 3.868 | 5.833 | hybrid_clim_st 5.063 | climatology 5.206 |
| phys_synth_wind | 3.871 | 5.152 | hybrid_clim_st 4.914 | hybrid_clim_st 5.188 |
| phys_real_wind | 3.876 | 5.832 | hybrid_clim_st 5.083 | climatology 5.206 |

## Notes

- oxy_only: oxygen history only.
- phys_ts_sst: WOA T/S + stratification + OISST; wind zeroed.
- phys_synth_wind: offline monsoon synthetic wind.
- phys_real_wind: Open-Meteo ERA5-backed archive wind (real).
- CDS ERA5 optional via scripts/download_era5_cds.py when ~/.cdsapirc exists.

