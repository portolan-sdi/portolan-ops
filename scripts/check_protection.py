#!/usr/bin/env python3
"""Audit the fleet's required checks against sync/protection.yml.

Prints one markdown row per protected branch and exits non-zero when any
branch differs from the record, or when the token cannot read it.

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


def protection_contexts(repo: str, branch: str) -> tuple[list[str] | None, str]:
    """Contexts classic protection requires, or (None, why not)."""
    path = f"repos/{repo}/branches/{branch}/protection/required_status_checks"
    payload, error = gh_api(path)
    if payload is None:
        return None, error
    if not isinstance(payload, dict):
        return None, "unexpected answer shape"
    names = list(payload.get("contexts") or [])
    names += [c.get("context", "") for c in payload.get("checks") or []]
    return sorted({n for n in names if n}), ""


def ruleset_contexts(repo: str, branch: str) -> tuple[list[str] | None, str]:
    """Contexts the rulesets that cover this branch require."""
    payload, error = gh_api(f"repos/{repo}/rules/branches/{branch}")
    if payload is None:
        return None, error
    if not isinstance(payload, list):
        return None, "unexpected answer shape"
    names: set[str] = set()
    for rule in payload:
        if rule.get("type") != "required_status_checks":
            continue
        parameters = rule.get("parameters") or {}
        for check in parameters.get("required_status_checks") or []:
            context = check.get("context")
            if context:
                names.add(context)
    return sorted(names), ""


def live_contexts(repo: str, branch: str, regime: str) -> tuple[list[str] | None, str]:
    """Contexts the recorded regime reports for this branch."""
    if regime == "ruleset":
        return ruleset_contexts(repo, branch)
    return protection_contexts(repo, branch)


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
    print("| Repo | Branch | Regime | Missing | Extra |")
    print("|---|---|---|---|---|")
    problems = 0
    for entry in entries:
        repo = entry["repo"]
        branch = entry.get("branch", "main")
        regime = entry.get("regime", "protection")
        wanted = list(entry.get("contexts") or [])
        live, error = live_contexts(repo, branch, regime)
        if live is None:
            problems += 1
            print(f"| {repo} | {branch} | {regime} | UNREADABLE | {error} |")
            continue
        missing, extra = compare(wanted, live)
        if missing or extra:
            problems += 1
        print(
            f"| {repo} | {branch} | {regime} | "
            f"{', '.join(missing) or '-'} | {', '.join(extra) or '-'} |"
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
