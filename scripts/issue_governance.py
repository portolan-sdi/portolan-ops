#!/usr/bin/env python3
"""Apply the org issue rules to one issue.

Two rules run here. The project board add runs in the workflow because that
needs a token this script never sees.

Runs from .github/workflows/reusable-issue-governance.yml, which every repo
with issues enabled calls. Standard library only: the workflow runs this with
no install step.

Canonical milestones. An issue can have no milestone, `v1.0`, or
`Post-v1.0`. The rule removes any other milestone.

Transferred issues. The `transferred` event fires on the repo the issue
left, where its number now resolves to the new location. Both rules skip an
issue this repo no longer owns. The destination repo governs it through its
own `opened` event.

Canonical labels. Every label on the issue is checked against the set in
allowed-labels.json: the org-wide list plus whatever the repo adds. A
label outside that set is removed, and one comment says what went and
where the rules live. Re-running changes nothing, because an identical
comment is never posted twice.

Environment:
    GH_TOKEN        token with issues: write on the repo
    GITHUB_REPOSITORY   owner/name
    ISSUE_NUMBER    the issue to act on
    CONFIG_PATH     path to allowed-labels.json
    NORMS_URL       link the comment points at
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
MARKER = "<!-- issue-governance:stripped-labels -->"


def request(method: str, path: str, token: str, body: dict | None = None):
    """Call the REST API and return the decoded body, or None for 204."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as response:
        raw = response.read()
    return json.loads(raw) if raw else None


def paged(path: str, token: str) -> list:
    """Every page of a list endpoint, concatenated."""
    items: list = []
    page = 1
    while True:
        joiner = "&" if "?" in path else "?"
        batch = request("GET", f"{path}{joiner}per_page=100&page={page}", token)
        if not batch:
            return items
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def fetch_issue(repo: str, number: int, token: str) -> dict | None:
    """The issue, or None when this repo no longer owns it."""
    try:
        issue = request("GET", f"/repos/{repo}/issues/{number}", token)
    except urllib.error.HTTPError as error:
        if error.code not in (404, 410):
            raise
        print(f"issue: {repo}#{number} is gone, skipping")
        return None
    home = issue.get("repository_url", "")
    if home and not home.endswith(f"/repos/{repo}"):
        print(f"issue: {repo}#{number} now lives at {home}, skipping")
        return None
    return issue


def allowed_labels(config_path: str, repo_name: str) -> set[str]:
    """The label names this repo may carry."""
    with open(config_path, encoding="utf-8") as handle:
        config = json.load(handle)
    names = set(config["org_wide"])
    names.update(config.get("per_repo", {}).get(repo_name, []))
    return names


def allowed_milestones(config_path: str) -> set[str]:
    """The milestone names an issue may carry."""
    with open(config_path, encoding="utf-8") as handle:
        config = json.load(handle)
    return set(config["milestones"])


def comment_body(stripped: list[str], norms_url: str) -> str:
    """The one comment posted when labels come off."""
    listed = ", ".join(f"`{name}`" for name in stripped)
    plural = "labels" if len(stripped) > 1 else "label"
    return (
        f"{MARKER}\n"
        f"Removed {plural} outside the canonical set: {listed}.\n\n"
        f"Issue labels come from a fixed taxonomy so that a query means the "
        f"same thing in every repo. The set, and how to change it, is in "
        f"[repo norms]({norms_url}). If one of these belongs in the "
        f"taxonomy, open an issue against portolan-ops rather than "
        f"re-adding it here."
    )


def strip_labels(
    repo: str,
    number: int,
    token: str,
    issue: dict,
    allowed: set[str],
    norms_url: str,
) -> int:
    """Remove labels outside the canonical set. Return how many went."""
    present = [label["name"] for label in issue.get("labels", [])]
    stripped = sorted(name for name in present if name not in allowed)
    if not stripped:
        print("labels: nothing to strip")
        return 0

    for name in stripped:
        quoted = urllib.parse.quote(name, safe="")
        try:
            request("DELETE", f"/repos/{repo}/issues/{number}/labels/{quoted}", token)
            print(f"labels: removed {name}")
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            print(f"labels: {name} already gone")

    body = comment_body(stripped, norms_url)
    existing = paged(f"/repos/{repo}/issues/{number}/comments", token)
    if any(comment.get("body") == body for comment in existing):
        print("comment: identical comment already present, not posting")
        return len(stripped)

    request("POST", f"/repos/{repo}/issues/{number}/comments", token, {"body": body})
    print("comment: posted")
    return len(stripped)


def strip_milestone(
    repo: str, number: int, token: str, issue: dict, allowed: set[str]
) -> bool:
    """Remove a milestone outside the canonical set."""
    milestone = issue.get("milestone")
    if milestone is None:
        print("milestone: none")
        return False
    if milestone["title"] in allowed:
        print(f"milestone: {milestone['title']} is allowed")
        return False
    request(
        "PATCH",
        f"/repos/{repo}/issues/{number}",
        token,
        {"milestone": None},
    )
    print(f"milestone: removed {milestone['title']}")
    return True


def main() -> int:
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    number = int(os.environ["ISSUE_NUMBER"])
    config_path = os.environ["CONFIG_PATH"]
    norms_url = os.environ["NORMS_URL"]

    issue = fetch_issue(repo, number, token)
    if issue is None:
        return 0

    labels = allowed_labels(config_path, repo.split("/", 1)[1])
    milestones = allowed_milestones(config_path)
    strip_milestone(repo, number, token, issue, milestones)
    strip_labels(repo, number, token, issue, labels, norms_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
