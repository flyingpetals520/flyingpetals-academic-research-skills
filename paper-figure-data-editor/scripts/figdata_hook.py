# -*- coding: utf-8 -*-
"""figdata_hook — let a plotting script take its numbers from the figure editor.

The plotting script keeps doing all the drawing. This module only decides
*which numbers* get drawn: the measured ones by default, the edited ones when
the editor is driving it.

Add to a plotting script (3 lines, right after the imports):

    import sys
    sys.path.insert(0, r"<repo>/figure_editor")
    import figdata_hook as fdh

Then wrap each quantity you want editable:

    # line / scatter series
    x, y = fdh.curve("fig3_snr", "Ours", x, y)

    # bar chart row (one value per column)
    vals, lo, hi = fdh.bars("fig7_thr", "Model-A", [42.0, 88.0],
                            cols=("Train", "Inference"),
                            lo=[6.0, 5.0], hi=[5.0, 4.0])

And call once at the end of the script:

    fdh.finish()

Environment variables (both optional):
    FIGDATA_OVERRIDE  path to the editor JSON; numbers in it replace the measured ones
    FIGDATA_DUMP      path to write what was actually drawn (used to seed the editor)

Nothing here ever writes to the measurement files.
"""
import json
import os

__version__ = "1.0"

_OVR_PATH = os.environ.get("FIGDATA_OVERRIDE")
_OVJ = None
if _OVR_PATH and os.path.exists(_OVR_PATH):
    try:
        with open(_OVR_PATH, encoding="utf-8") as f:
            _OVJ = json.load(f)
    except Exception:                      # a half-written file must not kill the plot
        _OVJ = None

_DUMP = {}
_META = {}


def enabled():
    """True when the editor is driving this run."""
    return _OVJ is not None


def meta(cid, name=None, unit=None, xlabel=None, type=None, note=None):
    """Register display metadata used when seeding the editor."""
    _META[cid] = dict(name=name, unit=unit, xlabel=xlabel, type=type, note=note)


def _chart(cid):
    if not _OVJ:
        return None
    for c in _OVJ.get("charts", []):
        if c.get("id") == cid:
            return c
    return None


def _as_floats(seq):
    return [None if v is None else float(v) for v in seq]


# --------------------------------------------------------------------- curves
def curve(cid, label, x, y):
    """Substitute one line series. Returns (x, y), sorted by x."""
    x = list(x)
    y = list(y)
    _DUMP.setdefault(cid, {})[label] = {"kind": "curve",
                                        "x": _as_floats(x), "y": _as_floats(y)}
    c = _chart(cid)
    if c is None or label not in (c.get("cols") or []):
        return x, y
    j = c["cols"].index(label)
    xs_in = [float(v) for v in x]
    xs_new, ys_new = [], []
    for i, row in enumerate(c.get("rows") or []):
        try:
            xv = float(row)
        except (TypeError, ValueError):
            continue
        k = None
        for t, xv0 in enumerate(xs_in):
            if abs(xv0 - xv) <= 1e-6:
                k = t
                break
        if k is None:                       # this x is not on the curve we drew
            continue
        try:
            v = c["data"][i][j]
        except (IndexError, TypeError):
            continue
        if v is None:
            continue
        xs_new.append(xv)
        ys_new.append(float(v))
    if not xs_new:                          # nothing matched: leave the curve alone
        return x, y
    order = sorted(range(len(xs_new)), key=lambda t: xs_new[t])
    out_x = [xs_new[t] for t in order]
    out_y = [ys_new[t] for t in order]
    _DUMP[cid][label] = {"kind": "curve", "x": out_x, "y": out_y}
    return out_x, out_y


points = curve                            # scatter uses the same contract


# ----------------------------------------------------------------------- bars
def bars(cid, row, values, cols=None, lo=None, hi=None):
    """Substitute one bar-chart row. Returns (values, lo, hi).

    `values` holds one number per column; `lo`/`hi` are the lower/upper whisker
    offsets (as positive distances). Pass cols=... on the first call so the
    editor knows the column names.
    """
    values = [float(v) for v in values]
    n = len(values)
    lo = [0.0] * n if lo is None else [float(v) for v in lo]
    hi = [0.0] * n if hi is None else [float(v) for v in hi]
    entry = _DUMP.setdefault(cid, {}).setdefault(row, {"kind": "bars"})
    entry.update({"values": values, "lo": lo, "hi": hi})
    if cols:
        entry["cols"] = list(cols)

    c = _chart(cid)
    if c is None or row not in (c.get("rows") or []):
        return values, lo, hi
    i = c["rows"].index(row)
    out_v, out_lo, out_hi = list(values), list(lo), list(hi)
    for j in range(min(n, len(c.get("cols") or []))):
        v = c["data"][i][j] if i < len(c["data"]) and j < len(c["data"][i]) else None
        if v is None:
            continue
        out_v[j] = float(v)
        for key, out in (("errlo", out_lo), ("errhi", out_hi)):
            src = c.get(key)
            if src and i < len(src) and j < len(src[i]) and src[i][j] is not None:
                out[j] = float(src[i][j])
    entry.update({"values": out_v, "lo": out_lo, "hi": out_hi})
    return out_v, out_lo, out_hi


# ---------------------------------------------------------------------- finish
def finish():
    """Write the dump when FIGDATA_DUMP is set. Call once, after all drawing."""
    path = os.environ.get("FIGDATA_DUMP")
    if not path:
        return
    out = {}
    for cid, series in _DUMP.items():
        out[cid] = dict(series)
        if cid in _META:
            out[cid]["__meta__"] = _META[cid]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("figdata: dumped", path)
