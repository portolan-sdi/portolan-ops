#!/usr/bin/env python3
"""Compare the canonical label set against the labels the org actually has.

The enforcement workflow removes any label outside
issue-governance/allowed-labels.json. A label created in a repo and left out
of that file therefore disappears the next time anyone touches the issue, and
nothing warns whoever created it. Run this after adding a label anywhere, and
before changing the file:

    python3 scripts/check_label_config.py

Reads the live label list with `gh`, so it needs an authenticated CLI and
network. Exits non-zero when a repo defines a label the set does not allow.
The reverse direction, a label allowed but defined nowhere, is reported and
does not fail: it costs nothing and often means the label is coming.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "issue-governance" / "allowed-labels.json"
ORG = "portolan-sdi"


def run(args: list[str]) -> str:
    """Run gh and return stdout, or exit with its error."""
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        sys.exit(f"{' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def repos_with_issues() -> list[str]:
    """Every non-archived repo in the org that has issues turned on."""
    fields = "name,hasIssuesEnabled"
    raw = run(
        ["gh", "repo", "list", ORG, "--no-archived", "--limit", "200", "--json", fields]
    )
    return sorted(r["name"] for r in json.loads(raw) if r["hasIssuesEnabled"])


def labels(repo: str) -> set[str]:
    """Label names defined in one repo."""
    raw = run(["gh", "api", f"repos/{ORG}/{repo}/labels?per_page=100"])
    return {label["name"] for label in json.loads(raw)}


def main() -> int:
    config = json.loads(CONFIG.read_text())
    org_wide = set(config["org_wide"])
    per_repo = config.get("per_repo", {})

    defined: dict[str, set[str]] = {}
    for repo in repos_with_issues():
        defined[repo] = labels(repo)

    problems = 0
    for repo, names in defined.items():
        stray = sorted(names - org_wide - set(per_repo.get(repo, [])))
        if stray:
            problems += 1
            print(f"{repo}: defines labels the set does not allow: {', '.join(stray)}")

    everywhere: set[str] = set().union(*defined.values()) if defined else set()
    unused = sorted(org_wide - everywhere)
    if unused:
        print(f"note: allowed org-wide but defined nowhere: {', '.join(unused)}")
    for repo, extras in per_repo.items():
        missing = sorted(set(extras) - defined.get(repo, set()))
        if missing:
            print(
                f"note: allowed in {repo} but not defined there: {', '.join(missing)}"
            )

    if problems:
        print(
            f"\n{problems} repo(s) would have a label stripped. Either delete "
            f"the label there or add it to {CONFIG.relative_to(ROOT)} and to "
            f"the table in norms/repos.md."
        )
        return 1

    print(f"label config ok: {len(defined)} repos, no label outside the set")
    return 0


if __name__ == "__main__":
    sys.exit(main())
