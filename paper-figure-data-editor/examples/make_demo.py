# -*- coding: utf-8 -*-
"""Demo plotting script: one line chart, one grouped bar chart with whiskers."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, r"E:/tmp/figdemo/figure_editor")
import figdata_hook as fdh          # noqa: E402

fdh.meta("demo_line", name="Demo line", unit="dB", xlabel="SNR (dB)", type="line")
fdh.meta("demo_bar", name="Demo bars", unit="k pts/s", type="bar")

# ------------------------------------------------------------------ line chart
X = [-10, -5, 0, 5, 10, 20]
SERIES = {"Model-A": [1.0, 3.0, 8.0, 15.0, 22.0, 28.0],
          "Model-B": [0.0, 2.0, 6.0, 12.0, 18.0, 24.0]}

fig, ax = plt.subplots(figsize=(4, 3))
for label, Y in SERIES.items():
    x, y = fdh.curve("demo_line", label, X, Y)
    ax.plot(x, y, marker="o", label=label)
ax.legend()
ax.set_xlabel("SNR (dB)")
ax.set_ylabel("SDR (dB)")
fig.savefig(os.path.join(OUT, "demo_line.png"), dpi=120)
plt.close(fig)

# ------------------------------------------------------- bar chart, whiskers
ROWS = [("Model-A", 42.0, 88.0, 6.0, 5.0, 5.0, 4.0),
        ("Model-B", 30.0, 61.0, 2.0, 3.0, 1.0, 2.0)]

fig, ax = plt.subplots(figsize=(4, 3))
for i, (name, tr, inf, tlo, thi, ilo, ihi) in enumerate(ROWS):
    vals, lo, hi = fdh.bars("demo_bar", name, [tr, inf],
                            cols=("Train", "Inference"),
                            lo=[tlo, ilo], hi=[thi, ihi])
    ax.bar([i * 0.4, i * 0.4 + 0.2], vals, width=0.18, yerr=[lo, hi], label=name)
ax.set_xticks([0.1, 0.5])
ax.set_xticklabels(["Train", "Inference"])
ax.legend()
fig.savefig(os.path.join(OUT, "demo_bar.png"), dpi=120)
plt.close(fig)

fdh.finish()
print("saved demo figures")
