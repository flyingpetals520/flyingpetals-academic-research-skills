#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only AST scan of a Python research repository.

Never imports or executes repository code, never writes inside --root.
Example:
  python scan_repo.py --root /path/to/repo --out codebase_scan.json
"""
import argparse
import ast
import json
import os
import re
import sys

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
MAX_FILE_BYTES = 1_000_000

CATEGORY_TOKENS = {
    "attention": ("attention", "attn", "flash", "sdpa"),
    "moe": ("moe", "expert", "router", "routing"),
    "optimizer": ("optim", "optimizer", "muon", "adam", "sgd"),
    "train": ("train", "trainer", "pretrain"),
    "config": ("config", "configs", "args", "settings", "hparams"),
    "data": ("data", "dataset", "dataloader", "tokenizer", "corpus"),
    "logging": ("log", "logging", "wandb", "tensorboard", "metrics"),
    "test": ("test", "tests", "pytest"),
    "kernel": ("kernel", "kernels", "cuda", "triton"),
    "model": ("model", "models", "module", "modules", "layer", "layers"),
}


def classify_path(path):
    """Return likely module categories from a file path."""
    norm = path.lower().replace("\\", "/")
    words = set(re.split(r"[^a-z0-9]+", norm))
    cats = []
    for cat, tokens in CATEGORY_TOKENS.items():
        if any(tok in words for tok in tokens):
            cats.append(cat)
    return cats


def _imports(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return sorted(found)


def _config_keys(tree):
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    found.add(key.value)
        elif isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in {"config", "cfg", "args", "ArgumentParser", "add_argument"}:
                for kw in node.keywords:
                    if kw.arg:
                        found.add(kw.arg)
    return sorted(found)


def scan_repo(root, max_files=2000):
    """Scan a repo read-only and return a JSON-serializable summary."""
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise ValueError("not a directory: %s" % root)

    modules = []
    files_seen = 0
    python_files = 0
    skipped_large = 0
    parse_errors = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        )
        for name in sorted(filenames):
            if files_seen >= max_files:
                break
            files_seen += 1
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if not name.endswith(".py"):
                continue
            try:
                if os.path.getsize(full) > MAX_FILE_BYTES:
                    skipped_large += 1
                    continue
                with open(full, "rb") as fh:
                    source = fh.read().decode("utf-8", "replace")
                tree = ast.parse(source, filename=full)
            except (OSError, SyntaxError, ValueError):
                parse_errors += 1
                continue

            python_files += 1
            modules.append(
                {
                    "path": rel,
                    "categories": classify_path(rel),
                    "classes": [
                        n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
                    ],
                    "functions": [
                        n.name
                        for n in ast.walk(tree)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ],
                    "imports": _imports(tree),
                    "config_keys": _config_keys(tree),
                }
            )

    return {
        "root": root,
        "modules": modules,
        "summary": {
            "files": files_seen,
            "python_files": python_files,
            "classes": sum(len(m["classes"]) for m in modules),
            "functions": sum(len(m["functions"]) for m in modules),
            "categories": sorted({c for m in modules for c in m["categories"]}),
            "skipped_large": skipped_large,
            "parse_errors": parse_errors,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only AST scan of a Python repo")
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-files", type=int, default=2000)
    args = parser.parse_args(argv)

    try:
        result = scan_repo(args.root, args.max_files)
    except Exception as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    s = result["summary"]
    print(
        "scanned %d files (%d Python) -> %s | classes=%d functions=%d categories=%s"
        % (
            s["files"],
            s["python_files"],
            args.out,
            s["classes"],
            s["functions"],
            ",".join(s["categories"]) or "-",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
