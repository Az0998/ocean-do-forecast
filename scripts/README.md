# Scripts

| 脚本 | 作用 |
|------|------|
| `survey_argo_coverage.py` | Argovis 覆盖调查 + `--freeze` 写 `configs/region.yaml` |
| `fetch_argo_stations.py` | BGC-Argo / 断面站点 JSON（`--sparse argo`） |
| `build_demo_cube.py` | 合成区域氧场 NetCDF |
| `download_gobai.py` | GOBAI 指引 / 本地文件导入（可选） |
| `subset_gobai.py` | 全场 GOBAI → 区域立方体 |
| `download_woa_oxygen.py` | 下载 WOA18 O2 并裁区域 |
| `download_woa_ts.py` | 下载 WOA18 T/S 并裁区域 |
| `download_oisst_monthly.py` | NOAA OISST 月均 SST |
| `download_openmeteo_wind.py` | Open-Meteo/ERA5 风场（或 `--offline-synth`） |
| `build_woa_informed_cube.py` | WOA 气候态 + 合成距平氧立方体 |
| `build_physics_cube.py` | 多源物理立方体（O₂+T/S/N²+SST+风） |
| `eval_section_extrapolation.py` | 断面稀疏输入 → 全场预报评估 |
| `run_region_sensitivity.py` | 黄海 / 长江口敏感性（不永久覆盖 ECS 立方体） |
| `forecast_demo.py` | 简易预报 demo + 误差图 |
| `export_summary.py` | 汇总 `RESULTS_SUMMARY.md` |
| `compose_paper_figures.py` | 2×2 投稿组合图 |
| `bootstrap_and_smoke.py` | 一键冒烟 |

根目录实验：`run_multilead.py`（`--physics` / `--maskview` / `--sparse …`）。
