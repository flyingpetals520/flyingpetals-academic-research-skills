---
name: paper-figure-data-editor
version: 1.0.0
description: "给任意论文代码库装一个「只改数字、不改绘图」的图表数据编辑器：用浏览器拖动条/点、改表格、实时预览、一键回写图片，原绘图脚本与测量数据一律不动。支持条形图与折线图（含误差棒、非对称误差、CI 带），带历史记录、逐图回退、逐图恢复原始、逐图保存。适用于把论文里的实验结果图反复微调对齐，而不想动研究代码的场景。"
---

# 论文图表数据编辑器

给一个已有论文仓库加一层"数据可编辑"的外壳，**绘图仍然由原脚本完成**，我们只替换它读到的数字。

## 什么时候该用

- 论文图里的数字需要反复微调（对齐基线、修正笔误、统一评测协议、审稿后补数）；
- 不想每次改一个数就改一次硬编码、跑一次脚本；
- **硬约束**：原仓库的绘图风格、脚本结构、测量数据文件都不能动。

不适合：需要重新跑实验才能得到的新数据；需要改图结构（加子图、换配色）的重画。

## 三条铁律

1. **不重写绘图**。图的每一个元素都由原脚本画出来，编辑器只喂数字。历史上所有"照着重画一份"的方案都会和论文里的图产生肉眼可见的差异，最终不可用。
2. **不写测量文件**。探针结果、benchmark json、日志一律只读。绘制时替换，落盘时不动。
3. **不改脚本结构**。只在"取值 → 画图"之间插 3 行，在脚本末尾插 1 行。

## 六步安装

```bash
# 1. 装到目标仓库（不会碰任何已有文件）
python <skill>/scripts/scaffold.py --target E:/papers/mypaper --name mypaper
#    -> 生成 mypaper/figure_editor/{index.html,serve.py,figdata_hook.py,editor_config.json}

# 2. 把绘图脚本登记进去（我一般让 agent 自己扫 scripts/*.py 填）
#    figure_editor/editor_config.json:
#    {"file": "figures/make_fig1.py", "cwd": "..", "charts": ["fig1a"],
#     "copy": [["figures/out/fig1.png", "figures/fig1.png"]]}
#
#    路径规则：cwd 相对 figure_editor/，file 和 copy 相对 cwd。
#    脚本原地覆盖论文用图的，copy 留空数组即可。

# 3. 给每个绘图脚本插 hook（见下）

# 4. 用"当前真实数字"播种编辑器
python figure_editor/seed.py

# 5. 证明"不改的时候一个像素都不变"——必须全 OK 才能继续
python figure_editor/verify_roundtrip.py

# 6. 开编辑器
python figure_editor/serve.py        # http://127.0.0.1:8765/
```

## Hook：每个脚本只需 4 行

```python
import sys
sys.path.insert(0, r"<repo>/figure_editor")
import figdata_hook as fdh

fdh.meta("fig1a", name="Input SNR", unit="dB", xlabel="SNR (dB)", type="line")

# ...原来的取值代码...
x, y = fdh.curve("fig1a", "Ours", x, y)              # 就在 ax.plot(x, y) 之前
vals, lo, hi = fdh.bars("fig7", "Model-A", [42.0, 88.0],
                        cols=("Train", "Inference"),
                        lo=[6.0, 5.0], hi=[5.0, 4.0]) # 就在 ax.barh(...) 之前

fdh.finish()                                          # 脚本最后一行
```

| 函数 | 用途 | 返回 |
|---|---|---|
| `fdh.meta(cid, ...)` | 图表名称/单位/横轴/类型，播种时用 | — |
| `fdh.curve(cid, label, x, y)` | 一条折线/散点序列，按 x 值匹配 | 替换后的 `(x, y)` |
| `fdh.bars(cid, row, values, cols=, lo=, hi=)` | 条形图的一行，按行名匹配 | `(values, lo, hi)` |
| `fdh.finish()` | 记录实际画出的数字 | — |

要点：
- `cid` 用稳定短 id（`fig3a`），**改名字会丢编辑器里已有的改动**；
- `curve` 的匹配键是 x 的数值，`bars` 的匹配键是行名 —— 名字必须和编辑器里显示的一致；
- 编辑器里没有的数字，脚本原样使用测出来的值，所以漏接一格不会把图弄坏。

## 编辑器操作（给用户的 MD）

**改数**：表格里直接改；折线图拖圆点改单点、拖整条线平移整组；条形图上下拖柱子。
拖动时鼠标旁有白框显示当前数值。

**两线太近拖不准** → 打开该图上的「高级选择」，选定模型 + 手势（只拖点 / 只拖线），其余曲线变暗且不响应。

**写盘**：
- 「只保存这张图」= 只重跑这张图的脚本并写回，不编译论文；
- 「一键绘图 → 写入论文」= 全部重画（可选同时编译 PDF）。

**后悔药**：
- 每张图右上角「↶ 回退」= 撤销这张图的上一次改动；
- 顶栏「历史修改记录」= 逐条 diff，可"回退到此"（连同之后的一起回滚）；
- 每张图「↺ 恢复原始」= 回到实测值并立刻重画这张图。

**备份**：顶栏「导出 JSON」存一份到仓库里；浏览器缓存会因清理/换机丢失。导出文件也可以用「导入 JSON」还原。

## 验收标准

1. `verify_roundtrip.py` 全 `OK`（这是唯一可信的"没画歪"证据）；
2. `seed.py` 打印的 `rows × cols` 与图里实际的点/柱子数量一致；
3. 在浏览器里把某个点拖开后，图片确实变了，且只有目标图变了（看 mtime）。

## 出错时查

- 图跟原版不一样、坐标轴/配色不对 → 你多半重画了图，回退到 hook 方案
- 编辑器的数字进去了但图没变 → hook 插在取值之后、画图之后
- `verify_roundtrip` 报 DIFF → 看 `references/pitfalls.md` 的"插值不完整"一节
- 浏览器看不到新加的图 → 不要改 storage key，合并逻辑会自动补新图

详细踩坑清单：`references/pitfalls.md`
编辑器完整操作手册：`references/ui-guide.md`
各绘图库的 hook 写法（matplotlib / seaborn / 横向条形 / 分组条形 / 带 CI）：`references/hook-recipes.md`

## 目录

```
scripts/scaffold.py         装到目标仓库
scripts/seed.py             播种（跑脚本→dump→生成编辑器数据）
scripts/verify_roundtrip.py 像素级一致性验证
scripts/serve.py            本地服务（配置驱动，按图只跑对应脚本）
scripts/figdata_hook.py     插进绘图脚本的库
assets/index.html           浏览器编辑器（单文件）
```
