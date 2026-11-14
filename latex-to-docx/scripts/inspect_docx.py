#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect a converted DOCX: equations, figures, tables, captions, leftovers.

Use after latex_to_docx.py and before/after format_docx.py.  The table dump
is meant for authoring the table-fix manifest: it shows each table's shape
and header cells, including cells that are already merged.

Usage:
  python inspect_docx.py paper_word.docx --tables --json report.json
  python inspect_docx.py paper_word.docx --pdf paper_word.pdf \
      --pages 1,3,7 --outdir renders
"""
import argparse
import json
import os
import re
import sys
import zipfile

import docx
import fitz


def docx_stats(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
        media = [n for n in z.namelist() if n.startswith("word/media/")]
    return {
        "oMath": xml.count("<m:oMath"),
        "oMathPara": xml.count("<m:oMathPara"),
        "tables": xml.count("<w:tbl>"),
        "images": len(media),
        "raw_begin": xml.count("\\begin{"),
        "raw_cite": xml.count("\\cite"),
        "raw_ref": xml.count("\\ref"),
        "unresolved": xml.count("??"),
    }


def table_dump(path):
    d = docx.Document(path)
    out = []
    for i, t in enumerate(d.tables, 1):
        rows = len(t.rows)
        cols = len(t.columns) if rows else 0
        head = []
        for r in range(min(3, rows)):
            cells = []
            for c in t.rows[r].cells:
                cells.append((c.text or "").replace("\n", " ")[:30])
            head.append(cells)
        out.append({"index": i, "rows": rows, "cols": cols, "head": head})
    return out


def caption_dump(path):
    d = docx.Document(path)
    caps = []
    for p in d.paragraphs:
        t = (p.text or "").strip()
        if not t:
            continue
        if re.match(r"^(Table|Figure|Fig\.)\s*\d+", t):
            caps.append(t[:160])
    return caps


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx")
    ap.add_argument("--json", help="write full report as JSON")
    ap.add_argument("--tables", action="store_true", help="dump table headers")
    ap.add_argument("--pdf", help="rendered DOCX PDF for page images")
    ap.add_argument("--pages", default="", help="pages to render, e.g. 1,3,7")
    ap.add_argument("--outdir", default="renders")
    args = ap.parse_args()

    path = os.path.abspath(args.docx)
    stats = docx_stats(path)
    tables = table_dump(path) if args.tables else []
    caps = caption_dump(path)

    print("stats:", stats)
    print("captions:", len(caps))
    if tables:
        for t in tables:
            print(f"table {t['index']}: {t['rows']}x{t['cols']}")
            for r, cells in enumerate(t["head"]):
                print("   r%d:" % (r + 1), cells)

    if args.pdf and args.pages:
        os.makedirs(args.outdir, exist_ok=True)
        doc = fitz.open(args.pdf)
        for spec in args.pages.split(","):
            spec = spec.strip()
            if not spec:
                continue
            if "-" in spec:
                a, b = spec.split("-", 1)
                nums = range(int(a), int(b) + 1)
            else:
                nums = [int(spec)]
            for n in nums:
                if 1 <= n <= len(doc):
                    out = os.path.join(args.outdir, f"docx_page_{n}.png")
                    doc[n - 1].get_pixmap(dpi=130).save(out)
                    print("rendered:", out)
        print("pdf pages:", len(doc))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"stats": stats, "captions": caps,
                       "tables": tables}, fh, ensure_ascii=False, indent=1)
        print("report:", os.path.abspath(args.json))
    return 0


if __name__ == "__main__":
    sys.exit(main())
