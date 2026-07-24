#!/usr/bin/env python3
"""Validate sync/manifest.yml.

Checks that the manifest parses, every src path exists in this repo, every
target has a well-formed owner/name repo and a non-empty dest, modes are
known, block-mode sources carry the ops-sync markers, and no two entries
write the same (repo, dest) pair.

    python3 scripts/check_manifest.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "sync" / "manifest.yml"
REPO_RE = re.compile(r"^[\w.-]+/[\w.-]+$")
MODES = {"copy", "block"}


def main() -> int:
    errors: list[str] = []
    try:
        data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"manifest does not parse: {e}", file=sys.stderr)
        return 1

    entries = (data or {}).get("sync")
    if not isinstance(entries, list) or not entries:
        print("manifest has no 'sync' entry list", file=sys.stderr)
        return 1

    seen: set[tuple[str, str]] = set()
    for i, entry in enumerate(entries):
        where = f"sync[{i}]"
        src = entry.get("src")
        if not src or not (ROOT / src).is_file():
            errors.append(f"{where}: src missing on disk: {src!r}")
        mode = entry.get("mode", "copy")
        if mode not in MODES:
            errors.append(f"{where}: unknown mode {mode!r}")
        if mode == "block" and src and (ROOT / src).is_file():
            text = (ROOT / src).read_text(encoding="utf-8")
            if "ops-sync:begin" not in text or "ops-sync:end" not in text:
                errors.append(f"{where}: block src lacks ops-sync markers")
        targets = entry.get("targets")
        if not isinstance(targets, list) or not targets:
            errors.append(f"{where}: no targets")
            continue
        for j, target in enumerate(targets):
            twhere = f"{where}.targets[{j}]"
            repo = target.get("repo", "")
            dest = target.get("dest", "")
            if not REPO_RE.match(repo):
                errors.append(f"{twhere}: bad repo {repo!r}")
            if not dest or dest.startswith("/") or ".." in dest:
                errors.append(f"{twhere}: bad dest {dest!r}")
            key = (repo, dest)
            if key in seen:
                errors.append(f"{twhere}: duplicate write to {repo}:{dest}")
            seen.add(key)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"manifest ok: {len(entries)} entries, {len(seen)} writes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
