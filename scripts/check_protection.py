#!/usr/bin/env python3
"""Audit the fleet's merge gates against sync/protection.yml.

Prints one markdown row per protected branch and exits non-zero when any
branch differs from the record, or when the token cannot read it. A row
covers the required checks and the number of approving reviews a merge
waits for.

GitHub holds the gate in one of two places, and they do not share state.
Classic branch protection answers `branches/{branch}/protection`, and
reading it needs administration:read. A repository ruleset answers
`rules/branches/{branch}` from contents:read. A repo that moves from one
to the other keeps none of its old contexts.

This script never writes. See norms/ci.md, "Branch Protection".

    python3 scripts/check_protection.py
    python3 scripts/check_protection.py --repo portolan-sdi/portolan-cli
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "sync" / "protection.yml"
REGIMES = ("protection", "ruleset")


def gh_api(path: str) -> tuple[object | None, str]:
    """Return (payload, error). payload is None when the call fails."""
    result = subprocess.run(
        ["gh", "api", path],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        lines = (result.stderr or "").strip().splitlines()
        return None, lines[-1] if lines else f"gh exited {result.returncode}"
    try:
        return json.loads(result.stdout or "null"), ""
    except json.JSONDecodeError as e:
        return None, f"unreadable answer: {e}"


class Gate(NamedTuple):
    """What a branch makes a merge wait for."""

    contexts: list[str]
    reviews: int


def protection_gate(repo: str, branch: str) -> tuple[Gate | None, str]:
    """The gate classic protection holds, or (None, why not).

    One call for both halves. The full protection object carries the
    checks and the review rule together, and a branch with no review
    rule answers null rather than zero.
    """
    payload, error = gh_api(f"repos/{repo}/branches/{branch}/protection")
    if payload is None:
        return None, error
    if not isinstance(payload, dict):
        return None, "unexpected answer shape"
    checks = payload.get("required_status_checks") or {}
    names = list(checks.get("contexts") or [])
    names += [c.get("context", "") for c in checks.get("checks") or []]
    reviews = payload.get("required_pull_request_reviews") or {}
    count = reviews.get("required_approving_review_count") or 0
    return Gate(sorted({n for n in names if n}), int(count)), ""


def ruleset_gate(repo: str, branch: str) -> tuple[Gate | None, str]:
    """The gate the rulesets covering this branch hold.

    Rulesets stack, and a merge waits for all of them, so the strictest
    review count wins and every context counts.
    """
    payload, error = gh_api(f"repos/{repo}/rules/branches/{branch}")
    if payload is None:
        return None, error
    if not isinstance(payload, list):
        return None, "unexpected answer shape"
    names: set[str] = set()
    reviews = 0
    for rule in payload:
        parameters = rule.get("parameters") or {}
        if rule.get("type") == "required_status_checks":
            for check in parameters.get("required_status_checks") or []:
                context = check.get("context")
                if context:
                    names.add(context)
        elif rule.get("type") == "pull_request":
            count = parameters.get("required_approving_review_count") or 0
            reviews = max(reviews, int(count))
    return Gate(sorted(names), reviews), ""


def live_gate(repo: str, branch: str, regime: str) -> tuple[Gate | None, str]:
    """The gate the recorded regime reports for this branch."""
    if regime == "ruleset":
        return ruleset_gate(repo, branch)
    return protection_gate(repo, branch)


def compare(wanted: list[str], live: list[str]) -> tuple[list[str], list[str]]:
    """(missing, extra) between the record and the live setting."""
    missing = sorted(set(wanted) - set(live))
    extra = sorted(set(live) - set(wanted))
    return missing, extra


def load_record() -> list[dict]:
    data = yaml.safe_load(RECORD.read_text(encoding="utf-8"))
    entries = (data or {}).get("protected")
    if not isinstance(entries, list) or not entries:
        raise SystemExit(f"{RECORD} has no 'protected' entry list")
    for entry in entries:
        regime = entry.get("regime", "protection")
        if regime not in REGIMES:
            raise SystemExit(f"{entry.get('repo')}: unknown regime {regime!r}")
    return entries


def audit(entries: list[dict]) -> int:
    """Print the table; return 1 when any branch differs."""
    print("| Repo | Branch | Regime | Missing | Extra | Reviews |")
    print("|---|---|---|---|---|---|")
    problems = 0
    for entry in entries:
        repo = entry["repo"]
        branch = entry.get("branch", "main")
        regime = entry.get("regime", "protection")
        wanted = list(entry.get("contexts") or [])
        wanted_reviews = int(entry.get("reviews", 0))
        live, error = live_gate(repo, branch, regime)
        if live is None:
            problems += 1
            print(f"| {repo} | {branch} | {regime} | UNREADABLE | {error} | - |")
            continue
        missing, extra = compare(wanted, live.contexts)
        reviews = f"{wanted_reviews}/{live.reviews}"
        if missing or extra or wanted_reviews != live.reviews:
            problems += 1
        print(
            f"| {repo} | {branch} | {regime} | "
            f"{', '.join(missing) or '-'} | {', '.join(extra) or '-'} | "
            f"{reviews} |"
        )
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="audit one owner/name repo only")
    args = parser.parse_args()

    entries = load_record()
    if args.repo:
        entries = [e for e in entries if e["repo"] == args.repo]
        if not entries:
            raise SystemExit(f"{args.repo} is not in sync/protection.yml")
    return audit(entries)


if __name__ == "__main__":
    sys.exit(main())
