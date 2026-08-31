#!/usr/bin/env python3
"""Fail when the release tag lags main on enforcement files.

Downstream repo-checks callers pin this repo's reusable workflow at a major
tag. A rule merged to main reaches nobody until the tag moves, and moving it
is a manual step (norms/ci.md, "Changing and releasing CI"). This check makes
forgetting loud: it fails whenever a file the fleet enforces with has changed
since the tag.

    python3 scripts/check_release_tag.py            # checks v1 against HEAD
    python3 scripts/check_release_tag.py --tag v2

Needs the full history and tags: run after `git fetch --tags` on an
unshallow clone. Standard library only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

# Files whose behavior downstream repos consume through the tag. A change
# here that the tag does not carry means the fleet runs stale rules.
GUARDED = (
    ".github/workflows/reusable-repo-checks.yml",
    "scripts/lint_body.py",
    "scripts/check_repo_layout.py",
    ".github/workflows/reusable-issue-governance.yml",
    ".github/workflows/reusable-pr-board.yml",
    "scripts/issue_governance.py",
    "issue-governance/allowed-labels.json",
)


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def changed_since(tag: str, paths: tuple[str, ...], run=run_git) -> list[str]:
    """Guarded files that differ between the tag and HEAD.

    Raises RuntimeError when the tag cannot be resolved.
    """
    resolved = run(["rev-parse", "--verify", f"refs/tags/{tag}"])
    if resolved.returncode != 0:
        raise RuntimeError(
            f"Tag {tag} is not present. Fetch tags first: git fetch --tags"
        )
    diff = run(["diff", "--name-only", f"refs/tags/{tag}..HEAD", "--", *paths])
    if diff.returncode != 0:
        raise RuntimeError(diff.stderr.strip() or "git diff failed")
    return [line for line in diff.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="v1")
    args = parser.parse_args(argv)

    try:
        stale = changed_since(args.tag, GUARDED)
    except RuntimeError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if stale:
        print(
            f"{args.tag} lags main on files the fleet enforces with:\n",
            file=sys.stderr,
        )
        for path in stale:
            print(f"  - {path}", file=sys.stderr)
        print(
            f"\nEvery downstream repo-checks run still uses the old rules. "
            f"Release per norms/ci.md, then move the tag:\n"
            f"  git tag -f {args.tag} origin/main && "
            f"git push -f origin {args.tag}",
            file=sys.stderr,
        )
        return 1

    print(f"{args.tag} carries the current enforcement files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
