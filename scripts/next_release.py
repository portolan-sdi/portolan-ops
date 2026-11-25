#!/usr/bin/env python3
"""Compute the next release tag from the conventional commits since the last.

release.yml runs this on every green push to main. It finds the newest
vX.Y.Z tag that is an ancestor of the commit and reads the commits since it.
A `feat` commit bumps the minor version. Anything else bumps the patch.

A breaking commit (`type!:` or a `BREAKING CHANGE:` footer) stops the
release, because v1 must not move to code that breaks its callers. Release
it under v2 by hand, or pass `--bump minor` when no caller uses what broke.
An explicit `--bump` skips the breaking check.

    python3 scripts/next_release.py                 # checks HEAD
    python3 scripts/next_release.py --bump minor --rev <sha>

On a release, stdout is the tag on the first line and one `- subject` line
per commit after it. With nothing to release, stdout is empty and the exit
code is 0. Needs the full history and tags. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

VERSION = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
SUBJECT = re.compile(r"^(?P<type>\w+)(\([^)]*\))?(?P<bang>!)?:")
FOOTER = re.compile(r"^BREAKING[ -]CHANGE:", re.MULTILINE)


class ReleaseError(Exception):
    """The release cannot go ahead without a person."""


def run_git(args: list[str]) -> str:
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise ReleaseError(done.stderr.strip() or f"git {args[0]} failed")
    return done.stdout


def versions(tags: str) -> list[tuple[int, int, int]]:
    """The vX.Y.Z tags in `git tag` output, as numbers. Others are skipped."""
    found = []
    for line in tags.splitlines():
        match = VERSION.match(line.strip())
        if match:
            found.append((int(match[1]), int(match[2]), int(match[3])))
    return found


def is_breaking(subject: str, body: str) -> bool:
    match = SUBJECT.match(subject)
    return bool(match and match["bang"]) or bool(FOOTER.search(body))


def bump_for(commits: list[tuple[str, str]]) -> str:
    """minor when any commit is a feat, patch otherwise."""
    for subject, _ in commits:
        match = SUBJECT.match(subject)
        if match and match["type"] == "feat":
            return "minor"
    return "patch"


def plan(rev: str, bump: str, run=run_git) -> tuple[str, list[str]] | None:
    """The next tag and the commit subjects it covers. None: nothing to do."""
    later = versions(run(["tag", "--list", "v*", "--contains", rev]))
    base = max(versions(run(["tag", "--list", "v*", "--merged", rev])), default=None)
    if base is None:
        raise ReleaseError(f"No vX.Y.Z tag is an ancestor of {rev}.")
    # A tag at or after this commit means a newer run already released it.
    if later:
        return None
    base_tag = "v{}.{}.{}".format(*base)
    log = run(
        [
            "log",
            "--reverse",
            "--no-merges",
            "--format=%s%x00%b%x1e",
            f"{base_tag}..{rev}",
        ]
    )
    commits = []
    for record in log.split("\x1e"):
        if record.strip():
            subject, _, body = record.strip("\n").partition("\x00")
            commits.append((subject, body))
    if not commits:
        return None

    if bump == "auto":
        breaking = [s for s, b in commits if is_breaking(s, b)]
        if breaking:
            listed = "\n".join(f"  - {s}" for s in breaking)
            raise ReleaseError(
                f"Breaking commits since {base_tag}:\n{listed}\n\n"
                "v1 is not moved to a breaking change. Release it under v2 "
                "by hand, or, when no caller uses what broke, run:\n"
                "  gh workflow run release.yml -f bump=minor"
            )
        bump = bump_for(commits)

    major, minor, patch = base
    if bump == "minor":
        tag = f"v{major}.{minor + 1}.0"
    else:
        tag = f"v{major}.{minor}.{patch + 1}"
    if versions(run(["tag", "--list", tag])):
        raise ReleaseError(f"{tag} already exists but is not an ancestor of {rev}.")
    return tag, [subject for subject, _ in commits]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bump", choices=("auto", "patch", "minor"), default="auto")
    parser.add_argument("--rev", default="HEAD")
    args = parser.parse_args(argv)

    try:
        result = plan(args.rev, args.bump)
    except ReleaseError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    if result is None:
        print("nothing to release", file=sys.stderr)
        return 0
    tag, subjects = result
    print(tag)
    for subject in subjects:
        print(f"- {subject}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
