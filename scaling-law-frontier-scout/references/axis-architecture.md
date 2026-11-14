# 架构轴：深度/宽度/形状与 MoE

> last_updated: 2026-11-15
> status: 已基于 architecture 与 loops-optimizer 两个 agent 的 24 篇 PDF/HTML 与精读报告核对；未验证处标 `[待确认]`。
> 证据等级：A = 大规模受控 sweep + 留出拟合；B = 扎实但规模/模型族较窄；C = 理论/立场/再分析。
> 坐标约定：任何 law 必须同时记录 `(N_total, N_active, G 定义, S 定义, depth, width, D, fit_range, version)`；跨定义直接比较指数是无效的。

## 0. 这一轴的核心结论

1. **文献现在跑在两套不兼容的坐标系上**：MoE law 用 `(N_total, N_active, E/G, S, D)`，shape/μP 工作用 `(width, depth, aspect ratio)`。没有论文把两者整合成一个 fitted law。
2. **MoE 论文一致认为稀疏有益、存在内点最优，但对“最优专家数是否不变”有分歧**。分歧部分是定义问题：`G` 在 Krajewski 是粒度乘子（granularity multiplier），在 Zhao 是激活专家数（active-expert count），不是同一个量。
3. **μP 的“只适用于宽度”已经不是前沿**：CompleteP（NeurIPS 2025）和 2026 的 spectral condition 把 HP transfer 扩展到深度，并解释了 Transformer 为什么属于 `k ≥ 2`（CompleteP 分支）。
4. **所有定量 law 的拟合上限约在 9B total / 3B active 参数**；671B/1T 是 existence proof，不是 validated fit。
5. **最高价值的开放方向是 joint shape × sparsity law + 显式成本模型**（训练 FLOPs、显存、延迟），因为现有“最优形状”和“最优稀疏度”各自优化的是不同预算。

## 1. 时间线与谱系

| 时间 | 工作 | 攻击了什么假设 | 留下了什么新盲区 |
|---|---|---|---|
| 2020–2022 | Kaplan / Chinchilla | 参数数足以描述规模；`6ND` 不含架构变量 | 架构固定、所有参数都激活 |
| 2022-02 | Clark et al., Unified Scaling Laws for Routed LMs（2202.01169） | “参数 = 计算” | 固定 130B token 预算，大模型被欠训练 |
| 2022-02 | Yang et al., μTransfer（2203.03466） | 最优超参必须在目标规模重调 | 只覆盖宽度；深度/数据/正则未覆盖 |
| 2024-01 | DeepSeekMoE（2401.06066） | 专家必须是完整 FFN、所有专家都路由 | 无 scaling law；粒度/共享比例是设计选择 |
| 2024-02 | Krajewski et al., Fine-Grained MoE（2402.07871） | 架构是固定背景，只有 N/D 可 scaling | 只到 ~1B active、4–8 层；G 是粒度不是激活专家数 |
| 2024-05/12 | DeepSeek-V2 / V3 | 大 MoE 必须靠 aux balance loss；MoE 效率不需要压缩 KV | 技术报告不是受控 law；架构/数据/基础设施混杂 |
| 2025-02 | Ludziejewski et al., Joint MoE Scaling Laws（2502.05172） | FLOPs 是唯一预算 | ≤5B total；无粒度/共享比例；显存记账依赖硬件 |
| 2025-05 | Dey et al., CompleteP（2505.01618） | width-only μP 足够；深度可以靠 LayerNorm/init | ≤1.9B、20 TPP；dense only；理论是渐近的 |
| 2025-09 / EMNLP 2026 | Zhao et al., Comprehensive MoE Law（2509.23678） | dense law + 专家数项就够了 | ≤9B total；经典 top-k+aux loss；G 是激活专家数 |
| 2026 | Zheng et al., Spectral μP（2603.00541） | μP 必须按架构重新推导 | 实验仅 GPT-2 规模；softmax/MoE router 未完全覆盖 |
| 2026 | Liu & Gore, Universality（2606.25008） | 指数必须按模型族重新拟合 | 立场论文；未测试 MoE/MLA/long-context |

## 2. 深度/宽度/形状

### 2.1 Paper cards

#### μTransfer / Tensor Programs V（2203.03466，NeurIPS 2022 [待确认]）

- **设置**：Transformers 与 ResNets；从 13M 迁移到 350M BERT-large，从 40M 迁移到 6.7B GPT-3 风格模型。
- **贡献**：不是 loss law，而是坐标缩放规则——逐层 LR 与初始化方差随宽度缩放，使 hidden-feature updates 在无限宽极限下保持 Θ(1)。包含 “abc” 参数化与 attention-logit multiplier。
- **假设**：无限宽极限；宽度是唯一 scaling 轴；深度固定；正则超参不迁移。
- **证据**：A-。13M→350M 超过已发表 BERT-large，调参成本约等于一次 BERT-large 预训练；40M→6.7B 超过已发表 GPT-3，调参成本约 7%。
- **局限**：论文明确把深度、batch size、序列长度、训练时间留给未来；dropout/weight decay 不迁移；attention-logit multiplier 跨宽度有噪声；有限宽偏差仍在。
- **分析**：这是 HP transfer 范式的起点，盲区正是 CompleteP 三年后攻击的：width-only coordinate check 不保证深度迁移，也不保证非 lazy 学习。

#### CompleteP（2505.01618，NeurIPS 2025）

- **设置**：Pre-LN Transformers；深度 2–128 层；75M–1.9B 总参数，20 tokens/parameter；Cerebras CS-3；base `(N_base, L_base) = (256, 2)`。
- **Law/参数化**：一族 mean-field 参数化，深度指数 `β ∈ [0.5, 1]`；CompleteP 取 `β = 1`：残差分支乘 `m_L^{-1}`，hidden-layer LR 乘 `m_N^{-1} m_L^{-1}`，并修正 LayerNorm LR、bias LR、weight decay、AdamW ε。论文主张 `β = 1` 是唯一同时给出深度 HP transfer 与所有层完整（非 lazy）特征学习的选择。
- **假设**：渐近 width/depth mean-field；残差块；pre-LN；AdamW；“完整特征学习”是正确的目标。
- **证据**：A-。强消融；最优形状下比 μP 省 11.8% FLOPs，179 层模型省 34.4%（摘要给 12–34%）。
- **局限**：≤1.9B、20 TPP；dense only；理论渐近；最大 shape 测试（179 层）离生产深度很远；下游指标不是主要测量。
- **分析**：把 μP 从“保持训练稳定”重定义为“让每一层都留在 feature-learning regime”；这才使深度成为一等 scaling 轴。

#### Spectral Condition for μP under Width–Depth Scaling（2603.00541，preprint）

- **设置**：含 k 个变换的残差块；RMS operator norms；优化器特定映射（含 AdamW）；GPT-2 风格模型，OpenWebText，base `(n_base, L_base)=(256,4)`，宽度到 4096、深度到 256。
- **Law/结论**：Condition 3.1 是 joint width-depth scaling 下权重范数与每步更新范数的谱条件。核心是 `k=1` 与 `k≥2` 的 transition：`k=1` 允许较弱的 Depth-μP 式深度缩放；`k≥2` 强制更严格的 CompleteP 式缩放。Transformer 有多变换分支，属于 `k≥2`。`k=1` 分支的精确指数 [待确认]（PDF 提取丢失了根号）。
- **假设**：谱/次乘性界；残差块分解；简化多步非线性分析；渐近 regime。
- **证据**：B+。理论广、调和了此前分散的 μP 形式；实验受控但规模小。
- **局限**：实验远低于 foundation-model 规模；attention/softmax 与 MoE router 未完全进入理论；条件是充分不必要。
- **分析**：这是目前最好的解释：为什么 CompleteP 有效、为什么 Depth-μP（`k=1`）在 Transformer 上失败；把“选哪个 μP 变体”变成残差块结构问题。

#### Scaling Inference-Efficient Language Models（2501.18107，ICML 2025）

- **设置**：63 个 dense 模型，80M–1B 参数，1.6B–30B token；单卡 A100 40GB，batch 1，输入 128，输出 256；aspect ratio `R = d_model / n_layers`。
- **Law**：`L(N,D,R) = (E + A N^{-α} + B D^{-β})(1 + ε R^{γ})`。ε、γ 的具体值未在报告中提取 [待确认]。
- **假设**：aspect-ratio 惩罚可与 N/D 项分离；延迟只在一种硬件配置上测量；dense only。
- **证据**：B+。63 个模型；相对 Chinchilla，MSE 0.0033→0.0006，R² 0.9895→0.9982；Morph-1B 同精度下快 1.8×；同尺寸模型延迟可差 3.5×。
- **局限**：≤1B、dense；延迟依赖硬件/batch；预测 loss，下游精度可能分叉；shape 范围有限。
- **分析**：shape 不只是训练 FLOPs 变量，也是推理成本变量；“最优形状”是目标依赖的——宽而浅常更 latency-friendly，训练 FLOPs 最优形状可能更深。

#### Neural Scaling Universality（2606.25008，preprint position）

- **设置**：立场/再分析论文；拟合公开 Pythia/Chinchilla checkpoints，不训练新大模型。
- **Law/主张**：loss 分解为 time/data 项 `~t^{-1/3}`（等价于 one-epoch 的 `D^{-1/3}`）、inverse-width `~m^{-1}`、inverse-depth `~l^{-1}`，加饱和 floor。最优 aspect ratio 下得到 `N ~ C^{1/3}`、`L ~ C^{-1/6}`。
- **假设**：online one-epoch；Softmax 控制 1/3；superposition 控制 inverse width；层间 ensemble averaging 控制 inverse depth。
- **证据**：C+。对 Pythia/Chinchilla 的拟合支持，但不是新的受控 sweep；“固定指数”未在 MoE/MLA/long-context 上测试。
- **局限**：架构只通过系数进入是假设；step-limited vs data-limited 可能破坏 D 映射；无 MoE；最优 aspect ratio 推导依赖特定参数几何。
- **分析**：如果指数固定，实际工作是估系数与形状，而不是每换一个架构就重拟合指数。这个主张可证伪，应测试而非默认接受。

### 2.2 综合

- 深度和宽度不是独立的：残差缩放、初始化、LR 必须随二者联合调整。
- “给定参数量，形状怎么选”没有统一答案；它取决于训练 FLOPs、推理延迟、显存、优化器。
- μP 的价值是**迁移超参**，不是“发现最优形状”；它让中小规模实验更能预测大规模。
- CompleteP 的 `β=1` 与 Spectral μP 的 `k≥2` 是目前最可信的深度扩展解释，但都只在小规模验证。
- 形状轴与数据/优化器/稀疏度存在交互；单独报告“深度更好/宽度更好”很容易被混杂因素误导。

### 2.3 矛盾与空白

- **T4（μP 宽度 vs 深度）**：Yang 明确把深度留给未来；CompleteP 证明 `β=1` 同时给深度迁移与非 lazy 学习；Zheng 解释 `k=1` vs `k≥2` 的分裂。**结论**：残差块结构指定后没有矛盾；剩余缺口是理论渐近、实验规模小。
- **T5（最优形状）**：CompleteP 优化训练 FLOPs；2501 优化推理延迟；2606 用固定指数推导 aspect ratio。**结论**：目标函数不同，所谓矛盾主要是语义问题。**规则**：报告“最优 aspect ratio”必须同时说明预算（训练 FLOPs / 推理延迟 / 显存 / 成本）。
- **空白**：joint shape × sparsity law 不存在；μP/CompleteP 未覆盖 softmax attention、MLA/GQA、MoE router、dropout、weight decay；router HP 是否跨宽度/深度迁移未测试；loss→downstream 缺校准层。

## 3. MoE / 稀疏专家

### 3.1 坐标定义（先定坐标，再谈 law）

MoE 文献里最容易出错的是同名不同义：

- `N_total`：总参数（含所有专家）。
- `N_active` / `N_a`：每 token 激活参数。
- `E`：专家数（routed experts）。
- `G`：两种用法——
  - Krajewski：**粒度乘子**（granularity multiplier），改变专家大小与激活专家数；
  - Zhao：**激活专家数**（active-expert count，routed + shared）。
- `S`：两种用法——
  - Zhao：**共享专家比例**（shared-expert ratio）；
  - 2501.12370：**稀疏度**（inactive parameter fraction，`1-S` 是激活比例）。
- `top-k`：每 token 路由到几个专家。
- `capacity factor`、`aux loss`、`aux-loss-free balancing`：路由实现细节，会改变 loss 与显存。

**规则**：任何 MoE law 必须记录 `(N_total, N_active, G 定义, S 定义, top-k, D, fit_range, version)`；跨定义直接比较指数无效。

### 3.2 Paper cards

#### Unified Scaling Laws for Routed Language Models（2202.01169，ICML 2022 [待确认]）

- **设置**：S-BASE、RL-R、HASH 三种路由技术；五个数量级；最多数百专家、数千亿参数；每个模型固定 130B token、250k steps。
- **Law**：`log L(N,E) = a log N + b log E + c log N log E + d`（bilinear log-log，含乘性交互）。用 dense 等价 `L(N,1)=L(N)` 锚定；由 `L(N_eff,1)=L(N,E)` 定义 Effective Parameter Count。
- **假设**：固定数据预算；E 是独立轴；同一架构族/路由技术；dense 与 routed 共享 loss scale。
- **证据**：B+。规模 sweep 大，但固定 130B token 是严重混杂；留出 RMSLE 56–90e-4（依赖路由技术）。
- **局限**：没有 data-size 轴，大模型被欠训练，所以“expert benefit 随 N 缩小”的结论被混杂；无粒度/共享专家；只有三种路由。
- **分析**：最常被引用的结论也是最容易被推翻的。机制很可能是固定 token 预算：N 增大时模型越来越欠训练，制造出“routing 价值下降”的表象。

#### DeepSeekMoE（2401.06066，ICLR 2025 [待确认]）

- **设置**：2B、16B、145B。2B：1 shared + 63 routed，激活 7 routed，expert size 0.25× FFN；16B：2 shared + 64 routed，激活 6 routed，2.8B active / 16.4B total；145B：4 shared + 128 routed，激活 12 routed，expert size 0.125× FFN。
- **贡献**：无 law；细粒度专家分割 + 共享专家隔离。
- **假设**：更多更小的专家提高组合灵活性；共享专家吸收共性、降低路由专家冗余；top-k + aux balance loss。
- **证据**：B。2B 与 16B 受控比较：2B 匹配 GShard 2.9B（1.5× 专家参数与计算）；16B 匹配 LLaMA2 7B（约 40% 计算）；145B 结果初步。
- **局限**：无 scaling law；规模小；无 iso-FLOP frontier；路由开销/负载均衡敏感；共享比例是选择不是优化。
- **分析**：提供了后续 law 需要的两个结构变量——粒度与共享比例；也说明“MoE”不是一种架构，跨论文比较指数很危险。

#### Scaling Laws for Fine-Grained MoE（2402.07871，ICML 2024 [待确认]）

- **设置**：64 专家；非 embedding 总参数到 64×1B（约 1B active）；16B/33B/66B token（部分 130B）；粒度 `G ∈ {1,2,4,8,16}`；4–8 层 Transformer。
- **Law**：`L(N,D,G) = c + g/G^γ + a/N^α + b/D^β`。MoE 拟合：`a=18.1, α=0.115, b=30.8, β=0.147, g=2.1, γ=0.58, c=0.47`；dense 拟合：`α=0.126, β=0.127, c=0.47`；验证 RMSE 0.019，拟合 RMSE 0.015。
- **假设**：N、D、G 可加分离；无 N×G 交互（论文测试过）；routing FLOPs 可测并进入 compute 约束；深度固定。
- **证据**：A-。64 专家受控 sweep，带 bootstrap 不确定性与留出验证；弱点是规模与深度。
- **局限**：仅 4–8 层，深度-形状交互不可见；≤1B active；G 是粒度乘子，不是激活专家数；仅 64 专家、英文。
- **分析**：最早清晰证明粒度是 scaling 变量。`G_opt` 从 2.95e18 FLOPs 的 8 升到 1.93e20 FLOPs 的 16——这是后来与 Zhao 争议的经验锚点。

#### DeepSeek-V2（2405.04434，技术报告）

- **设置**：236B total / 21B active（8.9%）；每 MoE 层 2 shared + 160 routed，top-6 routed；expert hidden dim 1536；MLA；8.1T 预训练 token；128K context。
- **贡献**：无 law；架构与成本报告。
- **证据**：B。大规模 existence proof：训练成本比 DeepSeek 67B 低 42.5%，KV cache 降 93.3%，最大生成吞吐 5.76×，21B active 下质量居开源前列。
- **局限**：无 law；MLA 与 MoE 混杂；成本依赖集群/数据/实现；固定 compute 下无 G/S 消融。
- **分析**：证明 ~9% 激活比例在 236B total 可行；对“激活比例随 N 变稀疏”是数据点，不是检验。

#### DeepSeek-V3（2412.19437，技术报告）

- **设置**：671B total / 37B active（5.5%）；1 shared + 256 routed，top-8 routed；expert hidden dim 2048；14.8T token；auxiliary-loss-free 负载均衡；multi-token prediction (MTP)；2.788M H800 GPU-hours。
- **贡献**：无 law；架构/训练报告。
- **证据**：B+。异常详细的大规模报告，训练稳定（无不可恢复 loss spike/rollback），但单一模型族，无受控 law。
- **局限**：无 law；架构/优化器/数据/基础设施混杂；专有数据；5.5% 激活比例是设计选择，不是 fitted optimum。
- **分析**：当前最激进的稀疏度 existence proof；与 Zhao 的 `N_a/N` 趋势一致，但未识别因果指数。

#### Joint MoE Scaling Laws（2502.05172，venue [待确认]）

- **设置**：280+ 实验；≤2.7B active、5B total；dense 与 MoE；专家数大范围变化（拟合饱和参数 `E_max ≈ 290`）；数据量变化；1.1B 验证在匹配 compute/memory 下。
- **Law**：`L(N_act,D,Ê) = a Ê^δ N_act^{α+γ ln Ê} + b Ê^ω D^{β+ζ ln Ê} + c`，其中 Ê 是专家数的饱和单调变换（`E_start=2.0732, E_max=290.4521`）。拟合：`a=35.91, α=-0.1889, δ=-0.2285, γ=0.0098, b=35.98, β=-0.1775, ω=0.5529, ζ=-0.0259, c=1.3637`。
- **假设**：专家数影响系数与指数（对 ln Ê 线性）；Ê 饱和捕捉递减收益；显存可由 total params/架构建模；top-k routing。
- **证据**：A-。大 joint dense/MoE sweep + 显式显存模型 + 1.1B 匹配预算验证。
- **局限**：≤5B total；无粒度/共享比例；显存记账依赖硬件；无 depth/width shape 轴。
- **分析**：最能调和 Clark 与 Krajewski：expert 价值不是 N 的固定函数，而与 D 交互；论文观察到 MoE 收益随 token 增长，直接反驳 Clark 的固定数据解释。

#### Parameters vs FLOPs（2501.12370，abstract only）

- **设置**：预训练 + few-shot；稀疏 MoE；稀疏度 S = inactive parameter fraction；约束参数规模与训练 compute。未下载全文；经 arXiv abstract 与 Zhao Eq. 37 转述。
- **Law（Zhao 转述）**：`L(N,D,S) = a/N^α + b/D^β + c/(1-S)^γ + d/((1-S)^δ N^λ) + e`。第三项惩罚高稀疏，第四项耦合稀疏与模型规模；原始记号/指数 [待确认]。
- **假设**：固定参数或 compute 预算下存在内点最优稀疏度；惩罚单调，除 N 交互外可分离。
- **证据**：B（仅 abstract 级）。
- **局限**：全文未读；规模/拟合质量未知；S 是不同于 Zhao `N_a/N` 与 Krajewski `G` 的坐标。
- **分析**：把稀疏度当连续约束变量，而不是架构选择；是 MoE law 与 inference-cost 优化的天然桥梁。

#### Towards a Comprehensive Scaling Law of MoE（2509.23678，EMNLP 2026 Main）

- **设置**：腾讯混元；arXiv v1 446 个受控实验（EMNLP 版 450）；268 fitting、88 validation、90 small-size 用于 G 边际效应；验证到 9B total / 100B token。
- **Law**：`L(N,D,N_a,G,S) = (eG + f/G + mS^2 + nS)(1/N^α + k/N_a^α + h N_a/N) + a/N^α + b/D^β + c/N_a^α + ε`。拟合：`e=0.1577, f=7.2446, m=5.1395, n=-3.2363, k=0.0013, h=0.0450, a=38.0510, α=0.2383, b=27129.0488, β=0.4694, c=31.0958, ε=1.8182`。推出 `G_opt = sqrt(f/e) ≈ 6.78`、`S_opt = -n/(2m) ≈ 0.31`、`(N_a/N)_opt ~ N^{-α/(1+α)} ≈ N^{-0.19}`。
- **假设**：经典 top-k + aux balance loss；五因子可分离；G/S 非单调（二次/极点）；attention 层不与 MoE 因子交互。
- **证据**：A-。当前最大的受控 MoE 因子 sweep，带留出验证与 EMNLP 2026 main 记录；446 vs 450 是版本差异。
- **局限**：≤9B total；仅经典 MoE；attention/训练目标交互不在范围；工业模型（Kimi-K2、gpt-oss-120b）的实际激活比例低于推荐范围（`N_a/N ≤ 4%`），说明“最优”不是普适的；G 是激活专家数，不是 Krajewski 的粒度。
- **分析**：目前最完整的 MoE law，给出可证伪不变量（G_opt、S_opt、activation-ratio slope）；弱点正是 foundation-model 研究者最需要的 9B→1T 外推未验证。

### 3.3 矛盾与综合

- **T1：expert benefit 是否随模型变大而下降？**
  - Clark：`b(N)` 随 N 变大而 less negative，结论 routing 收益缩小。
  - Krajewski：MoE 总是更高效，与规模无关。
  - Joint：专家收益随训练 token 增长。
  - **分析**：不是同一量的三个估计。Clark 固定 130B token，大模型被欠训练，额外参数（无论 routed 还是 dense）价值被机械压低。**最可能的解释**：Clark 是固定数据伪影，不是 routing 的普遍 law。**能解决**：`(N,E,D)` 三维 sweep，保持 token/param 大致恒定，拟合含/不含 E×D 交互。
- **T2：最优专家数是不变 ~6.8，还是随 compute 增长？**
  - Zhao：`G_opt ≈ 6.78`，与 N/N_a/D 无关（G=激活专家数）。
  - Krajewski：最优粒度 8（2.95e18 FLOPs）→16（1.93e20 FLOPs）（G=粒度乘子）。
  - **分析**：两个 G 是不同对象；可以同时成立：激活专家数有 ~7–9 的内点最优，而专家尺寸随 compute 缩小（粒度上升）。**能解决**：固定 active params/tokens，做 `(G_active, d_expert)` 二维 sweep，law 分离两者。
- **T3：最优共享专家比例 ~0.31？**
  - Zhao：`S_opt ≈ 0.31`，loss surface 在附近很平。
  - 实际部署更低：DeepSeekMoE 16B `S=2/(2+6)=0.25`；V2 `0.25`；V3 `1/(1+8)=0.11`；Kimi-K2/gpt-oss-120b `N_a/N ≤ 4%`。
  - **分析**：平坦 ridge + 推理成本把部署推向低 S/低激活侧。**能解决**：`(S, N_a/N, inference budget)` 联合优化，而不是 loss-only fit。
- **T4：MoE 是省显存还是吃显存？**
  - 常识：所有专家都要存，MoE 吃显存。
  - Joint：匹配 loss/training budget 时，MoE 可能比 dense 更省显存，因为 dense 需要更多 active params 才能达到同 loss。
  - **分析**：只在特定显存记账（weights、optimizer state、activations、communication）下成立；all-to-all/专家并行可能反转。**能解决**：硬件显式成本模型 + 至少两种集群配置。
- **T7：指数不可跨论文比较。**
  - Krajewski：`α=0.115`（total）、`β=0.147`；Joint：`α=-0.1889`（active）、`β=-0.1775`（含交互）；Zhao：`α=0.2383`、`β=0.4694`（五因子）。
  - **分析**：N 的含义、D 范围、E 是否进入指数、固定了什么，全都不同；平均这些指数没有意义。**规则**：每个指数必须带坐标定义与拟合范围。
- **T8：版本漂移。**
  - Zhao arXiv v1 446 实验，EMNLP 2026 450；系数引用自 arXiv v1。结论不变，但缓存数字必须 pin version。

### 3.4 开放问题（MoE）

1. **没有 joint shape × sparsity law**：CompleteP/2501 管 dense 的 width/depth；Krajewski/Joint/Zhao 管固定 shape 的 sparsity；foundation model 同时选二者，交互未测。**这是本轴最大的结构空白。**
2. **规模天花板**：Zhao 到 9B total/100B token；Joint 到 5B total/2.7B active；Krajewski 到 ~64B total 但 ~1B active、4–8 层；没有论文在 >10B active 上拟合 law。671B/1T 是 existence proof。
3. **定义漂移**：N 可指 total/active/non-embedding；G 可指粒度/激活专家数；S 可指共享比例/稀疏度。跨论文数值比较必须先统一 schema。
4. **固定数据混杂**：Clark 的 130B token 最典型；data exponent 是 MoE law 里最不稳定的参数。
5. **μP/CompleteP 覆盖不足**：softmax attention、MLA/GQA、MoE router、dropout、weight decay 未完全覆盖；router HP 跨宽度/深度迁移未测。
6. **路由算法缺席**：top-k、expert-choice、aux-loss-free、sequence-level routing 会改变 loss/显存；所有 reviewed law 都假设 top-k + aux loss，而 DeepSeek-V3 的主要创新正是去掉 aux loss。
7. **显存/通信硬件依赖**：“memory-efficient MoE”取决于显存指什么（weights/optimizer/activations/KV/interconnect）；没有可移植成本模型。
8. **loss→downstream 缺口**：2501 显示同 loss 模型下游精度可分叉；MoE law 只预测 loss。
9. **数据质量/混合未表示**：所有 law 用固定 corpus 或窄 corpus；系数随数据分布变化，“不可约”项并非跨数据集不可约。
10. **非单调因子外推危险**：Zhao 的 G/S 项是二次/极点，Krajewski 的粒度项是正系数幂律；拟合范围外，小系数误差会翻转最优预测。

## 3.5 循环 / 递归深度

> 来源：loops-optimizer agent 报告；12 篇 PDF/HTML 核对。

### 3.5.1 定义与坐标

- `L_unique`：唯一层数；`r`：训练时循环次数；`r_bwd`：BPTT 回传深度；`T_infer`：推理时循环次数。
- `prelude → shared recurrent block → coda`：Huginn 式结构；输入注入与 recurrent state 组织是设计轴。
- `φ`：recurrence-equivalence exponent。`r` 次循环约等于 `r^φ` 个唯一块；φ<1 表示 loop 的边际收益低于唯一层。
- **匹配口径**：P-match（参数）、F-match（FLOPs）、KV-match（KV cache）、W-match（wall-clock）。不同论文用不同口径，结论不可直接比较。

### 3.5.2 Paper cards

#### Universal Transformers（arXiv:1807.03819，ICLR 2019）

- 设置：weight-tied self-attention 递归应用；per-position ACT halting；WMT14 En-De、LAMBADA、算法任务。
- 结论：递归带来 fixed-depth Transformer 没有的长度泛化；WMT14 +0.9 BLEU。
- 证据：Medium；pre-LLM、小规模；halting 收益 task-dependent。
- 局限：无 compute-matched 对比；无 scaling law；未在 >1B 复现。

#### Looped Transformers as Programmable Computers（arXiv:2301.13196）

- 设置：构造性证明；13 层 looped encoder 模拟 calculator、线性代数库、in-context 梯度下降。
- 结论：表达性上界；“loop = 串行算法”。
- 证据：High as theory, low as practice；构造不可由 SGD 直接学习；不说明 loss-vs-compute。
- 局限：常被过度引用为“loop 在 scale 上一定有用”。

#### Huginn（arXiv:2502.05171，2025-02）

- 设置：3.5B、800B token、47k steps；prelude → recurrent block → coda；每步输入注入；truncated BPTT + 随机深度（Poisson）；测试 r∈{1,4,8,16,32,64}。
- 结论：loss 随 test-time recurrence 单调改善；r=32 时 FLOP-equivalent 约 50B dense；Table 1 r=32：ARC 69.91、HellaSwag 65.21、MMLU 38.80。
- 证据：Medium；单 seed；LR 从未 decay（作者自述）；无非 recurrent baseline 在 >180B token 的 matched-FLOP 对比。
- 局限：“50B-equivalent”是 FLOP-budget 比较，不是 matched-loss；无 scaling law。

#### Ouro（arXiv:2510.25741，2025-10）

- 设置：LoopLM，所有层 weight-tied，T_max=4；per-step exit gate + entropy regularization；1.4B/2.6B；7.7T token。
- Law：`L_t = E + A/(N+t1)^α + B/(D+t2)^β + C/(T_max+t3)^γ`，R²=0.9596；拟合规模 53M–1.36B、r∈{1,2,4,8}、20B token；指数未从提取文本恢复 [待确认]。
- 证据：Medium；大 token budget + 诚实附录；law 未外推到 7.7T run。
- **内部矛盾**：正文称 1.4B/2.6B “match up to 12B SOTA”；Appendix D 说 matched size/step 下标准 untied 模型在**每个 r** 都赢，gap 随 r 增大、随模型增大缩小。两者可同时为真（12B 比较不是 compute-matched），但 headline 会误导。

#### Iso-Depth（arXiv:2604.21106，NeurIPS 2026 Spotlight）

- 设置：固定 effective depth（因此 FLOPs/KV 固定），变 unique params；r∈{1,2,4,8}；116 runs、~50× compute、六个 budget 到 2.15e19 FLOPs；FineWeb-Edu、Llama-2 tokenizer、2049-token；MuonH（LR 0.014）+ AdamW。
- Law：`L = E + A(N_once + r^φ N_rec)^-α + B D^-β`；**φ=0.46，95% CI [0.41,0.53]**；α=0.199、β=0.369、E=1.57；R²=0.9972。限制拟合：φ=0 → E 1.71, R²=0.9858；φ=1 → E 1.66, R²=0.9552。
- 解释：每次 recurrence 约等于 `r^0.46` 个唯一块：r=4 时 1.9×，r=8 时 2.6×，而 FLOP 成本线性。r=4 时 410M looped 匹配 580M non-looped，但训练成本相当于 1B non-looped。compute-optimal allocation 随 r 向宽度移动（N ∝ C^0.57 at r=1 → C^0.76 at r=4；D ∝ C^0.53 → C^0.37）。
- 证据：High；bootstrap CI 排除 0 和 1；low/high-budget refit φ=0.44/0.49；20× 外推检查 0.061 nats。
- 局限：unique params 仅 ~40M–1B；所有 run 用 MuonH → φ 可能 optimizer-dependent；iso-depth 固定 test-time depth，看不到 inference-time compute 收益。
- **关键**：φ 是 recipe-dependent：truncated BPTT 降到 **0.38**（即使 val loss 下降），hyperconnections 升到 **0.65**。

#### Parcae（arXiv:2604.12946，2026-04）

- 设置：middle-looped + 稳定性修复（negative-diagonal parameterization 约束 injection 谱范数）；140M/370M/1.3B；RDM(Huginn) 与 nanochat-Transformer。
- Law：训练上 looping 是 orthogonal FLOP axis；固定 unique params 时 compute-optimal **rec ∝ C^0.40**、**D ∝ C^0.78**；拟合 `L(rec,D)=E+X N(rec)^-x + Y D^-y`，N(rec) 是 unrolled 参数；外推误差 1.3%/0.8%。
- 证据：Medium-high；1.3B、+2.99 CORE / +1.18 CORE-Ext；87.5% of 2× model quality。
- 局限：**参数/数据匹配，不是 FLOP 匹配**——depth、inference FLOPs、KV 都随 r 增长；SMELT 指出该拟合无法分离 per-parameter sharing cost 与 growing budgets；87.5% 也承认 looped 1.3B 仍差于 2.6B dense。

#### SMELT（arXiv:2609.01343，2026-09）

- 设置：MoE transformer，middle half layers 循环两次；同时匹配 per-token FLOPs、non-embed params、KV cache；四个尺寸到 54B non-embed、S≈97%。
- Law：baseline `E=1.4439, a=0.3703, c=0.6594`；SMELT `E=1.4493, a=0.3892, c=0.7011`；frontier exponent `α=ac/(a+c)`：0.237→0.250（+5.5%）；**节省 6.8–18.0% training FLOPs**（C=10^21 时 14.7%）。
- 证据：High；54B、四个尺寸、四个 sparsity、downstream gains 超过 val-loss 预测；机制故事（第二次 visit 减少 attention sink）。
- 局限：只测 r=2；单一架构族；优势在 Code 最大、随序列长度/in-context 例子增长——task-dependent，单指数对可能不跨数据 mixture 迁移。

#### DeepLoop（arXiv:2607.13491，2026-07）

- 设置：Post-LN DeepNorm looped transformer，GPT-2 small/medium；一阶 perturbation bound + visit-alignment coefficient κ_R。
- 结果：stability condition `κ_R·M·(β/α)² = O(1)`；DeepNorm 阈值 p=1/4 在 visits decorrelate 时恢复；aligned regime 下 p 从 1/4 升到 1/2；DeepLoop 设 `α=(2N)^{1/2}, β=(8N)^{-1/2}`。
- 证据：Medium；理论干净、无参数规则；仅 GPT-2 small/medium；无 loss scaling law。
- 局限：κ_R 未直接测；1/2 是保守上界，不是拟合值。

#### Loopie（arXiv:2607.16051，2026-07）

- 设置：两个 MoE looped：20B total/2B active、6B/0.6B active；两个 loop step；Qwen3-MoE 30B-A3B baseline 800B token；4-rung scaling ladder + wall-clock-matched baselines。
- 结论：Loopie-20B-A2B 早期落后，**~600B token 后超过 30B-A3B**，之后保持领先；ladder 上 +0.6–2.2 points。
- 证据：Medium；最大公开 looped 模型（20B）+ 真 compute-matched baseline；单一 recipe；crossover 无模型解释。
- 局限：600B crossover 意味着 ≤300B 的 ablation（literature 常态）会得出相反结论；wall-clock matching 混淆 FLOPs/memory bandwidth/communication。

#### Towards Looped Models Done Right（arXiv:2610.23036，2026-10）

- 设置：730M、336B token 受控消融；转移到 MoE 8B-A0.8B（unrolled 32B-A3B）、500B token；隔离 iteration envelope、input injection、recurrent-state organization。
- 结论：完整 Huginn 架构在十个 benchmark 上全胜 Ouro；Huginn-over-Ouro 优势转移到 MoE；matched train+inference FLOPs 下 Huginn 风格比 112 层 feedforward MoE 少 **75% resident params**，并在 DROP/GSM8K 上胜、MATH500 持平。
- 证据：Medium-high for design, low for scaling；干净消融、两个 scale、dense→MoE；无 scaling law、每格单 seed。
- 局限：“Huginn > Ouro” 是比较完整 recipe，无法隔离三轴中哪个贡献；random init/separate H-L states 结果混合/负面。

### 3.5.3 循环轴矛盾

- **“loop 行不行”是定义问题**：

| 论文 | 固定什么 | 结论 |
|---|---|---|
| Iso-Depth | per-token FLOPs + effective depth（因此 KV） | loop 输（φ=0.46；+0.03–0.12 nats） |
| Parcae | unique params + data（FLOPs 随 r 增长） | loop 赢（+2.99 CORE） |
| SMELT | per-token FLOPs + non-embed params + KV | loop 赢（6.8–18% FLOP saving） |
| Loopie | wall-clock per step | ~600B token 后 loop 赢 |

这些不是同一个实验。Iso-Depth 固定最多、因果证据最强；Parcae 固定最少、因果证据最弱；SMELT 同时匹配三个 deployment 约束，是最有说服力的正结果。
- **φ 是 recipe 属性，不是架构属性**：0.38（truncated BPTT）/ 0.46（baseline）/ 0.65（hyperconnections）。同一架构可以看起来“loop 几乎没用”或“loop 有 65% 唯一参数价值”，取决于训练方式。
- **Parcae vs Iso-Depth**：Parcae 参数饥饿（loop 是唯一不增加内存的 FLOP 花费方式）；Iso-Depth FLOP 受限（loop 浪费 FLOP 在共享权重）。统一 law 需要同时有 parameter axis 与 effective-depth axis，两者都没有。
- **Ouro 自相矛盾**：正文 headline vs Appendix D；不要把“matches 12B”当数据点。
- **crossover 未建模**：Loopie 只给一个点（~600B）；没有 law 预测 crossover 随 scale 的位置。
- **weight decay 未建模**：Moonlight 显示 WD 是 Muon 稳定关键；Parcae/DeepLoop 的稳定性修复与 WD 功能竞争；φ 可能依赖 WD。
- **BPTT 截断是隐藏下界**：r_bwd=r/2 使 φ 降 ~0.08；大多数 loop 结果是 full BPTT 的下界，跨 r_bwd 比较无效。

### 3.5.4 循环轴方向种子

1. **φ(N, optimizer, r_bwd)**：3×3×2 网格，N∈{0.2B,0.7B,2B} × optimizer∈{AdamW,Muon,MuonH} × BPTT∈{full,r/2}；预测 φ_Muon−φ_AdamW>0.10 且 ∂φ/∂logN>0；约 54 runs。
2. **Joint train/test law**：`L(N_u, r_train, D, T_infer)=E+A(N_once+r_train^φN_rec)^-α + B D^-β + C exp(-T_infer/τ(r_train))`；交叉 r_train∈{1,2,4}、T_infer∈{1..16}；检验交互项。
3. **Crossover law**：`D*(r,s)` = looped 模型首次超过 wall-clock-matched dense/MoE 的 token 数；四个 rung（0.15B/0.5B/2B/8B）；Loopie 只给一个点。
4. **WD vs spectral-norm constraints**：λ∈{0.1,1.0} × injection parameterization∈{unconstrained, Parcae negative-diagonal}；测 φ 每格；检验冗余 vs 互补。
5. **Depth-allocation law**：Ouro 式 exit gate 的 p(t|x) 随 N∈{0.1B..2B}、D∈{20B..1T} 的分布；拟合 `T̄=a(D/N)^b`；b≈0 则是 routing trick，b>0 则是第三轴。

## 4. 创新动作（来自本轴文献）

1. **Active/total decomposition**：Clark、Joint、Zhao 都把 total 与 active 参数分开；这是 MoE 文献最重要的坐标变化，让“模型大小”变成二维对象。
2. **Granularity as a continuous variable**：Krajewski 的 G 把专家大小变成可 scaling 超参。
3. **Shared-expert ratio as an explicit factor**：Zhao 的 S 与 DeepSeekMoE 的 shared experts 把设计启发式变成可拟合变量。
4. **Multiplicative interaction terms**：Clark 的 `log N log E`、Joint 的 exponent-linear-in-`ln Ê`、Zhao 的 `(eG+f/G+mS²+nS)` 都编码“架构改变斜率，不只是截距”。
5. **Spectral/operator-norm analysis**：Zheng 用 RMS operator norms 替代逐坐标 μP 检查，统一宽度-深度与优化器配方。
6. **“Complete feature learning” as a desideratum**：CompleteP 把目标从“HP 可迁移”升级为“每层都非 lazy”。
7. **Aspect-ratio penalty factor**：2501 的 `(1+εR^γ)` 是把 shape 加进现有 law 的简单模板。
8. **Fixed exponents, fitted coefficients**：Liu & Gore 反转流程；即使只部分成立，也能减少自由参数。
9. **Auxiliary-loss-free balancing + MTP**：DeepSeek-V3 证明大 MoE 可以不用 aux balance loss 稳定训练，改变所有假设 aux loss 的 law。
10. **Memory-constrained optimization**：Joint 用 joint compute/memory 约束替代 FLOP-only，改变最优专家数；是 inference-aware scaling 的模板。

## 5. 方向种子（来自本轴报告）

### Seed 1：粒度不变的 MoE law，调和 `G_opt≈6.8` 与粒度上升

- **假设**：把 `G_active` 与 `d_expert` 分开后，`G_active,opt` 约在 7–9 不变，而 `d_expert,opt` 随 compute 缩小。
- **设计**：3 个 active 规模（0.5B/2B/8B），`G_active ∈ {2,4,8,16}`，`d_expert ∈ {0.25,0.5,1.0}×FFN`，token 匹配 20–100 TPP；拟合含/不含交互项，留出最大规模。
- **Falsifier**：8B active 时 `G_active,opt` 漂移超过 2×（偏离 7），或交互项不改善留出误差。
- **顶会理由**：用干净二维实验解决一个活跃矛盾，并给出 1T-scale MoE 设计规则。

### Seed 2：稀疏度是否改变最优 width/depth 比？

- **假设**：固定 active 参数与训练 FLOPs 时，MoE 偏好更深更瘦的形状；最优 aspect ratio 是稀疏度的函数。
- **设计**：dense vs MoE，1B active；`R ∈ {32,64,128,256,512}`；D 20B–100B；拟合 `L=(E+A N^-α+B D^-β)(1+εR^γ)(1+δ·sparsity·R)`；同时测 loss 与推理延迟。
- **Falsifier**：`γ_MoE≈γ_dense` 且交互项不显著。
- **顶会理由**：首次直接桥接 shape 文献（CompleteP、2501）与 MoE 文献（Krajewski、Zhao）。

### Seed 3：Router-specific μP

- **假设**：标准 μP/CompleteP 不能迁移 router temperature、aux-loss 系数、expert LR；top-k softmax routing 引入宽度依赖的梯度尺度。
- **设计**：GPT-2 风格 MoE，宽度 256–4096、深度 4–64、8–64 专家；网格搜索 router temperature 与 aux-loss 系数；测 HP 漂移与同 token loss；从 2603.00541 的谱条件推导 router coordinate check。
- **Falsifier**：最优 router HP 在 baseline μP/CompleteP 下漂移低于噪声。
- **顶会理由**：MoE router 的 μP 是开放的理论+实践问题；正结果会是首个有原则的 sparse HP transfer 配方。

### Seed 4：显存/推理约束下的激活比例 law

- **假设**：最优 `N_a/N` 是 total N、TPP、每卡显存的函数，而不只是 N；1T total + inference-heavy 时最优可能低于 3%。
- **设计**：0.5B–9B total，`N_a/N ∈ {4%,8%,12%,25%}`，D 20B–100B；加 serving 成本模型（延迟/显存/吞吐）；30B 验证，预测 1T 配置；与 DeepSeek-V3、Kimi-K2、gpt-oss-120b 对照。
- **Falsifier**：memory/latency-aware 最优与 loss-only 最优在拟合范围内统计不可分。
- **顶会理由**：统一 Zhao（loss）、2501.12370（sparsity）、Joint（memory）成一个可执行 law，并对下一代 frontier MoE 做出可证伪预测。

### Seed 5：指数普适性的压力测试

- **假设**：Liu & Gore 的固定指数普适类在 MoE/MLA/long-context 上不成立；至少一个架构族的 width/depth 指数偏离 -1 超过系数拟合不确定性。
- **设计**：用统一协议再分析公开 checkpoint（Pythia、OLMo、DeepSeek-V2/V3、Qwen）；拟合 `L=c_t t^{-1/3}+c_w m^{-1}+c_d l^{-1}+floor` 与自由指数版本；在最大模型上比较留出预测。
- **Falsifier**：所有族的自由指数都在 `(-1/3,-1,-1)` 置信区间内。
- **顶会理由**：直接高杠杆检验 2026 立场论文；两种结果都会改变领域拟合方式。

## 6. 阅读阶梯

- **Level 0**：Chinchilla（2203.15556）+ Fine-Grained MoE（2402.07871）+ CompleteP（2505.01618）+ Zhao（2509.23678）。
- **Level 1**：μTransfer（2203.03466）、Spectral μP（2603.00541）、Unified Routed Scaling（2202.01169）、Joint MoE（2502.05172）、DeepSeekMoE（2401.06066）。
- **Level 2**：DeepSeek-V2/V3（2405.04434 / 2412.19437）、2501.18107、2606.25008、2501.12370（abstract）。
- **Level 3**：按 `failures-and-tensions.md` 的 T1–T8 回查原文。

## 7. 来源

见本目录 `canonical-papers.md` 的 architecture/MoE 条目；所有数字以原文为准，`[待确认]` 在增量更新时核对。主要来源：

- 2203.03466, 2505.01618, 2603.00541, 2202.01169, 2402.07871, 2502.05172
- 2401.06066, 2405.04434, 2412.19437, 2509.23678, 2501.18107, 2606.25008
- 2501.12370（abstract only）
