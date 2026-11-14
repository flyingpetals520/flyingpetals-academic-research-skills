---
name: pdf-review-highlights
version: 1.0.0
description: "在论文 PDF 上创建或补全整句高亮批注（review highlights）：把只覆盖半行的既有高亮扩展到完整句子，跨行、跨公式、跨栏、跨页都能正确覆盖；保留原批注文字、便签图标、颜色与不透明度，绝不改动 PDF 正文。适用于 LaTeX/CVPR 风格论文的审稿批注、合作者批注、批注覆盖率检查。"
metadata:
  requires:
    python: ["PyMuPDF >= 1.22"]
---

# PDF 整句高亮批注（review highlights）

在论文 PDF 上做两类事：

1. **新建批注**：给问题句子加半透明底色高亮 + 右边距便签图标，批注里写中文问题说明，按严重程度配色。
2. **补全高亮**：已有高亮往往只标了句子的一行或一个片段。把每处高亮扩展到它所在的**完整句子**，跨行、跨公式、跨栏、跨页都要连续覆盖；不动批注文字，不动正文。

配套脚本在 `scripts/`：

- `add_review_annotation.py`：按文本查找添加一处高亮 + 便签。
- `complete_sentence_highlights.py`：把所有既有高亮补全为整句；可先 `--dry-run --report` 检查。

## 何时使用 / 不使用

**使用**：给论文 PDF 加审稿批注；把“只标了半句”的高亮补全；检查批注覆盖是否完整；给合作者发带批注的 PDF。

**不使用**：修改 PDF 正文内容；把 Word 转 PDF；提取 PDF 文本做其它分析。这些不归本 skill。

## 环境

- Python + PyMuPDF（`fitz`）。本机实测 1.22.5；新版 API 略有差异，见“踩坑”。
- Windows 路径可用 `/` 或 `\\`；脚本内部一律 `os.path.abspath`。
- 先用 `page.get_text("dict")` 抽一页，确认正文的**字体名和字号**。默认值针对 CVPR/LaTeX 模板（`NimbusRomNo9L`，9.9–10.1 pt）；别的模板必须改参数，否则正文行会被过滤光或混入图注。

## 一、批注的语义约定

沿用本组论文批注的约定，合作者已经熟悉：

| 颜色 | 预设名 | 用途 | subject 示例 |
|---|---|---|---|
| 红 | `red` | P0：长句、定义堆叠、where 连续定义 | `P0 长句/定义堆叠` |
| 橙 | `orange` | P1：两层从句、ranges from...to... 嵌套、长枚举 | `P1 长句/嵌套` |
| 琥珀 | `amber` | P2：偏长但结构尚可，酌情拆 | `P2 偏长` |
| 棕 | `brown` | 分号密集、两个独立判断塞一句 | `分号密集短句` |
| 黄 | `yellow` | 短句信息密度高、引用密集 | `短句信息密度高` |

- 高亮不透明度 `0.38`，`title = "Writing review"`。
- 每处批注 = 一个 Highlight（带 `content`，即批注文字）+ 一个 Text 便签（同样 `content`，放在右边距）。便签是读者点开的入口，**补全高亮时不要删便签**。
- 批注措辞只描述问题，不改原文。

## 二、新建一处批注

在句子的**第一行**里选一小段唯一文本作为锚点（不要拿整句，跨行搜索容易失败）：

```bash
python scripts/add_review_annotation.py paper.pdf --page 3 \
  --find "The injected update is" --color red \
  --subject "P0 长句/定义堆叠" \
  --comment "P0：约 72 词，两个 where，且夹两个公式；建议拆成 Z_t 定义、投影定义、符号说明三部分。"
```

脚本会：`search_for` 定位 → 建多行高亮（若锚点本身跨行）→ 设颜色/透明度/批注 → 在右边距加便签 → 自动备份并保存。

把所有要批注的句子加完后，**再跑一次补全脚本**，让每处都覆盖整句。

## 三、补全整句高亮（核心）

```bash
# 先干跑，输出每处批注最终覆盖的句子，人工过一遍
python scripts/complete_sentence_highlights.py paper.pdf --dry-run --report spans.json

# 确认后写回（自动备份 paper_backup.pdf）
python scripts/complete_sentence_highlights.py paper.pdf

# 或另存
python scripts/complete_sentence_highlights.py paper.pdf --out paper_full.pdf
```

### 算法步骤

1. **盘点批注**：遍历每页 `page.annots()`，只取 `type[1] == "Highlight"`；记录 `rect / content / subject / title / colors / opacity`。
2. **抽正文行**：
   - `page.get_text("rawdict")`，逐 line 取 chars 和 bbox。
   - 只保留含正文字体（默认 `NimbusRomNo9L`）且字号在 9.4–10.9 的行；正文 9.9–10.1，粗体小标题与正文同字号混合在一行内，仍然保留。
   - 丢掉：页眉页脚（`y<60` / `y>820`）、行号（`x1<50`）、标题（11–12 pt）、图注（9.0 pt）、表格（8 pt）、图内坐标标签、纯公式行（无正文字体）、单独成行的公式编号 `(12)`。
3. **判断版式**：正文若大量行宽 >350 pt，判为单栏附录；否则按 `x<=300` / `x>=305` 分左右栏。单栏附录不能按双栏切，否则正文本行两边都不落，批注会锚到图内标签上。
4. **拼全局字符流**：按阅读顺序（每页左栏→右栏，或单栏整页）把行首尾相接，行间补一个空格；记录每行在全局串里的 `[start, end)` 和每个字符的 bbox。**公式行不进流**，于是被公式打断的句子在流里自然连续。跨栏、跨页也靠这个全局流解决（例：第 5 页 “The generator exposes … their modulation” 接右栏 “and bandwidth …”）。
5. **锚点映射**：拿旧高亮 rect 与该页正文行求交，取重叠面积最大的行；再取字符中心落在 rect 内的第一个/最后一个字符，得到全局下标 `a`。
6. **找句子边界**：
   - 向后扫描：`[.!?]` + 空格 + 大写字母/引号才算句末；**排除后面跟 `(` `[` 的情况**（`Eq. (9)`、引文 `[12]` 不是句末），数字也不算句首（`Fig. 7` 不切）。
   - 向前扫描：从 **`a+1`** 开始，不是从高亮末尾开始。旧高亮可能已经把句号包含进去了，从末尾扫会直接跳进下一句。
   - 高亮若从句子中间开始，向后会回到句首；反之亦然。
7. **生成 quads**：对句子覆盖的每一行，取字符 bbox 的并集，上下各加 0.5 pt；同一行被行内公式切成两段时，两段各出一个 quad。一个 Highlight annot 可以带多个 quad（整页一次创建），跨页则每页一个。
8. **按批注合并**：同一页、同一 `content`、同一 `subject` 的多处高亮是同一段话（常被公式切成三段）。把它们的句子区间合并（`next.start <= current.end + 2` 即视为连续），只生成一组新高亮，避免同一句叠三层颜色。便签图标原样保留。
9. **替换**：删除旧 Highlight（`page.delete_annot(annot)`），按原颜色、透明度、subject、title、content 新建。
10. **保存**：见踩坑 1。

### 验收清单

- 高亮组数 = 批注条数（例：21 条批注 → 21 个 Highlight；便签数不变）。
- 逐页渲染抽查（`page.get_pixmap(dpi=150).save(...)`），重点看：跨行句、公式打断的句子、跨栏句、单栏附录。
- 正文未变：改写前后对每页 `page.get_text("text")` 做比较（只应看到批注，不应有文本差异）。
- 备份文件存在；原文件仍可正常打开。

## 四、踩坑（都实际踩过）

1. **PyMuPDF 不允许非增量保存回原路径**：`doc.save(原路径)` 报 `save to original must be incremental`。解决：先存 `<out>.tmp`，`doc.close()`，再 `os.replace(tmp, out)`；覆盖前 `shutil.copyfile` 备份。
2. **Annot 对象会 orphaned**：`doc[pno].annots()` 里拿到的 Page 是临时对象，循环结束后 Annot 的 parent 被回收，再访问 `annot.info` 就报 `orphaned object: parent is None`。解决：一开始 `pages = [doc[i] for i in range(len(doc))]`，全程持有 Page 引用。
3. **`fitz.Quad(rect)` 在 1.22.5 会抛 `Point: bad args`**。多行高亮要传四元组：
   ```python
   quads = [(fitz.Point(r.x0, r.y0), fitz.Point(r.x1, r.y0),
             fitz.Point(r.x0, r.y1), fitz.Point(r.x1, r.y1)) for r in rects]
   page.add_highlight_annot(quads=quads)
   ```
4. **`annot.get_text()` 对这种多 quad 高亮返回空串**。不要用它验收；按 `annot.vertices`（每 4 个点一个 quad）反查相交的行文本，或直接用脚本的 `--report`。
5. **`rawdict` 的 span 没有 `"text"` 键**，文本要 `"".join(ch["c"] for ch in span["chars"])`。用 `dict` 模式取字号/字体，用 `rawdict` 取字符 bbox。
6. **行号会被当成正文**：LaTeX 投稿 PDF 左边距有 `081` 这类行号，字体 `NimbusSanL-Bold` 8 pt，`x1<50`。不过滤的话会进入阅读流，句子边界全乱。页眉 `CVPR 2027 Submission...` 用 `y<60` 过滤。
7. **图注/表格/公式不能进正文流**：图注 9.0 pt、表格 8 pt、标题 11–12 pt，用字号一刀切掉；纯公式行没有任何 `NimbusRomNo9L` span，用字体切掉；单独成行的公式编号用正则 `^\(\d+\)$` 丢掉。正文里夹行内公式的行保留，整行涂底色是合理的。
8. **双栏页与单栏附录不能用同一套切分**：附录正文行宽接近 495 pt（x 从 58.5 到 553.5），按双栏切会两边都不落，锚点会跑到图的坐标标签上。先按“宽行占比”判版式。
9. **同一视觉行可能被拆成多个 line 段**（行内公式/上下标），y 相同、x 相邻。排序键用 `(round(y,1), x)`，段间拼空格；quads 分段生成，避免一行被涂成一整条宽矩形。
10. **句末判断的特例**：`Eq. (9)`、`Appendix D.2`、`Fig. 7`、`[12]`、小数 `77.6M`、`\alpha=0.01` 都不能切句。规则：标点后必须是空格，再下一个非空字符必须是大写字母或引号；`(`、`[`、数字一律不算句首。
11. **旧高亮已经含句末标点**：向前扫描必须从锚点起点 `a+1` 开始（见算法第 6 步），否则会漏掉本句句号、把下一句也涂上。
12. **同一批注的多段高亮要合并**：例如 “where” 定义段被两个公式切成三处高亮，各自扩展后区间相同；不合并会叠三层颜色、生成三个高亮 annot。按 `(page, content, subject)` 分组并合并相邻区间。
13. **便签不能删**：便签（Text annot）是批注入口；只替换 Highlight，保留 Text 的位置和内容。
14. **不同模板字体不同**：IEEE、ACM、Springer 的正文不是 Nimbus。先 `get_text("dict")` 看字体名/字号，再传 `--font-substr`、`--size-min`、`--size-max`；否则脚本会报 “no highlight annotations found” 或覆盖错行。
15. **不要改正文**：本流程只增删 annots；`page.get_text("text")` 前后一致是硬验收条件。不要为了“好看”重排 PDF。

## 五、脚本参数速查

`complete_sentence_highlights.py`

| 参数 | 默认 | 说明 |
|---|---|---|
| `pdf` | 必填 | 输入 PDF |
| `--out` | 覆盖输入 | 输出路径；与输入相同则走 tmp 替换 |
| `--backup` | `<stem>_backup.pdf` | 覆盖前备份（已存在则不覆盖备份） |
| `--font-substr` | `NimbusRomNo9L` | 正文字体名子串 |
| `--size-min` / `--size-max` | 9.4 / 10.9 | 正文字号范围（pt） |
| `--report` | 无 | 输出每处批注最终覆盖句子的 JSON（UTF-8） |
| `--dry-run` | 关 | 只分析不写回 |

`add_review_annotation.py`

| 参数 | 说明 |
|---|---|
| `--page` | 1-based 页码 |
| `--find` | 目标行上的短唯一片段 |
| `--comment` | 批注中文说明 |
| `--subject` | 分类，如 `P0 长句/定义堆叠` |
| `--color` | `red / orange / amber / brown / yellow` |
| `--no-note` | 不加右边距便签 |
| `--out` | 输出路径（默认覆盖输入，自动备份） |

## 六、最小复现命令

```bash
# 1) 给几处句子加批注（逐条）
python scripts/add_review_annotation.py paper.pdf --page 2 \
  --find "Delta-rule linear attention ranges" --color orange \
  --subject "P1 长句/嵌套" \
  --comment "P1：ranges from ... to ..., which ..., and ..., which ...；两层从句，建议拆成两句。"

# 2) 干跑检查每处最终覆盖的整句
python scripts/complete_sentence_highlights.py paper.pdf --dry-run --report spans.json

# 3) 正式补全并写回（自动备份）
python scripts/complete_sentence_highlights.py paper.pdf

# 4) 抽查
python -c "import fitz; d=fitz.open('paper.pdf'); print(sum(1 for p in d for a in (p.annots() or []) if a.type[1]=='Highlight'))"
```
