# 学术研究 Skills 合集

个人维护的学术研究 skill 集合，面向 Claude Code（以及其它读取 `SKILL.md` 约定的 Agent）。每个 skill 是一个独立文件夹，包含一份 `SKILL.md`（触发条件与工作流），以及可选的 `references/`（方法论与案例库）、`scripts/`（辅助脚本）、`templates/`（报告模板）。

四个 skill 覆盖学术研究中的四个环节：**找方向 / 写论文 / 改批注 PDF / 转可编辑 Word**。

## Skills 一览

| Skill | 用途 | 典型场景 |
|---|---|---|
| [lm-arch-bottleneck-scout](lm-arch-bottleneck-scout/) | LLM 架构与训练算法的瓶颈挖掘、创新点发现 | "这个方向下一步该做什么""帮我找一个 research idea" |
| [paper-writing-audit](paper-writing-audit/) | 论文写作分阶段审查（只报告、不改稿） | "审查这篇论文的写作""检查长句和分号" |
| [pdf-review-highlights](pdf-review-highlights/) | PDF 整句高亮批注的创建与补全 | "给这篇论文加批注""把高亮补成整句" |
| [latex-to-docx](latex-to-docx/) | LaTeX 论文转可编辑 Word（DOCX） | "给合作者一份可编辑 Word""公式和表格要保真" |

## 各 skill 说明

### 1. lm-arch-bottleneck-scout — 架构瓶颈挖掘与创新发现

把"找创新点"工程化为一场**瓶颈接力**：每篇论文解决上一代的一个具体瓶颈，同时引入一个新瓶颈；下一代论文从新瓶颈出发。

五步工作流：

1. 确定谱系坐标（残差流 / 稀疏注意力 / 线性注意力 / 优化器 / 嵌入）
2. 用五类瓶颈来源解剖当前前沿（表达、稳定性、成本-复杂度、硬件匹配、尺度外推）
3. 用十二条解决动作原语匹配候选解法（参数化、约束化、升维/加流、稀疏化、压缩化、解耦化、混合化、缓存复用、初始化手术、硬件协同、数学证书、换轴）
4. 生成可证伪假设，并用五问筛选
5. 按报告模板输出"瓶颈 → 动作 → 新瓶颈"分析

附带资料：

- `references/bottleneck-taxonomy.md`：五类瓶颈来源 + 18 条启发式提问清单
- `references/invention-primitives.md`：12 条解决动作原语及选择规则
- `references/case-library.md`：HC/mHC/xHC、NSA/DSA/CSA、DeltaNet/KDA、Muon 等真实论文案例

适合读论文找 idea、梳理某个组件的改进脉络、把一批论文写成分析报告。

### 2. paper-writing-audit — 论文写作分阶段审查

按《写作戒律》对论文做**只读审查**：输出逐条问题报告，不改 `.tex` / `.docx`。

- 分阶段检查：S1 叙事立场 → S2 文体与数字 → S3 句子机械结构与同义拆句 → S4 公式/术语/括号 → S5 跨节一致性 → S6 复检
- 重点排查：`and` 过多、分号堆叠、分句碎句并列造成的长句，并给出可执行的同义拆句方案
- 严重度分级 P0 / P1 / P2，报告使用 `templates/report_template.md`
- `scripts/scan_sentences.py`：从 LaTeX 生成候选长句（只做分诊，不做判定）
- 若同环境装有 `pdf-review-highlights`，可把报告自动转成整句高亮批注 PDF

### 3. pdf-review-highlights — PDF 整句高亮批注

在论文 PDF 上创建或补全 review highlights，全程不修改 PDF 正文：

- **新建批注**：半透明高亮 + 右边距便签，按 P0 / P1 / P2 配色，批注中写中文问题说明
- **补全高亮**：把只覆盖半行的旧高亮扩展到完整句子；跨行、跨公式、跨栏、跨页都能连续覆盖
- 保留原有批注文字、便签图标、颜色与不透明度；自动备份原文件
- 默认适配 CVPR/LaTeX 模板（NimbusRomNo9L，9.9–10.1 pt），其它模板可调字体/字号参数

脚本：

- `scripts/add_review_annotation.py`：按文本查找添加一处高亮 + 便签
- `scripts/complete_sentence_highlights.py`：把所有既有高亮补全为整句（支持 `--dry-run --report` 预检）

### 4. latex-to-docx — LaTeX 论文转可编辑 Word

从 **LaTeX 源文件**（不是 PDF）生成可编辑的 Word 工作副本，适合给合作者/审稿人改稿：

- Pandoc 3.x 生成**原生 OMML 公式**，不经过图片；PDF 图按 300 dpi 转 PNG
- 保留表格结构，自动恢复合并表头；论文特定的表格修补写进 `table_fixes.json`
- 从 `.aux` 回填 `\ref` / `\eqref`，用 `.bib` + CSL 生成参考文献
- Word COM 排版（Windows + Word）：页边距、字体、图表缩放、表头跨页重复、页码，并导出 PDF 验收
- 硬约束：不改源 `.tex`，不把公式转图片，不以 XML 计数代替渲染验收

脚本：

- `scripts/latex_to_docx.py`：LaTeX 预处理 + Pandoc 转换 + DOCX 表格隔断
- `scripts/inspect_docx.py`：统计公式/图/表、dump 表头、渲染抽查
- `scripts/format_docx.py`：Word COM 排版、通用表头合并、应用 manifest、导出 PDF
- `templates/table_fixes.example.json`：表格修补清单模板


## 目录结构

```text
flyingpetals-academic-research-skills/
├── lm-arch-bottleneck-scout/
│   ├── SKILL.md
│   └── references/
├── paper-writing-audit/
│   ├── SKILL.md
│   ├── references/
│   ├── scripts/
│   └── templates/
├── pdf-review-highlights/
│   ├── SKILL.md
│   └── scripts/
└── latex-to-docx/
    ├── SKILL.md
    ├── references/
    ├── scripts/
    └── templates/
```

## 使用方式

Claude Code 会自动发现 `~/.claude/skills/<skill-name>/SKILL.md`。克隆后把需要的文件夹复制进去：

```bash
git clone https://github.com/flyingpetals520/flyingpetals-academic-research-skills.git
cp -r flyingpetals-academic-research-skills/lm-arch-bottleneck-scout ~/.claude/skills/
cp -r flyingpetals-academic-research-skills/paper-writing-audit ~/.claude/skills/
cp -r flyingpetals-academic-research-skills/pdf-review-highlights ~/.claude/skills/
cp -r flyingpetals-academic-research-skills/latex-to-docx ~/.claude/skills/
```

也可以只拷单个 skill。其它支持 `SKILL.md` 约定的 Agent，按各自的 skills 目录放置即可。

## 环境依赖

- `pdf-review-highlights`：Python + PyMuPDF ≥ 1.22（`pip install pymupdf`）
- `paper-writing-audit`：`scan_sentences.py` 仅使用 Python 标准库
- `lm-arch-bottleneck-scout`：纯方法论，无额外依赖
- `latex-to-docx`：Pandoc ≥ 2.11（推荐 3.x）+ `python-docx`、`PyMuPDF`、`pywin32`；排版步骤需要 Windows + Microsoft Word

## 联动关系

```text
paper-writing-audit  ──生成批注清单──▶  pdf-review-highlights
     （写作问题报告）                      （整句高亮批注 PDF）
```

`paper-writing-audit` 检测到环境中有 `pdf-review-highlights` 时，会把审查结果自动转成批注 PDF。
