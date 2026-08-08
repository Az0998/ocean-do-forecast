# 研究计划：区域海洋溶解氧中长期预报

## 1. 科学问题

在 BGC-Argo 稀疏、船测不均的条件下，能否对目标海区给出 **7–90 天** 有技巧的溶解氧预报，并对 **缺氧/低氧事件** 给出可用预警指标？

约束：

- 不做全球月尺度重建产品（GOBAI-O2 / BLENDR 已占位）
- 不只报 RMSE，必须报事件技巧（CSI / F1 / lead–skill 曲线）
- 代码与关键数据路径开源 + DOI（AMS/AGU 硬要求）

## 2. 与现有工作的关系

| 工作 | 任务 | 本项目差异 |
|------|------|------------|
| Sharp et al. GOBAI-O2 (ESSD 2023) | Argo→月格点重建 | 用其作输入/气候态，不重做产品 |
| Ito et al. ML4O2 (JGR:MLC 2024) | 船测+Argo 映射与去氧趋势 | 做预报，不做长期趋势主叙事 |
| BLENDR (ESSD 2025 preprint) | 深海重建至 ~5900 m | 聚焦上层/陆架相关深度预报 |
| Chesapeake hypoxia AI (AIES) | 日尺度河口 | 中长期 + 陆架/开阔海区 |
| GoM ST-Transformer (2026) | 日尺度缺氧分类 | 回归+风险、更长 lead |
| water-ai-do-forecast（本仓库） | 湖泊插补+下游预警 | 方法迁移：Mask-View / 时空图 |

## 3. 区域选择（优先序）

1. **东海 / 黄海陆架** — 缺氧与渔业相关、中文组易讲故事；需确认 Argo-O2 密度
2. **南海北部** — 层结强、内波/季风调制；数据可能更稀
3. **黑潮延伸体** — 动力学清晰、开源再分析好；缺氧叙事弱于陆架

决策准则：目标区内有效 BGC-O2 剖面数、季节覆盖、是否有独立船测验证段。  
**第 1–2 周冻结区域，写入 `configs/region.yaml`。**

## 4. 数据

| 源 | 用途 | 备注 |
|----|------|------|
| BGC-Argo DO | 标签 / 稀疏监督 | Delayed-mode + QC；注意 Argo 相对船测偏差 |
| GOBAI-O2 | 格点场 / 气候态 / 预训练 | 月尺度；预报时勿泄漏未来 |
| Core-Argo T/S | 物理协变量 | 密度/层结代理 |
| ERA5 | 风、热通量等强迫 | 预报场景需用再分析或预报场做敏感性 |
| WOA / GLODAP | 气候态基线 | persistence / climatology |
| 可选 CMEMS/GLORYS | 三维物理场 | 提升技巧，增加依赖 |

时间切分：**按年块**（非随机剖面）划分 train / val / test，避免泄漏。

## 5. 方法

1. **基线：** climatology、persistence、线性回归、浅层 LSTM/CNN
2. **主模型：** Spatiotemporal Transformer 或 GNN+Temporal Attention（复用滇池架构思想）
3. **稀疏性：** Mask-View 多模式掩码（point / block_time / sensor）
4. **物理：** 溶解度/AOU 代理残差、非负氧约束、分层相关特征
5. **任务头：** 连续 DO 回归 + 低氧二分类（阈值阈值或 2 mg/L 等区域阈值）

## 6. 评估协议

- Lead：7 / 14 / 30 / 60 / 90 天（按数据分辨率可调）
- 连续：RMSE、MAE、ACC、相对于 persistence 的 skill score
- 事件：CSI、F1、POD/FAR；分季节
- 空间：技巧地图；深度：误差剖面
- 稀疏压力测试：人为加大掩码率，对应 Mask-View 消融

## 7. 12 周里程碑

| 周 | 交付 | 完成定义 | 状态 |
|----|------|----------|------|
| 1–2 | 区域冻结 + 数据卡 + 下载脚本 | `dataset_card/` 可独立复现样本统计 | ✅ demo 立方体；`subset_gobai.py` 就绪 |
| 3–5 | 全部基线跑通 | `results/tables/baselines.md` | ✅ + `run_multilead.py` 1/2/3 月 |
| 6–8 | 主模型 + 物理残差 + Mask-View | 消融表；beat persistence @30d | ✅ ST+物理；`--sparse station/point/block` |
| 9–10 | 事件评估 + 主图 | 投稿级图 ≥300 dpi | ✅ lead/深度/空间/季节/Mask-View/物理对比板；bootstrap CI |
| 11–12 | Zenodo + 手稿 v1 | 按 AIES 词数与结构成稿 | 🟡 `paper/manuscript_final.md` 已定稿；待 Zenodo DOI + GOBAI 复现 |

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 目标区 Argo-O2 太稀 | 换东海/延伸体；或用 GOBAI 作伪标签 + 独立船测验证 |
| 只能拟合气候态 | 强调 anomaly skill 与事件指标 |
| 审稿人认作「又一个 Transformer」 | 突出稀疏观测协议 + 物理残差 + 与重建产品的任务差异 |
| APC 预算 | 优先 AIES（~$2200）；或走机构协议 / waiver |

## 9. 成功标准（可投稿）

同时满足：

1. 至少一个 lead（建议 30 天）在区域平均 anomaly RMSE 上稳定优于 persistence 与 climatology  
2. 缺氧事件 F1/CSI 优于无技巧基线，并给出空间差异解释  
3. 代码可一键复现主表；数据可用性声明完整  
4. 手稿明确回答「相对 GOBAI 类重建，预报任务多解决了什么」
