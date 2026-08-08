# 期刊地图与投稿要求摘要

> 信息截至 2026-08，APC/政策以期刊官网为准，投稿前复核。

## 推荐顺序

```
AIES (主投)
  → Ocean Modelling（备选 / AI 专刊）
    → JAMES（方法极强时）
      → Frontiers Mar. Sci. / Sci. Reports（保底）
JGR: Oceans —— 仅当有明确海洋过程洞见
ESSD —— 仅当拆出可引用的预报产品数据集
```

## 分刊要点

### 1. AIES — Artificial Intelligence for the Earth Systems (AMS)

- **适合：** AI/ML 方法在海洋/气候中的应用；物理约束 AI；预报
- **篇幅：** Articles 正文约 ≤7500 词（不含摘要/参考文献/图表）
- **费用：** 全 OA，约 **$2200**/篇（机构 Read&Publish 可能全免）
- **先例：** Chesapeake Bay hypoxia AI 预报
- **链接：** https://www.ametsoc.org/ams/publications/journals/artificial-intelligence-for-the-earth-systems/

### 2. Ocean Modelling (Elsevier)

- **适合：** 海洋模式、预报系统、AI 与模式融合
- **动态：** 有 “Applications of AI in Ocean Modeling” 等专刊
- **费用：** APC 约 **USD 3390**（以投稿时为准）
- **链接：** https://www.sciencedirect.com/journal/ocean-modelling

### 3. JAMES — Journal of Advances in Modeling Earth Systems (AGU)

- **适合：** 建模方法进步、物理信息 ML、可迁移框架
- **硬要求：** 开源数据+软件；文内 **Open Research**；Zenodo 等 DOI
- **政策：** https://www.agu.org/publish-with-agu/publish/author-resources/data-and-software-for-authors
- **提交：** http://james-submit.agu.org/

### 4. JGR: Oceans (AGU)

- **适合：** 新的海洋过程理解（物理/生物地球化学）
- **红线：** 纯工具、纯方法对比、无海洋科学推进 → 编辑可能 desk-reject，建议转 JAMES/ESS
- **来源：** editorial “What’s New at JGR-Oceans?” (2022)

### 5. ESSD — Earth System Science Data

- **适合：** 数据描述文（算法是配角）
- **硬要求：** 数据集独立 DOI；质量与不确定度专节；非技术摘要；开放许可
- **APC：** 2025 起约 **€1400**/篇
- **链接：** https://www.earth-system-science-data.net/

### 6. Frontiers in Marine Science

- **适合：** 区域应用、缺氧预警、方法+案例
- **APC：** Original Research 约 **CHF 3150**（A 类）
- **链接：** https://www.frontiersin.org/journals/marine-science

## 所有目标刊共用检查清单

- [ ] Data Availability：原始数据 DOI/URL + 访问日期
- [ ] Code：GitHub + 归档 DOI（Zenodo）
- [ ] 训练/验证/测试按时间切分说明
- [ ] 基线含 persistence 与 climatology
- [ ] 图 ≥300 dpi；色盲友好
- [ ] 英文润色；利益冲突与基金声明
- [ ] APC / 机构协议确认

## 与滇池 Water 稿的关系

`water-ai-do-forecast` 走 MDPI *Water*；本项目走 **海洋/地球系统 AI 刊**，避免两篇挤同一应用刊。统一叙事放在共同 IP 说明，不共享同一主结果表。
