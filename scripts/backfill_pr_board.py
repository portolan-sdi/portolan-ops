#!/usr/bin/env python3
"""Put open pull requests on the org project board.

The pull request board workflow adds a pull request when somebody opens it.
It cannot reach a pull request that was open before the workflow existed.
This script closes that gap, and repairs the board after any run the
workflow missed.

It reads every active organization repository, keeps the open pull requests
whose author is a person, and adds each one to the board. The add is
idempotent. A pull request already on the board returns its existing item.

The default mode reports what it would add and changes nothing. Pass
``--apply`` to write.

    python3 scripts/backfill_pr_board.py
    python3 scripts/backfill_pr_board.py --apply

Needs the gh CLI, authenticated with a token that can write the org
project. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import NamedTuple

ORG = "portolan-sdi"
PROJECT_NUMBER = 1


class PullRequest(NamedTuple):
    """One open pull request that a person opened."""

    repo: str
    number: int
    node_id: str
    title: str


def gh(args: list[str], stdin: str | None = None) -> object:
    """Run one gh command and decode its JSON response."""
    result = subprocess.run(
        ["gh", *args],
        input=stdin,
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


def gh_api(path: str) -> object:
    """Read one REST endpoint, following pagination."""
    return gh(["api", "--paginate", path])


def project_id(org: str, number: int) -> str:
    """The node id of the org project with this number."""
    query = (
        "query($org:String!,$number:Int!){"
        "organization(login:$org){projectV2(number:$number){id}}}"
    )
    payload = gh(
        [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-F",
            f"org={org}",
            "-F",
            f"number={number}",
        ]
    )
    if not isinstance(payload, dict):
        raise TypeError("the project lookup has an unexpected shape")
    project = payload["data"]["organization"]["projectV2"]
    if not project:
        raise RuntimeError(f"{org} has no project number {number}")
    return str(project["id"])


def list_repos(org: str) -> list[str]:
    """Full names of the active repositories in the organization."""
    payload = gh_api(f"orgs/{org}/repos?per_page=100&type=all")
    if not isinstance(payload, list):
        raise TypeError("the repository list has an unexpected shape")
    return sorted(
        str(repo["full_name"])
        for repo in payload
        if not repo.get("archived") and not repo.get("disabled")
    )


def open_pull_requests(repo: str) -> list[PullRequest]:
    """Open pull requests in one repository that a person opened.

    The board workflow skips a bot the same way, on the author type that
    GitHub reports rather than on a list of names.
    """
    payload = gh_api(f"repos/{repo}/pulls?state=open&per_page=100")
    if not isinstance(payload, list):
        raise TypeError(f"{repo}: the pull request list has an unexpected shape")
    found: list[PullRequest] = []
    for item in payload:
        if (item.get("user") or {}).get("type") == "Bot":
            continue
        found.append(
            PullRequest(
                repo=repo,
                number=int(item["number"]),
                node_id=str(item["node_id"]),
                title=str(item.get("title") or ""),
            )
        )
    return found


def add_to_board(project: str, pull: PullRequest) -> None:
    """Add one pull request to the board. Adding twice is harmless."""
    mutation = (
        "mutation($project:ID!,$content:ID!){"
        "addProjectV2ItemById(input:{projectId:$project,contentId:$content})"
        "{item{id}}}"
    )
    gh(
        [
            "api",
            "graphql",
            "-f",
            f"query={mutation}",
            "-F",
            f"project={project}",
            "-F",
            f"content={pull.node_id}",
        ]
    )


def backfill(org: str, number: int, apply: bool) -> int:
    """Report or write the open pull requests missing from the board."""
    project = project_id(org, number)
    pulls: list[PullRequest] = []
    for repo in list_repos(org):
        pulls.extend(open_pull_requests(repo))

    if not pulls:
        print(f"No open pull requests to add for {org}.")
        return 0

    print("| Pull request | Title | Result |")
    print("|---|---|---|")
    for pull in pulls:
        result = "would add"
        if apply:
            add_to_board(project, pull)
            result = "added"
        print(f"| {pull.repo}#{pull.number} | {pull.title} | {result} |")
    print(f"\n{len(pulls)} pull requests.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--org", default=ORG)
    parser.add_argument("--project", type=int, default=PROJECT_NUMBER)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        return backfill(args.org, args.project, args.apply)
    except (RuntimeError, TypeError, KeyError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
