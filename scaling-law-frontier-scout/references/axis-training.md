# 训练轴：数据、优化器/配方、推理最优与过训练

> last_updated: 2026-11-15
> status: 已基于 foundations-data 与 loops-optimizer 两个 agent 的精读报告与 24 篇下载 PDF/HTML 核对；未验证处标 `[待确认]`。
> 证据等级：High = 多估计器或复现的受控 sweep；Medium-high = 一个大受控 sweep + 留出验证；Medium = 单实验室/中等规模/观察性；Low-medium = 理论 + 有限验证。
> 坐标约定：任何 law 必须记录 `(N, D, unique data U, epochs E, repetition, mixture, quality, optimizer, LR schedule, inference demand, fit_range)`；跨定义直接比较指数无效。

## 0. 这一轴的核心结论

1. **“Chinchilla 20 tokens/param” 是弱识别 policy，不是常数。** Chinchilla 三种估计器给出 0.50/0.50、0.49/0.51、0.46/0.54；Besiroglu 复现发现四舍五入参数隐含约 **70** tokens/param，而重拟合隐含约 **20**；Kricheli 2026 解释：共线 `D=kN` 设计使指数近似不可识别。
2. **数据 scaling 已经是四轴问题**：quantity（unique tokens）、repetition（epochs）、mixture（domain proportions）、quality（filtering）相互作用；2026 的 law 在 prescription 上互相矛盾。
3. **推理会把 overtraining 变成最优——但取决于成本模型。** FLOP-only 分析奖励小模型 + 多 token；内存带宽/延迟（Kinetics）和后训练退化（catastrophic overtraining）可以反转排序。
4. **前沿从“拟合 law”转向“审计 law”**：TPP-coverage 理论、复现审计、rank-reversal、prescriptive refit 是 2025–2026 最有创新的工作。
5. **前端证据仍是观察性的**：LLaMA 3、Gemma 2/3 是 intentional overtraining 的 existence proof，不是受控 allocation 实验；大多数拟合 law 停在 <10B 参数。

## 1. 坐标与定义

- `N`：参数量（dense）或激活参数量（MoE）。
- `D`：训练 token 数；`U`：unique tokens；`E`：epochs；重复次数 `R = D/U`。
- `TPP`：tokens per parameter（`D/N`）。
- `mixture`：domain 比例；`quality`：过滤/去重策略。
- `optimizer`：AdamW / Muon / MuonH 等；`LR schedule`：cosine / WSD / constant。
- `inference demand`：推理 token 数、采样数、latency SLO。
- `cost model`：FLOPs-only / FLOPs+memory / FLOPs+latency / wall-clock。

**规则**：报告 exponent 时必须同时报告上述坐标与拟合范围；否则数字不可复用。

## 2. 时间线与谱系

| 时间 | 工作 | 攻击了什么假设 | 新盲区 |
|---|---|---|---|
| 2020 | Kaplan | 架构/超参主导 → N/D/C 幂律 | 数据 unique/无限；early-stopping 记账 |
| 2022 | Chinchilla | 模型优先 → N/D 约等比例 | 参数四舍五入；无 inference/repetition |
| 2022–2023 | BNSL | 单一幂律 → 平滑 broken law | 描述性，无 allocation policy |
| 2023 | Data-Constrained | 数据无限/unique → repetition/effective data | C4、≤9B；2026 重拟合反转部分建议 |
| 2024 | Data Mixing / RegMix | mixture 是启发式 → 可拟合/可回归 | 小规模；无 quality/repetition |
| 2024 | Data Filtering | filtering 与 compute 无关 → quality-quantity tradeoff | VLM only；35 epoch crossover |
| 2024 | Beyond Chinchilla | 只看训练成本 → 加入 inference | 无 repetition/memory/latency |
| 2024–2025 | Inference scaling | test-time 是独立工程问题 → 与训练联合优化 | task/verifier-specific；FLOP-only |
| 2025–2026 | Overtraining | Chinchilla ratio 最优 → overtraining 是一等 regime | post-training 可反向；成本模型依赖 |
| 2026 | Meta-critique | fitted law 可迁移 → 先审计设计/可识别性 | 没有共识 law/报告标准 |

**一条线**：每一代增加一根轴或一个成本项，然后发现上一代建议**条件于它冻结的那根轴**。当前前沿第一次把**实验设计本身**作为研究对象。

## 3. 数据 scaling

### 3.1 Paper cards

#### Muennighoff et al. 2023, Scaling Data-Constrained LMs（arXiv:2305.16264，NeurIPS 2023）

- **设置**：400+ runs，10M–9B 参数，最多 900B token、1,500 epochs；English C4；受控 repetition/compute sweep。
- **Law**：扩展 Chinchilla 的 effective data/parameters：
  `L = E + A/N'^α + B/D'^β`，
  `D' = U_D + U_D R_D* (1 - e^{-R_D/R_D*})`，`R_D = D/U_D - 1`；`N'` 对称定义。
- **结论**：约 4 epochs 内近乎 loss-neutral；超过后重复 token 价值衰减趋零。
- **假设**：重复 token 价值指数衰减；unique corpus 固定；架构/超参固定。
- **证据**：High（4-epoch regime）。
- **局限**：≤9B；`R_D*` corpus-specific；effective-parameter 项可能吸收 baseline misspecification（Lovelace 2026）；code augmentation 另加 ~2× 但混杂。

#### Ye et al. 2024, Data Mixing Laws（arXiv:2403.16952，ICLR 2025）

- **设置**：RedPajama 七域；24 个 mixture、70M/160M 模型拟合；8 个 unseen mixture 验证；外推到 1B/100B。
- **Law**：`L_i = c_i + k_i exp(linear function of mixture vector)`；M1 变体 `2M+1` 系数；验证 MAE 约 **0.005–0.031**；与 step/model-size law 嵌套；优化 mixture 匹配默认 mixture 多训练 **48% steps** 的效果。
- **假设**：mixture 效应平滑指数；domain loss 可组合；数据顺序固定；小模型 ranking 可迁移。
- **证据**：Medium-high。
- **局限**：3–7 域；仅 1B/100B；无 quality/repetition；跨域交互脆弱；平均 loss ≠ downstream accuracy。

#### Liu et al. 2024, RegMix（arXiv:2407.01492，ICLR 2025）

- **设置**：512 个 1M 参数模型、1B token；回归 surrogate 预测 unseen mixture；1B 模型 25B token（1,000× 大、25× 长）；验证到 7B/100B；64 个候选 1B mixture。
- **结论**：最佳预测 mixture 在 64 个候选 1B 模型中胜出；匹配或超过 DoReMi，用约 **10%** 其 compute。
- **假设**：小模型 mixture ranking 可迁移；downstream metric 可预测到足以排序。
- **证据**：Medium-high。
- **局限**：1M proxy 保真度是弱环；downstream 噪声；web corpus 与 downstream 最相关的结论可能是小规模/困惑度 artifact；无 repetition/quality。

#### Goyal et al. 2024, Scaling Laws for Data Filtering（arXiv:2404.07177）

- **设置**：DataComp 视觉-语言，对比训练，batch 4096；quality buckets A–F；per-pool scaling + repetition decay。
- **结论**：quality–quantity tradeoff（QQT）；超过约 **35 epochs**，完全未筛选数据击败 LAION 式 top-10% 高质量子集。
- **证据**：Medium（VLM/对比学习）。
- **局限**：不是 LLM 预训练；batch-size 敏感；pool-size transfer 未验证；35-epoch crossover 是 VLM 结果。

#### Lovelace et al. 2026, Prescriptive Scaling Laws for Data Constrained Training（arXiv:2605.01640，COLM 2026）

- **设置**：重拟合 data-constrained regime，加 additive overfitting penalty；weight decay case study。
- **结论**：超过某点，继续重复是反生产的，compute 应转向**模型容量**（更大模型、更少 epochs）；强 weight decay（λ=1.0）把 overfitting 系数降低约 **70%**。
- **假设**：overfitting 可分离成一个系数；Muennighoff 的 effective-parameter 项吸收了 baseline misspecification [待确认：二手总结]。
- **证据**：Medium（refit + case study，非新的大规模 sweep）。
- **局限**：新、未独立复现；规模有限；直接反驳 Muennighoff 的建议；“反转”可能依赖 specification。

#### Liu et al. 2026, InfoLaw（arXiv:2605.02364，ICML 2026）

- **设置**：预训练数据在 scale、quality distribution、repetition 上变化；拟合 252M–1.2B [待确认]；验证到 7B/425B；报告 3.7T dedup tokens、六个 quality buckets [待确认]。
- **Law**：把预训练建模为 information accumulation；quality 控制 information density；repetition 造成 scale-dependent diminishing returns；从 tokens/model size/mixture weights/repetition 预测 loss。
- **结论**：unseen recipes 与更大 run 上平均绝对 loss 误差 **0.15%**、最大 **0.96%**。
- **证据**：Medium-high。
- **局限**：最大 7B；粗 quality buckets；函数形式复杂；3.7T/六桶来自二手；无 post-training/inference。

#### Sedova et al. 2026, Scaling Laws for Mixture Pretraining Under Data Constraints（arXiv:2605.12715）

- **设置**：>2,000 runs，覆盖模型大小、target-data 大小、数据类型（多语言/领域/质量过滤 mixture）。
- **结论**：repetition-aware mixture law；target token 重复价值衰减，generic data 起正则作用；稀缺 target corpus 可重复 **15–20 次**；最优依赖 target size/compute/model scale。
- **证据**：Medium。
- **局限**：无 frontier 验证；target-fraction 设计可能约束 law；15–20 是 regime estimate，不是普适常数。

### 3.2 数据轴的四个交互

- quantity × repetition（Muennighoff；Lovelace）
- repetition × mixture（Sedova）
- quality × mixture（InfoLaw；Goyal）
- quality × quantity（Goyal QQT）

**结论**：四轴不是可加的。冻结三轴、拟合第四轴的 law 只在自己的切片有效，不能预测 cross-term。2026 的论文看起来像“特例塔”，因为每篇加一个变量，但系数是局部于 corpus/scale/filter pipeline 的。

最有复用价值的不是数值指数，而是：
- **effective-variable construction**（用 D' 替代 D，N' 替代 N）；
- **nested-law composition**（mixture law × step law × size law）。

两者是外推工程装置，不是机制主张。数据 pruning/selection 是最不“law-like”的区域：2024–2026 多为方法 + compute-saving claim（PreSelect、ADO、perplexity pruning），不是拟合 law；唯一显式 compute-aware law（Goyal）是 VLM。

### 3.3 数据轴矛盾

- **T2：data-constrained 建议反转**。Muennighoff：小模型、多 epochs；Lovelace 2026：重拟合后，超过某点应更大模型、更少 epochs；Selecting Repetition Counts 2026：最优重复数随模型大小变。**调和**：Muennighoff 的 `N'` 可能吸收 baseline misspecification；建议依赖 unique-data budget、corpus diversity、optimizer（WD 改变 overfitting 系数 ~70%）；“4 epochs free”是 C4-specific 经验，不是普适常数。
- **T3：repetition tolerance 取决于多样性，不是 epoch 数**。C4 4 epochs vs mixture 15–20 次 vs VLM 35 epochs。**调和**：数据多样性、semantic dedup、mixture regularization、quality distribution 决定重复 token 边际价值；需要 diversity-adjusted effective-data variable。
- **T6：mixture 可预测 vs mixture 效应超越 scaling law**。Data Mixing Laws/RegMix 能预测平均验证 loss；但 RegMix 自己说 mixture 效应 transcend scaling laws，且 web corpus 最相关可能反转。**调和**：law 预测小规模平均 loss，不保证 frontier downstream accuracy；1M proxy 可能不保留 7B+ ranking。
- **T7：filtering 依赖 compute vs selection 10×**。Goyal：quality 在高 compute 下可能输给低质量大数据；PreSelect：30B selected 在 1B 上超过 300B random，10× compute reduction。**调和**：两者在不同 regime；selection 收益在低 compute/高重复最大；超高 compute 下未筛选数据的边际价值可能超过更好 selection；proxy quality 也重要。

## 4. 优化器 / 训练配方

### 4.1 Paper cards

#### McCandlish et al. 2018, An Empirical Model of Large-Batch Training（arXiv:1812.06162）

- **设置**：MNIST/SVHN/CIFAR-10/ImageNet/Billion Word、Atari、Dota 2、autoencoders。
- **Law**：定义 gradient noise scale `B_noise` 与 critical batch size `B_crit = E_min/S_min`，预测 `B_crit ≈ B_noise`；noise scale 随 loss 下降而上升；**模型大小主要通过改善 loss 影响 B_crit，而不是独立作用**。
- **假设**：SGD-like updates；固定 optimizer；loss 是充分统计量。
- **证据**：High（其 setting）；任务覆盖极广。
- **局限**：pre-LM、pre-AdamW-at-scale；optimizer-agnostic by construction，被 2505.02222 对 Muon 的结果挑战；`B_noise = B*/(L/L*)^{1/α}` 的 α 未从提取文本恢复 [待确认]，不要引用 universal α。

#### μTransfer（2203.03466）

- 见 `axis-architecture.md`。核心：宽度方向 HP transfer；13M→350M BERT、40M→6.7B GPT-3；tuning cost 7%。**不覆盖深度/batch/token horizon**。

#### Muon / Moonlight（arXiv:2502.16982，2025-02，Moonshot AI）

- **设置**：Muon 需要两个 ingredient 才能 scale：(1) AdamW-style weight decay（否则 weight/layer-output RMS 超出 bf16）；(2) per-parameter update-scale matching `W_t = W_{t-1} - η_t(0.2·O_t·√max(A,B) + λW_{t-1})`，可复用 AdamW 的 LR/WD。
- **结论**：compute-optimal 训练下比 AdamW 约 **2×** compute efficiency；Moonlight 3B/16B MoE、5.7T token；匹配 MMLU frontier 用 0.519× FLOPs。
- **证据**：High（production run + open distributed implementation）。
- **局限**：2× 是 compute-optimal-scaling-law estimate，不是固定 token 下的受控 loss match；Newton–Schulz 迭代次数、分布式 reduction 精度是未研究混杂。

#### MiniCPM / WSD（arXiv:2404.06395，2024-04）

- **设置**：Warmup–Stable–Decay LR schedule：stable phase 常数 LR，末尾快速 decay。
- **贡献**：(i) 从任意 stable checkpoint 分叉新 decay，连续训练/领域适应变简单；(ii) **data 轴几乎免费**——一个 stable run 可通过分叉 decay 得到许多 (D,L) 点，把 scaling study 从 quadratic 降到 ~linear。报告 compute-optimal `D/N` 远高于 Chinchilla。
- **证据**：Medium-high（schedule 已成标准实践）。
- **局限**：“optimal ratio”依赖 loss envelope 形式（指数 vs 幂律）；最大 2.4B。

#### Step Law / Predictable Scale Part I（arXiv:2503.04715，2025-03）

- **设置**：3,700+ LLM from scratch，~100T token，~1M H800 GPU-hours；dense + MoE；多数据 recipe；LR × batch × N × D 网格。
- **Law**：
  `η(N,D) = 1.79 · N^{-0.713} · D^{0.307}`
  `B(D) = 0.58 · D^{0.571}`
  optimal batch size 对 N 不变；预测最优与 exhaustive grid global optimum 差 **0.094%**。
- **假设**：固定 (N,D) 下 (LR,batch) loss surface 凸、最优宽；系数 architecture/data-recipe invariant；optimal = final converged loss。
- **证据**：High within its regime（59M–1B，按后续 recalibration 的说明），是本 literature 最大 sweep。
- **局限**：**不是 loss-vs-step law，也不是 optimizer law**；输入是 N/D，不是 step；AdamW + warmup-cosine 校准；2026 recalibration 在 <59M 发现形式保留但系数移 ~4×；外推到 Muon 未验证。

#### 小规模 recalibration（arXiv:2609.27581，2026-09）

- **设置**：<59M 参数，29 个 (N,D) cell，935 runs，nanoGPT/TinyStories，AdamW + warmup-cosine。
- **结果**：接受“形式保留、系数不同”：
  `η* = 0.0985 N^{-0.508} D^{0.238}`（R²=0.834）
  `B* = 3.6×10^{-4} D^{0.931}`（R²=0.950）
  直接迁移 Step Law 会把 optimal LR 高估约 **4×**（2.4–6.6×）；batch exponent 约翻倍；确认 `B* ⊥ N`。
- **意义**：在小 regime 证伪“universal”，并给出 recalibration 模板。

#### 其他优化器/配方论文

- **2603.15958**：用 LMO 方法（含 normalized SGD、signSGD≈Adam、Muon）的 convergence bound 推导 LR/momentum/batch 的闭式 power law；固定模型大小；momentum×batch 交互 under-determined。理论，无新大规模实验。
- **2608.20061（COLM 2026）**：MoE + MLA + Muon 的 μP 适配；LR 跨宽度迁移；token 维 law 从小 proxy 线性回归外推到 10T token，R²=0.95；用 155B total/17B active MoE 验证。最强“LR transfer + Muon 可组合”证据，但迁移的是 LR，不是 loss law。
- **2505.02222**：Muon 在远超 critical batch size 时仍保留 data efficiency；与 μP 通过 “telescoping” 误差记账组合；验证到 4B。直接挑战 McCandlish 的 optimizer-agnosticism。
- **Weight decay**：2605.01640 显示 data-constrained 最优 WD 约高于标准实践一个数量级（λ=1.0 把 overfit 系数降 ~70%）。

### 4.2 优化器轴矛盾

- **T5（McCandlish optimizer-agnosticism is dead）**：McCandlish 认为 `B_crit` 是 loss landscape/data 的属性，模型大小只通过 loss 进入；2505.02222 显示 Muon 在远超 `B_crit` 时仍保留 data efficiency。**含义**：任何 AdamW 校准的 batch-size law 在 Muon 下可能大错；任何假设固定 `B_crit` 的 FLOP-matched 比较都是 misspecified；没人测过 looped model 的 `B_crit`。
- **T6（Step Law universality vs recalibration）**：Step Law 声称跨 dense/MoE/数据 recipe 通用、误差 0.094%；2026 recalibration 发现 <59M 形式保留但 LR 系数差 ~4×、batch exponent 近翻倍。**含义**：law 必须附 calibration envelope；超出 envelope 的外推是新拟合，不是预测。
- **Weight decay 未建模**：Moonlight 显示 WD 是 Muon 稳定的关键；2605.01640 显示 data-constrained 最优 WD 高一个数量级；没有 `λ*(N,D,epochs)` 的闭式 law。

## 5. 推理最优 / 过训练

### 5.1 Paper cards

#### Sardana et al. 2024, Beyond Chinchilla-Optimal（arXiv:2401.00448，ICML 2024）

- **设置**：47 个 MPT 模型，150M–6B，10–10,000 TPP；单 epoch；downstream Gauntlet。
- **结论**：最小化训练 + 推理成本（Chinchilla loss surface + inference term）。例：7B-quality 模型、1e11 inference token 时，最优是 6B 模型、1.18× Chinchilla 数据；30B-quality、1e13 inference token 时，最优 13.6B、2.84× 数据，总 FLOPs 降 **28%**。
- **假设**：inference demand 已知；每 FLOP 成本常数；Chinchilla 形式外推到 10,000 TPP。
- **证据**：Medium-high。
- **局限**：无 repetition；单 epoch；无 memory/latency；downstream 噪声；inference demand 是点估计。

#### Wu et al. 2024, Inference Scaling Laws（arXiv:2408.00724，ICLR 2025）

- **设置**：Pythia 410M–12B；Llemma 7B/34B；GSM8K/MATH；greedy、majority voting、best-of-n、weighted voting、tree search。
- **结论**：经验 accuracy–compute 曲线，不是单一闭式 law；小模型 + 高级 inference 常 Pareto-optimal；Llemma-7B + REBASE tree search 在 MATH 上超过 Llemma-34B，在 MATH500/GSM8K 上用约 **2× less FLOPs** 达到 competitive accuracy。
- **证据**：Medium-high。
- **局限**：task-specific；无统一 law；saturation；verifier/voting 依赖；无 memory/latency。

#### Snell et al. 2024, Scaling Test-Time Compute Optimally（arXiv:2408.03314，ICLR 2025）

- **设置**：PaLM 2-S*；MATH；process-reward-model search + iterative revisions；按 prompt difficulty 做 compute-optimal allocation。
- **结论**：比 best-of-N 效率高 **2–4×**；FLOPs-matched 评估中，test-time compute 可在小模型有 non-trivial success 的问题上击败 **14× larger** base model。
- **假设**：difficulty bins 是充分统计量；有 verifier/revision；math 有代表性。
- **证据**：Medium-high。
- **局限**：math only；proprietary；difficulty estimation 也耗 compute；无 memory/latency；无 joint pretraining law。

#### Roberts et al. 2026, Test-Time Scaling Makes Overtraining Compute-Optimal（arXiv:2604.01411）

- **设置**：<1B 参数 checkpoint，扩展为故意 overtraining run；8 个真实/合成任务；pass@k 重复采样。
- **Law**：联合优化 N、D、sample count k，`6ND ≤ C_train`、`2Nk ≤ C_inf`、`k = C_inf/(2N)`；Approach 1 `L = E + A/N + B/D + 2NG/C_inf`；预测超出标准 20 TPP 的极端 overtraining，并在预测区域验证；在他们的测试中 survives post-training。
- **假设**：repeated sampling 是 test-time 策略；pass@k 是正确 metric；inference cost 对 N/k 线性。
- **证据**：Medium（<1B）。
- **局限**：小规模；8 任务；无 memory/latency；post-training 验证有限；pass@k 假设独立采样。

#### LLaMA 3 / Gemma 2 / Gemma 3（2407.21783 / 2408.00118 / 2503.19786）

- **设置**：LLaMA 3：8B/70B/405B，~15T corpus，405B 15.6T；Gemma 2：2B/9B/27B on 2T/8T/13T；Gemma 3：1B/4B/12B/27B on 2T/4T/12T/14T。
- **结论**：没有 fitted law；经验 ratio 约 40–2,000 TPP：405B flagship 约 **39 TPP**（约 2× Chinchilla），8B 与小 Gemma 约 **1,000–2,000 TPP**。小模型 overtraining 是显式部署选择，降低推理成本。
- **证据**：Observational high（frontier existence proof）。
- **局限**：无 counterfactual allocation；data quality/architecture/distillation/post-training 混杂；不是受控 scaling test。

#### Gemstones（arXiv:2502.06857，NeurIPS 2025）

- **设置**：4,000+ checkpoints，Transformer ≤2B，多样 shape，LR/cooldown 消融。
- **结论**：拟合标准幂律，但 prescription 对 checkpoint selection 与实验设计高度敏感；附录认为固定 FLOPs 下 overtraining 提高预测 loss，但曲线相对平坦 [待确认：附录]。
- **证据**：Medium。
- **局限**：≤2B；overtraining claim 是附录分析；无 inference/post-training。

#### Springer et al. 2025, Overtrained LMs Are Harder to Fine-Tune（arXiv:2503.19206，ICLR 2025）

- **设置**：OLMo-1B 预训练 2.3T vs 3T token；受控 fine-tuning + 参数敏感性理论。
- **结论**：catastrophic overtraining——3T 模型在 instruction tuning 后多个 benchmark 比 2.3T 差 **>2%**；机制是预训练参数对修改的 broad sensitivity 系统性增加；OLMo-1B 在 ~2.5T 有 inflection [待确认]。
- **证据**：Medium-high。
- **局限**：单一模型族；机制不完整；task-dependent；无预测 inflection 的 law。

#### Kinetics（arXiv:2506.05333，2025）

- **设置**：0.6B–32B；加入 memory-access 与 attention cost 的 test-time scaling。
- **结论**：小模型有效性被高估；test-time compute 在模型大小超过阈值后更有效；sparse attention 有收益。
- **证据**：Medium；hardware-specific；AIME-centric。
- **意义**：直接挑战 FLOP-only inference optimum。

#### 其他 watchlist

- **xLSTM Scaling Laws（2510.02228，ICLR 2026）**：80M–7B、2B–2T，含 overtraining；`L(C)=λC^{-η}`，η≈0.047–0.050 [待确认]。
- **Noisy Channels（2605.23901，ICML 2026）**：训练视为 noisy channel；解释 U 形退化；12B/307B 外推 R²=0.847 [待确认]。
- **Selecting Repetition Counts（2610.05126）**：repetition ranking 随模型规模反转；520M Proof-Pile-2 把 repetition 从 16 降到 8 反而更好。
- **When Data Is Scarce（2606.01155，ICML 2026）**：稀疏模型重复训练 law；loss-optimal sparsity ~50%，compute-optimal 更高；1.92B fit / 7.68B dense-equivalent validation。
- **Hartenstein et al. 2026（NeurIPS 2026，无 arXiv ID）**：32 个模型；`D ∝ N^{0.226}` [待确认]；观察性。

### 5.2 Overtraining 的三层定义（关键）

文献把三种 overtraining 混用：

- **O1 allocation overtraining**：tokens/parameter 高于 compute-optimal ratio。T²、Gemstones、deployment-allocation 研究属于这一层。
- **O2 optimization overtraining**：固定 N/D 下训练超过验证 loss 改善点。
- **O3 adaptability overtraining**：预训练更长，base loss 改善，但 downstream fine-tuning 变差。Springer 属于这一层。

**规则**：一篇论文可以 O1 最优、O3 有害而不矛盾。报告 overtraining 必须说明是哪一层、什么目标、什么成本模型。

### 5.3 推理/过训练矛盾

- **T4：小模型 + inference vs memory-aware costs**。Wu/Snell/T² 显示小模型 + test-time compute Pareto-optimal；Kinetics 认为小模型有效性被高估，因为 Best-of-N 与长 CoT 是 memory-access bound，attention 而非参数数主导 test-time cost。**调和**：成本模型不同；FLOP-only 奖励小模型；memory-bandwidth/latency 可反转排序，尤其长上下文。
- **T5：overtraining 最优 vs 有害**。Sardana/T²/Gemstones 显示计入 inference 后 overtraining 最优；Springer 显示额外预训练让 fine-tuning 更差。**调和**：目标不同——O1 vs O3；缺一个 joint pretrain–SFT law。
- **定义问题**：没有单一 canonical overtraining law；T²、Gemstones、xLSTM、deployment allocation 用不同 dependent variable（base loss、downstream accuracy、parameter allocation），不可直接比较。

## 6. 开放问题

1. **Frontier-scale identifiability**：几乎所有 law 在 <10B 共线数据上拟合；无公开 30B+ 非共线 N×D 设计。
2. **Overtraining 定义**：O1/O2/O3 混用；需要标准 metric 与 counterfactual。
3. **Data quality 非标量**：quality bucket/perplexity filter/classifier score 偏差不同；InfoLaw information density 未跨 pipeline 验证。
4. **Repetition-law transfer**：`R_D*` corpus-specific；2026 rank-reversal 说明小规模选择不可靠迁移。
5. **Mixture laws under distribution shift**：预测平均 loss，不保证 downstream/task balance/safety。
6. **Joint pretraining–inference–posttraining law**：没有 law 包含 SFT/RL；catastrophic overtraining 能反转预训练最优。
7. **Hardware-aware inference scaling**：FLOP-only 忽略 memory bandwidth/latency/energy；Kinetics vs T² 未解决。
8. **Emergence vs metric artifacts**：见 `failures-and-tensions.md`。
9. **Compute accounting**：FLOPs 是 wall-clock/cost/energy 的糟糕代理；GPU-hours 最优与 FLOPs 最优可能不同。
10. **Data contamination/evaluation leakage**：污染会压平/弯曲曲线，很少审计。
11. **Step Law optimizer transfer**：η(N,D) 是 AdamW 校准；Muon 下的 coefficients 未在 scale 上重拟合。
12. **Weight decay law**：没有 `λ*(N,D,epochs)`；这是 optimizer scaling 最大空白。

## 7. 方向种子

### Seed 1：Identifiability benchmark

- **问题**：已发表 scaling-law 指数在其拟合设计下是否可识别？
- **假设**：off-ray 外推误差可由 Gauss–Newton 条件数预测；共线 `α≈β` 拟合在非共线设计上重拟合时，bootstrap CI 会排除原指数。
- **设计**：5M–1B 参数、factorial N×D 网格，TPP 5–5,000；拟合 Chinchilla/BNSL/repetition/mixture；留出整条 TPP ray；比较 CI coverage 与外推误差。
- **Falsifier**：条件数不预测 rank/error；非共线设计不改善留出外推。
- **Venue**：NeurIPS/ICML benchmark 或 D&B track。

### Seed 2：Joint pretraining–posttraining overtraining law

- **问题**：额外预训练何时改善 base loss 但降低 fine-tuning？
- **假设**：O1 最优 overtraining ratio 是 inference demand 与 task alignment 的函数；存在 O3 adaptability 主导的相边界，可由参数敏感性（Hessian trace/effective rank）预测，并随 weight decay 移动。
- **设计**：OLMo/Pythia checkpoint 1×–100× Chinchilla，SFT 任务覆盖不同预训练重叠，测 Δpost 与参数敏感性；拟合双目标 law（base loss + post-training penalty）。
- **Falsifier**：无 task-dependent reversal；post-training penalty 对预训练 token 单调且与 alignment 无关。
- **Venue**：ICML/NeurIPS。

### Seed 3：Diversity-adjusted repetition law

- **问题**：重复 token 价值能否由 corpus diversity 而非 epoch 数预测？
- **假设**：`R_D*` 由可测 diversity proxy（semantic dedup rate、compression ratio、domain entropy）预测；同 token 数不同 diversity 的 corpus 有不同最优重复数。
- **设计**：20 个跨语言/领域 corpus；100M–3B 模型；1–50 epochs；估 `R_D*`；回归 diversity metrics；测试是否比 epoch-based law 更好预测 2026 rank reversal。
- **Falsifier**：diversity metrics 在 token count/domain 外无解释力；rank reversal 不可预测。
- **Venue**：ACL/EMNLP/ICML。

### Seed 4：Hardware-aware inference scaling law

- **问题**：latency SLO 下最优模型大小是否系统性偏离 FLOP-optimal？
- **假设**：加入 memory-bandwidth/latency 项后，最优模型比 FLOP-only 预测更大；gap 随 attention share 与 context length 增长，从而调和 Kinetics 与 T²。
- **设计**：0.5B–30B，context 4K–128K，Best-of-N 与 CoT；测 FLOPs、HBM bytes、latency、accuracy，两种硬件；拟合三项成本模型。
- **Falsifier**：memory/latency 项不改变最优 N 超过噪声，或效应完全由 FLOPs 解释。
- **Venue**：MLSys/ICML。

### Seed 5：Mixture-to-downstream transfer law

- **问题**：mixture ranking 何时从验证 loss 分叉到 downstream accuracy？
- **假设**：分叉可由 task weights 与 domain overlap 预测；RegMix 的 “web is best” 是小规模/困惑度 artifact，7B+ 或 downstream-weighted 目标下反转。
- **设计**：1B–7B，100B–1T token，8 域，12 mixture；测 perplexity 与 15 downstream task；拟合多目标 mixture law；比较 1M proxy/1B loss/7B downstream 的 rank correlation。
- **Falsifier**：downstream ranking 对 perplexity 单调且跨 scale；1M proxy 保留 7B ranking。
- **Venue**：ICLR/NeurIPS。

## 8. 阅读阶梯

- **Level 0**：Chinchilla（2203.15556）+ Besiroglu（2404.10102）+ Muennighoff（2305.16264）+ Sardana（2401.00448）+ Step Law（2503.04715）。
- **Level 1**：Data Mixing Laws（2403.16952）、RegMix（2407.01492）、Goyal（2404.07177）、Lovelace（2605.01640）、Muon/Moonlight（2502.16982）、WSD（2404.06395）。
- **Level 2**：Wu（2408.00724）、Snell（2408.03314）、T²（2604.01411）、Gemstones（2502.06857）、Springer（2503.19206）、Kinetics（2506.05333）。
- **Level 3**：按 `failures-and-tensions.md` 的 T1–T8 与本文 T1–T7 回查原文。

## 9. 来源

- 2001.08361, 2203.15556, 2404.10102, 2605.08541, 2210.14891
- 2305.16264, 2403.16952, 2407.01492, 2404.07177, 2605.01640, 2605.02364, 2605.12715
- 1812.06162, 2203.03466, 2502.16982, 2505.02222, 2404.06395, 2503.04715, 2609.27581, 2603.15958, 2608.20061
- 2401.00448, 2408.00724, 2408.03314, 2604.01411
- 2407.21783, 2408.00118, 2503.19786, 2502.06857, 2503.19206, 2506.05333
- 2510.02228, 2605.23901, 2610.05126, 2606.01155
- 完整 paper cards/下载日志见构建时的 research reports；本文件已保留所有关键数字与 arXiv 出处。
