# Hook 写法（按图型照抄）

所有例子里，**画图的每一行都保持原样**，只在"取值 → 画图"之间插入 hook。

## 折线图（一组模型，各自一条曲线）

```python
import sys; sys.path.insert(0, r"E:/proj/figure_editor"); import figdata_hook as fdh

fdh.meta("fig3_snr", name="Input SNR", unit="dB",
         xlabel="SNR (dB)", type="line")

X = [-10, -5, 0, 5, 10, 16, 20]
series = {"Model-A": [...], "Model-B": [...], "Model-C": [...]}

for label, Y in series.items():
    x, y = fdh.curve("fig3_snr", label, X, Y)     # <- 唯一新增
    ax.plot(x, y, marker="o", label=label)        # 原样不动

fdh.finish()
```

## 带置信带的折线

编辑器目前**编辑带的中线**，带宽保留脚本自己的计算：

```python
x, y = fdh.curve("fig4", label, x, y)
ax.fill_between(x, y - ci, y + ci, alpha=.2)      # ci 仍是脚本算的
```

如果需要连带宽一起编辑，把 `ci` 也走 `fdh.curve(f"fig4_ci_{label}", ...)` 存成独立图表即可（推荐，简单可靠）。

## 横向条形图（含非对称误差棒）

```python
rows = [("Model-A", 42.0, 88.0, 6.0, 5.0, 5.0, 4.0),   # 名字, train, infer, 下偏, 上偏...
        ("Model-B", 30.0, 61.0, 2.0, 3.0, 1.0, 2.0)]

for name, tr, inf, tlo, thi, ilo, ihi in rows:
    vals, lo, hi = fdh.bars("fig7", name, [tr, inf],
                            cols=("Train", "Inference"),
                            lo=[tlo, ilo], hi=[thi, ihi])
    ax.barh(y, vals[0], height=.34, xerr=[[lo[0]], [hi[0]]])   # 原样
```

要点：
- `cols=` 只在第一行给一次即可（也可以每行都给，无副作用）；
- `lo`/`hi` 是**正偏移量**，不是绝对上下限；
- 编辑器里改数值时，偏移保持不变，误差棒跟着平移。

## 分组条形图（多模型 × 多指标）

```python
for model in models:
    vals, lo, hi = fdh.bars("fig4_k3", model, [sdr, sir, sar],
                            cols=("SDR", "SIR", "SAR"),
                            lo=[e1, e2, e3], hi=[e1, e2, e3])
    ax.bar(x + off, vals, yerr=[lo, hi], label=model)
```

## 多子图

每个子图一个独立 cid，用 `meta(type="bar"|"line")` 区分：

```python
fdh.meta("fig2a", name="(a) Time domain", unit="", type="line")
fdh.meta("fig2b", name="(b) Spectrum", unit="dB", type="line")
...
x, y = fdh.curve("fig2a", "signal", t, y_t)
x, y = fdh.curve("fig2b", "signal", f, y_f)
```

同一个脚本里的多个 cid 会一起重绘（"只保存这张图"实际重跑整个脚本），这是正常的。

## seaborn

seaborn 也吃 numpy 数组，通常在 `sns.lineplot(x=X, y=Y)` 之前拿到数组即可：

```python
Y = np.asarray(Y, dtype=float)
X2, Y2 = fdh.curve("fig5", "Ours", X, Y)
sns.lineplot(x=X2, y=Y2, label="Ours")
```

注意 seaborn 自己会做聚合（`estimator="mean"`）。要精确控制就把 `errorbar=None` 打开并在外面算好 CI，否则编辑器给的数和画出来的数可能对不上。

## pandas 直接画

```python
df = pd.read_csv(...)
df["Ours"], *_ = fdh.bars("fig6", "Ours", list(df["Ours"]), cols=("SDR",))
```

复杂表格建议先转成纯 list 再进 hook，避免 dtype 造成的 `numpy.float32` 精度差异。

## 什么时候不要接 hook

- 图是示意图（架构图、流程图）——没有"数据"可编；
- 图里的数字是从模型直接跑出来的可视化（频谱图、波形图）——不是表格数据；
- 图由 LaTeX/pgfplots 直接生成——应该改 `.tex` 里的表格数值，而不是接编辑器。

## Python 之外

MATLAB / R 的绘图脚本同理：只要能在"取数组 → 画"之间插一段读 JSON 的逻辑即可。
最小实现是一个 30 行的 `load_override(cid)`：读 `figure_data.json`，
按 id 找 chart，按行名/列名替换数组。参考 `scripts/figdata_hook.py` 的 `curve` / `bars`。
