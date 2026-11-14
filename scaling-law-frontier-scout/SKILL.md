---
name: scaling-law-frontier-scout
description: "Scaling law 文献综合与前沿方向挖掘。内置预消化文献底座（参数/数据/计算、深度宽度、MoE、循环、优化器、数据、推理最优、失效边界），下游只需读底座并对缺口做定向检索；结合当前项目代码库评估哪些 scaling 扩展做得动、值得做、够顶会。触发：梳理 scaling law、找 scaling 方向、分析某条 scaling 轴、结合代码库找研究点、评估顶会适配度、scaling 文献综述。"
metadata:
  requires:
    python: ["Python 3.9+ (stdlib only)"]
---

# Scaling Law 前沿挖掘

这个 skill 的核心不是“再搜一遍文献”，而是**站在预消化底座上做创新**。

底座由 skill 作者在构建时完成：大量检索、精读、交叉验证后，把领域理解固化成 `references/` 里的长文。下游模型默认先读底座，只在三种情况下做定向检索。这样可以把 token 和上下文花在“提出并验证新方向”，而不是“重新发现文献”。

## 核心原则

1. **底座优先**：先读 `references/foundations.md`、相关 `axis-*.md`、`failures-and-tensions.md`。不要重新检索整个领域。
2. **定向补搜**：只对底座标注 `[待确认]`、用户点名的方向/论文、或底座 `last_updated` 之后的新工作做检索。
3. **论证优先于罗列**：每条规律必须有机制解释 + 至少两篇论文的交叉证据；必须显式列出矛盾、空白和未验证假设。
4. **方向可证伪**：每个方向都要有假设、最小验证实验、预算、kill criteria。
5. **代码库接地**：如果用户给了代码库，先只读扫描，再判断“现有代码能做哪些扩展、改动量多大”。
6. **顶会导向**：方向要过“新颖性 × 证据可控性 × 规模可行性 × 故事性 ÷ 风险”的筛选。
7. **不编造**：检索不到就写“未找到 / 待确认”；所有数字带出处。

## 底座与阅读顺序

| 文件 | 用途 |
|---|---|
| `references/foundations.md` | 领域总览、从 Kaplan 到 Chinchilla 的范式转移、函数形式、八条轴地图、阅读阶梯 |
| `references/axis-architecture.md` | 深度/宽度/μP、MoE/稀疏专家、循环/递归深度 |
| `references/axis-training.md` | 数据 scaling、优化器/训练配方、推理最优/过训练 |
| `references/failures-and-tensions.md` | 涌现、double descent、数据耗尽、law break、跨轴矛盾与空白 |
| `references/innovation-moves.md` | 前人创新动作、方向生成 playbook、顶会判据、证据标准、代码库接地规则 |
| `references/canonical-papers.md` | 结构化论文卡片（arXiv/venue/设置/结论/证据等级） |

**默认阅读顺序**：`foundations.md` → 与问题相关的 `axis-*.md` → `failures-and-tensions.md` → `innovation-moves.md`。`canonical-papers.md` 用于核对引用与数字，不需要从头读到尾。

## 工作流

### Step 0：确定模式与范围

- 模式 A：领域综合（只做文献地图、规律综合、方向生成）。
- 模式 B：代码库接地（在 A 基础上读取当前项目代码库）。
- 明确 1–3 个可回答的子问题、目标 venue、算力约束。

### Step 1：读底座

- 读 `foundations.md` 与相关轴文件，建立领域坐标。
- 读 `failures-and-tensions.md`，先看已知矛盾与空白。
- **不要**在这一步调用检索；底座已经覆盖的内容不重搜。

### Step 2：定向补搜（仅三种情况）

1. 底座标注 `[待确认]` 或明确未覆盖的轴/论文。
2. 用户点名感兴趣的方向或论文。
3. 底座 `last_updated` 之后的新工作（增量）。

工具：

```bash
python scripts/search_arxiv.py --query "<关键词>" --max-results 10 --out papers.csv
```

优先找综述、立场论文、复现/质疑论文，而不是继续堆同质化结果。搜到的新论文用 `templates/paper_note.json` 记录，再用 `scripts/build_matrix.py` 汇总。

### Step 3：综合

- 横向：同一轴不同论文为什么结论不同？（数据、tokenizer、优化器、拟合范围）
- 纵向：每个扩展在攻击前作的哪个假设？
- 矛盾与空白：哪些结论冲突？哪些轴从未被交叉验证？哪些规模区间没有数据？
- 写出一条**自己的分析逻辑链**：这个领域怎么一步步想过来的，下一步最自然的延伸是什么。

### Step 4：代码库接地（模式 B）

先只读扫描：

```bash
python scripts/scan_repo.py --root <repo> --out codebase_scan.json
```

基于 `codebase_scan.json` 写“代码库能力地图”：

- 已支持的轴/组件
- 扩展点（文件/类/函数）
- 缺口（需要新实现）
- 观测能力缺口（缺哪些日志/指标）
- 算力约束
- 每个方向的改动量：S（只改配置）/ M（一个模块 + 测试）/ L（新子系统或 kernel）

**只读**：不执行仓库代码、不修改仓库、不安装依赖、不读取密钥。

### Step 5：生成方向

每个方向写成一张 `templates/direction_card.md`：

- 一句话可证伪假设
- 文献依据（≥2 篇，含冲突或空白）
- 为什么现在可行（代码/算力/数据/测量）
- 代码落点（真实文件/符号）
- 改动量 S/M/L
- 最小验证实验（规模、token、baseline、主指标、seed）
- 预算（GPU-hours、显存、数据量）
- kill criteria
- 顶会评分（1–5）
- 目标 venue 与理由

### Step 6：顶会筛选

按 `references/innovation-moves.md` 的评分标准逐项打分，排序：
`新颖性 × 证据可控性 × 规模可行性 × 故事性 ÷ 风险`。

### Step 7：产出与自检

用 `templates/synthesis_report.md` 输出：

- `scaling_law_synthesis_<topic>_<date>.md`
- `direction_cards/<slug>.md`
- `papers.csv` + `notes/*.json`
- 模式 B 额外包含代码库能力地图

自检：

- [ ] 有没有“只罗列不分析”的段落？
- [ ] 每条规律是否有机制 + ≥2 篇论文？
- [ ] 是否列出矛盾与空白？
- [ ] 每个方向是否可证伪、有预算、有 kill criteria？
- [ ] 代码落点是否引用真实文件/符号？
- [ ] 是否明确区分“作者声称 / 实验数据 / 第三方复现”？

## 何时使用 / 不使用

**使用**：

- “系统梳理 scaling law 在 <轴> 上的规律，并给出下一步方向”
- “读完这批论文，告诉我这个领域是怎么一步步想过来的”
- “结合我们的代码库，哪些 scaling 扩展适合冲 ICLR/NeurIPS？”
- “给我 5 个顶会级的 scaling law 实验方向”

**不使用**：

- 通用文献综述（用 `deep-research`）
- 论文摘要拼接
- 跑实验、改代码、写论文
- 纯架构瓶颈分析（用 `lm-arch-bottleneck-scout`）

## 与其他 skill 的关系

- `lm-arch-bottleneck-scout`：看架构瓶颈接力；本 skill 看 scaling 轴上的规律与假设演进。两者可以串联：先用瓶颈 scout 找架构问题，再用本 skill 判断 scaling 上是否值得做、怎么做。
- `paper-writing-audit`：方向确定后，用写作审查 skill 检查论文。
- `pdf-review-highlights`：需要给相关论文做整句批注时使用。
- 若环境有 `deep-research`：只用于底座未覆盖的缺口，不要重跑整个领域。

## 硬规则

1. 不允许“某论文提出了 X”式罗列；每条规律必须有机制解释 + ≥2 篇交叉证据。
2. 必须显式列出矛盾、空白、未被验证的假设。
3. 方向必须可证伪，并给出最小验证实验、预算、kill criteria。
4. 所有数字带出处；检索不到写“未找到 / 待确认”。
5. 代码库只读；不执行、不修改、不安装依赖。
6. 区分“现有代码已支持”与“需要新实现”；代码落点必须引用真实文件/符号。
7. 顶会评分是启发式判断，不承诺录用。
8. 不在报告外偷偷修改论文或代码。

## 快速开始

```bash
# 1) 定向检索（只在底座未覆盖时）
python scripts/search_arxiv.py --query "scaling laws mixture of experts" --max-results 10 --out papers.csv

# 2) 只读扫描代码库
python scripts/scan_repo.py --root /path/to/repo --out codebase_scan.json

# 3) 汇总论文笔记
python scripts/build_matrix.py --notes notes/ --out matrix.md --csv matrix.csv
```
