# -*- coding: utf-8 -*-
"""Seed the editor with the numbers your plotting scripts actually draw.

    python figure_editor/seed.py             # run every script, rebuild the seed
    python figure_editor/seed.py --dry-run   # print what would be seeded

For each script in editor_config.json this runs the script with FIGDATA_DUMP set
(and FIGDATA_OVERRIDE cleared), collects what the hook recorded, and writes:

    figure_editor/figure_data.json   the working copy the server uses
    figure_editor/index.html                 the embedded DEFAULTS = the pristine seed

The pristine seed is what the editor's "restore original numbers" button goes
back to, so it must be produced from the raw measurements — that is, this script
must be run before anyone edits anything, or after deleting the override file.
"""
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load_cfg():
    with io.open(os.path.join(HERE, "editor_config.json"), encoding="utf-8") as f:
        return json.load(f)


def run_script(spec, cfg, dump_path):
    env = {k: v for k, v in os.environ.items() if k != "FIGDATA_OVERRIDE"}
    env["FIGDATA_DUMP"] = dump_path
    py = cfg.get("python") or sys.executable
    cwd = os.path.normpath(os.path.join(HERE, spec.get("cwd", ".")))
    path = os.path.normpath(os.path.join(cwd, spec["file"]))
    p = subprocess.run([py, path], cwd=cwd, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def fmt_x(v):
    return str(int(v)) if float(v).is_integer() else ("%g" % v)


def build_charts(dump):
    """Turn raw hook dumps into editor chart objects."""
    charts = []
    for cid, series in dump.items():
        meta = series.get("__meta__") or {}
        items = {k: v for k, v in series.items() if k != "__meta__"}
        kinds = {v.get("kind") for v in items.values() if isinstance(v, dict)}
        if not items:
            continue
        if "curve" in kinds:
            cols = [k for k, v in items.items() if v.get("kind") == "curve"]
            xs = sorted({float(x) for k in cols for x in items[k]["x"] if x is not None})
            rows, data = [], []
            lut = {k: {float(a): b for a, b in zip(items[k]["x"], items[k]["y"])}
                   for k in cols}
            for x in xs:
                rows.append(fmt_x(x))
                data.append([lut[k].get(x) for k in cols])
            charts.append({"id": cid, "name": meta.get("name") or cid, "on": True,
                           "type": "line", "unit": meta.get("unit") or "",
                           "xlabel": meta.get("xlabel") or "", "orient": "rows",
                           "rows": rows, "cols": cols, "data": data,
                           "err": [[0.0 for _ in cols] for _ in rows]})
        else:
            rows = [k for k, v in items.items() if isinstance(v, dict)]
            cols = []
            for k in rows:
                if items[k].get("cols"):
                    cols = list(items[k]["cols"])
                    break
            if not cols:
                n = max(len(items[k].get("values") or []) for k in rows)
                cols = ["C%d" % (i + 1) for i in range(n)]
            data, errlo, errhi = [], [], []
            for k in rows:
                v = items[k].get("values") or []
                lo = items[k].get("lo") or []
                hi = items[k].get("hi") or []
                data.append([v[i] if i < len(v) else None for i in range(len(cols))])
                errlo.append([lo[i] if i < len(lo) else 0.0 for i in range(len(cols))])
                errhi.append([hi[i] if i < len(hi) else 0.0 for i in range(len(cols))])
            chart = {"id": cid, "name": meta.get("name") or cid, "on": True,
                     "unit": meta.get("unit") or "", "orient": "rows",
                     "rows": rows, "cols": cols, "data": data,
                     "err": [[round((errlo[i][j] + errhi[i][j]) / 2.0, 4)
                              for j in range(len(cols))] for i in range(len(rows))]}
            if any(any(e for e in r) for r in errlo):
                chart["errlo"] = errlo
                chart["errhi"] = errhi
            charts.append(chart)
    return charts


def embed_defaults(charts):
    """Rewrite the DEFAULTS constant inside index.html."""
    path = os.path.join(HERE, "index.html")
    html = io.open(path, encoding="utf-8").read()
    payload = json.dumps({"charts": charts}, ensure_ascii=False)
    start = html.index("const DEFAULTS = ")
    end = html.index(";\n", start)
    html = html[:start] + "const DEFAULTS = " + payload + html[end:]
    io.open(path, "w", encoding="utf-8").write(html)


def collect(cfg, quiet=False):
    """Run every script and return the merged dump."""
    merged = {}
    for spec in cfg.get("scripts", []):
        tmp = os.path.join(tempfile.gettempdir(), "figdata_%d.json" % os.getpid())
        if os.path.exists(tmp):
            os.remove(tmp)
        rc, out = run_script(spec, cfg, tmp)
        if rc != 0:
            print("FAILED %s\n%s" % (spec["file"], out[-1200:]))
            raise SystemExit(1)
        if not os.path.exists(tmp):
            print("WARNING: %s recorded nothing — did you call fdh.finish()?" % spec["file"])
            continue
        with io.open(tmp, encoding="utf-8") as f:
            d = json.load(f)
        os.remove(tmp)
        for cid, series in d.items():
            if cid in merged:
                print("WARNING: chart id %r recorded by more than one script" % cid)
            merged[cid] = series
        if not quiet:
            print("  %-40s %d chart(s)" % (spec["file"], len(d)))
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_cfg()
    if not cfg.get("scripts"):
        raise SystemExit("editor_config.json has no scripts yet")
    print("running %d script(s) ..." % len(cfg["scripts"]))
    dump = collect(cfg)
    charts = build_charts(dump)
    print("\ncharts:")
    for c in charts:
        print("  %-24s %-4s %d x %d  %s" % (c["id"], c.get("type", "bar"),
                                            len(c["rows"]), len(c["cols"]), c["name"]))
    if args.dry_run:
        return
    with io.open(os.path.join(HERE, "figure_data.json"), "w",
                 encoding="utf-8") as f:
        f.write(json.dumps({"charts": charts}, ensure_ascii=False, indent=1))
    embed_defaults(charts)
    print("\nseeded figure_data.json and the DEFAULTS in index.html")


if __name__ == "__main__":
    main()
