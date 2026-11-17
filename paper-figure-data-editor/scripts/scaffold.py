# -*- coding: utf-8 -*-
"""Install the figure data editor into any paper repository.

    python scaffold.py --target E:/papers/mypaper --name mypaper
    python scaffold.py --target . --name mypaper --python <path-to-python>

Creates <target>/figure_editor/ with:
    index.html          the browser editor
    serve.py            local server (config-driven)
    figdata_hook.py     the 3-line hook your plotting scripts import
    editor_config.json  which script draws which chart

It never touches existing plotting code: adding the hook is a manual 4-line edit
that the script prints for you.
"""
import argparse
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))

SKELETON = {
    "name": "",
    "python": None,
    "compile": {"cmd": ["pdflatex", "-interaction=nonstopmode",
                        "-file-line-error", "paper.tex"],
                "cwd": "..", "log": "paper.log", "passes": 2},
    "scripts": [],
}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "figure"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="repo root that holds the plotting scripts")
    ap.add_argument("--name", default="", help="project name, used for the browser storage key")
    ap.add_argument("--python", default=None, help="interpreter that can run the plot scripts")
    ap.add_argument("--force", action="store_true", help="overwrite an existing figure_editor/")
    args = ap.parse_args()

    root = os.path.abspath(args.target)
    if not os.path.isdir(root):
        sys.exit("target does not exist: %s" % root)
    name = args.name or os.path.basename(root)
    dest = os.path.join(root, "figure_editor")
    if os.path.exists(dest) and not args.force:
        sys.exit("figure_editor/ already exists (use --force to overwrite)")

    os.makedirs(dest, exist_ok=True)
    for f in ("serve.py", "figdata_hook.py", "seed.py", "verify_roundtrip.py"):
        shutil.copyfile(os.path.join(HERE, f), os.path.join(dest, f))

    html = io.open(os.path.join(ASSETS, "index.html"), encoding="utf-8").read()
    key = "figdata_%s_v1" % slug(name)
    html = re.sub(r'const LS = "[^"]+";', 'const LS = "%s";' % key, html, count=1)
    io.open(os.path.join(dest, "index.html"), "w", encoding="utf-8").write(html)

    cfg_path = os.path.join(dest, "editor_config.json")
    if not os.path.exists(cfg_path):      # never clobber a registered config

        cfg = dict(SKELETON)
        cfg["name"] = name
        cfg["python"] = args.python
        io.open(cfg_path, "w", encoding="utf-8").write(
            json.dumps(cfg, indent=2, ensure_ascii=False))

    rel = os.path.relpath(dest, root).replace("\\", "/")
    print("installed ->", dest)
    print("storage key:", key)
    print("""
next steps
----------
1. register your plotting scripts in
   %s/editor_config.json

     {"file": "figures/make_fig1.py",
      "cwd": "..",
      "charts": ["fig1a"],
      "copy": [["figures/out/fig1.png", "figures/fig1.png"]]}

2. add the hook to each plotting script (keep every drawing line as it is):

     import sys
     sys.path.insert(0, r"%s")
     import figdata_hook as fdh

     fdh.meta("fig1a", name="Input SNR", unit="dB", xlabel="SNR (dB)", type="line")
     ...
     x, y = fdh.curve("fig1a", "Ours", x, y)      # before ax.plot(...)
     ...
     fdh.finish()                                  # last line of the script

3. seed the editor with today's numbers, then check the round trip:

     python %s/seed.py
     python %s/verify_roundtrip.py

4. run it:

     python %s/serve.py        ->  http://127.0.0.1:8765/
""" % (rel, dest.replace("\\", "/"), rel, rel, rel))


if __name__ == "__main__":
    main()
