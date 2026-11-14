#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a comparison matrix from structured paper-note JSON files.

Example:
  python build_matrix.py --notes notes/ --out matrix.md --csv matrix.csv
"""
import argparse
import csv
import json
import os
import sys

REQUIRED = [
    "title",
    "arxiv_id",
    "year",
    "venue",
    "axis",
    "setup",
    "law_form",
    "exponents",
    "assumptions",
    "evidence_strength",
    "limitations",
    "key_claims",
    "sources",
]

COLUMNS = [
    ("Title", "title"),
    ("arXiv", "arxiv_id"),
    ("Year", "year"),
    ("Venue", "venue"),
    ("Axis", "axis"),
    ("Law form", "law_form"),
    ("Exponents", "exponents"),
    ("Assumptions", "assumptions"),
    ("Evidence", "evidence_strength"),
    ("Key claims", "key_claims"),
]


def _cell(value):
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(v) for v in value)
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def load_notes(notes_dir):
    """Load and validate every *.json note in notes_dir (sorted by filename)."""
    notes = []
    for name in sorted(os.listdir(notes_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(notes_dir, name)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        missing = [key for key in REQUIRED if key not in data]
        if missing:
            raise ValueError("%s missing keys: %s" % (path, ", ".join(missing)))
        notes.append(data)
    return notes


def to_markdown(notes):
    lines = [
        "| " + " | ".join(header for header, _ in COLUMNS) + " |",
        "|" + "|".join("---" for _ in COLUMNS) + "|",
    ]
    for note in notes:
        lines.append("| " + " | ".join(_cell(note[key]) for _, key in COLUMNS) + " |")
    return "\n".join(lines) + "\n"


def to_csv_rows(notes):
    return [
        {header: _cell(note[key]) for header, key in COLUMNS}
        for note in notes
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a paper comparison matrix")
    parser.add_argument("--notes", required=True, help="directory of *.json notes")
    parser.add_argument("--out", required=True, help="Markdown output path")
    parser.add_argument("--csv", help="optional CSV output path")
    args = parser.parse_args(argv)

    try:
        notes = load_notes(args.notes)
    except Exception as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(to_markdown(notes))
    if args.csv:
        rows = to_csv_rows(notes)
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=[h for h, _ in COLUMNS])
            writer.writeheader()
            writer.writerows(rows)
    print("wrote %d notes -> %s" % (len(notes), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
