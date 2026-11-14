#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search arXiv and emit a CSV/JSON paper list.

Stdlib only. Example:
  python search_arxiv.py --query "scaling laws language models" \
      --max-results 20 --out papers.csv
"""
import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def _compact(text):
    return " ".join((text or "").split())


def _date_bound(value, end=False):
    if not value:
        return "199101010000" if not end else "210001012359"
    digits = value.replace("-", "")
    if len(digits) != 8:
        raise ValueError("date must be YYYY-MM-DD: %s" % value)
    return digits + ("2359" if end else "0000")


def build_query_url(query, max_results=20, start_date=None, end_date=None, category=None):
    """Build an arXiv API query URL with optional date and category filters."""
    parts = ["all:%s" % query]
    if category:
        parts.append("cat:%s" % category)
    if start_date or end_date:
        parts.append(
            "submittedDate:[%s TO %s]"
            % (_date_bound(start_date, end=False), _date_bound(end_date, end=True))
        )
    params = {
        "search_query": " AND ".join(parts),
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    return ARXIV_API + "?" + urllib.parse.urlencode(params)


def parse_atom(xml_text):
    """Parse an arXiv Atom feed into a list of paper dicts."""
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall("a:entry", NS):
        raw_id = _compact(entry.findtext("a:id", default="", namespaces=NS))
        arxiv_id = raw_id.rsplit("/abs/", 1)[-1]
        arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
        papers.append(
            {
                "title": _compact(entry.findtext("a:title", default="", namespaces=NS)),
                "authors": [
                    _compact(a.findtext("a:name", default="", namespaces=NS))
                    for a in entry.findall("a:author", NS)
                ],
                "published": _compact(entry.findtext("a:published", default="", namespaces=NS)),
                "updated": _compact(entry.findtext("a:updated", default="", namespaces=NS)),
                "arxiv_id": arxiv_id,
                "categories": [c.get("term", "") for c in entry.findall("a:category", NS)],
                "abstract": _compact(entry.findtext("a:summary", default="", namespaces=NS)),
                "url": raw_id,
            }
        )
    return papers


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "scaling-law-frontier-scout/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def write_output(papers, out, fmt):
    if fmt == "json":
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(papers, fh, ensure_ascii=False, indent=2)
        return
    fields = ["title", "authors", "published", "updated", "arxiv_id", "categories", "abstract", "url"]
    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for p in papers:
            row = dict(p)
            row["authors"] = "; ".join(p["authors"])
            row["categories"] = "; ".join(p["categories"])
            writer.writerow(row)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search arXiv and write papers.csv/json")
    parser.add_argument("--query", required=True, help="search terms")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--start-date", help="YYYY-MM-DD")
    parser.add_argument("--end-date", help="YYYY-MM-DD")
    parser.add_argument("--category", help="e.g. cs.LG, cs.CL")
    parser.add_argument("--out", required=True)
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    args = parser.parse_args(argv)

    url = build_query_url(
        args.query, args.max_results, args.start_date, args.end_date, args.category
    )
    try:
        papers = parse_atom(fetch(url))
    except Exception as exc:  # network / XML errors should be visible, not silent
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    write_output(papers, args.out, args.format)
    print("retrieved %d papers -> %s" % (len(papers), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
