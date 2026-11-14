# 重难点：公式、图、表的转换方法

本文是 `latex-to-docx` 的深挖手册。原则：**从 LaTeX 源转，不从 PDF 转**；公式要原生 OMML，图要保比例，表要保结构。

---

## 一、公式（Equations）

### 1.1 为什么必须是 OMML

Pandoc 读 `.tex` 时把 `$...$`、`equation`、`align` 等直接翻译成 Word 的 Office Math（`<m:oMath>` / `<m:oMathPara>`）。这是可编辑的 Word 公式，不是图片。检查方法：

```python
# document.xml 中
<m:oMath>       # 行内公式
<m:oMathPara>   # 独立成段的显示公式
```

如果 DOCX 里公式是图片（`w:drawing` 包着数学），说明走了 PDF 路线或用了错误的转换器，必须重来。

### 1.2 常见 LaTeX 结构

| LaTeX | Pandoc→OMML | 注意事项 |
|---|---|---|
| `$x_t$` | 行内公式 | 正常 |
| `\begin{equation}...\end{equation}` | 显示公式 | **编号会丢**，见 1.3 |
| `align` / `aligned` | 多行对齐 | 检查换行与对齐点 |
| `cases` | 分段函数 | 检查左花括号 |
| `\frac`、`\sqrt`、`\sum`、`\prod` | 正常 | 上下限位置可能变化 |
| `\text{...}` | 正体文字 | 大量 `\text` 说明公式里塞了解释，按写作规范应移到正文 |
| `\operatorname{...}` | 正常 | 检查是否变成斜体 |
| `\bm`、`\boldsymbol` | 粗斜体 | 复杂宏可能失败 |
| `\newcommand` | 文档内简单宏可展开 | 复杂宏先展平 |
| `TikZ`、`pstricks`、`chemfig` | **无法转 OMML** | 单独渲染成图，见 1.5 |

### 1.3 公式编号

Pandoc 故意丢弃 LaTeX 的公式编号。分四种情况：

1. **顺序编号**（全篇 equation 环境，1,2,3…）  
   用 `--number-equations`：脚本给每个 `equation` 末尾追加 `\quad (n)`。转换后核对正文 `Eq. (n)` 是否对得上。
2. **按节编号**（2.1, 2.2…）  
   不要用顺序编号。要么在临时副本里把编号写成固定文本（从 PDF/`.aux` 读取），要么关闭编号、在 Word 里手工补。交付时在报告中注明。
3. **align 多行共享一个编号**  
   Pandoc 会把整个 align 当一个显示公式；编号只能手工加在整段末尾。若每行都要编号，先把 align 拆成多个 equation（会改变排版，谨慎）。
4. **`\tag{...}` 自定义编号**  
   Pandoc 可能保留也可能丢失；转换后在 Word 里核对，必要时用 `\quad \tag` 的文本替代。

### 1.4 宏与自定义命令

- 文档导言区的简单 `\newcommand{\x}{...}`，Pandoc 的 LaTeX reader 通常能展开。
- 参数宏、带可选参数的宏、依赖 `\ifthenelse` 的宏，Pandoc 可能失败。
- 处理顺序：
  1. 在临时副本里把宏定义集中复制到 `\begin{document}` 之前；
  2. 仍失败则用脚本/手工把宏替换成展开形式；
  3. 最后才考虑把该公式渲染成图片（会失去可编辑性）。

### 1.5 无法转 OMML 的公式

TikZ、电路图、复杂交换图、化学式等：

1. 在 PDF 中定位该公式所在页/区域；
2. 用 PyMuPDF 以 300–400 dpi 裁剪成 PNG；
3. 在临时 `.tex` 里用 `\includegraphics` 替换该段；
4. 在交付说明中列出“这些公式是图片”，避免合作者误以为可编辑。

### 1.6 公式验收

- 逐页看渲染图，不看计数。
- 检查：上下标、分式嵌套、求和上下限、矩阵括号、多行对齐、编号连续性。
- 检查正文引用：`Eq. (3)` 是否指向正确公式。
- 检查行内公式是否被拆成两行或丢失空格。

### 1.7 公式故障速查

| 现象 | 处理 |
|---|---|
| 公式变成普通文字 `$x$` | Pandoc 太旧或 `--mathml` 之类参数错；用 3.x 默认 |
| 公式是图片 | 走了 PDF/OCR 路线；回到 `.tex` |
| 编号全丢 | 用 `--number-equations` 或手工补 |
| 编号错位 | section 编号/`\tag`/align；关闭自动编号，人工核对 |
| 宏未展开 | 展平宏或复制宏定义到临时文件 |
| 符号错（如 `\mathbb`） | 检查 OMML 字体；必要时改为 `\mathrm` 或图片 |

---

## 二、图（Figures）

### 2.1 DOCX 不能嵌 PDF

Pandoc 遇到 `\includegraphics{fig.pdf}` 无法把 PDF 嵌入 DOCX。处理：

1. 用 PyMuPDF 把 PDF 第 1 页渲染成 PNG（300 dpi，白底）；
2. 多页 PDF 用 `page=` 选项选择页；
3. 重写临时 `.tex` 中的路径为 PNG；
4. 找不到图时报告，不能静默跳过。

```python
import fitz
doc = fitz.open("fig.pdf")
doc[0].get_pixmap(dpi=300, alpha=False).save("fig.png")
```

### 2.2 路径与扩展名

- LaTeX 允许 `\includegraphics{fig}` 自动找 `fig.pdf/.png/.jpg`；预处理要模拟这个解析顺序。
- 相对路径以主 `.tex` 所在目录为基准，不是当前工作目录。
- 文件名含空格/中文时，Pandoc 通常能处理，但路径要加引号或统一改成 ASCII 临时名。

### 2.3 figure* 与多面板

- `figure*`（跨双栏）→ `figure`；Word 里按文本宽度缩放。
- `subfigure`、`minipage` 并排多面板：Pandoc 往往拆成独立图片/段落，caption 也会散。
  - 首选：在绘图阶段把多面板合成一张 PNG，再插入；
  - 次选：接受分开的图片，逐张检查顺序与 caption；
  - 不要指望 Word 里自动恢复 LaTeX 的 (a)(b)(c) 布局。
- 图的宽高比必须保持；脚本按高度/宽度比选择目标宽度。

### 2.4 图注

- 图注中的数学会变成 OMML，检查是否完整。
- 图注里的 `\ref` 在预处理阶段已回填；若图注引用表号，检查编号。
- 图注过长时 Word 可能跨页；`Keep with next` 只对表格做了，图注需要人工检查。

### 2.5 EPS / 其它格式

- DOCX 不支持 EPS。用 `epstopdf`、Ghostscript 或 ImageMagick 转 PDF，再转 PNG。
- 透明背景的 PNG 在 Word 中可能显示异常；渲染时用白底（`alpha=False`）。

---

## 三、表（Tables）

表是最容易失真的部分。核心认识：**Pandoc 保留单元格文字，但不保留 LaTeX 的合并结构**；Word 又会自动合并相邻表格。所以需要“LaTeX 预处理 + DOCX 后处理 + Word 端合并 + 清单修补”四层。

### 3.1 转换链路

```text
LaTeX tabular
  → 预处理（展开 resizebox/tabular*，展平 multicolumn，规范列格式）
  → Pandoc 生成 Word 表（文字在、合并没有）
  → DOCX 后处理（相邻表之间插段落，防 Word 粘表）
  → Word COM（通用表头合并 + manifest 显式合并）
  → 逐表渲染验收
```

### 3.2 multicolumn（组表头）

LaTeX：

```latex
\begin{tabular}{lccc}
\toprule
& \multicolumn{3}{c}{Group A} \\
Method & SDR & SIR & SAR \\
...
```

Pandoc 后常见两种坏形态：

1. 组表头文字只在第一格，后面两格为空；
2. 组表头文字被复制到每一格（`Group A Group A Group A`）。

处理：

- 预处理把 `\multicolumn{n}{spec}{body}` 展平成 `body` + `n-1` 个空单元，保证行宽；
- Word 端通用规则：表头前几行里，非空非数字单元格后面跟空单元或相同文字 → 横向合并；
- 特殊情况（组表头跨列但中间夹着非空单元格）用 `table_fixes.json` 的 `merges`。

### 3.3 multirow（纵向合并）

`\multirow{2}{*}{Method}` 在 Pandoc 里通常会重复文字或错位。

- 优先用 manifest 的 `vmerges`：`{"row_start": 2, "row_end": 3, "col": 1}`；
- 合并后 Word 只保留首格文字；需要时用 `cells` 重写；
- 不要用“自动删除重复文字”的启发式，容易误删真实重复数据。

### 3.4 resizebox / tabular* / p{} 列

这些结构会让 Pandoc 把整张表读成普通段落：

```latex
\resizebox{\columnwidth}{!}{\begin{tabular}...}
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}lccc@{}}
\begin{tabular}{p{3cm}rrr}
```

预处理统一成普通 `tabular`：

- 解包 `\resizebox`，只留内部 tabular；
- `tabular*{width}{spec}` → `tabular{spec}`；
- 删除 `@{\extracolsep{...}}`、`|`；
- `p{...}` / `m{...}` / `b{...}` → `l`（Word 里再自动布局）。

### 3.5 booktabs 与边框

- Pandoc 能吃掉 `\toprule/\midrule/\bottomrule`，但 Word 里默认没有“三线表”样式。
- 通用脚本给全表加网格边框，保证可读；
- 要三线表，需在 Word 端单独设置边框（上/下/表头下），或接受网格作为工作副本。
- 交付前确认：表头加粗、跨页重复、行不跨页。

### 3.6 相邻表格

Word 打开 DOCX 时，如果两个 `<w:tbl>` 之间没有段落（哪怕只有书签），会**自动粘成一张表**，并可能吞掉第二张表的 caption。

- 后处理：在相邻表之间插入空段落（`latex_to_docx.py` 已做）；
- 如果 caption 丢了，从 LaTeX 源补一个 Table Caption 段落；
- 验收时数一数表数量：Pandoc 输出 N 张，Word 里也应是 N 张。

### 3.7 表内数学与“丢失”的数值

表里的 `$-3.05$`、`$10^{-4}$` 会变成 OMML。python-docx 的 `cell.text` 读不到 `<m:t>`，于是看起来“负号/数值没了”。

- **不要**据此修改表格；
- 用 Word 渲染或 `inspect_docx.py` 的渲染页判断；
- 若确实丢了（Pandoc 解析失败），用 manifest 的 `cells` 写入纯文本（如 `-3.05`、`10^-4`）。

### 3.8 列宽与对齐

- Word 表默认按内容自动布局；数值列可能宽度不一。
- 通用脚本左对齐所有单元格，保证稳定；
- 可在 manifest 之外用 Word 手工把数值列设成右对齐/固定宽度；
- 不要给每列写死厘米宽度，Word 页面与字体变化会让表格溢出。

### 3.9 表格验收

用 `inspect_docx.py --tables` 看每张表的行数、列数、前三行；再渲染页面看：

- 组表头是否只出现一次，且横跨正确列数；
- 纵向合并是否正确；
- 数字列是否有负号、上下标；
- 表头是否跨页重复；
- 表格是否超出页宽；
- caption 是否紧邻表格。

---

## 四、交叉引用与参考文献

- `\ref` / `\eqref`：从 `.aux` 回填。`.aux` 必须来自当前版本的编译；旧 aux 会产生错误编号。
- `\cite`：Pandoc `--citeproc --bibliography refs.bib --csl style.csl`。
- 没有 CSL 时 Pandoc 用默认样式；投稿 Word 只是工作副本，引用格式以 LaTeX/期刊模板为准。
- 正文中的 `??` 是硬错误，必须清零或明确列出无法解析的 label。

---

## 五、版式与字体

- 正文默认 Times New Roman 10 pt；标题 14/12/10.5 pt 加粗；页边距 0.9 in。
- 标题样式要覆盖 Pandoc 模板的蓝色主题字体（Word COM 里设 `Font.Color=0`、`ColorIndex=1`）。
- 图片按文本宽度；高瘦图更窄，避免独占一页且 caption 被挤走。
- 页脚页码按节添加；封面/标题页是否要页码按论文要求处理。

---

## 六、保真度与交付说明

交付 Word 时同时说明：

1. 这是**工作副本**，排版以 LaTeX/期刊模板为准；
2. 哪些公式是图片（如有）；
3. 哪些表格用了 manifest 修补；
4. 无法解析的引用/缺失图清单；
5. 页数与 LaTeX 不同是正常的。

不要声称“完全一致”；要给出可核对的项目（公式数、图数、表数、缺失清单）。
