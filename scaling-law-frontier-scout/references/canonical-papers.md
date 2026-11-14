# Canonical Papers

> last_updated: 2026-11-15
> status: 已基于四个 agent 的 44 篇 PDF/HTML 与精读报告核对；未验证处标 `[待确认]`。
> 覆盖：foundations、data、optimizer/recipe、loops、architecture/MoE、failure boundaries、inference/overtraining、2025–2026 frontier、lab reports。
> 证据等级：High = 多估计器/复现的受控 sweep；Medium-high = 一个大受控 sweep + 留出验证；Medium = 单实验室/中等规模/观察性；Low-medium = 理论 + 有限验证。
> 规则：`[待确认]` 表示未从 primary metadata 验证；不要把它当确定事实引用。任何数值必须带 arXiv/venue 与坐标定义。

## Foundations / method

| Title | Year | Venue | arXiv | Law / claim | Evidence | Notes |
|---|---|---|---|---|---|---|
| Scaling Laws for Neural Language Models | 2020 | preprint | 2001.08361 | L(N)=(Nc/N)^0.076, L(D)=(Dc/D)^0.095, L(C)=(Cc/C)^0.050; N_opt∝C^0.73, D_opt∝C^0.27 | High | 768–1.5B, WebText2 22B; data unique/fixed; policy contradicted by Chinchilla |
| Training Compute-Optimal Large Language Models (Chinchilla) | 2022 | preprint | 2203.15556 | L=E+A/N^α+B/D^β; E=1.69, A=406.4, B=410.7, α=0.34, β=0.28; three estimators 0.50/0.50, 0.49/0.51, 0.46/0.54 | High | 400+ models 70M–16B; ~20 TPP; rounded parameters |
| Chinchilla Scaling: A Replication Attempt | 2024 | Epoch AI | 2404.10102 | E=1.8172, A=482.01, B=2085.43, α=0.3478, β=0.3658; 80% CI ~50× wider; rounded params imply ~70 TPP | Medium-high | 240 digitized points, 4,000 bootstraps; reported fit rejected p<1e-16 |
| Tokens-per-Parameter Coverage Is Critical for Robust LLM Scaling Law Extrapolation | 2026 | NeurIPS 2026 | 2605.08541 | Collinear D=kN makes Gauss–Newton ill-conditioned; condition number ~1/(α−β)^2; non-collinear 97.3% win rate | Medium-high | 5M–77M, four formalisms, five corpora |
| Broken Neural Scaling Laws | 2022/2023 | ICLR 2023 | 2210.14891 | Smooth broken power law with multiple breaks; n breaks → n+1 segments | Medium | Descriptive; captures double descent; no allocation policy |
| Neural Scaling Universality: If Exponents Are Fixed, Time to Understand Coefficients | 2026 | preprint (position) | 2606.25008 | t^-1/3, width^-1, depth^-1; N~C^1/3, L~C^-1/6 | Low-medium | Pythia/Chinchilla reanalysis; not tested on MoE/MLA |

## Data scaling

| Title | Year | Venue | arXiv | Law / claim | Evidence | Notes |
|---|---|---|---|---|---|---|
| Scaling Data-Constrained Language Models | 2023 | NeurIPS 2023 | 2305.16264 | Effective D'=U+U R* (1−e^{−R/R*}); ~4 epochs nearly free; beyond decays | High | 400+ runs, 10M–9B, C4; R* corpus-specific |
| Data Mixing Laws | 2024 | ICLR 2025 | 2403.16952 | L_i=c_i+k_i exp(linear mixture); MAE 0.005–0.031; optimized mixture ≈ +48% steps | Medium-high | RedPajama 7 domains; 70M/160M → 1B/100B |
| RegMix: Data Mixture as Regression | 2024 | ICLR 2025 | 2407.01492 | Regression surrogate over 512 1M models; 1B/25B validation; ~10% DoReMi compute | Medium-high | 7B/100B checks; 1M proxy fidelity weak link |
| Scaling Laws for Data Filtering — Data Curation cannot be Compute Agnostic | 2024 | arXiv | 2404.07177 | Quality–quantity tradeoff; beyond ~35 epochs uncurated beats top-10% subset | Medium | DataComp VLM/contrastive, not LLM |
| Prescriptive Scaling Laws for Data Constrained Training | 2026 | COLM 2026 | 2605.01640 | Additive overfitting penalty; beyond a point use larger models/fewer epochs; WD λ=1.0 cuts coefficient ~70% | Medium | Contradicts Muennighoff; new, not replicated |
| InfoLaw: Information Scaling Laws with Quality-Weighted Mixture Data and Repetition | 2026 | ICML 2026 | 2605.02364 | Quality = information density; repetition scale-dependent; 0.15% mean / 0.96% max loss error | Medium-high | 252M–1.2B fit, 7B/425B validation; 3.7T/six buckets [待确认] |
| Scaling Laws for Mixture Pretraining Under Data Constraints | 2026 | preprint | 2605.12715 | Repetition-aware mixture law; scarce target reused 15–20×; generic data regularizes | Medium | >2,000 runs; no frontier validation |
| Selecting Repetition Counts Across Model Scales | 2026 | arXiv | 2610.05126 | Repetition rankings reverse with model size; 520M prefers 8 over 16 | Medium | Undermines small-scale repetition transfer |
| When Data Is Scarce: Scaling Sparse Language Models with Repeated Training | 2026 | ICML 2026 | 2606.01155 | Law over active params, unique tokens, repetition, sparsity; loss-optimal sparsity ~50% | Medium | 1.92B fit / 7.68B dense-equivalent validation |
| PreSelect: The Data That Predicts Is the Data That Teaches | 2025 | ICML 2025 | 2503.00808 | 30B selected beats 300B random at 1B; 10× compute reduction | Medium | Proxy-dependent |
| Adaptive Data Optimization (ADO) | 2024 | arXiv | 2410.11820 | Online per-domain scaling laws; ~0.4% overhead [待确认] | Medium | Limited scale; no repetition axis |

## Optimizer / training recipe

| Title | Year | Venue | arXiv | Law / claim | Evidence | Notes |
|---|---|---|---|---|---|---|
| An Empirical Model of Large-Batch Training | 2018 | OpenAI | 1812.06162 | B_crit=E_min/S_min ≈ B_noise; model size affects B_crit through loss | High | Pre-LM; optimizer-agnostic, challenged by 2505.02222 |
| Tensor Programs V: μTransfer | 2022 | NeurIPS 2022 [待确认] | 2203.03466 | Width-wise HP transfer; 13M→350M BERT, 40M→6.7B GPT-3; 7% tuning cost | High | Depth/batch/token horizon not covered |
| Muon is Scalable for LLM Training / Moonlight | 2025 | Moonshot AI | 2502.16982 | WD + update-scale matching; ~2× compute efficiency vs AdamW; 3B/16B MoE, 5.7T tokens | High | 2× is scaling-law estimate; Newton–Schulz confound |
| Practical Efficiency of Muon for Pretraining | 2025 | arXiv | 2505.02222 | Muon retains data efficiency beyond B_crit; combines with μP | High | Up to 4B; breaks McCandlish optimizer-agnosticism |
| MiniCPM / WSD | 2024 | arXiv | 2404.06395 | Warmup–Stable–Decay; branched decays make data axis ~linear cost | Medium-high | D/N far above Chinchilla; 2.4B max |
| Predictable Scale Part I: Step Law | 2025 | arXiv | 2503.04715 | η=1.79 N^−0.713 D^0.307; B=0.58 D^0.571; 0.094% from grid optimum | High | 3,700 runs, ~100T tokens, ~1M H800-hours; AdamW + warmup-cosine, 59M–1B |
| Does Step Law Transfer to Small-Scale LMs? | 2026 | arXiv | 2609.27581 | η*=0.0985 N^−0.508 D^0.238; B*=3.6e−4 D^0.931; direct transfer overestimates LR ~4× | Medium | <59M, 935 runs; falsifies “universal” in smallest regime |
| Deriving Hyperparameter Scaling Laws via Modern Optimization Theory | 2026 | SciForDL workshop | 2603.15958 | Closed-form LR/momentum/batch laws for LMO family incl. Muon | Medium (theory) | Fixed model size; momentum×batch under-determined |
| Let's Scale Step by Step | 2026 | COLM 2026 | 2608.20061 | μP + MoE + MLA + Muon; LR transfer; token-dim law R²=0.95 to 10T tokens | High | 155B total / 17B active validation |

## Loops / recurrence

| Title | Year | Venue | arXiv | Law / claim | Evidence | Notes |
|---|---|---|---|---|---|---|
| Universal Transformers | 2018 | ICLR 2019 | 1807.03819 | Weight-tied recurrent depth + ACT halting; +0.9 BLEU WMT14 | Medium | Pre-LLM; no compute-matched comparison |
| Looped Transformers as Programmable Computers | 2023 | arXiv | 2301.13196 | 13-layer looped encoder emulates a computer | High theory, low practice | Constructions not SGD-learnable; no loss-vs-compute |
| Huginn: Scaling up Test-Time Compute with Latent Reasoning | 2025 | arXiv | 2502.05171 | 3.5B/800B tokens; prelude–recurrent–coda; r=32 ≈ 50B dense FLOP-equivalent | Medium | Single seed; LR never decayed; no scaling law |
| Ouro: Scaling Latent Reasoning via Looped Language Models | 2025 | arXiv | 2510.25741 | 1.4B/2.6B, 7.7T tokens, T_max=4; four-variable fit R²=0.9596 | Medium | Appendix D contradicts headline; exponents [待确认] |
| How Much Is One Recurrence Worth? Iso-Depth Scaling Laws | 2026 | NeurIPS 2026 Spotlight | 2604.21106 | L=E+A(N_once+r^φN_rec)^−α+BD^−β; φ=0.46 [0.41,0.53]; α=0.199, β=0.369 | High | 116 runs; φ=0.38 truncated BPTT; 0.65 hyperconnections; MuonH |
| Parcae: Scaling Laws for Stable Looped Language Models | 2026 | arXiv | 2604.12946 | rec∝C^0.40, D∝C^0.78; stability via negative-diagonal injection | Medium-high | Params-matched, not FLOP-matched; 1.3B |
| SMELT: Scaling Laws for Compute-Matched MoE Looped Transformers | 2026 | arXiv | 2609.01343 | Three-budget match; 6.8–18.0% FLOP saving; exponent 0.237→0.250 | High | 54B, r=2 only; task-dependent advantage |
| DeepLoop: Depth Scaling for Looped Transformers | 2026 | arXiv | 2607.13491 | Stability κ_R·M·(β/α)²=O(1); exponent 1/4→1/2 | Medium | GPT-2 small/medium only |
| Loop the Loopies! | 2026 | arXiv | 2607.16051 | 20B-A2B/6B-A0.6B; crossover ~600B tokens vs 30B-A3B | Medium | Single recipe; crossover unmodeled |
| Towards Looped Models Done Right, Part I | 2026 | arXiv | 2610.23036 | Full Huginn beats Ouro on 10 benchmarks; 75% fewer resident params than 112-layer MoE | Medium-high design, low scaling | 730M/336B + MoE 8B-A0.8B; single seed per cell |

## Architecture / MoE

| Title | Year | Venue | arXiv | Law / claim | Evidence | Notes |
|---|---|---|---|---|---|---|
| Tensor Programs V: μTransfer | 2022 | NeurIPS 2022 [待确认] | 2203.03466 | Width-wise HP transfer | High | See optimizer table |
| Don't Be Lazy: CompleteP | 2025 | NeurIPS 2025 | 2505.01618 | β=1 depth parameterization; 12–34% FLOP savings | High | 75M–1.9B, depth 2–128, 20 TPP |
| Spectral Condition for μP under Width–Depth Scaling | 2026 | preprint | 2603.00541 | k=1 vs k≥2 spectral condition | Medium-high | GPT-2 style; widths ≤4096, depths ≤256 |
| Scaling Inference-Efficient Language Models | 2025 | ICML 2025 | 2501.18107 | L=(E+AN^−α+BD^−β)(1+εR^γ); latency 3.5× differences | Medium-high | 63 dense 80M–1B |
| Unified Scaling Laws for Routed Language Models | 2022 | ICML 2022 [待确认] | 2202.01169 | log L(N,E)=a log N+b log E+c log N log E+d | Medium-high | Fixed 130B tokens confound |
| DeepSeekMoE | 2024 | ICLR 2025 [待确认] | 2401.06066 | Fine-grained + shared experts | Medium | 2B/16B/145B; no law |
| Scaling Laws for Fine-Grained MoE | 2024 | ICML 2024 [待确认] | 2402.07871 | L(N,D,G)=c+g/G^γ+a/N^α+b/D^β; α=0.115, β=0.147, γ=0.58 | High | 64 experts; 4–8 layers; G_opt 8→16 with FLOPs |
| DeepSeek-V2 | 2024 | technical report | 2405.04434 | 236B total/21B active; MLA; 160+2 experts | Medium | Existence proof |
| DeepSeek-V3 | 2024 | technical report | 2412.19437 | 671B/37B; 256+1 experts; aux-loss-free; 14.8T tokens | Medium-high | 2.788M H800 GPU-hours |
| Joint MoE Scaling Laws | 2025 | arXiv [待确认] | 2502.05172 | L(N_act,D,Ê) with Ê saturation; E_max≈290 | High | ≤5B total/2.7B active; memory model |
| Parameters vs FLOPs | 2025 | arXiv | 2501.12370 | L(N,D,S) with sparsity penalty | Medium (abstract) | Full text not downloaded |
| Towards a Comprehensive Scaling Law of MoE | 2025/2026 | EMNLP 2026 Main | 2509.23678 | Five-factor law; G_opt≈6.78, S_opt≈0.31, N_a/N~N^−0.19 | High | 446/450 experiments; ≤9B total |

## Failure boundaries / evaluation

| Title | Year | Venue | arXiv | Law / claim | Evidence | Notes |
|---|---|---|---|---|---|---|
| Emergent Abilities of Large Language Models | 2022 | TMLR 2022 | 2206.07682 | Abilities absent in small models, unpredictable from extrapolation | Medium | Present/absent binarization; post hoc tasks |
| Are Emergent Abilities a Mirage? | 2023 | NeurIPS 2023 [待确认] | 2304.15004 | >92% BIG-Bench emergence uses discontinuous metrics | Medium-high | Metric nonlinearity + low power bundled |
| Broken Neural Scaling Laws | 2022/2023 | ICLR 2023 | 2210.14891 | Smoothly broken power law | Medium | Sharpness is representation-dependent |
| Will we run out of data? | 2022/2024 | arXiv | 2211.04325 | Full utilization 2026–2032, median 2028 | Medium | Common Crawl 130T, indexed web 510T, whole web 3100T |
| Deep Double Descent | 2019 | ICLR 2020 [待确认] | 1912.02292 | Non-monotonic test error in size/epochs/samples | Medium | Vision-centric; LLM relevance regime-specific |
| Beyond the Log-Linear Frontier | 2026 | arXiv | 2611.13534 | Three-term pre-asymptotic expansion; 5.89% holdout MAPE | Medium-high | 45 spectra; Pythia/Chinchilla/RegMix |
| Ambiguous Fits: Rashomon Effect | 2026 | arXiv | 2610.34514 | Near-optimal fits diverge; certified envelopes | Medium-high | ~74.6% gap [待确认] |
| Emergent Capabilities Arise Randomly from Sparse Attention Patterns | 2026 | arXiv | 2606.25010 | Scale-dependent hazard tied to attention patterns | Medium | Small/synthetic + Pythia |
| Claims of emergence should be grounded in information decomposition | 2026 | NeurIPS 2026 Position | 2610.28479 | PID synergy as emergence criterion | Low-medium (position) | No new experiments |
| Data-Constrained Language Model Pretraining | 2026 | arXiv | 2606.06888 | Chinchilla additive law misspecified; SoftQ; MIR ≈1.3× unique data | Medium-high | 72M–1.4B, 100M unique tokens |
| Revisiting the Scaling Properties of Downstream Metrics | 2025 | ICLR 2026 [待确认] | 2512.08894 | Direct log-accuracy power law at fixed TPP | Medium-high | Better extrapolation than two-stage |
| Prescriptive Scaling | 2026 | ICML 2026 Oral | 2602.15327 | Capability boundaries vs log FLOPs | Medium-high | 7k checkpoints 2022–2026 |

## Inference-optimal / overtraining

| Title | Year | Venue | arXiv | Law / claim | Evidence | Notes |
|---|---|---|---|---|---|---|
| Beyond Chinchilla-Optimal | 2024 | ICML 2024 | 2401.00448 | Training + inference cost; examples reduce total FLOPs 28% | Medium-high | 47 MPT 150M–6B, 10–10,000 TPP; single epoch |
| Inference Scaling Laws | 2024 | ICLR 2025 | 2408.00724 | Empirical accuracy–compute curves; Llemma-7B REBASE beats 34B; ~2× less FLOPs | Medium-high | GSM8K/MATH; task-specific |
| Scaling LLM Test-Time Compute Optimally | 2024 | ICLR 2025 | 2408.03314 | 2–4× over best-of-N; can beat 14× larger model in FLOPs-matched eval | Medium-high | PaLM 2-S*; math only |
| Test-Time Scaling Makes Overtraining Compute-Optimal | 2026 | arXiv | 2604.01411 | T² law; L=E+A/N+B/D+2NG/C_inf; k=C_inf/(2N) | Medium | <1B; 8 tasks; no memory/latency |
| The Llama 3 Herd of Models | 2024 | technical report | 2407.21783 | 405B ~39 TPP; small models ~1,000–2,000 TPP | Observational high | Existence proof; confounded |
| Gemma 2 | 2024 | technical report | 2408.00118 | 2B/9B/27B on 2T/8T/13T | Observational | Existence proof |
| Gemma 3 | 2025 | technical report | 2503.19786 | 1B/4B/12B/27B on 2T/4T/12T/14T | Observational | Existence proof |
| Gemstones: A Model Suite for Multi-Faceted Scaling Laws | 2025 | NeurIPS 2025 | 2502.06857 | Prescriptions sensitive to checkpoint selection/design | Medium | 4,000+ checkpoints ≤2B; appendix overtraining [待确认] |
| Overtrained Language Models Are Harder to Fine-Tune | 2025 | ICLR 2025 | 2503.19206 | Catastrophic overtraining: 3T OLMo-1B >2% worse after SFT than 2.3T | Medium-high | One family; mechanism incomplete |
| Kinetics: Rethinking Test-Time Scaling Laws | 2025 | arXiv | 2506.05333 | Memory-access/attention costs; smaller-model effectiveness overestimated | Medium | 0.6B–32B; hardware-specific |
| xLSTM Scaling Laws | 2026 | ICLR 2026 | 2510.02228 | L(C)=λC^−η, η≈0.047–0.050 [待确认] | Medium | 80M–7B, 2B–2T |
| LLMs as Noisy Channels: A Shannon Perspective | 2026 | ICML 2026 | 2605.23901 | Noisy-channel SNR explains U-shaped degradation; R²=0.847 [待确认] | Low-medium | Limited validation |
| What Does Language Model Overtraining Reveal About Deployment Objectives? | 2026 | NeurIPS 2026 | no arXiv ID | D∝N^0.226 [待确认] | Medium | 32 models; observational |

## Frontier scan (2025-06 to 2026-11)

| arXiv | Venue | One-line finding |
|---|---|---|
| 2602.15327 | ICML 2026 Oral | Capability boundaries from 7k checkpoints; temporal validation |
| 2611.13534 | arXiv 2026-11 | Pre-asymptotic three-term expansion; 5.89% holdout MAPE |
| 2610.34514 | arXiv 2026-10 | Certified prediction envelopes; Rashomon effect |
| 2610.28479 | NeurIPS 2026 Position | PID synergy criterion for emergence |
| 2606.25010 | arXiv 2026-06 | Emergence as scale-dependent hazard via sparse attention patterns |
| 2512.08894 | ICLR 2026 [待确认] | Direct log-accuracy law at fixed TPP |
| 2509.24012 | ICLR 2026 [待确认] | Three pass@k scaling laws; predict expensive models from cheap ones |
| 2510.13786 | ICLR 2026 [待确认] | Sigmoidal RL compute-performance curves; >400k GPU-hours |
| 2512.10858 | ICLR 2026 [待确认] | Discrete diffusion LM scaling across noise types |
| 2601.03764 | ICLR 2026 [待确认] | pass@k failure exponent is training-dependent |
| 2604.01411 | arXiv 2026-04 | T² laws; inference cost makes overtraining compute-optimal |
| 2611.02270 | arXiv 2026-11 | Hinted scaling laws below the noise floor |
| 2606.06888 | arXiv 2026-06 | SoftQ; data-constrained law; MIR ≈1.3× unique data |
| 2607.25271 | arXiv 2026-07 | Token-effectiveness function for repeated/paraphrased data |
| 2611.03590 | arXiv 2026-11 | Multi-epoch DMFT; logit averaging delays late-training deterioration |
| 2610.05591 | arXiv 2026-10 | Repeated-token pricing; value halves after critical epoch count |
| 2610.23946 | NeurIPS 2026 | Agentic RL data scaling across task/environment/trajectory |
| 2610.37648 | arXiv 2026-10 | Tool-use agent scaling law; 458,752 tasks, 849 models |
| 2609.27588 | arXiv 2026-09 | Capability manifold; bounded scaling functions + Jacobians |
| 2610.16297 | arXiv 2026-10 | SLDBench v2; active scaling-law discovery |

## Lab technical reports

| Lab | Report | arXiv | Date | Content |
|---|---|---|---|---|
| DeepSeek | DeepSeek-V3 Technical Report | 2412.19437 | 2024-12 | 671B/37B MoE; MLA; aux-loss-free; 14.8T tokens |
| Qwen | Qwen3 Technical Report | 2505.09388 | 2025-05 | 0.6B–235B dense/MoE; unified thinking modes |
| Kimi | Kimi K2: Open Agentic Intelligence | 2507.20534 | 2025-07 | 1T/32B MoE; MuonClip; 15.5T tokens; zero loss spike |
| MiniMax | MiniMax-01 | 2501.08313 | 2025-01 | 456B/45.9B; lightning attention + MoE; long context |

## Verification notes

- Every arXiv ID above was resolved against `arxiv.org/abs/<id>` by one of the four research agents on 2026-11-15.
- Venues marked `[待确认]` were not verified from primary metadata.
- Numbers marked `[待确认]` came from secondary summaries or were OCR/extraction-limited.
- Do not compare exponents across papers without matching the coordinate definition (`N_total`/`N_active`, `G` granularity vs active experts, `S` shared ratio vs sparsity, fit range, optimizer).
