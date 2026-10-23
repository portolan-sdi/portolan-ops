#!/usr/bin/env python3
"""Apply the org issue rules to one issue.

Four rules run here. The project board add runs in the workflow because that
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

One priority. An issue carries at most one of P0, P1, P2, and P3. When it
has none, the rule applies the one the body's Priority section names. The
issue forms ask for it, and the writing hook requires it. When a person adds
a second P label, the rule keeps the one just added and removes the rest. A
re-rank is then one click. With no event to go by, the most urgent one stays.

The issue form. GitHub applies a form only in the web UI, so an issue filed
with `gh issue create --body` or the API can skip it. The rule reads the
repo's forms, or the org defaults in the .github repo, and checks the body
against each form whose labels the issue carries. The check is the one the
writing hook runs before filing, imported from .claude/hooks/writing_check.py.
A body that fails gets `needs-rewrite` and one comment that lists the gaps.
An edit that fixes the body removes the label again. The rule skips issues a
bot opened, issues labelled `automated`, and issues opened before
`forms_enforced_since` in the config.

Environment:
    GH_TOKEN        token with issues: write on the repo
    GITHUB_REPOSITORY   owner/name
    ISSUE_NUMBER    the issue to act on
    CONFIG_PATH     path to allowed-labels.json
    NORMS_URL       link the comment points at
    LABEL_NAME      the label a `labeled` event added, empty otherwise
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com"
MARKER = "<!-- issue-governance:stripped-labels -->"
FORM_MARKER = "<!-- issue-governance:form-check -->"
REWRITE_LABEL = "needs-rewrite"

_HOOK = (
    Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "writing_check.py"
)
_spec = importlib.util.spec_from_file_location("writing_check", _HOOK)
assert _spec and _spec.loader
writing_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(writing_check)
PRIORITIES = writing_check.PRIORITIES


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


def label_names(issue: dict) -> list[str]:
    return [label["name"] for label in issue.get("labels", [])]


def add_label(repo: str, number: int, token: str, issue: dict, name: str) -> None:
    request("POST", f"/repos/{repo}/issues/{number}/labels", token, {"labels": [name]})
    issue.setdefault("labels", []).append({"name": name})
    print(f"labels: added {name}")


def remove_label(repo: str, number: int, token: str, issue: dict, name: str) -> None:
    quoted = urllib.parse.quote(name, safe="")
    try:
        request("DELETE", f"/repos/{repo}/issues/{number}/labels/{quoted}", token)
        print(f"labels: removed {name}")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        print(f"labels: {name} already gone")
    issue["labels"] = [x for x in issue.get("labels", []) if x["name"] != name]


def apply_priority(
    repo: str, number: int, token: str, issue: dict, added: str
) -> str | None:
    """Leave exactly one P label where the issue or its body names one."""
    present = [name for name in label_names(issue) if name in PRIORITIES]
    if len(present) > 1:
        keep = added if added in present else min(present)
        for name in present:
            if name != keep:
                remove_label(repo, number, token, issue, name)
        return keep
    if present:
        print(f"priority: {present[0]}")
        return present[0]
    named = writing_check.priority_from_body(issue.get("body") or "")
    if named is None:
        print("priority: none named")
        return None
    add_label(repo, number, token, issue, named)
    return named


def fetch_forms(repo: str, token: str) -> list:
    """The forms GitHub shows for the repo: its own, else the org defaults."""
    owner = repo.split("/", 1)[0]
    for source in (repo, f"{owner}/.github"):
        base = f"/repos/{source}/contents/.github/ISSUE_TEMPLATE"
        try:
            listing = request("GET", base, token)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            continue
        found = []
        for entry in listing or []:
            name = entry.get("name", "")
            if entry.get("type") != "file" or not name.endswith((".yml", ".yaml")):
                continue
            blob = request("GET", f"{base}/{urllib.parse.quote(name)}", token)
            text = base64.b64decode(blob["content"]).decode("utf-8")
            form = writing_check.parse_form(text, name)
            if form is not None:
                found.append(form)
        if found:
            return found
    return []


def form_comment(problems: list[str], norms_url: str) -> str:
    """The one comment posted when the body skips its issue form."""
    listed = "\n".join(f"- {problem}" for problem in problems)
    return (
        f"{FORM_MARKER}\n"
        f"This issue body does not match its issue form:\n\n{listed}\n\n"
        f"Edit the body to add each missing section under its heading. The "
        f"`{REWRITE_LABEL}` label comes off when the body passes. The forms "
        f"and the priority rubric are in [repo norms]({norms_url})."
    )


def check_form(
    repo: str,
    number: int,
    token: str,
    issue: dict,
    forms: list,
    since: str,
    norms_url: str,
) -> list[str]:
    """Flag a body that skips its form. Return the gaps found."""
    labels = label_names(issue)
    if (issue.get("user") or {}).get("type") == "Bot" or "automated" in labels:
        print("form: opened by automation, skipping")
        return []
    if (issue.get("created_at") or "")[:10] < since:
        print(f"form: opened before {since}, skipping")
        return []
    if not forms:
        print("form: no issue forms found, skipping")
        return []

    problems = writing_check.form_problems(issue.get("body") or "", labels, forms)
    comments = paged(f"/repos/{repo}/issues/{number}/comments", token)
    if not problems:
        flagged = any(FORM_MARKER in (c.get("body") or "") for c in comments)
        if REWRITE_LABEL in labels and flagged:
            remove_label(repo, number, token, issue, REWRITE_LABEL)
        print("form: body matches")
        return []

    if REWRITE_LABEL not in labels:
        add_label(repo, number, token, issue, REWRITE_LABEL)
    body = form_comment(problems, norms_url)
    if any(c.get("body") == body for c in comments):
        print("form: identical comment already present, not posting")
    else:
        request(
            "POST", f"/repos/{repo}/issues/{number}/comments", token, {"body": body}
        )
        print("form: comment posted")
    return problems


def main() -> int:
    token = os.environ["GH_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    number = int(os.environ["ISSUE_NUMBER"])
    config_path = os.environ["CONFIG_PATH"]
    norms_url = os.environ["NORMS_URL"]
    added = os.environ.get("LABEL_NAME", "")

    issue = fetch_issue(repo, number, token)
    if issue is None:
        return 0

    with open(config_path, encoding="utf-8") as handle:
        since = json.load(handle)["forms_enforced_since"]
    labels = allowed_labels(config_path, repo.split("/", 1)[1])
    milestones = allowed_milestones(config_path)
    strip_milestone(repo, number, token, issue, milestones)
    strip_labels(repo, number, token, issue, labels, norms_url)
    apply_priority(repo, number, token, issue, added)
    check_form(repo, number, token, issue, fetch_forms(repo, token), since, norms_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
