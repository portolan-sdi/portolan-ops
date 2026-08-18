#!/usr/bin/env python3
"""Fail when a workflow filters its pull_request trigger by branch.

GitHub matches `branches:` under `pull_request` against the base branch.
A workflow that names `main` there queues nothing for a pull request into
any other branch, so a stacked or release branch merges unchecked. The
`push` trigger keeps its filter: a push to a side branch is not a merge.

Scans this repo's own workflows and the caller templates under ci/, which
the fleet copies verbatim.

    python3 scripts/check_workflow_triggers.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = (".github/workflows", "ci")
FILTER_KEYS = ("branches", "branches-ignore")


def workflow_files(root: Path) -> list[Path]:
    """Every workflow file under the scanned directories, sorted."""
    found: list[Path] = []
    for name in SCAN_DIRS:
        directory = root / name
        if not directory.is_dir():
            continue
        for suffix in ("*.yml", "*.yaml"):
            found.extend(directory.rglob(suffix))
    return sorted(found)


def branch_filters(text: str) -> list[str]:
    """Filter keys the pull_request trigger carries. Empty when clean.

    PyYAML reads the bare `on:` key as the boolean True, because YAML 1.1
    says so. Look for both spellings rather than trusting either.
    """
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return []
    triggers = data.get("on", data.get(True))
    if not isinstance(triggers, dict):
        return []
    for event in ("pull_request", "pull_request_target"):
        config = triggers.get(event)
        if not isinstance(config, dict):
            continue
        found = [key for key in FILTER_KEYS if key in config]
        if found:
            return found
    return []


def main() -> int:
    problems: list[str] = []
    files = workflow_files(ROOT)
    for path in files:
        try:
            found = branch_filters(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            problems.append(f"{path.relative_to(ROOT)}: does not parse: {e}")
            continue
        for key in found:
            rel = path.relative_to(ROOT)
            problems.append(
                f"{rel}: pull_request carries {key!r}. Delete it. A pull "
                f"request into another branch runs none of these checks."
            )

    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"pull_request triggers ok: {len(files)} workflows scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
