# Scaling Law 基础与领域逻辑

> last_updated: 2026-11-15
> status: 已基于 foundations-data agent 的精读报告与 12 篇下载 PDF 核对；未验证处标 `[待确认]`。
> 覆盖：N/D/C 基础、函数形式、计算最优分配、复现与可识别性、八条轴地图、领域演化逻辑
> 用法：下游模型先读本文，再读与问题相关的 `axis-*.md`，最后读 `failures-and-tensions.md`。不要重新检索整个领域。

## 0. 一句话论点

Scaling law 不是“模型越大越好”的经验口号，而是关于**在给定数据分布、架构族和训练配方下，损失如何随参数量 N、数据量 D、计算量 C 可预测地变化**的定量假设。

它的价值在两点：**外推**（用中小规模实验预测大规模）与**分配**（固定算力下决定 N、D、形状、稀疏度、训练时长怎么分）。

它的脆弱点也在这里：**所有结论都条件于实验设计**。2024–2026 最重要的进展不是又拟合出一个新指数，而是发现许多已发表指数在共线设计下**不可识别**。因此：

> **“20 tokens/parameter” 是一个 policy，不是一条 law。** 把它当常数，是这个领域最常见的误读。

## 1. 这个领域到底在预测什么

三个核心量：`N`（参数量/激活参数量）、`D`（训练 token 数）、`C`（训练计算量，通常 `C ≈ 6ND`，注意力项另计）、`L`（验证损失）。

三个层次，可靠性依次下降：

1. **单模型损失预测**：在拟合范围内最可靠。
2. **计算最优分配**：依赖拟合形式与外推；2026 的可识别性研究说明它比想象中脆弱。
3. **下游能力预测**：最弱；loss 下降不保证下游指标线性提升，涌现/评估口径/数据污染都会破坏预测。

必须区分：拟合（interpolation）、外推（extrapolation）、机制（mechanism）。Scaling law 是现象学描述，不是第一性原理；现有机制解释（数据流形维度、方差受限、参数-数据权衡）没有单一共识。

## 2. Kaplan → Chinchilla → 复现 → 可识别性

### 2.1 Kaplan et al. 2020（arXiv:2001.08361）

- **设置**：decoder-only Transformer，768–1.5B non-embedding 参数，WebText2（22B tokens）；扫 N、D、C。
- **拟合**：
  - `L(N) = (N_c/N)^{0.076}`，`N_c = 8.8×10^13`
  - `L(D) = (D_c/D)^{0.095}`，`D_c = 5.4×10^13`
  - `L(C_min) = (C_c/C_min)^{0.050}`，`C_c = 3.1×10^8` PF-days
  - 计算最优分配：`N_opt ∝ C^{0.73}`，`D_opt ∝ C^{0.27}`
- **假设**：架构/超参在探索范围内是次要因素；数据 unique 且固定；幂律在观测范围成立；compute 在 early-stopping 点测量。
- **证据**：High（loss 趋势）。拟合覆盖约 8 个数量级 compute、6 个数量级 N、2 个数量级 D。
- **局限**：无理论；最小 D 拟合差；无 repetition；共线设计混杂指数；最大 1.5B；政策被 Chinchilla 推翻。
- **分析**：贡献不是“越大越好”，而是把“规模”拆成 N/D/C，使“规模”变成可拟合、可外推的对象。它隐含假设“数据无限且 unique”，这正是下一代攻击的点。

### 2.2 Hoffmann et al. 2022 / Chinchilla（arXiv:2203.15556）

- **设置**：400+ 模型，70M–16B 参数，5B–500B token；三种估计器：固定模型扫 D、IsoFLOP 剖面、参数化拟合。
- **Law**：`L(N,D) = E + A/N^α + B/D^β`，`E=1.69, A=406.4, B=410.7, α=0.34, β=0.28`。
- **三种估计器的分配指数**：
  - Approach 1：`N_opt ∝ C^0.50`，`D_opt ∝ C^0.50`
  - Approach 2：`0.49 / 0.51`
  - Approach 3：`0.46 / 0.54`
- **政策**：约 20 tokens/parameter；70B Chinchilla 用 1.4T tokens，击败 280B Gopher、175B GPT-3、530B MT-NLG；MMLU 67.5%。
- **假设**：unique data；单一幂律；`FLOPs ≈ 6ND`；拟合大多低于 100 TPP。
- **证据**：High（三种估计器 + 70B/1.4T 实证）。
- **局限**：参数被四舍五入；Approach 3 的置信区间异常窄；报告拟合在重建数据上被拒绝（Besiroglu）；无 inference/repetition；最大 16B。
- **分析**：三种估计器本应互相验证，结果它们自己就给出 0.50/0.50 vs 0.46/0.54 的差异。这已经暗示：**指数是弱识别的**。

### 2.3 Besiroglu et al. 2024 复现（arXiv:2404.10102）

- **设置**：数字化 Hoffmann 的 Figure 4（240 个点），重拟合参数形式，bootstrap 4,000 次。
- **重拟合**：`E=1.8172, A=482.01, B=2085.43, α=0.3478, β=0.3658`。
- **关键结果**：
  - 80% 置信区间比 Hoffmann 报告的宽约 **50×**。
  - 复现拟合隐含约 **20 tokens/parameter**，而 Hoffmann 的**四舍五入参数**隐含约 **70 tokens/parameter**。
  - 似然比检验在无 outlier 时拒绝报告拟合（`p < 1e-16`）。
- **证据**：Medium-high（统计审计，不是新的大规模 sweep）。
- **局限**：数字化噪声；仅 240 点；无法恢复真实数据生成参数；仍是 70M–16B；依赖重建数据集。
- **分析**：20 vs 70 不是“谁算错了”，而是**同一组数据/同一形式下，参数与拟合协议的不确定性**。这直接动摇了“20 tokens/param 是自然常数”的叙事。

### 2.4 Kricheli et al. 2026：TPP coverage 与可识别性（arXiv:2605.08541，NeurIPS 2026）

- **设置**：理论 + 受控实验，5M–77M 参数，四种 scaling-law 形式，五个 corpus。
- **核心结果**：
  - 共线设计 `D = kN` 使 Gauss–Newton 问题 **ill-conditioned**；当 N- 与 D-指数接近时，条件数按 `1/(α-β)^2` 增长。
  - 推导出闭式的 TPP-diversity threshold。
  - 非共线设计在留出数据上以 **97.3%** 胜率优于共线设计（bfloat16 下 98.7%）。
- **假设**：N/D 指数接近；局部二次近似；四种形式之一。
- **证据**：Medium-high（理论 + 受控 win-rate）。
- **局限**：小模型 5M–77M；leading-order threshold；未解决数据质量混杂；无 frontier 验证。
- **分析**：这是 2026 最重要的方法论贡献：把“指数不稳定”从经验尴尬变成**可测试的设计规则**。结论：**一个没有设计信息与不确定性的指数，不是可复用事实。**

### 2.5 这一段的逻辑链

1. Kaplan 发现幂律，把规模变成可拟合对象；但数据被当作无限 unique。
2. Chinchilla 攻击“模型优先”的分配，用三种估计器推出 N/D 约等比例；但三种估计器自己就不一致。
3. Besiroglu 攻击 Chinchilla 的拟合：数字化重拟合后，20 vs 70 tokens/param 的差距来自参数四舍五入与置信区间。
4. Kricheli 解释为什么：共线 `D=kN` 设计使指数近似不可识别；要估计指数，必须设计非共线的 TPP 覆盖。
5. **结论**：不要问“指数是多少”，先问“在这个设计下，指数是否可识别、能外推到哪个 regime”。

## 3. 函数形式与拟合

### 3.1 常见形式

- 单变量幂律：`L(x) = L∞ + a·x^{-α}`
- 联合 N/D：`L(N,D) = E + A/N^α + B/D^β`（Chinchilla）
- Broken power law（Caballero et al., 2210.14891）：
  `y = a + b x^{-c0} ∏_{i=1}^{n} (1 + (x/d_i)^{1/f_i})^{-c_i f_i}`
  有 n 个断点时有 n+1 个近似幂律段，平滑连接；n=0 退化为单幂律。
- 带饱和/过渡的形式：sigmoid、double descent、数据耗尽拐点

### 3.2 拟合时的关键选择

1. **损失度量**：per-token CE 受 tokenizer 影响；跨 tokenizer 比较要用 bits-per-byte 或统一 tokenizer。
2. **数据**：去重、质量、混合比例改变曲线。
3. **学习率 schedule**：cosine、WSD、constant 形状不同；最优 LR 是否随规模调整会改变拟合。
4. **模型形状**：深度/宽度/头数/MLP 比例是否随规模同步调整。
5. **拟合区间与设计**：只用小模型拟合再外推风险最高；共线 `D=kN` 设计会使指数不可识别（2605.08541）。
6. **权重**：按 token 加权还是按模型等权；是否拟合最大模型；是否报告置信区间。
7. **计算记账**：`6ND` 是否含 attention、embedding、重计算、通信；MoE 用总参数还是激活参数。
8. **报告标准**：至少 3 个 compute budget、每个预算 5+ 模型规模；报告拟合区间、方法、置信区间/预测包络；留出最大模型或整条 TPP ray。

### 3.3 外推的边界

- 局部幂律在跨过某个规模后可能断裂（broken law、涌现、数据耗尽）。
- 下游指标比 loss 更容易出现平台期或阶跃。
- **用 scaling law 做方向判断，不要用它做精确的外推承诺。**

## 4. 计算最优分配是 policy，不是常数

Chinchilla 的 “20 tokens/param” 是一个**特定目标**下的最优：最小化训练算力下的 loss。

但“最优”取决于目标函数：

- **训练算力最优**：Chinchilla 式分配。
- **推理最优**：模型要服务大量请求时，推理成本改变最优——通常偏向更小的模型、更多训练 token（overtraining）。
- **部署约束**：延迟、显存、吞吐、batch size 进一步改变最优。
- **数据受限**：数据不够时，重复/合成/质量筛选改变曲线。
- **架构轴**：MoE、循环、长上下文引入新的“参数/计算/显存”折算关系，Chinchilla 两轴不够。
- **可识别性**：如果拟合设计不可识别，所谓“最优”只是一个 near-minimizer set 的任意成员（2610.34514）。

所以：**“计算最优”是随目标、约束、架构、实验设计变化的函数，不是常数。**

## 5. 八条轴地图

| 轴 | 核心问题 | 详见 |
|---|---|---|
| 参数/数据/计算 | N、D、C 怎么分配？指数是否可识别？ | 本文 + `axis-training.md` |
| 深度/宽度/形状 | 给定参数量，深度、宽度、头数、MLP 比例怎么选？μP 能否迁移超参？ | `axis-architecture.md` |
| MoE/稀疏专家 | 总参数、激活参数、专家数、粒度、共享专家怎么 scaling？ | `axis-architecture.md` |
| 循环/递归深度 | 重复层能否替代更多参数？loop 次数是不是第三根 scaling 轴？ | `axis-architecture.md`（待 loops agent 补） |
| 优化器/训练配方 | AdamW vs Muon、LR/batch/weight decay 怎么随规模变？ | `axis-training.md`（待 optimizer agent 补） |
| 数据 | 数据质量、重复 epoch、数据混合、tokenizer 如何改变 law？ | `axis-training.md` |
| 推理最优/过训练 | 训练/推理总成本下，模型该多小、token 该多少？ | `axis-training.md` |
| 失效边界 | 涌现、double descent、数据耗尽、law break 在哪里发生？ | `failures-and-tensions.md` |

## 6. 这个领域是怎么一步步想过来的

这一节是本文的核心：不是文献列表，而是一条**假设攻击链**。

### 第一代：损失服从幂律

Kaplan 把“规模”拆成 N/D/C，证明 loss 在双对数坐标下近似线性，使规模成为可拟合、可外推的对象。隐含假设：幂律在感兴趣区间成立；模型族/数据/训练配方在缩放时同构；计算最优分配可从拟合曲线解析推出。

### 第二代：分配错了，数据要和参数一起长

Chinchilla 攻击“只扩模型”的分配，用联合 `L(N,D)` 与 IsoFLOP 剖面说明 Kaplan 式分配高估模型、低估数据。但三种估计器自己给出 0.50/0.50 与 0.46/0.54 的差异，已经暴露指数的弱识别。新假设/盲区：数据无限；架构固定；训练算力是唯一目标；简单可加幂律。

### 第三代：数据不是无限的

数据受限研究攻击“数据无限”：重复数据递减收益；约 4 epoch 内近乎免费，之后价值衰减；数据质量、去重、混合改变有效数据量。新盲区：质量如何度量？合成数据收益是否饱和？混合比例能否跨规模迁移？

### 第四代：形状与稀疏度改变“有效参数”

μP/CompleteP 攻击“形状固定”：形状是可控变量，μP 试图让最优超参随宽度/深度迁移。MoE 攻击“参数量 = 计算量”：总参数、激活参数、专家数、粒度、共享专家是新的 scaling 轴。循环模型攻击“层数 = 唯一深度”。新盲区：多轴联合 law 不存在；不同轴“换算率”是否稳定？架构改动后原指数是否还成立？

### 第五代：目标是总成本，不是训练算力

Inference-optimal / overtraining 攻击“训练算力最小化”：若模型要服务大量请求，最优模型更小、训练 token 更多。T² 进一步说明：计入推理成本后，overtraining 可以是 compute-optimal。新盲区：推理需求/硬件成本/latency 怎么建模？过训练到什么程度仍划算？后训练/RL 算力怎么计入？

### 第六代：循环/递归是第三根轴

Looped/recurrent LLM 把“重复应用同一组层”作为新计算轴。Iso-Depth 给出 recurrence-equivalence exponent **φ=0.46**（95% CI [0.41,0.53]）：r 次循环约等于 **r^0.46** 个唯一块（r=4 时 1.9×，r=8 时 2.6×），而 FLOP 成本线性增长；匹配 FLOP+KV 时 loop 输给唯一层。但 φ 是 **recipe-dependent**：truncated BPTT 降到 **0.38**，hyperconnections 升到 **0.65**；Parcae/SMELT/Loopie 在参数匹配、三预算匹配、wall-clock 匹配下分别报告 loop 胜出。**“loop 行不行”首先是匹配口径与训练配方问题，不是架构问题。** 新盲区：loop 次数/参数共享/输入注入/prelude-coda 如何共同决定 law？训练时 loop 与推理时 loop 的换算率是否一致？MoE+loop 的联合 law 是什么？

### 第七代：law 会断，指标会说谎

Emergence/mirage、broken law、数据耗尽、double descent 说明：局部拟合的 law 在跨过某些边界后会失效；下游“涌现”有时是评估口径伪影。2026 的进一步结论：law break 至少有五种来源（真实 regime change、有限预算曲率、函数形式错设、估计不可识别、测量伪影），单条 ladder 无法区分。新盲区：如何区分真实能力跃迁与指标伪影？哪些边界是数据/架构/优化器造成的，哪些是评估造成的？

### 第八代：实验设计本身成为研究对象

2026 的 TPP-coverage 理论、复现审计、rank-reversal 研究、prescriptive refit 说明：**“指数是多少”不再是唯一问题；“在这个设计下指数是否可识别、能外推到哪个 regime”才是。** 这是最新一代，也是本 skill 最应该教给下游的视角。

### 这条链的启示

每一代创新都不是“提出一个新结构”，而是**攻击上一代的一个隐含假设**：

`数据无限` → `数据受限`；`架构固定` → `形状/稀疏/循环可调`；`训练算力唯一` → `总成本`；`幂律恒成立` → `law break`；`loss 代表能力` → `评估口径`；`指数可估计` → `实验设计/可识别性`。

所以找方向的高效方式不是“再想一个新模型”，而是：

1. 列出当前主流 law 的隐含假设；
2. 找哪个假设在你们的规模/架构/数据/部署条件下最可能先崩；
3. 设计一个能**观测到崩溃**的最小实验；
4. 如果崩溃真实存在，再提出修正 law 或新轴。

这正是 `innovation-moves.md` 里的“破假设”原语。

## 7. 当前前沿与空白

1. **Frontier-scale identifiability**：几乎所有 law 在 <10B 参数的共线数据上拟合；没有公开的 30B+ 非共线 N×D 设计。
2. **Overtraining 的定义**：O1（allocation）、O2（optimization）、O3（adaptability）被混用；同一篇论文可以 O1 最优、O3 有害而不矛盾。
3. **Data quality 不是标量**：quality bucket、perplexity filter、classifier score 是不同偏差的代理；InfoLaw 的 information density 尚未跨 pipeline 验证。
4. **Repetition-law transfer**：`R_D*` 是 corpus-specific；2026 rank-reversal 说明小规模 repetition 选择不可靠迁移。
5. **Mixture laws under distribution shift**：现有 law 预测平均验证 loss，不保证下游 accuracy/task balance/safety。
6. **Joint pretraining–inference–posttraining law**：没有 law 包含 SFT/RL；catastrophic overtraining 说明后训练目标能反转预训练最优。
7. **Hardware-aware inference scaling**：FLOP-only 成本模型忽略内存带宽、延迟、能耗；Kinetics vs T² 未解决。
8. **Emergence vs metric artifacts**：BNSL 能拟合拐点，但拟合不解释拐点；真伪之争未定。
9. **Compute accounting**：FLOPs 是 wall-clock/cost/energy 的糟糕代理；Gemstones 指出 GPU-hours 最优与 FLOPs 最优可能不同。
10. **Data contamination/evaluation leakage**：污染会压平或弯曲曲线，很少被审计。

## 8. 下游怎么用这份底座

1. 先读本文，建立“假设攻击链 + 可识别性”的视角。
2. 读与问题相关的 `axis-*.md`，不要从头读所有论文。
3. 读 `failures-and-tensions.md`，先看已知矛盾与空白。
4. 用 `canonical-papers.md` 核对引用与数字；不要凭记忆写 arXiv ID。
5. 只在三种情况下检索：底座标注 `[待确认]`、用户点名、底座更新时间之后的新工作。
6. 如果用户给了代码库，先跑 `scripts/scan_repo.py`，再写方向卡。
7. 方向卡用 `templates/direction_card.md`，每个方向必须可证伪、有预算、有 kill criteria。

## 9. 阅读阶梯

- **Level 0（30 分钟）**：本文 + `canonical-papers.md` 中标注必读的 5 篇（Kaplan、Chinchilla、Besiroglu、Kricheli、BNSL）。
- **Level 1（半天）**：本文 + 一条轴的 `axis-*.md` + 该轴 3–5 篇必读。
- **Level 2（按需）**：`failures-and-tensions.md` 中与你的方向相关的矛盾，回查原文。
- **Level 3（增量）**：用 `scripts/search_arxiv.py` 查底座更新时间之后的新论文，只补缺口。

## 10. 来源

- Kaplan et al., 2001.08361
- Hoffmann et al., 2203.15556
- Besiroglu et al., 2404.10102
- Kricheli et al., 2605.08541
- Caballero et al., 2210.14891
- Muennighoff et al., 2305.16264
- 各轴详细来源见 `axis-*.md` 与 `canonical-papers.md`
