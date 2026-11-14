#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add one review highlight + sticky note to a PDF, by text search.

This is the authoring helper: point it at a short unique fragment on the first
line of the sentence you want to flag, give it the Chinese review comment and
a severity colour, and it creates the same annotation pair used throughout the
review PDFs: a translucent highlight carrying the comment plus a margin note
icon with the same text.  Run complete_sentence_highlights.py afterwards to
extend the mark over the whole sentence.

Usage:
  python add_review_annotation.py paper.pdf --page 3 \
      --find "The injected update is" --color red \
      --subject "P0 长句/定义堆叠" \
      --comment "P0：约 72 词，两个 where，且夹两个公式；建议拆分。"

Colour presets: red=P0, orange=P1, amber=P2, brown=分号密集, yellow=短句密度高.
Requires: PyMuPDF (fitz) >= 1.22.
"""
import argparse
import os
import shutil
import sys

import fitz

COLORS = {
    "red": (0.95, 0.10, 0.10),
    "orange": (0.95, 0.45, 0.05),
    "amber": (0.95, 0.70, 0.05),
    "brown": (0.95, 0.55, 0.10),
    "yellow": (0.95, 0.85, 0.10),
}
OPACITY = 0.38
TITLE = "Writing review"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--page", type=int, required=True, help="1-based page")
    ap.add_argument("--find", required=True,
                    help="short unique text fragment on the target line")
    ap.add_argument("--comment", required=True)
    ap.add_argument("--subject", default="review")
    ap.add_argument("--color", choices=sorted(COLORS), default="yellow")
    ap.add_argument("--no-note", action="store_true",
                    help="skip the margin sticky-note icon")
    ap.add_argument("--out", help="output path (default: overwrite input)")
    args = ap.parse_args()

    src = os.path.abspath(args.pdf)
    out = os.path.abspath(args.out) if args.out else src
    doc = fitz.open(src)
    page = doc[args.page - 1]

    rects = page.search_for(args.find)
    if not rects:
        print(f"text not found on page {args.page}: {args.find!r}")
        return 2

    quads = [(fitz.Point(r.x0, r.y0), fitz.Point(r.x1, r.y0),
              fitz.Point(r.x0, r.y1), fitz.Point(r.x1, r.y1)) for r in rects]
    hl = page.add_highlight_annot(quads=quads)
    hl.set_colors(stroke=COLORS[args.color])
    hl.set_opacity(OPACITY)
    hl.set_info(content=args.comment, title=TITLE, subject=args.subject)
    hl.update()

    if not args.no_note:
        x = page.rect.width - 56
        y = rects[-1].y0 - 2
        note = page.add_text_annot(fitz.Point(x, y), args.comment)
        note.set_info(content=args.comment, title=TITLE, subject=args.subject)
        note.update()

    if out == src:
        backup = os.path.splitext(src)[0] + "_backup.pdf"
        if not os.path.exists(backup):
            shutil.copyfile(src, backup)
            print("backup:", backup)
        tmp = out + ".tmp"
        doc.save(tmp, garbage=3, deflate=True)
        doc.close()
        os.replace(tmp, out)
    else:
        doc.save(out, garbage=3, deflate=True)
        doc.close()
    print(f"annotated page {args.page}: {args.find!r} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
