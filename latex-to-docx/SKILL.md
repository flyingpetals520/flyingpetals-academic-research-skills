---
name: latex-to-docx
version: 1.0.0
description: "把 LaTeX 论文源文件转成可编辑的 Word（DOCX）：Pandoc 3.x 生成原生 OMML 公式，PDF 图转 PNG，表格保留结构并修复合并表头，最后用 Word COM 排版并导出校验 PDF。适用于期刊/会议论文的 LaTeX→Word 工作副本、合作者改稿、公式与图表保真转换。不是 PDF→Word 的 OCR 方案。"
metadata:
  requires:
    os: ["Windows + Microsoft Word (for format step)"]
    python: ["Pandoc >= 2.11 (3.x recommended)", "python-docx", "PyMuPDF (fitz)", "pywin32 (win32com)"]
---

# LaTeX 论文 → 可编辑 Word（DOCX）

目标：从 **LaTeX 源文件**（不是 PDF）生成一个可编辑的 Word 工作副本，公式是原生 OMML、图是可缩放图片、表是可编辑表格；同时导出一份 PDF 用于逐页验收。

**不要用 PDF→Word 的 OCR 路线**：公式会变成文字碎片或图片，符号错乱，表格结构丢失。Pandoc 读 `.tex` 才能保留结构。

本 skill 是**论文无关**的通用管线。论文特定的表格修补（特殊表头、丢失的单元格、上标）写到 `table_fixes.json` 清单里，脚本本身不改。

## 何时使用 / 不使用

**使用**：有完整 `.tex` + 图 + `.bib`；需要给合作者/审稿人一个可编辑 Word；需要保留公式与表格结构。

**不使用**：只有 PDF 没有源码；纯文字稿；不需要公式/表格保真的快速预览。这些场景不要用本管线。

## 环境与前置条件

- **Pandoc ≥ 2.11**，强烈建议 3.x。系统 PATH 里可能是很老的 1.19，先 `pandoc --version` 检查；用 `--pandoc <path>` 指定 3.x。
- Python 包：`python-docx`、`PyMuPDF`、`pywin32`（仅 Word 排版步骤需要）。
- 排版步骤需要 **Windows + 已安装的 Microsoft Word**（COM 接口）；Linux/macOS 只能做 Pandoc 转换，表格合并和 PDF 导出需另想办法（LibreOffice 保真度更差，见文末）。
- 源文件先能编译：有干净的 `.aux` 才能回填交叉引用。

## 管线总览

```text
0. 编译出干净 PDF/.aux
1. latex_to_docx.py   LaTeX 预处理 + Pandoc + DOCX 表格隔断
2. inspect_docx.py    统计/表头 dump/渲染抽查 → 写 table_fixes.json
3. format_docx.py     Word COM 排版 + 通用合并 + manifest + 导出 PDF
4. 验收               公式/图/表/引用/乱码/页数
```

所有命令以 skill 目录为基准：

```bash
SKILL=~/.claude/skills/latex-to-docx
```

## 第 0 步：编译出干净的 PDF 和 .aux

```bash
rm -f paper.aux paper.out paper.fls paper.fdb_latexmk
pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex
```

坑：旧的/损坏的 `.aux` 会让引用编号错、PDF 截断。转换前必须重新编译；`.aux` 是引用回填和图表编号的唯一可靠来源。

## 第 1 步：转换

```bash
python $SKILL/scripts/latex_to_docx.py paper.tex \
  -o paper_word.docx \
  --bib refs.bib --csl ieee.csl \
  --pandoc "D:/tools/pandoc-3.1.11/pandoc.exe" \
  --number-equations --number-captions \
  --report latex_report.json
```

脚本做的事（全部在**临时副本**上，不改源文件）：

- 从 `.aux` 回填 `\ref` / `\eqref`；找不到的记为 `??` 并写进报告。
- `figure*` → `figure`；删除 `\looseness`、`\bibliography` 等 Pandoc 不认的命令。
- `center + \captionof{table}` 提升为真正的 `table` 环境，避免整张表被当成普通段落。
- `\resizebox` 解包；`tabular*` 规范化；`\multicolumn` 展平为“文字 + 空单元”，保住行宽。
- PDF 图按 300 dpi 渲染成 PNG（支持 `page=`），扩展名缺省时自动找 `.pdf/.png/.jpg`。
- 可选：给 equation 环境补顺序编号；从 `.aux` 给 caption 补 `Table N:` / `Figure N:`。
- Pandoc 用 `--citeproc` 生成参考文献。
- DOCX 后处理：在相邻两张表之间插入一个空段落，**防止 Word 打开时把两张表粘成一张**。
- 输出统计：OMML 公式数、图片数、表格数、缺失引用/图片。

**检查报告**：缺失引用、缺失图片、`oMath`/`tables`/`images` 数量是否与源论文大致相符。此时不要急着排版，先看 `inspect_docx.py` 的表结构。

常用开关：

| 开关 | 什么时候用 |
|---|---|
| `--number-equations` | 论文按 equation 环境顺序编号，且正文引用 Eq. (n)。section 编号或 `\tag` 需手工处理 |
| `--number-captions` | 图/表 caption 没有自带编号，需要从 `.aux` 补 |
| `--fig-dpi 300` | 图很多很大时可降到 200 控制体积 |
| `--keep-temp` | 调试预处理结果时保留临时 `.tex` |
| `--reference-doc` | 有固定 Word 样式模板时传入 |

## 第 2 步：检查 DOCX 并写表格修补清单

```bash
python $SKILL/scripts/inspect_docx.py paper_word.docx --tables \
  --json docx_report.json
```

看三件事：

1. **公式**：`oMath` 数量是否接近源文件中的公式数；显示公式是否成段（`oMathPara`）。
2. **表格**：每张表的行列数、前三行表头。合并丢失的表头通常表现为“同一个词重复三遍”或“第一个单元有字、后面空着”。
3. **caption**：数量是否与源文件一致；相邻表是否被空段落隔开。

对通用合并规则处理不了的表，写 `table_fixes.json`（模板见 `templates/table_fixes.example.json`）：

```json
{
  "tables": [
    {
      "match": {"cols": 7, "contains": ["Method", "SDR"]},
      "merges": [
        {"row": 1, "col_start": 2, "col_end": 4, "text": "Group A"},
        {"row": 1, "col_start": 5, "col_end": 7, "text": "Group B"}
      ],
      "vmerges": [
        {"row_start": 2, "row_end": 3, "col": 1}
      ],
      "cells": [
        {"row": 2, "col": 5, "text": "10^-4"}
      ]
    }
  ]
}
```

- `match.cols` + `match.contains` 定位表格，**不要按表序号写死**；插图表后序号会变。
- 行/列从 1 开始。
- `merges` 横向合并，`vmerges` 纵向合并，`cells` 覆盖单元格文字（用于 Pandoc 丢掉的数学值、需要补的上标等）。
- 纵向合并后 Word 只保留首格文字；需要的话在 `text` 里重写。

## 第 3 步：Word 排版

```bash
python $SKILL/scripts/format_docx.py paper_word.docx \
  -o paper_word_final.docx \
  --manifest table_fixes.json \
  --pdf paper_word_final.pdf
```

脚本做：

- 页边距、正文 Times New Roman 10 pt、标题层级、正文两端对齐。
- 图按文本宽度缩放（高瘦图更窄），表宽 100%、加边框、表头加粗并跨页重复、单元格 8.5 pt、行不跨页。
- **通用表头合并**：前三行内，非空非数字单元格后面跟着空单元格或相同文字时，判定为组表头并合并（从右往左合并，避免索引错位）。
- 应用 `table_fixes.json` 的显式合并/覆盖。
- 页脚页码、标题居中、导出 PDF（目标 PDF 被占用时自动改名）。

`--no-auto-merge` 可关闭通用合并（表格数据里本来就有重复文字时用）；`--header-rows` 控制扫描行数。

## 第 4 步：验收（必做）

```bash
python $SKILL/scripts/inspect_docx.py paper_word_final.docx --tables \
  --json final_report.json

python $SKILL/scripts/inspect_docx.py paper_word_final.docx \
  --pdf paper_word_final.pdf --pages 1,3,7,12 --outdir renders
```

**XML 统计通过不等于渲染正确。** 必须逐页看渲染图，重点：

- 公式：符号、上下标、分式、矩阵、多行对齐；编号是否连续。
- 图：是否缺图、是否被拉伸、caption 是否紧跟图。
- 表：表头合并、纵向合并、数字列、负号、上下标、跨页表头。
- 引用：正文是否残留 `??`、`[?]`、原始 `\cite`。
- 页码与页数：Word 页数通常比 LaTeX 多，不是内容缺失；确认总页数合理。

验收清单：

- [ ] `oMath` / 图片 / 表格数与源文件相符（允许少量合理差异）
- [ ] 无 `??`、`\begin{`、`\cite`、`\ref` 残留
- [ ] 所有图存在，宽高比未被破坏
- [ ] 每张表表头正确，合并单元格无重复文字
- [ ] 公式编号与正文引用一致
- [ ] 源 `.tex` 未被修改（只改临时副本/输出 DOCX）

## 重难点方法（摘要）

细节见 `references/hard-elements.md`，这里给决策要点。

### 公式

1. **永远优先原生 OMML**：Pandoc 直接从 LaTeX 生成，不经过图片。
2. 编号：Pandoc 不保留 LaTeX 编号。顺序编号用 `--number-equations`；section 编号、`align` 子编号、`\tag` 需手工核对或写成固定文本。
3. 宏：Pandoc 能展开文档内 `\newcommand` 的简单宏；复杂宏先展平，或把宏定义复制到临时副本的导言区。
4. 复杂图（TikZ、pstricks）无法转 OMML：单独渲染成 PDF→PNG，作为图片插入，并在交付说明里注明。
5. 验收看渲染，不看 `<m:oMath>` 计数。

### 图

1. DOCX 不能嵌 PDF；先渲染 PNG（300 dpi），保留原始宽高比。
2. `figure*` 转 `figure`；Word 里按文本宽度缩放。
3. `subfigure/minipage` 多面板：Pandoc 往往拆散。优先把多面板合成一张 PNG，或接受分开放置并检查 caption。
4. 扩展名缺省、`page=` 多页 PDF、EPS 图，都要在预处理阶段解决；找不到的图列入报告，不要静默跳过。
5. 图注里的数学可能变成 OMML；检查图注是否完整。

### 表

1. **合并结构是最大坑**：`\multicolumn` 在 Pandoc 里只保留文字。预处理展平保行宽，Word 端按“重复/空表头”通用规则恢复；特殊表用 manifest。
2. **相邻表会被 Word 自动粘成一张**：DOCX 生成后、Word 打开前，在两张表之间插入空段落（脚本已做）。
3. `\resizebox`、`tabular*`、`p{}` 列、`@{\extracolsep{...}}` 会让 Pandoc 把表读成段落；预处理统一成普通 `tabular`。
4. 表内数字若是数学模式，会变成 OMML；python-docx 的 `.text` 读不到负号/公式，**不要据此判断“数字丢了”**，以 Word 渲染为准。
5. `\multirow` 可能重复文字；用 manifest 的 `vmerges` 或 `cells` 修正。
6. 表 caption 放在 `minipage`/`\captionof` 里容易丢：转换前提升为 `table` 环境，转换后核对 caption 数量。
7. 列宽：Word 自动布局即可；数字列可手工右对齐（本脚本默认左对齐以保证稳定）。

### 交叉引用与文献

- `\ref/\eqref` 必须在 Pandoc 前从 `.aux` 回填；`--citeproc` + `.bib` + `.csl` 生成参考文献。
- 没有 CSL 时 Pandoc 用默认样式，编号可能和期刊要求不同；投稿用 Word 只是工作副本，引用格式以 LaTeX 版为准。

## 常见故障速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 公式变成文字碎片/乱码 | 用了 PDF→Word 或旧版 Pandoc | 改用 LaTeX 源 + Pandoc 3.x |
| 缺图 | PDF 图未转 PNG / 路径错 | 看 `latex_report.json` 的 `missing_figures`；用 `--fig-dpi` 重跑 |
| 两张表粘在一起 | Word 打开时自动合并 | 确认 DOCX 中两表间有段落；`separate_adjacent_tables` 是否执行 |
| 表头错位/重复 | `\multicolumn` 被展平 | 通用合并 + `table_fixes.json` |
| 表格里负号/数值“丢了” | 数学模式是 OMML，`.text` 不显示 | 看渲染；需要时用 manifest 覆盖 |
| `??` | `.aux` 过期或 label 不存在 | 重新编译；检查 label；看 `missing_refs` |
| 排版脚本报“只读文件” | 目标 PDF 被阅读器占用 | 关闭阅读器；脚本自动改名 |
| Word COM 打开失败 | 相对路径 | 一律用绝对路径（脚本已处理） |
| 公式编号错 | LaTeX 用 section/align 编号 | 关闭 `--number-equations`，手工核对 |
| 页数变多 | Word 排版差异 | 正常；确认内容与图表完整即可 |

## 其他平台

没有 Microsoft Word 时：

- Pandoc 转换步骤仍可用（Windows/macOS/Linux）。
- 表格合并、图宽、边框、PDF 导出需要另写 LibreOffice/UNO 或 python-docx 版本；保真度低于 Word COM，公式仍是 OMML，但表格合并更不可控。
- 本 skill 的脚本不假装跨平台：`format_docx.py` 明确依赖 Windows + Word。

## 硬约束

1. **不改源 `.tex`**；所有预处理在临时副本上，结束删除（`--keep-temp` 除外）。
2. **不把公式转成图片**，除非原始内容是 TikZ 等无法转 OMML 的图。
3. **不以 XML 计数代替渲染验收**。
4. **论文特定修复写进 manifest**，不要改脚本；这样下一篇文章可以直接复用。
