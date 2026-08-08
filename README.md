# Ocean-DO-Forecast

区域海洋溶解氧 **中长期月尺度预报**（1–3 个月 ≈ 30–90 天）+ 缺氧事件指标。  
与 `water-ai-do-forecast` 同一 IP：**观测残缺下的溶解氧时空重建与预见期预报**。

- **Project site**: https://az0998.github.io/ocean-do-forecast/
- **Public repo**: https://github.com/Az0998/ocean-do-forecast

## 当前状态

| 模块 | 状态 |
|------|------|
| 区域冻结（东海陆架） | ✅ |
| Demo 立方体 / GOBAI 裁剪 | ✅ `build_demo_cube` / `subset_gobai` |
| 多 lead + 出图 | ✅ `run_multilead.py` |
| 稀疏 Argo 压力测试 | ✅ `--sparse station/point/block` |
| Clim / LSTM / ST | ✅ |
| 手稿/Cover letter/组合图 | ✅ `paper/` + `paper_plate_full.png` |
| 真实 GOBAI 训练 | ⬜ 手动下载后 `subset_gobai` |

## 30 秒冒烟

```bash
cd ocean-do-forecast
pip install -r requirements.txt
python scripts/bootstrap_and_smoke.py
```

在线调查 Argovis（需网络；若 400/429 请加短时间窗或稍后重试，开发默认用 `--offline-demo`）：

```bash
py -3.12 scripts/survey_argo_coverage.py --freeze --start 2020-01-01 --end 2021-12-31
```

## 常用命令

```bash
# 1) 调查并冻结区域
py -3.12 scripts/survey_argo_coverage.py --freeze --offline-demo

# 2) 数据
py -3.12 scripts/build_demo_cube.py
py -3.12 scripts/download_woa_oxygen.py                 # 真实 WOA18 气候态
py -3.12 scripts/build_woa_informed_cube.py             # WOA clim + 合成距平
py -3.12 scripts/download_gobai.py --from-file D:/data/GOBAI.nc
py -3.12 scripts/subset_gobai.py

# 3) 多 lead 主实验（含 hybrid clim+ST）
py -3.12 run_multilead.py --demo --quick
py -3.12 run_multilead.py --demo --quick --sparse station --stations 8
py -3.12 scripts/export_summary.py

# 单 lead 快捷
py -3.12 run_baselines.py --demo --quick
py -3.12 run_st_model.py --demo --quick
```

## 结果

- `results/tables/argo_coverage_survey.md`
- `results/tables/baselines.md`
- `results/tables/st_transformer.json`
- `checkpoints/*.pt`

## 期刊策略

见 [`docs/JOURNAL_MAP.md`](docs/JOURNAL_MAP.md) · 研究计划 [`docs/RESEARCH_PLAN.md`](docs/RESEARCH_PLAN.md)

**主投 AIES / Ocean Modelling**；叙事必须区分「预报」vs GOBAI 类「重建」。

## 目录

```
configs/   regions.yaml + 冻结后的 region.yaml
src/       数据、样本、模型、物理约束、指标
scripts/   调查 / 下载 / demo / 一键冒烟
paper/     投稿清单
dataset_card/
```

## 许可

代码拟随论文 MIT 开源；GOBAI 数据遵循 NCEI/CC0 与引用要求（Sharp et al. 2022/2023）。
