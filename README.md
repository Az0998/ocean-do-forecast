# Ocean-DO-Forecast

区域海洋溶解氧 **中长期月尺度预报**（1–3 个月 ≈ 30–90 天）+ 缺氧事件指标。  
与 `water-ai-do-forecast` / Dianchi Mask-View 同一 IP：**观测残缺下的溶解氧时空重建与预见期预报**。

- **Project site**: https://az0998.github.io/ocean-do-forecast/
- **Public repo**: https://github.com/Az0998/ocean-do-forecast

## 当前状态

| 模块 | 状态 |
|------|------|
| 区域冻结（东海陆架） | ✅ |
| Demo / WOA-informed O₂ 立方体 | ✅ |
| 物理协变量（WOA T/S · OISST · Open-Meteo 风） | ✅ `build_physics_cube.py` |
| 多 lead + hybrid | ✅ `run_multilead.py` |
| Mask-View 稀疏库（point/block/block_time/sensor/station/mixed/argo） | ✅ |
| 断面外推 / 多区域敏感性 | ✅ demo + physics 子集（黄海/长江口） |
| Mask-View 全模式消融 | ✅ `run_maskview_ablation.py` |
| 季节技巧 + bootstrap CI | ✅ `run_multilead.py` 输出 |
| 手稿最终稿（英）/ Cover letter | ✅ `paper/manuscript_final.md` · `cover_letter.md` |
| Forecast product NetCDF + Web Demo | ✅ `export_forecast_product` · [`docs/demo.html`](https://az0998.github.io/ocean-do-forecast/demo.html) |
| 失败模态（沿岸 / 跃层） | ✅ `eval_failure_modes.py` |
| GOBAI 真时变氧 | ⬜ NCEI 手动下载后 `--from-file`（自动拉取常超时） |

## 30 秒冒烟

```bash
cd ocean-do-forecast
pip install -r requirements.txt
python scripts/bootstrap_and_smoke.py
```

## 多源驱动（绕开 GOBAI）

```bash
py -3.12 scripts/download_woa_ts.py
py -3.12 scripts/download_oisst_monthly.py
# Real Open-Meteo / ERA5-backed wind (2° grid; 2015–2022 fetch + clim fill)
py -3.12 scripts/download_openmeteo_wind.py --step 2.0 --pause 4 --fetch-start 2015-01-01 --fetch-end 2022-12-31
py -3.12 scripts/build_physics_cube.py
py -3.12 run_multilead.py --physics --quick
# AIES ablation table
py -3.12 scripts/run_physics_ablation.py --skip-download
# Optional CDS ERA5 (needs ~/.cdsapirc)
py -3.12 scripts/download_era5_cds.py
```

## 真稀疏 / 断面 / 多区域 / 产品

```bash
py -3.12 scripts/fetch_argo_stations.py              # Argovis；失败则用长江口断面
py -3.12 scripts/run_maskview_ablation.py --quick    # 全 Mask-View 消融表
py -3.12 scripts/eval_section_extrapolation.py --quick
py -3.12 scripts/run_physics_region_sensitivity.py --quick  # physics 子集
py -3.12 scripts/export_forecast_product.py --quick  # lead-1 NetCDF
py -3.12 scripts/export_web_forecast.py              # Pages demo JSON
py -3.12 scripts/eval_failure_modes.py --quick
py -3.12 scripts/compose_comparison_figures.py
# GOBAI (manual download from NCEI 0259304, then):
# py -3.12 scripts/download_gobai.py --from-file path\to\gobai.nc
# py -3.12 scripts/subset_gobai.py && py -3.12 run_multilead.py --quick
```

## 常用命令

```bash
# 区域
py -3.12 scripts/survey_argo_coverage.py --freeze --offline-demo

# 氧立方体
py -3.12 scripts/build_demo_cube.py
py -3.12 scripts/download_woa_oxygen.py
py -3.12 scripts/build_woa_informed_cube.py

# 主实验
py -3.12 run_multilead.py --demo --quick
py -3.12 run_multilead.py --demo --quick --sparse station --stations 8
py -3.12 scripts/export_summary.py
```

## 结果

- `results/tables/multilead_*.md`
- `results/tables/section_extrapolation.md`
- `results/tables/forecast_demo.json`
- `dataset_card/README.md`

## 期刊策略

见 [`docs/JOURNAL_MAP.md`](docs/JOURNAL_MAP.md) · [`docs/RESEARCH_PLAN.md`](docs/RESEARCH_PLAN.md) · [`paper/manuscript_draft.md`](paper/manuscript_draft.md)

**主投 AIES / Ocean Modelling**；叙事必须区分「预报」vs GOBAI 类「重建」。

## 许可

代码拟随论文 MIT 开源；WOA/OISST/Argo 遵循各自引用要求。GOBAI（若使用）遵循 NCEI/CC0（Sharp et al. 2022/2023）。
