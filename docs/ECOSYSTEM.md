# 学术研究 Skills 生态调研

> 调研日期：2026-11-14
> 方法：GitHub REST API 仓库/代码检索 + 网页检索；star 数取当日快照，会随时间波动。
> 目的：给本仓库的六个 skill 找同类、找可借鉴点，也作为后续选型与安装的参考清单。

## 结论速览

- 学术科研类 Agent Skill 生态已经非常丰富，从"单个方法论 skill"到"上百个 skill 的合集"、再到"端到端自动科研流水线"都有。
- 综合型合集里最主流的是 [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)——本机 `~/.claude/skills` 里的 `academic-paper`、`academic-paper-reviewer`、`academic-pipeline`、`deep-research` 就与该仓库的 skill 对应（该仓库另有 `sr-screener`）。
- 市面上"找 idea"类 skill 多为通用科研创意 + 文献查新；本仓库的 `lm-arch-bottleneck-scout` 的差异在**领域专用**的"瓶颈接力"方法论和架构谱系案例库。
- 写作类 skill 大多在"帮你写/润色"；本仓库的 `paper-writing-audit` 的差异在**只读、分阶段、不改稿**，且重点检查 `and`/分号/拆句等机械结构。
- PDF 批注类 skill 多为"新建分类高亮"或"批注回写 LaTeX"；**未检索到与本仓库 `pdf-review-highlights` 完全同类的"整句补全 + 跨行/跨公式/跨栏/跨页 + 保留原批注"实现**。

## 一、综合型：研究 → 写作 → 审稿 → 成稿

| 仓库 | Stars | 内容 | 特点 |
|---|---:|---|---|
| [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | 56.9k | 5 个 skill：`deep-research`、`academic-paper`、`academic-paper-reviewer`、`academic-pipeline`、`sr-screener` | 13-agent 深度研究、12-agent 写作、5 人评审团、10 阶段流水线；本机已安装前 4 个 |
| [pedrohcgs/claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow) | 1.7k | 105 个 SKILL.md，MIT | 经济学/实证研究模板：论文、R/Stata/Python 分析、slides、可复现性协议、质量门 |
| [LeonChaoX/qinyan-academic-skills](https://github.com/LeonChaoX/qinyan-academic-skills) | 1.0k | 187 个 SKILL.md，MIT | 中文全生命周期：文献检索、科学写作、基金、生信、临床、ML |
| [beita6969/ScienceClaw](https://github.com/beita6969/ScienceClaw) | 1.0k | 319 个 SKILL.md，MIT | 自进化 AI-for-Science agent，含 academic-deep-research、literature-search |
| [wentorai/research-plugins](https://github.com/wentorai/research-plugins) | 317 | 473 个 SKILL.md，MIT | 350+ 科研 skills + MCP 配置 |
| [tsingyuai/scientify](https://github.com/tsingyuai/scientify) | 2.3k | 18 个 skill，无 license | 端到端自动科研：idea → 实验 → 论文 |
| [zLanqing/codex-claude-academic-skills](https://github.com/zLanqing/codex-claude-academic-skills) | 6.0k | 3 个 skill | 论文阅读/PPT/Word、写作润色/审稿回复、MATLAB/Python 科学计算 |
| [delibae/claude-prism](https://github.com/delibae/claude-prism) | 1.9k | 100+ skills | 本地离线科学写作工作区（LaTeX + Python） |

## 二、把控方向 / 找 idea / 研究设计

最接近本仓库 `lm-arch-bottleneck-scout` 的一类。

| 仓库 | Stars | 相关 skill | 与本仓库的关系 |
|---|---:|---|---|
| [EvoScientist/EvoSkills](https://github.com/EvoScientist/EvoSkills) | 487 | `research-ideation`、`paper-planning`、`experiment-craft` | 思路最接近：文献 grounding → 3 方向 × 3 personas（innovator/pragmatist/critic）→ 迭代 → ELO 锦标赛 → proposal；但为通用领域，不含架构谱系 |
| [lingzhi227/agent-research-skills](https://github.com/lingzhi227/agent-research-skills) | 465 | `idea-generation`、`novelty-assessment`、`literature-review` 等 31 个 | 有 Semantic Scholar 脚本化新颖性检查，可直接借鉴 |
| [yogsoth-ai/de-anthropocentric-research-engine](https://github.com/yogsoth-ai/de-anthropocentric-research-engine) | 512 | 267 个 skill 组成研究图：`decompose-research-goal`、`classify-research-gap`、`validate-research-gap` | 把"研究方向"拆到极细粒度的 gap 分类/验证 |
| [richard-kim-79/archora-skills](https://github.com/richard-kim-79/archora-skills) | 50 | `hypothesis`、`counterargument`、`synthesis`、`validation`、`peer-review` | 假设生成 + 反方论证 + 综合，轻量 |
| [CL-ML/open-collider](https://github.com/CL-ML/open-collider) | 347 | 语义碰撞式 idea 生成 | 用远领域知识强行碰撞，产出非平凡 idea；不是 SKILL.md 格式 |
| [gaasher/Agent-Loop-Skills](https://github.com/gaasher/Agent-Loop-Skills) | 182 | `hypothesis-gen`、`literature-survey`、`ml-autoresearch`、`claim-verify` | 以"循环 + 验证门"组织研究 |
| [fcakyon/labrat](https://github.com/fcakyon/labrat) | 461 | `literature-research`、`experiment-design`、`reproduce`、`paper-check`、`rebuttal` | PhD 研究技能包，偏实验与复现 |
| [lishix520/academic-paper-skills](https://github.com/lishix520/academic-paper-skills) | 1.5k | `strategist`（规划）+ `composer`（写作） | 规划端最接近"把控方向"的轻量方案 |
| [AlphaLab-USTC/ResearchClaw](https://github.com/AlphaLab-USTC/ResearchClaw) | 136 | `paper-scout`、`idea-generator`、`paper-reader`、`paper-writer` | 小而全的"找论文 → 找 idea → 写"闭环 |
| [RUC-NLPIR/Arbor](https://github.com/RUC-NLPIR/Arbor) | 1.1k | 自主研究 agent，含 `arbor-agent-ideate` | 偏自动跑实验的 agent，不是纯 skill |

## 三、写作与审查

最接近本仓库 `paper-writing-audit` 的一类。

| 仓库 | Stars | 内容 | 相关性 |
|---|---:|---|---|
| [Master-cai/Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills) | 8.3k | ML/CV/NLP 论文写作，改编自彭思达老师公开笔记 | 写作方法最系统、传播最广 |
| [SNL-UCSB/paper-writing-skill](https://github.com/SNL-UCSB/paper-writing-skill) | 249 | 编辑原则 + 五阶段写作流水线 + voice profile | 与本仓库《写作戒律》定位最像 |
| [Boom5426/Nature-Paper-Skills](https://github.com/Boom5426/Nature-Paper-Skills) | 672 | 28 个 skill：`anti-defensive-writing`、`scientific-prose-style`、`stats-reporting-audit`、`submission-audit`、`rebuttal-response` | 与本仓库 S1 叙事立场、S5 证据链高度重叠，值得对照 |
| [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer) | 4.95k | 去除 AI 写作痕迹（NSF/NIH 基金与论文） | 偏"去 AI 味"，可补充文风检查 |
| [dvdsosa/scientific-writing-skills](https://github.com/dvdsosa/scientific-writing-skills) | 33 | 6 个 skill，蒸馏自 Stanford《Writing in the Sciences》 | 句级编辑与 IMRaD 结构 |
| [claesbackman/AI-research-feedback](https://github.com/claesbackman/AI-research-feedback) | 562 | 13 个 skill：`review-paper`、`review-paper-code`、`audit-analysis`、`review-grant` 等 | 学术审稿/审计套件 |
| [pengkangzhen/scientific-research-plugin](https://github.com/pengkangzhen/scientific-research-plugin) | 8 | `ai-tone-audit`、`hedge-audit`、`term-audit`、`paper-polishing`、`paper-review` | 细粒度审计项可参考 |
| [gulucaptain/Best-Paper-Writing-Skill](https://github.com/gulucaptain/Best-Paper-Writing-Skill) | 387 | 模仿 CVPR/ICCV/NeurIPS 最佳论文风格写摘要/引言/方法/实验 | 顶会风格化写作 |
| [hanlulong/econ-writing-skill](https://github.com/hanlulong/econ-writing-skill) | 719 | 经济学论文写作，综合 Cochrane、McCloskey 等 50+ 指南 | 领域专用写作 |
| [SyntaxSmith/nature-writing-skill](https://github.com/SyntaxSmith/nature-writing-skill) | 194 | Nature 系期刊写作，面向中文 AI/ML 研究者 | 领域/期刊专用 |

## 四、PDF 批注与论文阅读

最接近本仓库 `pdf-review-highlights` 的一类。

| 仓库 / skill | 内容 | 与本仓库的差异 |
|---|---|---|
| [pengkangzhen/scientific-research-plugin](https://github.com/pengkangzhen/scientific-research-plugin) 的 `zotero-pdf-highlighting` | 按阅读笔记五章节给 PDF 关键词做五色高亮（PyMuPDF） | 做"分类高亮"，不做整句补全 |
| [MarcusBinder/MyClaudeSkills](https://github.com/MarcusBinder/MyClaudeSkills) 的 `pdf-annotation-review` | **反向**：提取 PDF 里的高亮+评论，映射回 LaTeX 源码并应用修改 | 方向相反；不做批注创建/补全 |
| [Adhvith-Reddy1/ScAI-Reader](https://github.com/Adhvith-Reddy1/ScAI-Reader) | `.claude/skills/pdf-text-highlight` | 0 stars，规模很小 |
| [917Dhj/DeepPaperNote](https://github.com/917Dhj/DeepPaperNote) | 1.4k★，论文精读 → Obsidian 笔记 | 偏阅读与笔记 |
| [zsyggg/paper-craft-skills](https://github.com/zsyggg/paper-craft-skills) | 1.5k★，论文深度解读、漫画、速览 | 偏阅读理解 |

> 未检索到与 `pdf-review-highlights` 完全同类的"把半行高亮补全为整句、跨公式/跨栏/跨页、保留原批注"实现，这是本仓库的差异点。

## 五、索引与聚合安装

- [O0000-code/awesome-academic-skills](https://github.com/O0000-code/awesome-academic-skills) — CC0，按科研生命周期组织的索引，逐项标注 license 和运行依赖。
- [neverbiasu/awesome-research-skills](https://github.com/neverbiasu/awesome-research-skills) — CC0，151 个学术 skill 精选。
- [cosen1024/awesome-academic-skills](https://github.com/cosen1024/awesome-academic-skills) — 机器校验过的目录。
- [brycewang-stanford/lit-review-agent-tools](https://github.com/brycewang-stanford/lit-review-agent-tools) — 70+ 文献综述工具（skill / MCP / PDF 解析 / 系统综述）。
- [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)（79k★）
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)（37k★）
- [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)（~50k★）
- [paper-writing-hub](https://socket.dev/npm/package/paper-writing-hub) — npm 聚合安装器，把 8–9 个学术合集（含 ARS、CCAS、nature-skills 等）装成 32 个 Claude Code skills。

## 六、本仓库 skill 的相对位置

| 本仓库 skill | 同类生态 | 差异 / 可借鉴点 |
|---|---|---|
| [lm-arch-bottleneck-scout](../lm-arch-bottleneck-scout/) | 通用 idea generation + 文献查新 | 差异：领域专用的"瓶颈接力"方法论、五类瓶颈、12 条原语、架构谱系案例库。可借鉴：EvoSkills 的多 persona + ELO 排序、lingzhi227 的 Semantic Scholar 新颖性自检脚本 |
| [paper-writing-audit](../paper-writing-audit/) | 写作辅助 / 润色 / 审稿 | 差异：只读、分阶段、不改稿，重点在 `and`/分号/拆句等机械结构。可借鉴：Boom5426 的 `anti-defensive-writing`、`stats-reporting-audit`；pengkangzhen 的 `hedge-audit`/`ai-tone-audit` |
| [pdf-review-highlights](../pdf-review-highlights/) | 分类高亮 / 批注回写 LaTeX | 差异：整句补全、跨行/跨公式/跨栏/跨页、保留原批注、不改正文；同类最少 |
| [latex-to-docx](../latex-to-docx/) | Pandoc / LaTeX→Word 转换 | 差异：面向论文的 LaTeX→DOCX，原生 OMML 公式、表格合并恢复、Word COM 排版与渲染验收；本次调研未专门覆盖格式转换类 skill |
| [scaling-law-frontier-scout](../scaling-law-frontier-scout/) | 通用 idea generation + 文献查新 | 差异：预消化 scaling law 底座（44 篇论文卡片）、可识别性视角、代码库接地、顶会筛选；下游只做定向补搜 |
| [paper-figure-data-editor](../paper-figure-data-editor/) | 图表数据编辑 / 论文配图微调 | 差异：不改绘图脚本与测量数据，只在"取值 → 画图"之间注入 hook；浏览器内改数、像素级 roundtrip 验收、逐图回写；同类工具多偏重画图/样式 |

## 七、选型与安全提醒

- **先看 license**：不少仓库标为 `NOASSERTION` 或无 license，商用/二次分发前需确认；MIT/Apache-2.0/CC0 相对安全。
- **先看脚本**：skill 可能带 Python/Shell 脚本，安装前至少浏览 `SKILL.md` 和 `scripts/`，不要在不可信目录里直接执行。
- **star 数会波动**：本表中的数字是 2026-11-14 的快照，不代表质量；部分高 star 仓库可能是合集/营销型仓库。
- **按需安装**：合集动辄上百个 skill，全部装入会稀释触发准确率；建议只复制当前需要的 skill 目录到 `~/.claude/skills/`。

## 附：检索关键词

`claude skills academic`、`academic research skills claude`、`paper writing skill claude`、`research skills SKILL.md`、`academic research agent workflow`、`literature review agent llm`、`research idea generation llm`、`scientific writing agent`、`academic paper review agent`；代码检索：`filename:SKILL.md "research gap"`、`"research direction"`、`"academic writing"`、`"idea generation"`、`"pdf" "highlight" annotation`。
