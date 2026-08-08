# Dataset card — Ocean-DO-Forecast

## 模式

| 模式 | 路径 | 用途 |
|------|------|------|
| **demo** | `build_demo_cube.py` → `regional_oxygen_cube.nc` | 纯合成冒烟 |
| **woa_informed** | WOA18 区域气候态 + 合成距平 | 半真实方法调试（当前默认立方体） |
| **woa18_annual** | `processed/woa18_oxygen_region.nc` | 真实气候态结构/掩膜 |
| **gobai** | `data/raw/gobai/*.nc` + `subset_gobai.py` | 正式论文主结果 |

## GOBAI-O2（正式）

- DOI: https://doi.org/10.25921/z72m-yz67
- 文献: Sharp et al., ESSD 2023
- 分辨率: 1° × 1° × 月 × 58 层
- 引用: 见项目 README

导入：

```bash
python scripts/download_gobai.py --from-file /path/to/gobai_file.nc
```

## Demo 立方体

由 `src/gobai_data.build_demo_cube` 生成：季节循环 + 深度衰减 + 近岸夏季低氧 + 弱年际趋势。  
attrs 含 `source=demo`。

## 切分

- Train: ≤ 2018-12
- Val: 2019-01 … 2020-12
- Test: ≥ 2021-01  
按目标月时间块切分，禁止随机剖面打乱。

## 区域

由 `scripts/survey_argo_coverage.py --freeze` 写入 `configs/region.yaml`。  
默认候选见 `configs/regions.yaml`。
