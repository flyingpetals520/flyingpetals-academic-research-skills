#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Expand every existing PDF highlight so it covers the whole sentence.

Use case: a paper PDF already carries review highlights, but each highlight
covers only the line (or fragment) that was picked by hand.  This script maps
every highlight back to the sentence it belongs to, then replaces it with a
multi-line highlight that covers the entire sentence, including wrapped lines,
text interrupted by display equations, and continuations across columns or
pages.  Comments, subjects, colours, opacity and the separate sticky-note
icons are kept; the page content itself is never touched.

Defaults assume a CVPR-like LaTeX layout (NimbusRomNo9L body text, 9.4-10.9 pt,
two-column main text, single-column appendix).  For another template inspect
`page.get_text("dict")` and pass --font-substr / --size-min / --size-max.

Usage:
  python complete_sentence_highlights.py paper.pdf
  python complete_sentence_highlights.py paper.pdf --out paper_full.pdf
  python complete_sentence_highlights.py paper.pdf --report spans.json --dry-run

Requires: PyMuPDF (fitz) >= 1.22 (tested with 1.22.5).
"""
import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict

import fitz

# ---------------------------------------------------------------------------
# Body-text model
# ---------------------------------------------------------------------------


def body_lines(page, font_substr, size_min, size_max):
    """Return the body-text lines of one page.

    Filters out margin line numbers, running headers/footers, section headings,
    figure captions, table cells, plot labels and display-equation lines.
    A display-equation line has no body-font span, so the font test drops it;
    mixed text/math lines stay because their prose is set in the body font.
    """
    d = page.get_text("rawdict")
    out = []
    for block in d["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            spans = line.get("spans", [])
            if not spans:
                continue
            x0, y0, x1, y1 = line["bbox"]
            if y0 < 60 or y1 > 820 or x1 < 50 or x0 > 590:
                continue
            sizes = []
            chars = []
            for span in spans:
                txt = "".join(ch["c"] for ch in span["chars"])
                if font_substr in span["font"] and txt.strip():
                    sizes.append(span["size"])
                for ch in span["chars"]:
                    chars.append((ch["c"], tuple(ch["bbox"])))
            if not sizes:
                continue
            if max(sizes) < size_min or max(sizes) > size_max:
                continue
            text = "".join(c for c, _ in chars)
            if len(text.strip()) < 2:
                continue
            if re.fullmatch(r"\(\d+\)", text.strip()):
                continue  # equation tag sitting on its own line
            out.append({"page": page.number, "bbox": (x0, y0, x1, y1),
                        "chars": chars, "text": text})
    return out


def page_streams(page, font_substr, size_min, size_max):
    """Split a page into reading-order streams (left/right column, or one
    stream for a single-column appendix)."""
    lines = body_lines(page, font_substr, size_min, size_max)
    if not lines:
        return []
    wide = [l for l in lines if (l["bbox"][2] - l["bbox"][0]) > 350]
    if len(wide) > max(3, len(lines) // 3):
        return [lines]  # single-column layout
    left = [l for l in lines if l["bbox"][2] <= 300]
    right = [l for l in lines if l["bbox"][0] >= 305]
    return [left, right]


# ---------------------------------------------------------------------------
# Sentence detection on one global reading-order string
# ---------------------------------------------------------------------------


def is_boundary(s, i):
    if i < 0 or i >= len(s) or s[i] not in ".!?":
        return False
    j = i + 1
    if j >= len(s):
        return True
    if s[j] != " ":
        return False
    k = j + 1
    while k < len(s) and s[k] == " ":
        k += 1
    if k >= len(s):
        return True
    c = s[k]
    if c in "([":  # "Eq. (9)", "[12]." etc. are not sentence starts
        return False
    return c.isupper() or c in "\"'"


def sentence_span(text, a):
    """Bounds of the sentence containing char index a.

    Forward scan starts at a + 1, not at the highlight end: a highlight can
    already contain the sentence-final period, and scanning from its end would
    jump into the next sentence.
    """
    start = 0
    for i in range(a - 1, -1, -1):
        if is_boundary(text, i):
            start = i + 1
            break
    while start < len(text) and text[start] == " ":
        start += 1
    end = len(text)
    for i in range(min(a + 1, len(text)), len(text)):
        if is_boundary(text, i):
            end = i + 1
            break
    while end > start and text[end - 1] == " ":
        end -= 1
    return start, end


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--out", help="output path (default: overwrite input)")
    ap.add_argument("--backup", help="backup path (default: <stem>_backup.pdf)")
    ap.add_argument("--font-substr", default="NimbusRomNo9L",
                    help="body font substring (default: NimbusRomNo9L)")
    ap.add_argument("--size-min", type=float, default=9.4)
    ap.add_argument("--size-max", type=float, default=10.9)
    ap.add_argument("--report", help="write a JSON report of covered sentences")
    ap.add_argument("--dry-run", action="store_true",
                    help="analyse and report only; do not modify the PDF")
    args = ap.parse_args()

    src = os.path.abspath(args.pdf)
    out = os.path.abspath(args.out) if args.out else src
    backup = os.path.abspath(args.backup) if args.backup else (
        os.path.splitext(src)[0] + "_backup.pdf")

    doc = fitz.open(src)
    # Keep strong references: Annot objects are orphaned if the Page is freed.
    pages = [doc[i] for i in range(len(doc))]

    streams = []
    for page in pages:
        for stream in page_streams(page, args.font_substr,
                                   args.size_min, args.size_max):
            if stream:
                streams.append(sorted(stream,
                                      key=lambda t: (round(t["bbox"][1], 1),
                                                     t["bbox"][0])))

    # One global reading-order character stream with per-line offsets.
    parts, line_meta = [], []
    pos = 0
    for stream in streams:
        for line in stream:
            if parts:
                parts.append(" ")
                pos += 1
            start = pos
            for ch, _ in line["chars"]:
                parts.append(ch)
                pos += 1
            line_meta.append((start, pos, line))
    text_all = "".join(parts)

    def anchor_span(rect, pno):
        r = fitz.Rect(rect)
        best, best_area = None, -1.0
        for ls, le, line in line_meta:
            if line["page"] != pno:
                continue
            lb = fitz.Rect(line["bbox"])
            inter = lb & r
            if inter.is_empty:
                continue
            area = inter.get_area()
            if area > best_area:
                best_area, best = area, (ls, le, line)
        if best is None:
            return None
        ls, le, line = best
        first = last = None
        for j, (_, bb) in enumerate(line["chars"]):
            cx = (bb[0] + bb[2]) / 2
            if r.x0 - 1 <= cx <= r.x1 + 1:
                if first is None:
                    first = j
                last = j + 1
        if first is None:
            return None
        return ls + first, ls + last

    def quads_for(span):
        start, end = span
        by_page = defaultdict(list)
        for ls, le, line in line_meta:
            a, b = max(start, ls), min(end, le)
            if b <= a:
                continue
            sel = line["chars"][a - ls:b - ls]
            boxes = [bb for ch, bb in sel if ch.strip()]
            if not boxes:
                boxes = [bb for _, bb in sel]
            if not boxes:
                continue
            x0 = min(bb[0] for bb in boxes)
            x1 = max(bb[2] for bb in boxes)
            y0 = min(bb[1] for bb in boxes)
            y1 = max(bb[3] for bb in boxes)
            if x1 - x0 < 1:
                continue
            by_page[line["page"]].append(
                fitz.Rect(x0, y0 - 0.5, x1, y1 + 0.5))
        return by_page

    # Collect highlights, grouped by page + comment + subject.  Several
    # highlight fragments can carry the same comment (e.g. a passage split by
    # display equations); they are merged into one continuous span.
    groups = defaultdict(list)
    failed = 0
    for pno, page in enumerate(pages):
        for annot in (page.annots() or []):
            if annot.type[1] != "Highlight":
                continue
            sp = anchor_span(annot.rect, pno)
            if sp is None:
                failed += 1
                print(f"[warn] anchor failed: page {pno + 1} {annot.rect}")
                continue
            s, e = sentence_span(text_all, sp[0])
            key = (pno, annot.info.get("content", ""),
                   annot.info.get("subject", ""))
            groups[key].append({"annot": annot, "span": (s, e), "page": page})

    if not groups:
        print("no highlight annotations found; nothing to do")
        return 1

    plans = []
    for key, items in groups.items():
        spans = sorted(it["span"] for it in items)
        merged = []
        for s, e in spans:
            if merged and s <= merged[-1][1] + 2:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        first = items[0]["annot"]
        plans.append({
            "content": first.info.get("content", ""),
            "subject": first.info.get("subject", ""),
            "title": first.info.get("title", "Writing review"),
            "color": tuple(first.colors.get("stroke") or (0.95, 0.85, 0.1)),
            "opacity": first.opacity if first.opacity and first.opacity > 0
                       else 0.38,
            "annots": [it["annot"] for it in items],
            "page": items[0]["page"],
            "spans": merged,
        })

    report = []
    for plan in plans:
        for span in plan["spans"]:
            report.append({
                "page": plan["page"].number + 1,
                "subject": plan["subject"],
                "content": plan["content"],
                "sentence": text_all[span[0]:span[1]],
            })

    print(f"pages: {len(pages)}  highlight groups: {len(plans)}  "
          f"old highlights: {sum(len(p['annots']) for p in plans)}  "
          f"anchor failures: {failed}")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
        print("report:", args.report)
    if args.dry_run:
        return 0

    for plan in plans:
        for annot in plan["annots"]:
            plan["page"].delete_annot(annot)

    new_count = 0
    for plan in plans:
        for span in plan["spans"]:
            for pno, rects in quads_for(span).items():
                quads = [(fitz.Point(r.x0, r.y0), fitz.Point(r.x1, r.y0),
                          fitz.Point(r.x0, r.y1), fitz.Point(r.x1, r.y1))
                         for r in rects]
                if not quads:
                    continue
                annot = pages[pno].add_highlight_annot(quads=quads)
                annot.set_colors(stroke=plan["color"])
                annot.set_opacity(plan["opacity"])
                annot.set_info(content=plan["content"], title=plan["title"],
                               subject=plan["subject"])
                annot.update()
                new_count += 1

    if out == src:
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
    print(f"new highlights: {new_count}  saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
