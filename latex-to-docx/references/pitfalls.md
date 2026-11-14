# 踩坑手册（LaTeX → DOCX）

按“现象 → 原因 → 处理”组织。都是在真实论文转换中踩过的。

## Pandoc 与源文件

**1. `--citeproc` 不存在 / 公式不转 OMML**
- 原因：系统 PATH 里是 Pandoc 1.19 等旧版本。
- 处理：`pandoc --version` 确认 ≥2.11；用 `--pandoc <3.x path>`。不要改 PATH 后假设立刻生效，脚本里要显式传路径。

**2. 引用编号错、PDF 截断、`??` 大量出现**
- 原因：`.aux` 是旧的或损坏的。
- 处理：删除 `.aux/.out/.fls/.fdb_latexmk`，重新 `pdflatex → bibtex → pdflatex ×2`。`.aux` 必须是当前版本的。

**3. 分节文件里的 `\ref`/表格/图没被处理**
- 原因：只处理了主 `.tex`，`\input{sec/...}` 里的内容没展开。
- 处理：脚本先递归展开 `\input/\include`；找不到的文件写入 `missing_includes`。也可用 `latexpand` 先 flatten。

**4. 图路径找不到**
- 原因：用了 `\graphicspath{{figs/}}`，或 `\includegraphics{fig}` 省略扩展名。
- 处理：脚本解析 `\graphicspath` 并按 `.pdf/.png/.jpg` 顺序探测；仍找不到的写报告，不要静默跳过。

## 公式

**5. 公式变成图片/文字碎片**
- 原因：PDF→Word、OCR、或旧版 Pandoc。
- 处理：从 `.tex` 用 Pandoc 3.x 转；检查 `<m:oMath>`。

**6. 公式编号全丢/错位**
- 原因：Pandoc 不保留 LaTeX 编号；section 编号、align、`\tag` 情况不同。
- 处理：顺序编号用 `--number-equations`；其它情况关闭自动编号，按 `.aux`/PDF 手工核对。

**7. 宏没有展开**
- 原因：复杂 `\newcommand`、参数宏、条件宏。
- 处理：把宏定义复制到临时副本导言区；仍失败则展平宏；最后才用图片。

**8. TikZ/化学式无法转**
- 处理：渲染成 300–400 dpi PNG 插入，并在交付说明中标注“图片公式”。

## 图

**9. DOCX 缺图**
- 原因：`\includegraphics{fig.pdf}` 原样传给 Pandoc。
- 处理：预处理把 PDF 渲染成 PNG；检查报告 `missing_figures`。

**10. 多面板图散架**
- 原因：`subfigure`/`minipage` 并排结构不被 Pandoc 保留。
- 处理：合成一张 PNG；或接受分开的图并逐张核对 caption/顺序。

**11. 图比例被破坏**
- 原因：只设宽度不设高度。
- 处理：按原始宽高比计算高度；脚本已按 aspect 选择目标宽度。

## 表

**12. 表头合并丢失（词重复三遍/后面空着）**
- 原因：`\multicolumn` 只保留文字。
- 处理：预处理展平保行宽；Word 端通用合并（重复/空单元）；特殊表用 manifest `merges`。

**13. 两张表变成一张**
- 原因：Word 打开时自动合并相邻 `<w:tbl>`（中间只有书签也算相邻）。
- 处理：DOCX 后处理在两表间插入空段落；确认表数量与源文件一致。

**14. 第二张表的 caption 消失**
- 原因：`\captionof` 在 `minipage` 里，Pandoc 丢失；或表被粘在一起。
- 处理：预处理提升为 `table` 环境；后处理隔开表；必要时从源文件补 caption 段落。

**15. 表被读成普通段落**
- 原因：`\resizebox`、`tabular*`、`p{...}` 列、`@{\extracolsep{...}}`。
- 处理：预处理统一成普通 `tabular`（脚本已做）。

**16. 表格里负号/数值“消失”**
- 原因：数学模式变成 OMML，python-docx 的 `.text` 读不到。
- 处理：以 Word 渲染为准；确实丢失时用 manifest `cells` 写纯文本。

**17. 纵向合并错位**
- 原因：`\multirow` 被展开成重复文字。
- 处理：manifest `vmerges`；合并后用 `cells` 重写首格。

**18. 通用表头合并误伤数据**
- 原因：表头里有重复的短标签（如两个 `SDR`）。
- 处理：`--no-auto-merge` 关闭自动合并，只用 manifest；或把 `--header-rows` 降到 1。

**19. 单元格写回后行高翻倍**
- 原因：`Cell.Range.Text` 带 `\r\x07`，留下空段落。
- 处理：先去掉 `\r` 和 `\x07` 再写；写回后统一 `SpaceBefore/SpaceAfter=0`（脚本已做）。

**20. 合并后旧 Cell 引用失效**
- 处理：`Merge` 后重新 `tbl.Cell(r,c)` 再赋值。

## Word COM

**21. 打开文件失败**
- 原因：相对路径。
- 处理：`os.path.abspath`；Word 的工作目录不是脚本目录。

**22. 导出 PDF 报“只读文件”**
- 原因：目标 PDF 被阅读器占用。
- 处理：先删除；失败则导出到 `_new.pdf`（脚本已做）。

**23. 标题蓝色/字体不对**
- 原因：Pandoc reference doc 的主题字体。
- 处理：在样式和 run 级别都设 `Font.Name`、`Color=0`、`ColorIndex=1`。

**24. 图注被挤到下一页**
- 原因：图太高。
- 处理：高瘦图用更小宽度（脚本按 aspect≥1.15 缩窄）；表格行设 `KeepWithNext`。

**25. 页数比 LaTeX 多很多**
- 原因：Word 排版差异。
- 处理：不是内容缺失；核对公式/图/表/引用即可，不要为了页数删内容。

## 验收

**26. XML 计数正常但渲染错**
- 原因：OMML/表格 XML 存在不等于显示正确（字体、合并、列宽）。
- 处理：必须导出 PDF 并渲染页面抽查。

**27. `??` 没清零**
- 处理：报告 `missing_refs`；补 label 或重新编译；无法解析的要在交付说明里列出。

**28. 只改 DOCX 却动了源文件**
- 原因：预处理直接写回 `.tex`。
- 处理：临时副本；结束删除；交付前核对源文件时间戳/`git diff`。
