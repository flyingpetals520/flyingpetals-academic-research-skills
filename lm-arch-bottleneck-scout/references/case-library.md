# 案例库：真实论文的"瓶颈 → 解决动作 → 新瓶颈"

每条案例严格按：上一瓶颈（含事实强度标注）→ 解决动作（对应原语编号，见 invention-primitives.md）→ 关键证据 → 新瓶颈。事实强度：★=论文作者声明，☆=论文消融/附录数据，◇=第三方测量/解读，?=未确证。
本库成文于 2026-11，之后的新论文需自行检索补充。

## 目录
1. 残差流谱系：HC → VWN / mHC → AttnRes → xHC（+支线）
2. 稀疏注意力谱系：NSA/MoBA → DSA → CSA/HCA、MSA → DoSA/GVR、SQA
3. 线性注意力谱系：Linear → DeltaNet → Gated DeltaNet → KDA → CKDA
4. 优化器谱系：AdamW → Muon → Moonlight → SAMuon
5. 嵌入方向：VWN 过宽嵌入、逐层嵌入、查表式记忆
6. 跨案例模式总结

## 1. 残差流谱系

### HC《Hyper-Connections》(arXiv:2409.19606, ByteDance, 2024-09; ICLR 2025)★
- 上一瓶颈：标准 Transformer 单股残差流限制跨层信息流的"记忆容量"，表达性随深度受限。★
- 解决动作：P3 升维——残差流扩成 N 路并行流，每层用三个可学习映射（pre/post/residual mapping）在流间读写。★
- 关键证据：多个预训练任务显著提升（作者报告）。★
- 新瓶颈（被后人暴露）：自由连接矩阵破坏恒等映射 → 深网信号无界放大、训练不稳定（mHC 报告的信号放大问题）◇；多流访存不规则、I/O 重。★（mHC 论文明确指出该家族"compromise the inherent identity mapping property")

### VWN《Virtual Width Networks》(arXiv:2511.11238, ByteDance Seed, 2025-11)★
- 上一瓶颈：模型宽度受硬件成本硬约束；嵌入层与残差流宽度绑定，参数/显存大头在嵌入。★
- 解决动作：P12 换轴 + P3 加流——"虚拟宽度"：Token 用 Over-Width Embedding 加宽，层内用 GHC（统一 HC 与 Frac-Connections）在过宽隐状态与骨干宽度间压缩/扩张，计算仍按骨干宽度走。★
- 新瓶颈：过宽状态与骨干间的反复压缩/扩张引入额外 I/O；GHC 继承了 HC 家族的稳定性问题需靠流形化/工程兜底。?

### mHC《Manifold-Constrained Hyper-Connections》(arXiv:2512.24880, DeepSeek, 2026-01)★
- 上一瓶颈：HC 在大规模训练数值不稳（信号放大；据 DeepSeek V4 系列解读，深层放大可达 3000×）◇；恒等映射丢失。★
- 解决动作：P2 约束化——把 residual mixing 矩阵经 Sinkhorn-Knopp 投影到双随机矩阵流形（Birkhoff polytope），恢复恒等映射与非扩张性；配套基础设施优化使访存规则化。★
- 关键证据：27B 规模稳定训练，仅 +6.7% 训练时间；被 DeepSeek-V4 采用（V4 残差即 mHC，4 路）。★（arXiv:2606.19348）
- 新瓶颈：Sinkhorn-Knopp 迭代开销（mHC-lite, arXiv:2601.05732, "You Don't Need 20 Sinkhorn-Knopp Iterations" 直接削减迭代数）★；N>4 扩展收益消失（write-back 信息供给不足 + mixing 成本 O(N³C)）★——成为 xHC 的立项靶子。

### AttnRes《Attention Residuals》(arXiv:2603.15031, Kimi Team, 2026-03)★
- 上一瓶颈："PreNorm 稀释"——固定单位权残差累积使隐状态范数随深度 O(L) 增长，早期层贡献被摊薄，大比例层可被剪掉而几乎不掉点（信息被均摊而非选择）。★
- 解决动作：P1 参数化 + P9 初始化手术——每层学一个伪查询 w_l，对之前所有层输出做深度维 softmax 注意力；伪查询零初始化使起点退化为均匀平均；Block 变体把层分块把记忆从 O(Ld) 压到 O(Nd)。★
- 关键证据：48B/1.4T token，GPQA-Diamond +7.5、HumanEval +3.1（作者声称，第三方 newsletter 转述）◇；匹配基线 1.25× 算力训练的精度（≈25% 有效算力节省）◇；48B 上 scaling law 曲线全段低于 PreNorm。★
- 新瓶颈：PP 下所有块表示需跨 stage 传（O(Ld) 通信）→ 跨 stage 缓存压到 O(P)★；1M prefill 块表示驻留 15GB → 序列维 TP 分片 + chunked prefill 压到 <0.3GB/设备★。推理 <2% 开销。
- 顺带教材：消融显示 input-dependent query 更好但引入逐维 I/O 故弃用；sigmoid 替代 softmax 掉点（竞争性归一化的价值）；input-independent 混合掉点——"学权重"要学到输入依赖才算数。☆

### xHC《Expanded Hyper-Connections》(arXiv:2607.14530, 2026-07; NeurIPS 2026 TR)★
- 上一瓶颈：HC 家族停在 N=4。两个归因明确的瓶颈：(1) 每层单一 write-back 向量供给不了越来越多的流（信息供给瓶颈）；(2) residual mapping 由 NC 维输入预测 N² 系数，成本 O(N³C)（成本瓶颈）。★
- 解决动作：P3+P4+P9——N=16 流、每子层只写回 k=4 流（读全部、写稀疏）；时间特征增强（temporal feature augmentation）让 write-back 携带更多历史信息；xHC-Flash 摊薄全状态访存（73.5C→40C，逼近 mHC@N=4 的 34C）。★
- 关键证据：18B MoE 平均下游 44.8(mHC)→48.8(xHC)，最终 loss 1.776→1.758，仅 +4.1% FLOPs vs vanilla★；scaling law：vanilla/mHC 需 1.50×/1.19× 算力才追平 xHC★；N=4→16：mHC 仅 −0.006 loss 且 +32% FLOPs，xHC −0.012 loss 且 +4% FLOPs★；在 Muon 训练下依然有效★。
- 新瓶颈：稀疏写回的路由决策本身、多流状态驻留显存；更大 N 后信息供给是否再饱和（待验证）。?

### 支线备忘
- iHC：未检索到同名论文（2026-11 前 arXiv 无 iHC 架构条目）。可能为 mHC-lite 或某篇非正式称谓的误记——引用前必须核实，切勿当作真实论文引用。
- ANCRe (arXiv:2602.09009)：自适应重分配神经连接，深度 scaling 支线。?
- Deep Delta Learning / DDL (arXiv:2601.00417)：直接改残差算子而非加跨层检索路径（Transformer² 论文的推荐路线）。?
- 更大家族（写报告时可引用作 prior art）：DenseFormer（深度加权平均，arXiv:2402.02622）、MUDDFormer（多路动态稠密连接，2502.12170）、DeepCrossAttention（ICML 2025）、RMT（残差矩阵外积记忆，2506.22696）、LAurel（ICML 2025）。

## 2. 稀疏注意力谱系

### NSA《Native Sparse Attention》(arXiv:2502.11089, DeepSeek, 2025-02)★
- 上一瓶颈：此前的稀疏模式多为推理期剪枝/手工模式，既不可训也不贴硬件。★
- 解决动作：P4+P10——可训的三分支（块压缩 + 细粒度选择 + 滑动窗口），门控融合；kernel 对齐 GPU tensor core，可端到端训练。★
- 新瓶颈：块级选择粒度粗；选择器复用主注意力表示 → 选择质量受主分支牵连。★（成为 DSA 靶子）

### DSA《DeepSeek Sparse Attention》(随 DeepSeek-V3.2, arXiv:2512.02556, 2025-12)★
- 上一瓶颈：NSA/MoBA 在块级选择；且用主分支 QK 打分使"选择"与"计算"纠缠。★
- 解决动作：P1+P6+P10——Lightning Indexer：专用低维 FP8 MQA 打分器，与主注意力解耦（训练时 detach）；token 级 top-k（V3.2：top-2048），主注意力只做选中 token 的精确注意力。★
- 关键证据：长上下文算力降 60-70% 且近似无损（作者报告）★；被 GLM-5 等采用◇。
- 新瓶颈：indexer 仍须对每个 key 打分 + top-k 排序成为解码关键路径，随长度线性增长 → 引出 DoSA/GVR/LiteTopK 一整条"selector 加速"支线★；以及"每个 token 的 KV 仍要存"（缓存瓶颈）→ 引出 V4 压缩路线。

### CSA/HCA《DeepSeek-V4》(arXiv:2606.19348, 2026-04)★
- 上一瓶颈：1M 上下文下 DSA 的 KV cache 按 token 全量保存（V3.2 约 84GB/1M）◇，序列维不压缩，内存不可行。★
- 解决动作：P5 压缩化 + P7 混合化——CSA：每 m=4 token（重叠窗）可学习压缩成一个 KV 条目，再跑 DSA 式 top-k；HCA：每 m'=128 token 压成一个条目，压缩后 dense 全看；两类层交错 + 128 滑窗 + 注意力 sink。★
- 关键证据：1M 上下文 V4-Pro 仅需 V3.2 的 27% 单 token 推理 FLOPs、10% KV cache（Flash 为 10%/7%）★；开源参考实现。★
- 新瓶颈：有损（压缩块不可拆、边界切分丢细节）★；MLA 时代的 RoPE 正确性论证不迁移到序列压缩表示（RoPE-on-K_pe 论证失效，位置正确性需重建）◇；top-k 在压缩条目上可能漏检远处单点信息。?

### MSA《MiniMax Sparse Attention》(arXiv:2606.13392, MiniMax, 2026-06)★
- 上一瓶颈：此前可训稀疏要么训练昂贵要么 tensor core 利用率崩；长上下文"理论上稀疏、部署上没赚到"。★（MiniMax 自己的弧线：M1 线性注意力→M2 回退全注意力→M3 稀疏◇）
- 解决动作：P4+P10+P9——GQA 骨干上的块稀疏：Index Branch 给 KV 块打分、每个 GQA 组独立 top-k（组内共享块集），Main Branch 精确注意力；exp-free top-k、KV-outer 布局；indexer warmup：先 40B token 全注意力 + KL 对齐再切稀疏。★
- 关键证据：109B/3T 训练质量与 GQA 持平；1M 上下文每 token 注意力算力 −28.4×，配 kernel H800 上 prefill −14.2×、decode −7.6×（FLOPs 倍数 ≠ wall-clock 倍数的教科书案例）★；kernel 与权重开源。★
- 新瓶颈：index branch 自身成本与"多长上下文才值得用"的交叉点未明☆；质量声明限 109B 规模；kernel 绑定 SM100。◇

### DoSA《Dots Sparse Attention》(arXiv:2610.13990, 2026-09)★
- 上一瓶颈（教科书级）：稀疏注意力"访问的少，但找到它们仍要对每个 key 打分"——top-k 选择本身成为关键路径。★
- 解决动作：P11 数学证书——Top-K 只需要"足以拒绝候选的证据"而非完整分数：种子集给出阈值下界；非负头投影 + 联合残差界给出正贡献上界；激活感知聚合界定负头的扣减量；只给仍存活的候选打全分，结果与精确 top-k 逐 token 一致（无损）。★
- 关键证据：Indexer 整体加速至 2.74×(vs SGLang)/1.69×(vs LiteTopK)；GLM-5.2 与 DeepSeek-V3.2 端到端 TTFT 1.94×/1.50×★。
- 方法价值：给"推理式加速"示范了通用模板——把"需要完整计算"重述为"需要拒绝证据"，再配界。?
- 同靶子的兄弟工作：GVR（seed+阈值搜索，Blackwell 上 radix-select 1.88×）◇。

### SQA《Sparse Query Attention》(arXiv:2510.01817, 2025-09)★
- 上一瓶颈：MQA/GQA 减 KV 头只省显存带宽不减 FLOPs，训练与全序列处理仍贵。★
- 解决动作：P12 换轴——不减 KV 头，减 Query 头，直接按比例砍注意力 FLOPs。★
- 关键证据：32k-200k 序列、计算受限场景吞吐至 3×，小规模质量影响轻微（初步实验）★。
- 意义：一篇论文同时证明"轴选择本身是创新维度"。?

## 3. 线性注意力谱系

### 前史：Linear Transformer → DeltaNet → Gated DeltaNet
- Linear Transformer（2020，kernel trick）→ DeltaNet（Yang et al. 2024，delta rule 秩-1在线更新）→ Gated DeltaNet（ICLR 2025，加头级标量遗忘门）。每一步都是 P1 参数化：更新规则参数化→衰减参数化。代价链：表达力受限于"固定大小循环状态"这一结构性瓶颈（被 hybrid 路线绕开）。★

### KDA《Kimi Delta Attention》(arXiv:2510.26692, Kimi Linear, 2025-10)★
- 上一瓶颈：Gated DeltaNet 的头级标量门控让所有维度同速遗忘，有限循环记忆没被精细利用；且通用 DPLR 转移矩阵的 chunkwise 计算太贵。★
- 解决动作：P1+P10+P7——逐通道（对角）遗忘门 Diag(α)；专用 DPLR 变体 + 定制 chunkwise 算法；与 MLA 按 3:1 层间混合。★
- 关键证据：同配方下首次在短/长上下文与 RL 后训练全场景超过全注意力；KV cache −75%，1M 上下文解码吞吐 6×；48B/3B MoE。★
- 新瓶颈：对角实数门使转移谱留在实轴，单层的持续旋转动力学表达不出 → CKDA 靶子★；线性化已有模型的转换是有损的且失败模式记录不全◇。

### CKDA《Complex KDA》(arXiv:2609.24797, 2026-09)★
- 上一瓶颈：KDA 非负门 + β∈[0,1] 的约束保住了高效 chunkwise 与非扩张性，但代价是谱限制在实数。★
- 解决动作：P1——复数域扩展解除谱约束。★
- 意义：谱系末端仍在用同一招（参数化/放开约束），说明"约束 ↔ 性质"的权衡是这条线的元瓶颈。?

## 4. 优化器谱系

### Muon (Jordan et al. 2024) → Moonlight (arXiv:2502.16982, 2025-02)★
- 上一瓶颈（Muon 初始）：AdamW 更新按坐标缩放，不是矩阵范数意义下的好方向。★
- 解决动作：P2 约束化（另一种）——动量经 Newton-Schulz 迭代正交化，更新近似正交矩阵。★
- Moonlight 补的瓶颈：Muon 只在小模型验证过；大规模化时更新尺度漂移 + 无权重衰减 → 不稳定。★
- 解决动作：P9 初始化/日程手术——加 weight decay + 按 RMS 精细调整每参数更新尺度；分布式 NS 实现（显存/通信最优）。★
- 关键证据：相对 AdamW ~2× 计算效率（scaling law），16B-A3B MoE/5.7T token（Moonlight）；开源实现。★
- 落地：DeepSeek-V4 大多数矩阵用 Muon，嵌入/输出头/mHC 静态偏置门/RMSNorm 留 AdamW（P6 解耦：按参数形态分派优化器）。★

### SAMuon (arXiv:2608.25990, 2026-08)★
- 上一瓶颈：Muon 正交化后更新谱平坦，实际谱轮廓显示头部维度更新不足、尾部有冗余——存在谱"headroom"。★
- 解决动作：P1——头锚定分配（head-anchored allocation）+ 尾部提升 γ，谱半径固定不动（沿用 Scion 免调参性质）。★
- 关键证据：124M/300M/1B 全网格优于调参后的 Muon，token 效率 +13.3%~24.0%，且优势随 batch size 增大而扩大。★

### 模式总结
优化器线的接力同样是"性质破坏→恢复→新性质空间被打开"：Muon 破坏了 Adam 的坐标自适应→Moonlight 用 decay+scale 补回稳定性→SAMuon 在已稳定的谱空间里再挖表达冗余。?


## 5. 嵌入方向

### VWN 过宽嵌入（见残差流谱系）
- 思路一句话：嵌入宽度与骨干宽度解耦——"Over-Width Embedding"加宽 token 表示，GHC 负责在过宽表示与骨干计算宽度间往返。把"加宽"从骨干搬到嵌入上，绕开硬件宽度约束（P12 换轴 + P3 加流）。★（arXiv:2511.11238）

### 逐层嵌入 / MatFormer 式
- Gemma 3n 的 Per-Layer Embeddings：每层独立的嵌入查找，主机内存卸载，给端侧模型加"记忆维度"（官方 model overview）◇。与 VWN 同旨：嵌入是"可独立扩展的轴"。
### 查表式记忆
- Conditional memory via scalable lookup（Cheng et al., ACL 2026）：N-gram 嵌入把单字查找泛化为局部上下文记忆检索，给"嵌入轴"再加稀疏检索维度。?
### 冻结小词表
- "Embeddings Are Overpriced? A Frozen 16MB Vocabulary"（arXiv:2610.22428, 2026-10）：小模型/三值模型冻结 16MB 词表，质疑嵌入参数的必要性——反向攻击"嵌入必须大"的默认假设（P12 换轴的极端形态）。?
- 模式：嵌入是被低估的创新轴——加宽（VWN）、分层（Gemma 3n）、检索化（查表记忆）、缩水冻结（frozen vocab），四个方向同时存在，说明该轴共识未立，是新手友好的接缝。?

## 6. 跨案例模式总结（写报告"瓶颈模式归纳"节时直接可用）

1. **新瓶颈常是旧解法的影子**：每代方案自身制造下一代瓶颈——HC→恒等映射破坏→mHC；DSA→全量打分→DoSA；MSA→indexer 成本；AttnRes→跨 stage 通信。写报告时沿时间轴标出"谁制造、谁暴露、在什么规模暴露"。
2. **粒度细化是永动机**：块→token（NSA→DSA）；层→块（AttnRes Full→Block）；每代细化都换来精度但付出选择成本，直到被证书/界封顶（DoSA）。
3. **"省 FLOPs 不交 wall-clock 税"需要硬件协同**：MSA 28.4×→14.2× 的落差是常态，凡是提效率的论文都要查 kernel 配套。
4. **稳定性手术三件套**：约束化（mHC 流形）、初始化手术（AttnRes 零初始化、xHC 0.01 门控）、预热日程（MSA warmup）——新机制要过规模关，三件套至少配一件。
5. **混合化是收敛答案**：单一机制在长上下文+短上下文、效率+精度上无法全优时，层间交错（KDA:MLA 3:1、CSA:HCA）成为 2026  frontier 模型的默认形态。
6. **换轴论文的立项证据**：xHC 靠"N=1→4 有收益"论证 N 轴存在；SQA 靠"KV 头路线不减 FLOPs"论证 Q 轴存在。换轴前必须先给"轴存在"的证据。
7. **无损/可证明是强卖点**：DoSA 的 exact-selection、mHC 的非扩张性——在部署敏感场景，"保证不变"比"平均差不多"更有市场。
