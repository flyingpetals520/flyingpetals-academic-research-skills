#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate long/over-connected sentence candidates from a LaTeX paper.

This is a triage helper for stage S3 of paper-writing-audit, not a judge.
It strips equations/figures/tables and most LaTeX markup, splits the remaining
prose into sentences, and ranks them by length plus the density of "and",
semicolons, relative clauses and comma-separated clause chains.

The model must still read every section manually: the scanner misses
cross-line splits and sentences whose wording changed after scanning.

Usage:
  python scan_sentences.py paper.tex --out candidates.md --json candidates.json
"""
import argparse
import json
import re
import sys

SKIP_ENVS = [
    "equation", "equation*", "align", "align*", "alignat", "alignat*",
    "gather", "gather*", "multline", "multline*", "eqnarray", "eqnarray*",
    "table", "table*", "figure", "figure*", "tabular", "tabular*",
    "algorithm", "algorithm*", "algorithmic", "lstlisting", "verbatim",
]
BEGIN_RE = re.compile(r"\\begin\{(" + "|".join(re.escape(e) for e in SKIP_ENVS) + r")\}")
END_RE = re.compile(r"\\end\{(" + "|".join(re.escape(e) for e in SKIP_ENVS) + r")\}")
SECTION_RE = re.compile(r"\\(section|subsection|subsubsection)\*?\{([^{}]*)\}")


def strip_line(line):
    """Remove comments and inline math/commands from one line of prose."""
    line = re.sub(r"(?<!\\)%.*", "", line)
    line = re.sub(r"\$\$.*?\$\$", " MATH ", line)
    line = re.sub(r"\$[^$]*\$", " MATH ", line)
    line = re.sub(r"\\\[.*?\\\]", " MATH ", line)
    line = re.sub(r"\\\(.*?\\\)", " MATH ", line)
    # two-argument link: keep only the visible text
    line = re.sub(r"\\href\{[^{}]*\}\{([^{}]*)\}", r"\1", line)
    line = re.sub(
        r"\\(cite|citep|citet|ref|eqref|label|url|bibliography|"
        r"bibliographystyle|includegraphics)\*?(\[[^\]]*\])?\{[^{}]*\}", "", line)
    # formatting commands: keep the argument
    for _ in range(4):
        line = re.sub(
            r"\\(textbf|textit|emph|text|mathrm|mathbf|mathsf|mathtt|"
            r"operatorname|textsc|underline)\{([^{}]*)\}", r"\2", line)
        line = re.sub(
            r"\\(?:[A-Za-z]+\*?)(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", line)
    line = re.sub(r"\\[A-Za-z]+\*?", " ", line)
    line = line.replace("{", "").replace("}", "")
    return line


def clean_text(text):
    text = text.replace("~", " ")
    text = re.sub(r"\\,|\\;|\\!|\\ ", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


ABBREV = [
    "e.g.", "i.e.", "et al.", "Fig.", "Figs.", "Eq.", "Eqs.", "Sec.",
    "Secs.", "Tab.", "vs.", "resp.", "cf.", "approx.", "et al",
]


def split_sentences(text):
    protected = text
    for ab in ABBREV:
        protected = protected.replace(ab, ab.replace(".", "․"))
    protected = re.sub(r"(\d)\.(\d)", r"\1․\2", protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])", protected)
    out = []
    for p in parts:
        p = p.replace("․", ".").strip()
        if len(p.split()) >= 8:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tex")
    ap.add_argument("--out", default="sentence_candidates.md")
    ap.add_argument("--json", default="sentence_candidates.json")
    ap.add_argument("--min-words", type=int, default=35,
                    help="shortest sentence reported as a candidate")
    args = ap.parse_args()

    with open(args.tex, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    paragraphs = []  # (section, start_line, text)
    section = "(front matter)"
    buf, buf_line = [], None
    skip_env = 0

    def flush():
        nonlocal buf, buf_line
        if buf:
            text = clean_text(" ".join(buf))
            if text:
                paragraphs.append((section, buf_line, text))
        buf, buf_line = [], None

    for no, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        if "\\begin{thebibliography}" in line or line.strip().startswith("\\bibliography"):
            flush()
            break
        m = BEGIN_RE.search(line)
        if m:
            flush()
            skip_env += 1
            continue
        if skip_env:
            if END_RE.search(line):
                skip_env -= 1
            continue
        sm = SECTION_RE.search(line)
        if sm:
            flush()
            section = sm.group(2)
            line = SECTION_RE.sub(" ", line)
        stripped = strip_line(line)
        if not stripped.strip():
            flush()
            continue
        if buf_line is None:
            buf_line = no
        buf.append(stripped)

    flush()

    candidates = []
    choppy = []
    for section, line_no, para in paragraphs:
        sents = split_sentences(para)
        for s in sents:
            words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9\-']*", s))
            and_n = len(re.findall(r"\band\b", s, re.I))
            semi = s.count(";")
            rel = len(re.findall(r"\b(which|while|where|that|who|whom|whose)\b",
                                 s, re.I))
            commas = s.count(",")
            triggers = []
            if words >= 60:
                triggers.append("very-long")
            elif words >= 45:
                triggers.append("long")
            if and_n >= 3:
                triggers.append("and-dense")
            if semi >= 1:
                triggers.append("semicolon")
            if rel >= 3 and words >= 40:
                triggers.append("nested-clauses")
            if commas >= 5 and words >= 40:
                triggers.append("clause-chain")
            if (words >= 35 and (and_n >= 2 or rel >= 2 or commas >= 4)
                    and not triggers):
                triggers.append("borderline")
            if not triggers or words < args.min_words:
                continue
            score = (words / 12.0 + 2.0 * and_n + 3.0 * semi
                     + 0.8 * rel + 0.3 * commas)
            candidates.append({
                "section": section,
                "line": line_no,
                "words": words,
                "and": and_n,
                "semicolon": semi,
                "relative": rel,
                "commas": commas,
                "triggers": triggers,
                "score": round(score, 2),
                "sentence": s,
            })
        # choppy runs: >=3 consecutive sentences shorter than 14 words
        run = []
        for s in sents + [None]:
            n = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9\-']*", s)) if s else 999
            # Math-heavy "sentences" are definitions, not choppy prose.
            if s and n < 14 and "MATH" not in s:
                run.append(s)
            else:
                if len(run) >= 3:
                    choppy.append({
                        "section": section,
                        "line": line_no,
                        "count": len(run),
                        "first": run[0],
                        "sentences": run,
                    })
                run = []

    candidates.sort(key=lambda x: -x["score"])
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump({"candidates": candidates, "choppy_runs": choppy},
                  fh, ensure_ascii=False, indent=1)

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# S3 sentence candidates\n\n")
        fh.write("Scanner output only. Re-read every section before judging; "
                 "cross-line sentences can be missed.\n\n")
        fh.write("| # | section | src line | words | and | ; | rel | triggers | sentence |\n")
        fh.write("|---|---|---|---|---|---|---|---|---|\n")
        for i, c in enumerate(candidates, 1):
            sent = c["sentence"].replace("|", "\\|")
            fh.write(f"| {i} | {c['section']} | {c['line']} | {c['words']} | "
                     f"{c['and']} | {c['semicolon']} | {c['relative']} | "
                     f"{','.join(c['triggers'])} | {sent} |\n")
        fh.write("\n## Choppy runs (>=3 consecutive short sentences)\n\n")
        if not choppy:
            fh.write("(none)\n")
        for i, r in enumerate(choppy, 1):
            fh.write(f"{i}. {r['section']} (src line {r['line']}): "
                     f"{r['count']} short sentences, starting with "
                     f"\"{r['first']}\"\n")

    print(f"candidates: {len(candidates)}  choppy runs: {len(choppy)}")
    print("markdown:", args.out)
    print("json:", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
