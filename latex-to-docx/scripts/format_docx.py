#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Format the Pandoc DOCX with Word COM and export a verification PDF.

What it does:
  * page margins, body font/size, heading styles, justified prose;
  * figures scaled to the text width; tables full width with borders,
    repeated header row and compact cell spacing;
  * a generic header-merge pass (duplicated or empty header cells produced by
    flattened LaTeX \\multicolumn);
  * an optional JSON manifest for paper-specific merges, vertical merges and
    cell overrides (lost math values, restored superscripts, ...);
  * centred title, footer page numbers;
  * DOCX + PDF export.

Windows + Microsoft Word required.  Paper-specific table repairs belong in
the manifest, not in this script.

Usage:
  python format_docx.py paper_word.docx -o paper_word_final.docx \
      --manifest table_fixes.json --pdf paper_word_final.pdf
"""
import argparse
import json
import os
import time

import win32com.client as win32

wdAlignParagraphCenter = 1
wdAlignParagraphJustify = 3
wdAlignRowCenter = 1
wdLineSpaceSingle = 0
wdPreferredWidthPercent = 2
wdHeaderFooterPrimary = 1
wdFieldPage = 33
wdStyleHeading1 = -2
wdStyleHeading2 = -3
wdStyleHeading3 = -4
wdStyleTitle = -63
wdExportFormatPDF = 17


def pts(inches):
    return inches * 72.0


def _txt(tbl, r, c):
    try:
        return (tbl.Cell(r, c).Range.Text
                .replace("\r", "").replace("\x07", "").strip())
    except Exception:
        return None


def _set_cell(tbl, r, c, text):
    try:
        cell = tbl.Cell(r, c)
        cell.Range.Text = text
        cell.Range.Font.Name = "Times New Roman"
        cell.Range.Font.Size = 8.5
        cell.Range.ParagraphFormat.SpaceBefore = 0
        cell.Range.ParagraphFormat.SpaceAfter = 0
        return True
    except Exception as exc:
        print(f"cell write failed r{r} c{c}: {exc}", flush=True)
        return False


def _merge(tbl, r, c1, c2, text=None):
    """Merge horizontally; re-fetch the cell before writing."""
    try:
        tbl.Cell(r, c1).Merge(tbl.Cell(r, c2))
        if text is not None:
            _set_cell(tbl, r, c1, text)
        return True
    except Exception as exc:
        print(f"merge failed r{r} c{c1}:{c2}: {exc}", flush=True)
        return False


def _vmerge(tbl, r1, r2, c, text=None):
    try:
        tbl.Cell(r1, c).Merge(tbl.Cell(r2, c))
        if text is not None:
            _set_cell(tbl, r1, c, text)
        return True
    except Exception as exc:
        print(f"vmerge failed r{r1}:{r2} c{c}: {exc}", flush=True)
        return False


def style_font(doc, style_id, name, size, bold=None):
    try:
        st = doc.Styles(style_id)
        st.Font.Name = name
        st.Font.Size = size
        st.Font.Color = 0
        st.Font.ColorIndex = 1
        if bold is not None:
            st.Font.Bold = bold
    except Exception as exc:
        print("style", style_id, "failed:", exc, flush=True)


def auto_merge_headers(doc, max_rows=2):
    """Merge repeated/empty header cells in the first rows.

    Pandoc flattens \\multicolumn into text plus empty cells (or duplicates
    the text).  In header rows, a non-empty non-numeric cell followed by
    empty or identical cells is a group header; merge the run.  Runs are
    merged right-to-left so cell indices stay valid.
    """
    for tbl in doc.Tables:
        try:
            ncols = tbl.Columns.Count
            nrows = tbl.Rows.Count
        except Exception:
            continue
        for r in range(1, min(max_rows, nrows) + 1):
            runs = []
            c = 1
            while c <= ncols:
                t = _txt(tbl, r, c)
                if not t or len(t) < 3 or t.replace(".", "").isdigit():
                    c += 1
                    continue
                end = c
                while end + 1 <= ncols:
                    nt = _txt(tbl, r, end + 1)
                    if nt is None:
                        break
                    if nt == "" or nt == t:
                        end += 1
                    else:
                        break
                if end > c:
                    runs.append((c, end, t))
                c = end + 1
            for c1, c2, text in reversed(runs):
                _merge(tbl, r, c1, c2, text)


def apply_manifest(doc, manifest):
    if not manifest:
        return
    for spec in manifest.get("tables", []):
        match = spec.get("match", {})
        cols = match.get("cols")
        contains = [s.lower() for s in match.get("contains", [])]
        targets = []
        for tbl in doc.Tables:
            try:
                if cols and tbl.Columns.Count != cols:
                    continue
            except Exception:
                continue
            head = " ".join(
                (_txt(tbl, r, c) or "")
                for r in range(1, min(2, tbl.Rows.Count) + 1)
                for c in range(1, min(tbl.Columns.Count, 12) + 1)).lower()
            if contains and not any(s in head for s in contains):
                continue
            targets.append(tbl)
        if not targets:
            print("manifest: no table matched", match, flush=True)
            continue
        for tbl in targets:
            for m in spec.get("merges", []):
                _merge(tbl, m["row"], m["col_start"], m["col_end"],
                       m.get("text"))
            for m in spec.get("vmerges", []):
                _vmerge(tbl, m["row_start"], m["row_end"], m["col"],
                        m.get("text"))
            for m in spec.get("cells", []):
                _set_cell(tbl, m["row"], m["col"], m["text"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("-o", "--out", help="output DOCX (default <stem>_final.docx)")
    ap.add_argument("--pdf", help="verification PDF path (default same stem)")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--font", default="Times New Roman")
    ap.add_argument("--body-size", type=float, default=10)
    ap.add_argument("--margin", type=float, default=0.9, help="inches")
    ap.add_argument("--table-size", type=float, default=8.5)
    ap.add_argument("--fig-width", type=float, default=6.3,
                    help="max figure width in inches")
    ap.add_argument("--fig-tall", type=float, default=5.3,
                    help="width for aspect >= 1.15")
    ap.add_argument("--manifest", help="JSON table fixes (see templates/)")
    ap.add_argument("--header-rows", type=int, default=2,
                    help="header rows for the generic merge pass")
    ap.add_argument("--no-auto-merge", action="store_true")
    args = ap.parse_args()

    src = os.path.abspath(args.input)
    out = os.path.abspath(args.out or os.path.splitext(src)[0] + "_final.docx")
    pdf = os.path.abspath(args.pdf or os.path.splitext(out)[0] + ".pdf")
    manifest = None
    if args.manifest:
        with open(args.manifest, encoding="utf-8") as fh:
            manifest = json.load(fh)

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(src, ReadOnly=False)
        ps = doc.PageSetup
        ps.PageWidth = pts(8.5)
        ps.PageHeight = pts(11.0)
        ps.TopMargin = ps.BottomMargin = pts(args.margin)
        ps.LeftMargin = ps.RightMargin = pts(args.margin)
        ps.HeaderDistance = pts(0.4)
        ps.FooterDistance = pts(0.4)

        normal = doc.Styles(-1)
        normal.Font.Name = args.font
        normal.Font.Size = args.body_size
        normal.ParagraphFormat.LineSpacingRule = wdLineSpaceSingle
        normal.ParagraphFormat.SpaceAfter = 4
        normal.ParagraphFormat.SpaceBefore = 0

        style_font(doc, wdStyleTitle, args.font, 17, True)
        style_font(doc, wdStyleHeading1, args.font, 14, True)
        style_font(doc, wdStyleHeading2, args.font, 12, True)
        style_font(doc, wdStyleHeading3, args.font, 10.5, True)

        for p in doc.Paragraphs:
            try:
                txt = p.Range.Text.strip()
                name = p.Style.NameLocal
                if (txt and not txt.startswith(("Figure ", "Table "))
                        and name not in ("Title", "Author")
                        and not name.startswith("Heading")):
                    p.Alignment = wdAlignParagraphJustify
            except Exception:
                pass

        for p in doc.Paragraphs:
            try:
                name = p.Style.NameLocal
                if name == "Author":
                    p.Range.Find.Execute(FindText="^t", ReplaceWith=" ",
                                         Replace=2)
                    p.Alignment = wdAlignParagraphCenter
                    p.Range.Font.Name = args.font
                    p.Range.Font.Size = 10.5
                elif name == "Title":
                    p.Alignment = wdAlignParagraphCenter
            except Exception:
                pass

        for p in doc.Paragraphs:
            try:
                name = p.Style.NameLocal
                if name == "Title" or name.startswith("Heading"):
                    p.Range.Font.Name = args.font
                    p.Range.Font.Color = 0
                    p.Range.Font.ColorIndex = 1
                    p.Range.Font.Bold = True
            except Exception:
                pass

        for shp in doc.InlineShapes:
            try:
                old_w, old_h = float(shp.Width), float(shp.Height)
                if old_w <= 0 or old_h <= 0:
                    continue
                aspect = old_h / old_w
                if aspect >= 1.15:
                    target = pts(args.fig_tall)
                elif aspect <= 0.55:
                    target = pts(args.fig_width + 0.2)
                else:
                    target = pts(args.fig_width)
                shp.Width = target
                shp.Height = old_h * target / old_w
            except Exception as exc:
                print("figure resize failed:", exc, flush=True)

        for ti, tbl in enumerate(doc.Tables, 1):
            try:
                tbl.PreferredWidthType = wdPreferredWidthPercent
                tbl.PreferredWidth = 100
                tbl.Rows.Alignment = wdAlignRowCenter
                tbl.Range.Font.Name = args.font
                tbl.Range.Font.Size = args.table_size
                tbl.Range.ParagraphFormat.Alignment = 0
                tbl.Range.ParagraphFormat.SpaceBefore = 0
                tbl.Range.ParagraphFormat.SpaceAfter = 0
                tbl.Range.ParagraphFormat.LineSpacingRule = wdLineSpaceSingle
                tbl.Rows.AllowBreakAcrossPages = False
                if tbl.Rows.Count:
                    tbl.Rows(1).Range.Font.Bold = True
                    try:
                        tbl.Rows(1).HeadingFormat = True
                    except Exception:
                        pass
                if tbl.Rows.Count <= 18:
                    for r in range(1, tbl.Rows.Count):
                        tbl.Rows(r).Range.ParagraphFormat.KeepWithNext = True
                tbl.Borders.InsideLineStyle = 1
                tbl.Borders.OutsideLineStyle = 1
                tbl.Borders.InsideLineWidth = 4
                tbl.Borders.OutsideLineWidth = 8
            except Exception as exc:
                print("table", ti, "format failed:", exc, flush=True)

        if not args.no_auto_merge:
            auto_merge_headers(doc, args.header_rows)
        apply_manifest(doc, manifest)

        # Rewriting cells leaves Normal spacing; normalise all cells again.
        for tbl in doc.Tables:
            try:
                tbl.Range.ParagraphFormat.SpaceBefore = 0
                tbl.Range.ParagraphFormat.SpaceAfter = 0
                tbl.Range.ParagraphFormat.LineSpacingRule = wdLineSpaceSingle
                tbl.Range.ParagraphFormat.Alignment = 0
                tbl.Range.Cells.VerticalAlignment = 1
            except Exception:
                pass

        try:
            doc.Paragraphs(1).Alignment = wdAlignParagraphCenter
            doc.Paragraphs(1).Range.ParagraphFormat.SpaceAfter = 6
        except Exception:
            pass

        try:
            for sec in doc.Sections:
                footer = sec.Footers(wdHeaderFooterPrimary)
                footer.Range.Text = ""
                footer.Range.ParagraphFormat.Alignment = wdAlignParagraphCenter
                footer.Range.Fields.Add(footer.Range, wdFieldPage)
                footer.Range.Font.Name = args.font
                footer.Range.Font.Size = 9
        except Exception as exc:
            print("footer failed:", exc, flush=True)

        doc.SaveAs2(out, FileFormat=16)
        if not args.no_pdf:
            pdf_out = pdf
            if os.path.exists(pdf):
                try:
                    os.remove(pdf)
                except OSError:
                    pdf_out = os.path.splitext(pdf)[0] + "_new.pdf"
            doc.ExportAsFixedFormat(
                OutputFileName=pdf_out, ExportFormat=wdExportFormatPDF,
                OpenAfterExport=False, OptimizeFor=0, Range=0, Item=0,
                IncludeDocProps=True, KeepIRM=True, CreateBookmarks=1,
                DocStructureTags=True, BitmapMissingFonts=True,
                UseISO19005_1=False)
            print("pdf:", pdf_out, flush=True)
        print("pages:", doc.ComputeStatistics(2), flush=True)
        print("saved:", out, flush=True)
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=0)
            except Exception:
                pass
        try:
            word.Quit()
        except Exception:
            pass
        time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
