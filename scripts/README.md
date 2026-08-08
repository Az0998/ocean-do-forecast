# Scripts

| 脚本 | 作用 |
|------|------|
| `survey_argo_coverage.py` | Argovis 覆盖调查 + `--freeze` 写 `configs/region.yaml` |
| `build_demo_cube.py` | 合成区域氧场 NetCDF |
| `download_gobai.py` | GOBAI 指引 / 本地文件导入 |
| `subset_gobai.py` | 全场 GOBAI → 区域立方体 |
| `download_woa_oxygen.py` | 下载 WOA18 O2 并裁区域 |
| `build_woa_informed_cube.py` | WOA 气候态 + 合成距平立方体 |
| `export_summary.py` | 汇总 `RESULTS_SUMMARY.md` |
| `compose_paper_figures.py` | 2×2 投稿组合图 |
| `bootstrap_and_smoke.py` | 一键冒烟 |

根目录实验：`run_multilead.py`（多 lead + hybrid + 稀疏 + 深度剖面图）。
