#!/usr/bin/env python3
"""Keep repository automation enabled across the Portolan organization.

GitHub can disable one workflow without disabling Actions for its repository.
This occurs for scheduled workflows in forks and after repository inactivity.
The organization Actions policy does not override those workflow states.

This script restores three settings for each active organization repository:

* GitHub Actions is enabled.
* GitHub auto-merge is enabled.
* Each workflow on the default branch is active.

The default mode reports drift and changes nothing. Pass ``--apply`` from the
scheduled workflow after the GitHub App has Actions and Administration write
permissions.

    python3 scripts/reconcile_repo_automation.py
    python3 scripts/reconcile_repo_automation.py --apply
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import NamedTuple


class Change(NamedTuple):
    """One repository setting that differs from the organization policy."""

    repo: str
    kind: str
    target: str


def gh_api(path: str, method: str = "GET", body: dict | None = None) -> object:
    """Call the GitHub API and decode one JSON response."""
    command = ["gh", "api", path]
    if method != "GET":
        command.extend(["--method", method])
    payload = None
    if body is not None:
        command.extend(["--input", "-"])
        payload = json.dumps(body)
    result = subprocess.run(
        command,
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error = (result.stderr or "").strip()
        raise RuntimeError(error or f"gh exited {result.returncode}")
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def list_repos(org: str) -> list[dict]:
    """Return active repositories in the organization."""
    payload = gh_api(f"orgs/{org}/repos?per_page=100&type=all")
    if not isinstance(payload, list):
        raise TypeError("the repository list has an unexpected shape")
    return [
        repo
        for repo in payload
        if not repo.get("archived") and not repo.get("disabled")
    ]


def repo_changes(repo: str) -> list[Change]:
    """Return automation settings that need repair for one repository."""
    changes: list[Change] = []
    settings = gh_api(f"repos/{repo}")
    if not isinstance(settings, dict):
        raise TypeError(f"{repo}: repository settings have an unexpected shape")
    if not settings.get("allow_auto_merge"):
        changes.append(Change(repo, "auto-merge", "repository"))

    actions = gh_api(f"repos/{repo}/actions/permissions")
    if not isinstance(actions, dict):
        raise TypeError(f"{repo}: Actions settings have an unexpected shape")
    if not actions.get("enabled"):
        changes.append(Change(repo, "Actions", "repository"))

    payload = gh_api(f"repos/{repo}/actions/workflows?per_page=100")
    if not isinstance(payload, dict) or not isinstance(payload.get("workflows"), list):
        raise TypeError(f"{repo}: workflow list has an unexpected shape")
    for workflow in payload["workflows"]:
        if workflow.get("state") != "active":
            target = str(workflow.get("path") or workflow.get("id") or "unknown")
            changes.append(Change(repo, "workflow", target))
    return changes


def apply_change(change: Change) -> None:
    """Restore one repository setting."""
    if change.kind == "auto-merge":
        gh_api(f"repos/{change.repo}", "PATCH", {"allow_auto_merge": True})
        return
    if change.kind == "Actions":
        gh_api(
            f"repos/{change.repo}/actions/permissions",
            "PUT",
            {"enabled": True, "allowed_actions": "all"},
        )
        return

    workflows = gh_api(f"repos/{change.repo}/actions/workflows?per_page=100")
    assert isinstance(workflows, dict)
    match = next(
        workflow
        for workflow in workflows["workflows"]
        if (workflow.get("path") or workflow.get("id")) == change.target
    )
    gh_api(
        f"repos/{change.repo}/actions/workflows/{match['id']}/enable",
        "PUT",
    )


def reconcile(org: str, apply: bool) -> int:
    """Report or repair organization automation drift."""
    changes: list[Change] = []
    for entry in list_repos(org):
        changes.extend(repo_changes(entry["full_name"]))

    if not changes:
        print(f"All active {org} repositories match the automation policy.")
        return 0

    print("| Repository | Setting | Target | Result |")
    print("|---|---|---|---|")
    for change in changes:
        result = "needs repair"
        if apply:
            apply_change(change)
            result = "repaired"
        print(f"| {change.repo} | {change.kind} | {change.target} | {result} |")
    return 0 if apply else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org", default="portolan-sdi")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return reconcile(args.org, args.apply)


if __name__ == "__main__":
    sys.exit(main())
