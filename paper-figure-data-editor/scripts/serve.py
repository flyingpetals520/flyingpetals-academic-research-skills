# -*- coding: utf-8 -*-
"""Local server for the figure data editor.

    python figure_editor/serve.py            # -> http://127.0.0.1:8765/
    python figure_editor/serve.py --check    # validate editor_config.json and exit

All behaviour comes from editor_config.json next to this file:

{
  "name": "my-paper",                       # used for the browser storage key
  "python": null,                            # interpreter for the plot scripts
  "compile": {"cmd": ["pdflatex", "paper.tex"], "cwd": "..", "log": "paper.log"},
  "scripts": [
    {"file": "figures/make_fig1.py",         # relative to the project root
     "cwd": "..",                            # relative to figure_editor/
     "charts": ["fig1a", "fig1b"],           # chart ids this script draws
     "copy": [["figures/out/fig1.png", "figures/fig1.png"]]}
  ]
}

The server writes the posted numbers to figure_data.json, runs only the
scripts behind the requested charts with FIGDATA_OVERRIDE pointing at that file,
and copies whatever the config says. Plot scripts are never rewritten.
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(HERE, "editor_config.json")
JSON_PATH = os.path.join(HERE, "figure_data.json")
PORT = int(os.environ.get("PORT", "8765"))


def load_cfg():
    with io.open(CFG_PATH, encoding="utf-8") as f:
        return json.load(f)


def run(cmd, cwd, env=None):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def script_path(spec):
    """Absolute path of a plot script.

    Config rule: `cwd` is relative to figure_editor/, `file` is relative to `cwd`.
    """
    return os.path.normpath(os.path.join(HERE, spec.get("cwd", "."), spec["file"]))


def script_cwd(spec):
    return os.path.normpath(os.path.join(HERE, spec.get("cwd", ".")))


def make_figures(only=None):
    """Redraw the figures behind `only` (all figures when `only` is None)."""
    cfg = load_cfg()
    env = dict(os.environ)
    env["FIGDATA_OVERRIDE"] = JSON_PATH
    py = cfg.get("python") or sys.executable

    todo = []
    for spec in cfg.get("scripts", []):
        charts = spec.get("charts") or []
        if only and not (set(charts) & set(only)):
            continue
        todo.append(spec)

    if only and not todo:
        return 0, "unknown chart id(s): %s" % ",".join(only), []

    logs = []
    for spec in todo:
        rc, out = run([py, script_path(spec)], script_cwd(spec), env)
        logs.append(out)
        if rc != 0:
            return rc, "".join(logs), []

    figs = []
    for spec in todo:
        for src, dst in spec.get("copy") or []:
            s_path = os.path.normpath(os.path.join(script_cwd(spec), src))
            d_path = os.path.normpath(os.path.join(script_cwd(spec), dst))
            if not os.path.exists(s_path):
                return 1, "missing %s" % s_path, []
            if os.path.abspath(s_path) != os.path.abspath(d_path):
                shutil.copyfile(s_path, d_path)
            figs.append(os.path.relpath(d_path, script_cwd(spec)))
        for out in spec.get("report") or []:
            figs.append(out)
    return 0, "".join(logs), figs


def compile_pdf():
    cfg = load_cfg()
    c = cfg.get("compile")
    if not c:
        return True, "", None
    cwd = os.path.normpath(os.path.join(HERE, c.get("cwd", "..")))
    logs = []
    for _ in range(int(c.get("passes", 2))):
        rc, out = run(c["cmd"], cwd)
        logs.append(out)
        if rc != 0:
            return False, "".join(logs)[-1500:], None
    pages = None
    log = os.path.join(cwd, c.get("log", ""))
    if c.get("log") and os.path.exists(log):
        with io.open(log, encoding="utf-8", errors="replace") as f:
            for line in f:
                if "Output written on" in line:
                    pages = line.strip()
    return True, "", pages


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("[serve] " + (fmt % args) + "\n")

    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/favicon.ico"):
            self.send_response(204)
            self.end_headers()
            return
        if self.path.startswith("/api/ping"):
            cfg = load_cfg()
            self._send_json({"ok": True, "name": cfg.get("name", ""),
                             "scripts": len(cfg.get("scripts", []))})
            return
        if self.path in ("/", ""):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/render"):
            self._send_json({"ok": False, "error": "unknown endpoint"}, 404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            self._send_json({"ok": False, "error": "bad json: %s" % exc}, 400)
            return

        with io.open(JSON_PATH, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, indent=1))

        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        only = [c for c in q.get("only", [""])[0].split(",") if c]

        rc, out, figs = make_figures(only or None)
        if rc != 0:
            self._send_json({"ok": False, "error": out[-1500:]})
            return

        result = {"ok": True, "figures": figs}
        if not only and q.get("compile", ["0"])[0] == "1":
            ok, log, pages = compile_pdf()
            result["pdf"] = ok
            result["pages"] = pages
            result["log"] = log if not ok else ""
        self._send_json(result)


def check():
    cfg = load_cfg()
    bad = 0
    print("project: %s" % cfg.get("name", "(unnamed)"))
    print("python : %s" % (cfg.get("python") or sys.executable))
    for spec in cfg.get("scripts", []):
        p = script_path(spec)
        ok = os.path.exists(p)
        bad += 0 if ok else 1
        print("%s %-40s charts=%s" % ("OK  " if ok else "MISS", spec["file"],
                                      ",".join(spec.get("charts") or [])))
        for src, _dst in spec.get("copy") or []:
            sp = os.path.normpath(os.path.join(script_cwd(spec), src))
            if not os.path.exists(sp):
                print("     (output not created yet: %s)" % src)
    print("charts in figure_data.json: ", end="")
    try:
        with io.open(JSON_PATH, encoding="utf-8") as f:
            print(len(json.load(f).get("charts", [])))
    except Exception:
        print("not seeded yet")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        sys.exit(check())
    os.chdir(HERE)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("serving %s" % HERE)
    print("open  http://127.0.0.1:%d/" % PORT)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
