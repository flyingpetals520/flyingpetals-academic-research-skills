# -*- coding: utf-8 -*-
"""Prove the hook changes nothing: redraw with the seeded numbers, compare pixels.

    python figure_editor/verify_roundtrip.py

For every script: run it once with no override, hash the outputs, then run it
again with an override built from the dump of run 1 and hash again. Identical
pixels mean the editor will never silently change a figure it was not asked to
change. Run this after seeding and after every hook edit.

Returns a non-zero exit code when any figure differs.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from seed import build_charts, load_cfg          # noqa: E402


def img_hash(path):
    """Pixel hash for images (ignores timestamps), byte hash otherwise."""
    try:
        from PIL import Image
        import numpy as np
        a = np.asarray(Image.open(path).convert("RGB")).astype(int)
        return "pixels:%dx%d:%s" % (a.shape[0], a.shape[1],
                                    hashlib.md5(a.tobytes()).hexdigest()[:16])
    except Exception:
        with open(path, "rb") as f:
            return "bytes:" + hashlib.md5(f.read()).hexdigest()[:16]


def outputs_of(spec):
    """Every file the script produced that we care about.

    The copy sources always exist after a run; the destinations only exist once
    the server has copied them, so both are compared when present.
    """
    cwd = os.path.normpath(os.path.join(HERE, spec.get("cwd", ".")))
    out = []
    for src, dst in spec.get("copy") or []:
        for rel in (src, dst):
            p = os.path.normpath(os.path.join(cwd, rel))
            if os.path.exists(p) and p not in out:
                out.append(p)
    for rel in spec.get("report") or []:
        p = os.path.normpath(os.path.join(cwd, rel))
        if os.path.exists(p) and p not in out:
            out.append(p)
    return out


def run(spec, cfg, env_extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("FIGDATA_OVERRIDE", "FIGDATA_DUMP")}
    env.update(env_extra)
    py = cfg.get("python") or sys.executable
    cwd = os.path.normpath(os.path.join(HERE, spec.get("cwd", ".")))
    path = os.path.normpath(os.path.join(cwd, spec["file"]))
    p = subprocess.run([py, path], cwd=cwd, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    cfg = load_cfg()
    bad = 0
    for spec in cfg.get("scripts", []):
        name = spec["file"]
        dump = os.path.join(tempfile.gettempdir(), "rt_dump.json")
        if os.path.exists(dump):
            os.remove(dump)

        rc, out = run(spec, cfg, {"FIGDATA_DUMP": dump})
        if rc != 0:
            print("FAIL  %s (run 1)\n%s" % (name, out[-800:]))
            bad += 1
            continue
        before = {p: img_hash(p) for p in outputs_of(spec)}
        if not before:
            print("FAIL  %s (no output files found — check the 'copy' paths)" % name)
            bad += 1
            continue

        if not os.path.exists(dump):
            print("SKIP  %s (no dump — missing fdh.finish()?)" % name)
            continue
        with io.open(dump, encoding="utf-8") as f:
            charts = build_charts(json.load(f))
        ovr = os.path.join(tempfile.gettempdir(), "rt_override.json")
        with io.open(ovr, "w", encoding="utf-8") as f:
            json.dump({"charts": charts}, f)

        rc, out = run(spec, cfg, {"FIGDATA_OVERRIDE": ovr})
        if rc != 0:
            print("FAIL  %s (run 2)\n%s" % (name, out[-800:]))
            bad += 1
            continue
        after = {p: img_hash(p) for p in outputs_of(spec)}

        changed = [p for p in before if before[p] != after.get(p)]
        if changed:
            print("DIFF  %s" % name)
            for p in changed:
                print("        %s\n          seed %s\n          ovr  %s"
                      % (os.path.basename(p), before[p], after.get(p)))
            bad += 1
        else:
            print("OK    %-40s %d output(s) identical" % (name, len(before)))

    print("\n%s" % ("all figures reproduce exactly" if not bad
                    else "%d script(s) differ — see above" % bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
