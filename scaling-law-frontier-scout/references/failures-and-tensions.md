# 失效边界、矛盾与空白

> last_updated: 2026-11-15
> status: 已基于 boundaries-frontier agent 的精读报告与 10 篇下载 PDF 核对；venue 未从 primary metadata 验证处标 `[待确认]`。
> 证据等级：A = 大规模受控/多任务；B = 扎实但范围有限；C = 理论/立场/再分析。
> 核心论点：**sharpness 是 `(metric, axis, sampling noise, fit)` 这个四元组的属性，不是模型本身的属性。** 大多数“law break”要么是有限预算的 pre-asymptotic 曲率、metric 造成的非线性、拟合不可识别，要么是真正的 regime change；这五类必须用不同实验区分。

## 0. 这一轴的核心结论

1. **领域已经不再问“law 会不会断”，而在问“哪些测量不变性还活着”。**
2. 2022–2023 的 emergence 之争本质上是 metric 之争；2025–2026 的前沿转向 **construct validity（构念效度）、estimator identifiability（估计可识别性）、regime change（数据受限/RL/test-time/agent）**。
3. 最站得住脚的立场不是“涌现是真的”或“涌现是伪影”，而是：**在固定 metric、固定轴、固定采样噪声、固定拟合方式下，sharpness 可以被制造、被平滑化、也可以被真实机制产生。**
4. 一次 scaling ladder 无法区分五种“break”：真实相变、有限预算曲率、函数形式错设、估计不可识别、测量伪影。区分它们需要机制模型、带证书的留出外推、或一次只改一个因素的干预。

## 1. Law-break 争论的谱系

### 1.1 平滑 law 基线

Kaplan–Hoffmann 家族的幂律是基线：验证 loss 随 N、D、C 幂律下降，计算最优分配 `N ∝ C^a, D ∝ C^b`。它之所以有用，是因为**单调且可外推**：少量小规模 run 预测大规模 run。“Law break”是相对这个基线定义的；之后每一场争论，本质上都是“哪个 residual 是信号、哪个是测量误差”。

### 1.2 涌现作为异常（Wei et al., 2206.07682，TMLR 2022）

- 定义：能力“在小模型不存在、在大模型存在”，且“不能简单通过外推小模型性能预测”。
- 论证结构：survey few-shot 与 augmented prompting（CoT、scratchpad、self-consistency）；曲线在临界规模前接近随机，之后陡升；框架为相变。
- 两个承重属性：**sharpness**（看起来瞬时）与 **unpredictability**（临界规模不可从小模型预测）。
- 论文自己的 caveat 常被忽略：“能力首次被观察到涌现的规模取决于多个因素，不是能力的不可变属性。”
- 弱点：present/absent 把连续能力二值化；任务选择 post hoc；没有 metric 非线性/统计功效审计；模型族把 scale 与数据、tokenizer、配方混杂。

### 1.3 Metric 批评（Schaeffer et al., 2304.15004，NeurIPS 2023 [待确认]）

- 主张：对固定任务与模型族，涌现“源于研究者选择的 metric，而不是模型行为随规模的根本变化”。
- 核心证据：BIG-Bench 上 **>92%** 的涌现能力出现在 Multiple Choice Grade 或 Exact String Match 下，两者都是不连续 metric，会把平滑改善的 per-token error 非线性变形。
- 三种检验：InstructGPT/GPT-3 上的三条预测；BIG-Bench meta-analysis 的两条预测；在视觉任务中证明 metric 选择可以制造“从未见过的涌现”。
- 结论比证据略强：“所谓涌现能力在换 metric 或更好统计后消失，可能不是 scaling AI 的根本属性。”
- 两个混杂被捆绑：**metric 非线性**与**低统计功效**（测试项太少，小模型看起来完全不会）。后者不是 metric 伪影，而是采样伪影；2026 年以“below-noise”问题重新出现。
- 局限：固定模型输出，无法排除内部计算的真实突变；不主张所有涌现都是伪影；连续 metric 仍可能产生陡峭曲线；“mirage”框架容易变成假二元。

### 1.4 Broken-law 综合（Caballero et al., 2210.14891，ICLR 2023）

- BNSL：平滑 broken power law，即在 log-log 坐标下平滑连接的分段线性函数，可有多断点与多幂律段：
  `y = a + b x^{-c0} ∏_{i=1}^{n} (1 + (x/d_i)^{1/f_i})^{-c_i}`
- 主张：该形式可建模并外推大量 upstream/downstream 任务、架构与设置——视觉、语言、音频、视频、diffusion、多模态、对比学习、RL、OOD、校准、剪枝、公平性、代码、数学应用题，以及“涌现/相变”。
- 它能捕捉非单调 double descent 与算术任务中的延迟陡拐点；外推优于竞争形式。
- 与 Schaeffer 的调和（常被低估）：**log-log 坐标下的平滑函数，在 linear 坐标下可以看起来像不连续相变。** “Sharpness”是表示依赖的。
- BNSL 不证明涌现是机制的；它证明 **仅凭 sharpness 无法区分真实 break 与平滑但陡峭的曲线**。反过来，Schaeffer 也不证明底层曲线在 metric-invariant 意义上平滑。
- 局限：描述性而非因果；参数/断点多，可识别性存疑；无不确定性量化；外推验证在选定任务上，不是随机能力样本。

### 1.5 Double descent（Nakkiran et al., 1912.02292，ICLR 2020 [待确认]）

- 经典结果：测试误差可对模型大小（model-wise）、训练 epoch（epoch-wise）、甚至训练样本数非单调；引入 effective model complexity (EMC)；在某些 regime 下，训练样本增加 **4.5×** 反而损害测试性能。
- 这是“更多 scale 总是更好”不是自然律的最干净存在性证明，也是“law break”框架的祖先。
- **LLM 证据（2024–2026）**：
  - 2402.15175：把 grokking、double descent、涌现统一为 memorization 与 generalization 电路竞争，划分四个训练 regime。
  - 2410.00699：用 HMM 建模自回归 LLM，发现模型复杂度对微调泛化有非单调影响。
  - 2509.24974：用 double descent 比较自回归与离散 diffusion LM；diffusion 需要更大容量/更多 epoch 才逃离欠参数化 regime，但在强过参数化 regime，**两者在大范围尺寸上都没有明显第二次下降**。
  - 2610.04507：在四个视觉 backbone 与 7B 语言模型上发现 LoRA rank 的“second descent”延伸到参数对等之后——double descent 在 **adapter/fine-tuning** regime 最稳健。
  - 2601.08316：把 epoch-wise double descent 分解为 clean/noisy signal，关联大激活与 benign overfitting。
- **综合**：double descent 真实存在，但在 LLM 里主要是 **fine-tuning/LoRA 与小模型现象**，不是通用预训练 law。说“scaling law 因 double descent 断裂”必须说明 regime；frontier 预训练尺度上，第二次下降常常缺失或低于测量分辨率。

### 1.6 数据墙（Villalobos et al., 2211.04325）

- 预测训练 token 需求与公共人类文本存量；若趋势延续，模型将在 **2026–2032** 之间训练与可用存量相当的数据集；overtrained 模型会更早。
- 非 overtrained 模型中位数：**2028 年**、约 **4×10^14 tokens**、**5×10^28 FLOP**。
- 存量估计（tokens，median [95% CI]）：Common Crawl 130T [100T, 260T]；Indexed web 510T [130T, 2100T]；Whole web 3100T [1900T, 5200T]。
- 补救：合成数据、跨域迁移、数据效率；但“存量”定义（质量过滤、去重、tokenizer、许可、领域混合）可以把“有效存量”改变数量级。
- 2025–2026 文献基本接受“数据受限 regime 已经到来”，转而问 law 应如何改变，而不是墙是否存在。

### 1.7 2025–2026 的三条转向

1. **Construct validity（构念效度）**：scaling 的对象是什么？用 capability manifolds（2609.27588）、prescriptive capability boundaries（2602.15327）、capability-aligned OOD validation（2605.28179）、information-theoretic synergy（2610.28479）替代“benchmark 分数”。
2. **Estimation validity（估计效度）**：从 scaling ladder 能识别什么？用 certified prediction envelopes（2610.34514）、pre-asymptotic corrections（2611.13534）、hinted difficulty ladders（2611.02270）、active experiment selection（2610.16297）替代点拟合。
3. **Regime change（regime 变化）**：law 描述的是哪个 regime？数据受限/多 epoch 预训练（2606.06888, 2607.25271, 2611.03590, 2610.05591）、RL scaling（2510.13786, 2610.33420）、test-time scaling（2604.01411）、agentic/tool-use scaling（2610.37648, 2610.23946, 2605.16508）。

## 2. 关键论文卡片

### 卡 1：Emergent Abilities of Large Language Models（2206.07682，TMLR 2022）

- 主张：scaling 产生小模型不存在、且不可外推预测的能力。
- 证据：few-shot 与 augmented prompting survey；曲线在临界规模前接近随机、之后陡升；框架为相变。
- 局限：present/absent 二值化；任务 post hoc；无 metric 非线性/统计功效审计；模型族混杂 scale 与数据/tokenizer/配方。

### 卡 2：Are Emergent Abilities a Mirage?（2304.15004，NeurIPS 2023 [待确认]）

- 主张：涌现可由 metric 选择解释，而非模型行为随规模的根本变化。
- 证据：BIG-Bench >92% 涌现能力使用不连续 metric；三条 InstructGPT/GPT-3 预测 + 两条 BIG-Bench meta 预测；视觉任务中 metric 可制造涌现。
- 局限：固定输出，无法排除内部突变；不主张所有涌现都是伪影；连续 metric 仍可陡峭；metric 非线性与低统计功效捆绑。

### 卡 3：Broken Neural Scaling Laws（2210.14891，ICLR 2023）

- 主张：平滑 broken power law 可建模/外推 scaling，包括陡拐点与非单调 double descent。
- 证据：多断点 BNSL 形式；跨视觉/语言/音频/视频/diffusion/多模态/RL/OOD/校准/剪枝/公平性/代码/数学；外推优于竞争形式；捕捉 double descent 与算术拐点。
- 局限：描述性非因果；参数/断点多，可识别性存疑；无不确定性量化；外推验证在选定任务；平滑 log-log 曲线可模拟相变，拟合好不等于机制。

### 卡 4：Will we run out of data?（2211.04325，preprint）

- 主张：公共人类文本有限，将在本十年约束 LLM scaling。
- 证据：需求预测 vs 存量；full utilization 2026–2032，中位 2028；约 4×10^14 tokens、5×10^28 FLOP；存量估计见上。
- 局限：存量定义依赖过滤/去重/tokenizer/许可/领域混合；假设趋势延续；合成数据/迁移/数据效率只是定性补救；CI 很宽。

### 卡 5：Deep Double Descent（1912.02292，ICLR 2020 [待确认]）

- 主张：测试性能可对模型大小/epoch/样本数非单调。
- 证据：ResNet18/CIFAR-10 + label noise；model-wise 与 epoch-wise double descent；EMC 框架；样本增加 4.5× 反而变差。
- 局限：视觉中心、label noise；EMC 是描述性；不建立 LLM 预训练相关性；后续 LLM 证据混合（2509.24974）。

### 卡 6：Beyond the Log-Linear Frontier（2611.13534，2026-11）

- 主张：经典可分离幂律在有限预算下 misspecified；谱与领域异质性产生曲率与对数过渡。
- 证据：Mellin–Barnes 分析给出三项展开；KKT 把 K-domain mixing 化为 scalar water-filling；45 个 operator spectra、Pythia 70M–12B、Chinchilla 245 runs、RegMix 17 domains；5.89% holdout MAPE；高 compute allocation regret 降最多 76.4%；cross-scale mixture RMSE 降 59.4%，zero selection regret。
- 局限：理论假设特定谱/领域结构；经验范围是 Pythia/Chinchilla/RegMix，不是 frontier；pre-asymptotic 修正可能不外推；72 页附录；仍是参数近似。

### 卡 7：Ambiguous Fits / Rashomon（2610.34514，2026-10）

- 主张：标准 scaling-law 拟合返回一个宽 near-minimizer set 的任意成员，外推差异巨大。
- 证据：Rashomon effect；训练 loss 几乎相同的两个拟合，compute efficiency 可差约 **74.6%**（figure OCR [待确认]）；提出确定性 branch-and-bound，给 certified near-optimality 与 prediction envelopes。
- 局限：聚焦 Chinchilla 式参数形式；branch-and-bound 计算更重；不解决 misspecification；合成演示；只给“可辩护外推的包络”，不告诉哪个是真的。

### 卡 8：Emergent Capabilities Arise Randomly from Learning Sparse Attention Patterns（2606.25010，2026-06）

- 主张：涌现由任务相关 attention pattern 的突然学习驱动，而非平滑 loss 阈值。
- 证据：Pythia + synthetic linear-map/cellular-automata；pattern completion 与 indirect object identification 的涌现与 attention pattern 获取同步；把学到的 attention map patch 回早期 checkpoint 可恢复大部分性能；难度依赖 context length 与 pattern sparsity；增加 attention heads 提升学习效率，head dimension 收益递减；MLP-Mixer 在一个 linear-map 任务上比 Transformer 好一个数量级。
- 局限：小规模/合成；把“涌现”操作为任务成功；不建立 frontier 阈值；主结论单一架构族；机制在 studied tasks 中必要，非普遍证明。

### 卡 9：Claims of emergence should be grounded in information decomposition（2610.28479，NeurIPS 2026 Position）

- 主张：涌现/协同 claim 非形式化、不可证伪；partial information decomposition (PID) 给出精确判据。
- 证据：PID 把 joint information 分解为 unique/redundant/synergistic atoms；系统行为只有在携带 proper subset 没有的 task-relevant synergistic information 时才算 emergent；应用于 attention heads、multi-agent systems、human–AI teams。
- 局限：position paper，无新实验；高维 PID 估计困难；redundancy measure 不唯一；不直接解决 metric 伪影之争；判据很严，可能把很多非正式涌现 claim 判为不成立。

### 卡 10：Data-Constrained Language Model Pretraining（2606.06888，2026-06）

- 主张：Chinchilla 可加 law 在唯一数据（而非 compute）成为瓶颈时 misspecified；masked-input regularization (MIR) 改善 data-constrained trade-off。
- 证据：72M–1.4B 模型，DCLM/Stack-V2，100M unique tokens；SoftQ 耦合模型大小与 unique data，R²=0.9993；MIR 约等于 1.3× unique data；1.4B 上 +10.2 BoolQ、+2.2 SciQ。
- 局限：≤1.4B、100M unique tokens；MIR 增加训练 compute；下游收益只在最大规模；单一数据域；SoftQ 仍是参数拟合，外推证据有限。

### 卡 11：Revisiting the Scaling Properties of Downstream Metrics（2512.08894，ICLR 2026 [待确认]）

- 主张：固定 token-to-parameter ratio 时，下游 benchmark accuracy 对 training budget 呈简单幂律；直接拟合优于两阶段 loss→downstream。
- 证据：多个下游任务的 log accuracy 幂律；直接法外推优于两阶段（避免误差累积）；固定 TPP 是关键控制变量。
- 局限：benchmark-specific；log-accuracy 可能隐藏饱和；固定 TPP 限制泛化；不处理小模型 accuracy 在噪声底的任务；venue 未从 arXiv metadata 验证。

### 卡 12：Prescriptive Scaling（2602.15327，ICML 2026 Oral）

- 主张：给定预训练 compute budget，当代 post-training 下可达 downstream accuracy 可估为稳定 capability boundary。
- 证据：5k 已有 + 2k 新评估 checkpoint，2022–2026，六个 benchmark；用 monotone saturating sigmoid 做 smoothed quantile regression，估 benchmark score vs log pretraining FLOPs 的高条件分位；用早期 generation 拟合、后期 release 评估，验证时间可靠性。
- 局限：观察性非因果；post-training 是移动目标；六个 benchmark 未必代表 agentic/long-horizon；quantile boundary 取决于 checkpoint 样本；“prescriptive”只适用于历史 frontier。

## 3. 跨论文矛盾

### 3.1 涌现真 vs metric 伪影

争论常被简化为 Wei vs Schaeffer，但至少是四个不同 claim：

| Claim | 最强证据 | 什么能证伪 |
|---|---|---|
| 规模阈值处行为突变 | Wei 曲线；2606.25010 attention-pattern transitions | 固定输出上连续 metric 无阈值；阈值随 metric 移动 |
| 表观 sharpness 由非线性/不连续 metric 制造 | Schaeffer >92% BIG-Bench；合成视觉 | 控制统计功效后，不连续 metric 作用于真实平滑 per-token error 仍不出现 sharpness |
| sharpness 与平滑 broken power law 相容 | Caballero BNSL fits | BNSL 在留出任务上失败；断点跨 seed 不稳定 |
| 涌现是 synergy，不是 sharpness | 2610.28479 PID | 非正式涌现 claim 处没有 synergistic information；PID 估计不稳定 |

这些 claim **不互斥**：一个模型可以突然学会 attention pattern（机制）、在 exact-match 下产生陡升（metric）、在 log-log 下拟合平滑 broken law（描述）、并携带 synergistic information（构念）。真正的争议是**privilege 哪一层描述**——这是方法论选择，不是经验事实。

2606.25010 的贡献：涌现是 **stochastic but predictable in distribution**——更大模型更早、更可靠地获得 attention pattern，但固定 scale 下某个能力可能因初始化而没出现。这不是“sharp threshold”也不是“mirage”，而是 **scale-dependent hazard**。

**mirage 批评最强**：小测试集、all-or-nothing 的 benchmark accuracy。**最弱**：关于内部计算的机制 claim，以及多智能体/人-AI synergy claim。

### 3.2 Perplexity vs downstream

- 直接 law 在部分设置更好：2512.08894 固定 TPP 下 log accuracy 幂律，外推优于两阶段（避免误差累积）。
- 生成式评估需要自己的 law：2509.24012 比较三种 pass@k law（compute；parameters+tokens；log-likelihood），从便宜模型预测最贵模型的 pass@k；三种协变量集并存本身就是警告——“最佳 law”取决于你能测什么。
- 张力：
  1. **噪声底**：小模型 accuracy 接近 0 时没有趋势。2611.02270 用 hinted scaling：给 privileged information 造出更容易的任务连续统，让小于 1e20 FLOPs 训练的模型也能给出可测信号，并外推 GSM8K。
  2. **Benchmark 特异性**：直接 log-accuracy law 在一个 benchmark 拟合，未必迁移到另一个；2605.28179 主张 capability-level、capability-aligned OOD validation。
  3. **饱和**：accuracy 幂律最终必须饱和；log-accuracy 拟合可能在测量范围内好看、接近上限时失败。2602.15327 用 monotone saturating sigmoid。
- **综合**：正确的对象不是“那个 downstream law”，而是 **按 metric、任务族、测量 regime 索引的一族 law**，并显式处理噪声底。Perplexity 仍是最稳的预训练代理；downstream accuracy 只有在评估被设计成可预测时才可预测。

### 3.3 数据耗尽

三层常被混淆：

1. **存量耗尽**：Villalobos：公共人类文本有限；中位 full utilization 2028（2026–2032）。
2. **有效存量**：质量过滤、去重、tokenizer、许可、领域混合可改变数量级；“墙”不是单一日期。
3. **重复/合成数据的边际价值**：若重复 token 保留价值，墙会变软。2610.05591 给重复 token 定价：第二 epoch 几乎和新数据一样值钱，但超过一个临界 epoch 数后，重复 token 价值降到新数据的一半；临界 epoch 数随 training budget per parameter 增长，几乎不随模型大小变。2607.25271 引入 token-effectiveness function，从完全替代到毫无价值。2610.31867 推导 synthetic rewrite scaling law，并把生成 rewrite 的 compute 计入成本。
- **函数形式之争最重要**：Chinchilla 可加 law 预测两个 unique-data budget 之间的 loss gap **与模型大小无关**；2606.06888 实证显示 gap **随模型变大而扩大**（“fan-out”），提出 SoftQ 捕捉交互。2611.03590 用 multi-epoch SGD 的 DMFT 表明 logit averaging 减少 late-training 退化，并在匹配 parameter-token budget 时可能优于更宽/更深的单模型。
- **综合**：“数据耗尽”不是悬崖，而是生产函数变化。约束从 unique tokens 转向 **effective tokens**（quality × repetition × synthetic value × domain mix）。把数据当 scalar token count 的 law 在这个 regime 是 misspecified。

### 3.4 Law break vs misspecification vs non-identifiability

一个 claimed break 至少来自五种来源：

1. **真实 regime change**（学习动力学的相变）。
2. **有限预算 pre-asymptotic 曲率**（2611.13534）：可分离幂律是渐近近似；有限 N/D 下弯曲。
3. **函数形式错设**（2606.06888）：可加 Chinchilla 形式无法表示 data-model coupling。
4. **估计不可识别**（2610.34514）：near-optimal fits 发散；“break”可能是 Rashomon set 的任意成员。
5. **测量伪影**（2304.15004）：metric 变形了平滑的 per-token error。

**2026 最重要的方法论教训**：这五类从单条 scaling ladder 上不可区分。区分需要 (a) 机制模型，(b) 带证书的留出外推检验，(c) 一次只改一个因素的干预。大多数论文只做 (b)，而且常常只是 in-sample。

2610.34514 的重要性：标准做法——拟合灵活 law、报告最佳局部最小、外推——连 (4) 都无法建立，更不用说 (1)–(3)。所以“break”应被当作一个需要判别实验的假设，而不是曲线的视觉属性。

### 3.5 Pretraining vs RL/test-time

- 2510.13786：RL training 的 compute-performance 曲线是 **sigmoidal**（>400,000 GPU-hours），不是幂律。
- 2604.01411：Train-to-Test (T²) law 联合优化模型大小、训练 token、推理样本数；八个下游任务上，计入推理成本后 **overtraining 是 compute-optimal**。这直接反驳“Chinchilla-optimal 总是最优”的预训练直觉。
- 2601.03764：pass@k failure exponent 是 **training-dependent**：随训练样本数 N 增长，直到由难度分布决定的内在极限饱和。所以“inference scaling law”不是纯 k 的函数。
- 2610.33420：actor-critic 在 Starpilot/Craftax 上的经验 RL scaling law，但对 LLM RL 的普适性未证明。
- 2609.27588：capability manifold 把预训练/后训练/test-time 资源映射到能力，带 Jacobian 敏感性；早期尝试。
- **综合**：scaling law 对象正在分裂。Pretraining loss、RL reward、pass@k、agentic task success 的曲线形状不同（幂律、sigmoid、训练依赖幂律、可能非参数）。一个 skill 若只教一种函数形式，至少会在三个 regime 里错。

## 4. 2025–2026 前沿速览（精选）

这里保留对方向判断最有用的条目；完整 20 行表见 `canonical-papers.md` 的 “Frontier scan” 一节：

| arXiv | Venue | 发现 |
|---|---|---|
| 2602.15327 | ICML 2026 Oral | 用 7k checkpoints 估 capability boundary（高分位）vs log FLOPs，验证时间可靠性 |
| 2611.13534 | arXiv 2026-11 | 三项 pre-asymptotic 展开解释有限预算曲率；5.89% holdout MAPE；allocation regret 降最多 76.4% |
| 2610.34514 | arXiv 2026-10 | near-optimal fits 外推发散；certified branch-and-bound 给 prediction envelope |
| 2610.28479 | NeurIPS 2026 Position | 用 PID synergy 作为 metric-invariant 的涌现判据 |
| 2606.25010 | arXiv 2026-06 | 涌现跨 seed 随机，但与 sparse attention pattern 的突然获得绑定；大模型更早学会 |
| 2512.08894 | ICLR 2026 [待确认] | 固定 TPP 下 log downstream accuracy 幂律；直接拟合优于两阶段 |
| 2509.24012 | ICLR 2026 [待确认] | 比较三种 pass@k law，从便宜模型预测贵模型 |
| 2510.13786 | ICLR 2026 [待确认] | RL compute-performance 是 sigmoidal；>400k GPU-hours |
| 2604.01411 | arXiv 2026-04 | T² law；计入推理成本后 overtraining compute-optimal |
| 2611.02270 | arXiv 2026-11 | Hinted scaling 在噪声底下造信号；从 ≤1e20 FLOPs 模型预测 GSM8K |
| 2606.06888 | arXiv 2026-06 | Chinchilla 可加 law 在重复数据下 misspecified；SoftQ 捕捉 N-D 耦合 |
| 2607.25271 | arXiv 2026-07 | Compute-Data law；token-effectiveness function 从完全替代到无价值 |
| 2611.03590 | arXiv 2026-11 | multi-epoch SGD 的 DMFT；logit averaging 延迟退化，可能优于更宽/更深模型 |
| 2610.05591 | arXiv 2026-10 | 给重复 token 定价；第二 epoch 接近新数据，超过临界 epoch 后价值减半 |
| 2610.23946 | NeurIPS 2026 | agentic RL 数据分解为 task/environment/trajectory 轴 |
| 2610.37648 | arXiv 2026-10 | tool-use agent scaling law；458,752 tasks、849 models |
| 2609.27588 | arXiv 2026-09 | capability manifold；预训练/后训练/test-time 资源的 bounded scaling functions |
| 2610.16297 | arXiv 2026-10 | SLDBench v2；active scaling-law discovery，agent 选择买哪些 run |

## 5. 开放问题

1. **Metric-invariant capability**：没有公认的操作定义能同时跨 metric、benchmark 版本、采样噪声。
2. **Identifiability**：缺少 prediction envelope、fit multiplicity、held-out extrapolation 的报告标准；2610.34514 是模板不是规范。
3. **Below-noise forecasting**：很多能力在便宜模型上接近 0；hinted scaling 有希望但只在少数 benchmark 验证。
4. **Data-constrained functional form**：SoftQ、CD laws、multi-epoch theory 对正确参数化不一致；没有共识的 `L(N,U,E,s)`（U=unique data, E=epochs, s=synthetic fraction）。
5. **Quality vs quantity**：effective tokens 依赖过滤/去重，但 law 把数据当同质；“给数据质量定价”的 law 缺失。
6. **RL scaling**：sigmoidal 拟合是描述性的；没有机制理论解释为什么 RL compute 饱和，以及 saturation 如何依赖 reward density/task diversity/algorithm。
7. **Test-time scaling**：T² 与 training-dependent pass@k 指数表明 inference scaling 与 training 耦合；联合 law 早期且 task-specific。
8. **Agentic/compound systems**：tool-use agents、skill libraries、multi-agent systems 的 scaling 对象不是单个模型；“model size”是错的 independent variable。
9. **Evaluation confounds**：污染、benchmark 饱和、选择性报告、metric 不连续；负结果（law 拟合失败）很少发表，造成 survivorship bias。
10. **Mechanism-to-law bridge**：attention-pattern learning 与 circuit competition 解释小规模涌现；没有从机制难度到 frontier scaling 指数的定量映射。

## 6. 创新动作（来自本轴）

1. **把 scaling law 当作 fits 的分布，而不是点**：报告 certified envelopes 与 fit multiplicity。
2. **把 metric 纳入实验设计**：预注册连续与不连续 metric；同时报告 per-token error 与 benchmark accuracy。如果 break 在连续 metric 下消失、但 per-token error 仍非平滑，是测量效应；如果两者都持续，是行为效应。
3. **用 difficulty ladder 穿过噪声底**：hinted scaling 是通用技巧——给 privileged information 造更容易的任务版本，再外推 difficulty-accuracy 关系。
4. **用 data production function 替代 scalar token count**：分别建模 unique data、repetition、synthetic fraction、quality filtering、domain mix。
5. **把 capability 与 benchmark 分开**：IRT-like measurement、capability manifold、PID 估 latent capability。
6. **联合优化训练与推理**：T² law 表明 inference 进入预算后，compute-optimal 预训练点会移动。
7. **拟合机制，不只是曲线**：attention-pattern difficulty、circuit competition 提示正确的协变量是 pattern sparsity、context length、head count、initialization hazard。
8. **在解释 break 前审计 estimator**：用已知平滑 law 生成合成数据，拟合候选 broken law，看它多常报告 break；false-positive rate 高，则 break 不是证据。

## 7. 方向种子（来自本轴报告）

### Seed 1：Metric-invariance audit

- **问题**：控制 per-token error 与 test-set size 后，claimed emergent abilities 的 break location 是否对 metric 选择不变？
- **设计**：Pythia/OLMo 1B–12B ladder + 预注册任务电池；每个任务计算 per-token error、exact match、MC grade、continuous Brier、log-likelihood；对每个 metric 拟合 BNSL 与平滑幂律；bootstrap CI 估 break location；检验跨 metric 是否重合。
- **Falsification**：若 break location 随 metric 变而 per-token error 平滑，Schaeffer 对该任务胜；若连续/不连续 metric 下 break 位置一致，行为解释胜；若 break 移动但 per-token error 也非平滑，是机制层面 transition。
- **顶会理由**：把四年修辞之争转成 measurement invariance test，并产出可复用 benchmark。

### Seed 2：Certified forecasts of published laws

- **问题**：多少已发表 scaling-law forecast 落在其自身拟合数据的 certified prediction envelope 之外？
- **设计**：收集 20–30 个有公开拟合数据的 law；用 branch-and-bound 重拟合；计算外推尺度的 envelope；比较发表点预测与 envelope。
- **Falsification**：多数 forecast 在 envelope 内 → 拟合实践比担心的健康；多数在外 → “law break”文献部分是未识别的 fits。
- **顶会理由**：meta-science 贡献，统计量精确可复现，并建立报告标准。

### Seed 3：含 synthetic fraction 与 quality 的 data-constrained law

- **问题**：单一 law `L(N,U,E,s,q)` 能否预测 held-out loss（模型大小、unique data、epochs、synthetic fraction、quality filter）？
- **设计**：70M–1.5B 固定 corpus ladder；U 100M–1B、E 1–16、s 0–0.5、q 两个过滤阈值；拟合 SoftQ/CD 候选 + 新交互项；在 held-out **组合**（不是同网格留点）上评估；报告 certified envelopes。
- **Falsification**：在 held-out 组合上失败（尤其 s 与 E 联合变化时）→ data production function 不可分离，现有 law misspecified。
- **顶会理由**：data-constrained 是 2026–2028 实际 regime；验证过的多因子 law 会被立即采用。

### Seed 4：Emergence as scale-dependent hazard

- **问题**：能否从 attention-pattern difficulty（sparsity、context length、head count）跨 seed/scale 预测某能力到某 token 前出现的概率？
- **设计**：2606.25010 的 synthetic linear-map/CA suite + Pythia；每个任务测 pattern sparsity 与 context length；拟合 hazard model `P(emerge by t | scale, seed)`；预注册 held-out 任务的 emergence 曲线。
- **Falsification**：held-out 曲线落在预测 hazard band 外 → attention-pattern 解释不完整；在 band 内 → 涌现可分布预测，溶解真/伪二元。
- **顶会理由**：首个可证伪的机制性涌现预测，连接 interpretability 与 scaling law。

### Seed 5：Below-noise downstream scaling with hinted ladders

- **问题**：小模型 accuracy 在噪声底时，hinted scaling law 是否比标准幂律更好地外推 frontier benchmark accuracy？
- **设计**：GSM8K/MATH/HumanEval/MMLU/BBH 各造 5–8 级 hint ladder；用 ≤1e20 FLOPs 模型拟合标准与 hinted law；预测最大可用模型 accuracy；比较 out-of-sample error 与 bootstrap CI；消融 hint type。
- **Falsification**：五个 benchmark 中少于三个显著优于标准 law → 方法不通用；否则是通用评估设计原则：**先让 benchmark 可预测，再预测**。
- **顶会理由**：解决噪声底的实际痛点，实验干净、证伪标准强。

## 8. 来源

- Wei et al., 2206.07682
- Schaeffer et al., 2304.15004
- Caballero et al., 2210.14891
- Villalobos et al., 2211.04325
- Nakkiran et al., 1912.02292
- 2611.13534, 2610.34514, 2606.25010, 2610.28479, 2606.06888
- 2512.08894, 2509.24012, 2510.13786, 2512.10858, 2601.03764
- 2602.15327, 2604.01411, 2611.02270, 2607.25271, 2611.03590
- 2610.05591, 2610.23946, 2610.37648, 2609.27588, 2610.16297
- 2402.15175, 2410.00699, 2509.24974, 2610.04507, 2601.08316
- 完整下载日志见构建时 agent 报告；本文件的 arXiv 引用已逐条核对。
