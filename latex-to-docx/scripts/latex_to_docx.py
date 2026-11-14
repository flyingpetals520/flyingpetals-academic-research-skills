#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LaTeX paper -> editable Word (DOCX) with native OMML equations.

Pipeline:
  1. read the compiled .aux and resolve \\ref / \\eqref;
  2. prepare a temporary LaTeX copy: normalise tables/figures, optionally
     restore equation and caption numbers, replace PDF figures with PNG;
  3. run Pandoc >= 2.11 with --citeproc (native equations, images, tables);
  4. post-process the DOCX: insert a paragraph between adjacent tables so
     Word does not fuse them on open;
  5. print counts for equations, images and tables.

This script is paper-agnostic.  Paper-specific table repairs (missing headers,
unusual merges, cells lost by math) belong in the manifest consumed by
format_docx.py; see SKILL.md and references/hard-elements.md.

Usage:
  python latex_to_docx.py paper.tex -o paper_word.docx \
      --bib refs.bib --csl ieee.csl \
      --pandoc "D:/tools/pandoc-3.1.11/pandoc.exe" \
      --number-equations --number-captions

Requires: Python 3.8+, Pandoc >= 2.11 (3.x recommended), PyMuPDF (optional,
only for PDF figures), python-docx.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# ---------------------------------------------------------------------------
# LaTeX helpers
# ---------------------------------------------------------------------------


def match_brace(s, start):
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


def load_labels(aux_path):
    labels = {}
    if not aux_path or not os.path.exists(aux_path):
        return labels
    text = open(aux_path, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", text):
        labels[m.group(1)] = m.group(2)
    return labels


def unwrap_resizebox(tex):
    out, i = [], 0
    token = r"\resizebox"
    while True:
        j = tex.find(token, i)
        if j < 0:
            out.append(tex[i:])
            break
        out.append(tex[i:j])
        p = j + len(token)
        groups = []
        ok = True
        for _ in range(3):
            while p < len(tex) and tex[p].isspace():
                p += 1
            if p >= len(tex) or tex[p] != "{":
                ok = False
                break
            e = match_brace(tex, p)
            if e < 0:
                ok = False
                break
            groups.append(tex[p + 1:e - 1])
            p = e
        if not ok:
            out.append(token)
            i = j + len(token)
        else:
            out.append(groups[-1])
            i = p
    return "".join(out)


def flatten_multicolumn(tex):
    """\\multicolumn{n}{spec}{body} -> body + (n-1) empty cells.

    Pandoc keeps the text but loses the span.  Keeping the row width intact
    lets the DOCX merge pass recover group headers from duplicates/empties.
    """
    out, i = [], 0
    token = r"\multicolumn"
    while True:
        j = tex.find(token, i)
        if j < 0:
            out.append(tex[i:])
            break
        out.append(tex[i:j])
        p = j + len(token)
        groups = []
        ok = True
        for _ in range(3):
            while p < len(tex) and tex[p].isspace():
                p += 1
            if p >= len(tex) or tex[p] != "{":
                ok = False
                break
            e = match_brace(tex, p)
            if e < 0:
                ok = False
                break
            groups.append(tex[p + 1:e - 1])
            p = e
        if not ok:
            out.append(token)
            i = j + len(token)
            continue
        try:
            ncols = int(groups[0].strip())
        except ValueError:
            ncols = 1
        out.append(groups[2] + " & " * max(ncols - 1, 0))
        i = p
    return "".join(out)


def normalize_tabular_specs(tex):
    """Turn tabular*/tabular specs into something Pandoc parses."""
    # tabular*{width}{spec} -> tabular{spec}
    out, i = [], 0
    token = r"\begin{tabular*}"
    while True:
        j = tex.find(token, i)
        if j < 0:
            out.append(tex[i:])
            break
        out.append(tex[i:j])
        p = j + len(token)
        groups = []
        ok = True
        for _ in range(2):
            while p < len(tex) and tex[p].isspace():
                p += 1
            if p >= len(tex) or tex[p] != "{":
                ok = False
                break
            e = match_brace(tex, p)
            if e < 0:
                ok = False
                break
            groups.append(tex[p + 1:e - 1])
            p = e
        if not ok:
            out.append(token)
            i = j + len(token)
        else:
            out.append(r"\begin{tabular}{" + groups[1] + "}")
            i = p
    tex = "".join(out)
    tex = tex.replace(r"\end{tabular*}", r"\end{tabular}")

    out, i = [], 0
    token = r"\begin{tabular}"
    while True:
        j = tex.find(token, i)
        if j < 0:
            out.append(tex[i:])
            break
        out.append(tex[i:j + len(token)])
        p = j + len(token)
        while p < len(tex) and tex[p].isspace():
            p += 1
        if p >= len(tex) or tex[p] != "{":
            i = j + len(token)
            continue
        e = match_brace(tex, p)
        if e < 0:
            i = j + len(token)
            continue
        spec = tex[p + 1:e - 1]
        spec = re.sub(r"@\{[^{}]*\}", "", spec)
        spec = spec.replace("|", "")
        spec = re.sub(r"[pmb]\{[^{}]*\}", "l", spec)
        spec = re.sub(r"\s+", " ", spec).strip()
        out.append("{" + spec + "}")
        i = e
    return "".join(out)


def number_equations(tex):
    """Append sequential numbers to equation environments (optional).

    Valid only when the paper numbers equations sequentially with the
    equation environment.  Section-based numbering or \\tag{...} requires
    manual handling; see references/hard-elements.md.
    """
    counter = [0]

    def repl(m):
        counter[0] += 1
        return (r"\begin{equation}" + m.group(1)
                + r"\quad (%d)" % counter[0] + r"\end{equation}")

    return re.sub(r"\\begin\{equation\}(.*?)\\end\{equation\}", repl,
                  tex, flags=re.S)


def number_captions(tex, labels):
    """Add 'Table N:'/'Figure N:' from .aux when the caption lacks a number."""
    def repl_env(m):
        kind, opt, body = m.group(1), m.group(2) or "", m.group(3)
        lab = re.search(r"\\label\{([^}]+)\}", body)
        if not lab:
            return m.group(0)
        num = labels.get(lab.group(1))
        if not num:
            return m.group(0)
        prefix = "Table" if kind == "table" else "Figure"
        if re.search(r"\\caption\{(?:Table|Figure)\s", body):
            return m.group(0)
        body = body.replace(r"\caption{", r"\caption{%s %s: " % (prefix, num), 1)
        return r"\begin{%s}%s" % (kind, opt) + body + r"\end{%s}" % kind

    return re.sub(
        r"\\begin\{(table|figure)\}(\[[^\]]*\])?(.*?)\\end\{\1\}",
        repl_env, tex, flags=re.S)




def expand_inputs(tex, base, report, depth=0):
    """Inline \input / \include so the transforms reach every section."""
    if depth > 10:
        return tex

    def repl(m):
        name = m.group(2).strip()
        cand = name if os.path.isabs(name) else os.path.join(base, name)
        if not os.path.splitext(cand)[1]:
            cand += ".tex"
        if not os.path.exists(cand):
            report["missing_includes"].append(name)
            return m.group(0)
        sub = open(cand, encoding="utf-8", errors="replace").read()
        return expand_inputs(sub, os.path.dirname(cand), report, depth + 1)

    return re.sub(r"\\(input|include)\{([^}]+)\}", repl, tex)


def parse_graphicspath(tex, base):
    dirs = [base]
    m = re.search(r"\\graphicspath\{((?:\{[^}]*\})+)\}", tex)
    if m:
        for d in re.findall(r"\{([^}]*)\}", m.group(1)):
            dirs.append(os.path.join(base, d))
    return dirs

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")


def resolve_graphic(path, roots):
    candidates = [path] if os.path.isabs(path) else [os.path.join(r, path) for r in roots]
    for base in candidates:
        if os.path.splitext(base)[1]:
            if os.path.exists(base):
                return base
        else:
            for ext in (".pdf", ".png", ".jpg", ".jpeg", ".eps"):
                if os.path.exists(base + ext):
                    return base + ext
    return None


def convert_figures(tex, tex_dir, fig_dir, dpi, report, roots=None):
    """Replace PDF figures with PNGs so DOCX can embed them."""
    try:
        import fitz
    except ImportError:
        report["warnings"].append(
            "PyMuPDF not installed: PDF figures cannot be converted")
        return tex

    os.makedirs(fig_dir, exist_ok=True)

    def repl(m):
        opts = m.group(1) or ""
        path = m.group(2)
        full = resolve_graphic(path, roots or [tex_dir])
        if not full:
            report["missing_figures"].append(path)
            return m.group(0)
        if not full.lower().endswith(".pdf"):
            rel = os.path.relpath(full, tex_dir).replace("\\", "/")
            return r"\includegraphics" + opts + "{" + rel + "}"
        page = 1
        pm = re.search(r"page\s*=\s*(\d+)", opts)
        if pm:
            page = int(pm.group(1))
        stem = os.path.splitext(os.path.basename(full))[0]
        png = os.path.join(fig_dir, f"{stem}_p{page}.png")
        if not os.path.exists(png):
            doc = fitz.open(full)
            pix = doc[page - 1].get_pixmap(dpi=dpi, alpha=False)
            pix.save(png)
            doc.close()
        rel = os.path.relpath(png, tex_dir).replace("\\", "/")
        report["pdf_figures"].append({"src": full, "png": png, "page": page})
        return r"\includegraphics" + opts + "{" + rel + "}"

    return re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^}]+)\}", repl, tex)


# ---------------------------------------------------------------------------
# Pandoc
# ---------------------------------------------------------------------------


def pick_pandoc(explicit):
    cand = explicit or shutil.which("pandoc")
    if not cand:
        sys.exit("Pandoc not found. Install Pandoc 3.x or pass --pandoc <path>.")
    try:
        out = subprocess.check_output([cand, "--version"], text=True,
                                      errors="replace")
    except Exception as exc:
        sys.exit(f"Cannot run Pandoc at {cand}: {exc}")
    m = re.search(r"pandoc(?:\.exe)?\s+(\d+)\.(\d+)", out, re.I)
    if not m:
        sys.exit(f"Cannot parse Pandoc version at {cand}:\n{out[:200]}")
    major, minor = int(m.group(1)), int(m.group(2))
    if major < 2 or (major == 2 and minor < 11):
        sys.exit(f"Pandoc {major}.{minor} is too old; use Pandoc >= 2.11 "
                 f"(3.x recommended). Path: {cand}")
    return cand


# ---------------------------------------------------------------------------
# DOCX post-processing: keep adjacent tables separate
# ---------------------------------------------------------------------------


def separate_adjacent_tables(docx_path):
    d = docx.Document(docx_path)
    body = d.element.body
    last_tbl = False
    seen_para = True
    inserted = 0
    for el in list(body):
        tag = el.tag.split("}")[-1]
        if tag == "p":
            seen_para = True
        elif tag == "tbl":
            if last_tbl and not seen_para:
                p = OxmlElement("w:p")
                pPr = OxmlElement("w:pPr")
                spacing = OxmlElement("w:spacing")
                spacing.set(qn("w:before"), "0")
                spacing.set(qn("w:after"), "0")
                pPr.append(spacing)
                p.append(pPr)
                el.addprevious(p)
                inserted += 1
            last_tbl = True
            seen_para = False
    if inserted:
        d.save(docx_path)
    return inserted


def inspect_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
        media = [n for n in z.namelist() if n.startswith("word/media/")]
    return {
        "oMath": xml.count("<m:oMath"),
        "oMathPara": xml.count("<m:oMathPara"),
        "tables": xml.count("<w:tbl>"),
        "images": len(media),
        "raw_latex_refs": xml.count("\\cite"),
        "unresolved_refs": xml.count("??"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tex")
    ap.add_argument("-o", "--out", help="output DOCX (default <stem>_word.docx)")
    ap.add_argument("--aux", help="compiled .aux (default <stem>.aux)")
    ap.add_argument("--bib", help="bibliography .bib")
    ap.add_argument("--csl", help="CSL style (without it Pandoc uses its default)")
    ap.add_argument("--reference-doc", help="Pandoc reference DOCX")
    ap.add_argument("--pandoc", help="path to Pandoc >= 2.11 (default: PATH)")
    ap.add_argument("--fig-dir", default="word_figs",
                    help="directory for PDF->PNG figures (relative to tex)")
    ap.add_argument("--fig-dpi", type=int, default=300)
    ap.add_argument("--number-equations", action="store_true",
                    help="append sequential numbers to equation environments")
    ap.add_argument("--number-captions", action="store_true",
                    help="prefix Table/Figure numbers from .aux")
    ap.add_argument("--keep-temp", action="store_true")
    ap.add_argument("--report", default="latex_to_docx_report.json")
    args = ap.parse_args()

    tex_path = os.path.abspath(args.tex)
    tex_dir = os.path.dirname(tex_path)
    stem = os.path.splitext(os.path.basename(tex_path))[0]
    out = os.path.abspath(args.out or os.path.join(tex_dir, stem + "_word.docx"))
    aux = os.path.abspath(args.aux or os.path.join(tex_dir, stem + ".aux"))
    fig_dir = os.path.join(tex_dir, args.fig_dir)
    report = {"missing_refs": [], "missing_figures": [], "pdf_figures": [],
              "missing_includes": [], "warnings": []}

    tex = open(tex_path, encoding="utf-8", errors="replace").read()
    tex = expand_inputs(tex, tex_dir, report)
    fig_roots = parse_graphicspath(tex, tex_dir)
    labels = load_labels(aux)
    if not labels:
        report["warnings"].append(f"no labels loaded from {aux}")

    def ref_repl(m):
        key = m.group(1)
        if key in labels:
            return labels[key]
        report["missing_refs"].append(key)
        return "??"

    tex = re.sub(r"\\ref\{([^}]+)\}", ref_repl, tex)
    tex = re.sub(r"\\eqref\{([^}]+)\}",
                 lambda m: "(" + ref_repl(m) + ")", tex)
    tex = re.sub(r"\\looseness\s*=\s*-?\d+", "", tex)
    tex = tex.replace(r"\begin{figure*}", r"\begin{figure}")
    tex = tex.replace(r"\end{figure*}", r"\end{figure}")
    tex = re.sub(r"\\bibliographystyle\{[^}]*\}", "", tex)
    tex = re.sub(r"\\bibliography\{[^}]*\}", "", tex)
    tex = tex.replace(r"\begin{abstract}", r"\section*{Abstract}")
    tex = tex.replace(r"\end{abstract}", "")

    def center_table(m):
        block = m.group(1)
        if r"\captionof{table}" not in block:
            return m.group(0)
        block = block.replace(r"\captionof{table}", r"\caption")
        return r"\begin{table}" + block + r"\end{table}"

    tex = re.sub(r"\\begin\{center\}(.*?)\\end\{center\}",
                 center_table, tex, flags=re.S)
    tex = tex.replace(r"\captionof{table}", r"\caption")

    if args.number_equations:
        tex = number_equations(tex)
    if args.number_captions:
        tex = number_captions(tex, labels)

    for env in ("footnotesize", "small"):
        tex = tex.replace(r"\begin{%s}" % env, "").replace(
            r"\end{%s}" % env, "")
    tex = re.sub(r"\\renewcommand\{\\arraystretch\}\{[^}]*\}", "", tex)
    tex = re.sub(r"\\setlength\{\\tabcolsep\}\{[^}]*\}", "", tex)
    tex = unwrap_resizebox(tex)
    for _ in range(3):
        new = flatten_multicolumn(tex)
        if new == tex:
            break
        tex = new
    tex = normalize_tabular_specs(tex)
    tex = convert_figures(tex, tex_dir, fig_dir, args.fig_dpi, report,
                          roots=fig_roots)

    fd, tmp_tex = tempfile.mkstemp(suffix=".tex", dir=tex_dir)
    os.close(fd)
    with open(tmp_tex, "w", encoding="utf-8") as fh:
        fh.write(tex)

    pandoc = pick_pandoc(args.pandoc)
    cmd = [pandoc, tmp_tex, "-o", out, "--resource-path", tex_dir]
    if args.bib:
        cmd += ["--bibliography", os.path.abspath(args.bib), "--citeproc"]
        if args.csl:
            cmd += ["--csl", os.path.abspath(args.csl)]
    if args.reference_doc:
        cmd += ["--reference-doc", os.path.abspath(args.reference_doc)]
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
    rc = subprocess.run(cmd, cwd=tex_dir).returncode
    if not args.keep_temp:
        try:
            os.remove(tmp_tex)
        except OSError:
            pass
    if rc != 0:
        sys.exit(f"Pandoc failed with exit code {rc}")

    inserted = separate_adjacent_tables(out)
    report["adjacent_table_separators"] = inserted
    report["docx"] = out
    report["stats"] = inspect_docx(out)
    report["missing_refs"] = sorted(set(report["missing_refs"]))
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    print("saved:", out)
    print("stats:", report["stats"])
    print("missing refs:", len(report["missing_refs"]),
          report["missing_refs"][:10])
    print("missing figures:", len(report["missing_figures"]),
          report["missing_figures"][:10])
    print("adjacent-table separators inserted:", inserted)
    print("report:", os.path.abspath(args.report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
