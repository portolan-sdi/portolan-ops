#!/usr/bin/env python3
"""Check that a repo carries the org agent files in the shape ops expects.

AGENTS.md holds the norms and any repo-specific rules. CLAUDE.md holds the
import that lets Claude Code see them, and nothing else, because sync
overwrites it. A repo that keeps instructions in CLAUDE.md loses them on the
next sync run and, until then, hides them from every agent that reads
AGENTS.md instead.

    python3 scripts/check_repo_layout.py /path/to/repo

The checks are structural rather than byte-exact. A repo sitting between an
ops release and its sync pull request is behind, not broken, and should not go
red for it.

Standard library only: the reusable workflow runs this with no install step.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BEGIN_RE = re.compile(r"<!--\s*ops-sync:begin\b.*?-->", re.DOTALL)
END_RE = re.compile(r"<!--\s*ops-sync:end\s*-->")
BLOCK_RE = re.compile(r"<!--\s*ops-sync:begin\b.*?<!--\s*ops-sync:end\s*-->", re.DOTALL)
IMPORT_RE = re.compile(r"^\s*@AGENTS\.md\s*$", re.MULTILINE)

FIX_AGENTS = "Run the ops sync, or copy the block from templates/repo/AGENTS.md."
FIX_CLAUDE = "Move it into AGENTS.md, below that file's ops-sync:end marker."


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def check_agents(path: Path, is_source: bool = False) -> list[str]:
    if not path.is_file():
        return [f"AGENTS.md is missing. {FIX_AGENTS}"]

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    if is_source:
        # portolan-ops writes the block rather than receiving it, so its own
        # AGENTS.md carries no markers. Everything else still applies.
        return problems

    if not BEGIN_RE.search(text) or not END_RE.search(text):
        problems.append(f"AGENTS.md has no ops-sync block. {FIX_AGENTS}")
        return problems

    block = BLOCK_RE.search(text)
    if block is None:
        problems.append(
            "AGENTS.md has ops-sync markers in the wrong order. "
            "The begin marker must come first."
        )
        return problems

    if not strip_comments(block.group(0)).strip():
        problems.append(f"AGENTS.md's ops-sync block is empty. {FIX_AGENTS}")

    return problems


def check_claude(path: Path) -> list[str]:
    if not path.is_file():
        return [
            (
                "CLAUDE.md is missing. Claude Code never reads AGENTS.md, so "
                "without this file it sees no org norms at all. "
                "Copy templates/repo/CLAUDE.md."
            )
        ]

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    block = BLOCK_RE.search(text)
    if block is None:
        problems.append(
            "CLAUDE.md has no ops-sync block. Copy templates/repo/CLAUDE.md."
        )
    elif not IMPORT_RE.search(block.group(0)):
        problems.append(
            "CLAUDE.md's ops-sync block does not import AGENTS.md. "
            "The block must contain a line reading @AGENTS.md."
        )

    outside = BLOCK_RE.sub("", text) if block else text
    if strip_comments(outside).strip():
        lines = len([ln for ln in strip_comments(outside).splitlines() if ln.strip()])
        problems.append(
            f"CLAUDE.md carries {lines} lines outside the ops-sync block. "
            f"Sync overwrites this file. {FIX_CLAUDE}"
        )

    return problems


def check(repo: Path, is_source: bool = False) -> list[str]:
    return check_agents(repo / "AGENTS.md", is_source) + check_claude(
        repo / "CLAUDE.md"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, help="Path to the repo to check.")
    parser.add_argument(
        "--is-source",
        action="store_true",
        help="The repo is portolan-ops, whose AGENTS.md carries no markers.",
    )
    args = parser.parse_args(argv)

    if not args.repo.is_dir():
        print(f"not a directory: {args.repo}", file=sys.stderr)
        return 2

    problems = check(args.repo, args.is_source)
    if problems:
        print("This repo's agent files need work:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nWhy the two files differ:\n"
            "https://github.com/portolan-sdi/portolan-ops/blob/main/norms/repos.md",
            file=sys.stderr,
        )
        return 1

    print("Agent files ok: AGENTS.md carries the norms, CLAUDE.md imports them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
