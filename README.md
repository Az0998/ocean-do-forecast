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
| 断面外推 / 多区域敏感性 | ✅ `eval_section_extrapolation` · `run_region_sensitivity` |
| 手稿（英）/ Cover letter / 组合图 | ✅ `paper/` |
| Forecast demo | ✅ `scripts/forecast_demo.py` |
| GOBAI 真时变氧 | ⬜ 可选本地导入（非必须） |

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
py -3.12 scripts/download_openmeteo_wind.py          # 或 --offline-synth
py -3.12 scripts/build_physics_cube.py
py -3.12 run_multilead.py --physics --quick
py -3.12 run_multilead.py --physics --maskview --sparse mixed --quick
```

## 真稀疏 / 断面 / 多区域

```bash
py -3.12 scripts/fetch_argo_stations.py              # Argovis；失败则用长江口断面
py -3.12 run_multilead.py --sparse argo --quick
py -3.12 scripts/eval_section_extrapolation.py --quick
py -3.12 scripts/run_region_sensitivity.py           # 黄海 / 长江口
py -3.12 scripts/forecast_demo.py --physics --quick
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
