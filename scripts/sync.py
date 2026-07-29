#!/usr/bin/env python3
"""Fan out synced files to downstream repos as ops-sync pull requests.

Reads sync/manifest.yml, groups entries by target repo, and for each repo:
clones it shallowly, applies the file copies (or block splices), and, when
the result differs from the default branch, force-pushes an `ops-sync`
branch and ensures a single open PR for it. Re-runs update the same branch
and PR. Nothing is ever pushed to a default branch.

Repos listed under `auto_merge` in the manifest also get GitHub's
auto-merge armed on that PR, so their own required checks decide when it
lands. See auto_merge_decision for what disqualifies a run.

Usage:

    python3 scripts/sync.py --dry-run          # plan only, no clones pushed
    python3 scripts/sync.py                    # full run (needs gh auth)
    python3 scripts/sync.py --repo portolan-sdi/.github   # one target only

Requires: git, gh (authenticated with repo scope on the org), PyYAML.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "sync" / "manifest.yml"
BRANCH = "ops-sync"
WORKFLOW_PREFIX = ".github/workflows/"
BLOCK_RE = re.compile(r"<!-- ops-sync:begin.*?-->.*?<!-- ops-sync:end -->", re.DOTALL)
PR_TITLE = "chore: sync shared files from portolan-ops"
OPS_COMMIT_URL = "https://github.com/portolan-sdi/portolan-ops/commit"
AUTO_MERGE_ATTEMPTS = 3
AUTO_MERGE_BACKOFF = 5.0
# GitHub refuses auto-merge for two reasons that clear on their own: the
# base branch moved under the PR, and the required checks have not been
# reported yet on a freshly pushed head. Every other refusal, such as a
# repo with allow_auto_merge off, is a standing fact and is reported once.
TRANSIENT_AUTO_MERGE_ERRORS = (
    "base branch was modified",
    "required status checks are expected",
)


def run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def ops_sha() -> str:
    """Short SHA of the ops checkout driving this sync, for provenance."""
    try:
        return run(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT)
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def commit_message(sha: str) -> str:
    return f"{PR_TITLE}\n\nsource: portolan-sdi/portolan-ops@{sha}"


def pr_body(sha: str, dests: list[str]) -> str:
    """Body for the sync PR, shaped to pass scripts/lint_body.py --kind pr.

    The file list sits in the fenced block, which counts toward neither
    the word budget nor the six-line section cap. A repo receiving
    twenty files therefore gets as valid a body as one receiving two.

    The waiver checkbox stays unticked on purpose. Sync sometimes
    delivers workflow files, which do change behavior. The pasted
    manifest and the commit link carry the evidence instead.
    """
    count = len(dests)
    noun = "file" if count == 1 else "files"
    files = "\n".join(sorted(dests))
    return (
        "## What this changes\n\n"
        f"Copies {count} {noun} into this repo from portolan-ops, which holds "
        "the org's shared policies, templates, and CI callers.\n\n"
        "## Why\n\n"
        "These files are org ground truth. Change one by opening a pull "
        "request in portolan-ops. An edit made here is overwritten on the "
        "next run, and re-runs update this same branch.\n\n"
        "## Verification\n\n"
        "```\n"
        f"source: portolan-sdi/portolan-ops@{sha}\n"
        f"{files}\n"
        "```\n\n"
        f"{OPS_COMMIT_URL}/{sha}\n"
    )


def load_manifest() -> dict[str, list[dict]]:
    """Return {repo: [{src, dest, mode}, ...]}."""
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    by_repo: dict[str, list[dict]] = {}
    for entry in data["sync"]:
        src = entry["src"]
        mode = entry.get("mode", "copy")
        for target in entry["targets"]:
            by_repo.setdefault(target["repo"], []).append(
                {"src": src, "dest": target["dest"], "mode": mode}
            )
    return by_repo


def load_auto_merge() -> set[str]:
    """Return the repos that opted in to auto-merge on their sync PR."""
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return set((data or {}).get("auto_merge") or [])


def auto_merge_decision(
    repo: str,
    changed: list[str],
    auto_merge_repos: set[str],
    required_checks: list[str],
    dry_run: bool,
) -> tuple[bool, str]:
    """Decide whether to arm auto-merge, and say why. Pure; no gh calls.

    Three things disqualify a run. A repo that never opted in keeps
    today's behavior. A dry run pushes nothing to merge. A PR that
    touches `.github/workflows/` waits for a human, because a malformed
    workflow breaks every event in the repo.

    The last guard matters most: with no required status checks on the
    base branch, GitHub's auto-merge merges the PR on the spot, which
    throws away the CI signal the PR exists for.
    """
    if repo not in auto_merge_repos:
        return False, "not opted in"
    if dry_run:
        return False, "dry run"
    workflows = sorted(p for p in changed if p.startswith(WORKFLOW_PREFIX))
    if workflows:
        return False, f"touches {', '.join(workflows)}"
    if not required_checks:
        return False, "base branch has no required status checks"
    return True, f"gated by {', '.join(required_checks)}"


def _gh_api_lines(path: str, jq: str) -> list[str]:
    try:
        out = run(["gh", "api", path, "--jq", jq])
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def required_checks(repo: str, branch: str) -> list[str]:
    """Contexts the branch requires before a merge. Empty when it has none.

    Two places can hold the gate. Classic branch protection answers 404
    on an unprotected branch and needs administration:read to answer at
    all, so an unreadable answer counts as no gate and the caller skips
    auto-merge. Rulesets answer from contents:read, which is what the
    sync token already carries.
    """
    protection = _gh_api_lines(
        f"repos/{repo}/branches/{branch}/protection/required_status_checks",
        "[(.contexts // [])[], ((.checks // [])[] | .context)] | unique | .[]",
    )
    rules = _gh_api_lines(
        f"repos/{repo}/rules/branches/{branch}",
        '[.[] | select(.type == "required_status_checks")'
        " | .parameters.required_status_checks[]?.context] | unique | .[]",
    )
    return sorted(set(protection) | set(rules))


def is_transient_auto_merge_error(error: str) -> bool:
    """True when a refusal is worth another attempt a few seconds later."""
    lowered = error.lower()
    return any(pattern in lowered for pattern in TRANSIENT_AUTO_MERGE_ERRORS)


def enable_auto_merge(
    repo: str,
    number: str,
    attempts: int = AUTO_MERGE_ATTEMPTS,
    sleep=time.sleep,
) -> str:
    """Arm auto-merge on one PR; return an error string, or "" on success.

    A repo with `allow_auto_merge` off rejects the command. That is one
    repo's setting, not a reason to fail the fan-out, so the error comes
    back as text for the summary line.

    A transient refusal buys a retry with a widening pause, because the
    force-push that precedes this call is what unsettles the base branch
    and the check list in the first place. The last error survives, so a
    run that exhausts its attempts still names what GitHub said.
    """
    error = ""
    for attempt in range(1, attempts + 1):
        try:
            run(["gh", "pr", "merge", "--repo", repo, "--auto", "--squash", number])
        except subprocess.CalledProcessError as e:
            error = (e.stderr or "").strip() or str(e)
            if attempt == attempts or not is_transient_auto_merge_error(error):
                return error
            sleep(AUTO_MERGE_BACKOFF * attempt)
        else:
            return ""
    return error


def extract_block(text: str) -> str:
    m = BLOCK_RE.search(text)
    if not m:
        raise SystemExit("source file has no ops-sync block markers; cannot splice")
    return m.group(0)


def apply_file(item: dict, repo_dir: Path) -> None:
    src_path = ROOT / item["src"]
    dest_path = repo_dir / item["dest"]
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if item["mode"] == "copy":
        shutil.copyfile(src_path, dest_path)
        return
    # mode "block": replace the delimited region, keep the rest.
    # A missing dest gets the block only, so first sync and re-sync
    # produce the same managed region either way.
    block = extract_block(src_path.read_text(encoding="utf-8"))
    if dest_path.exists():
        dest_text = dest_path.read_text(encoding="utf-8")
        if BLOCK_RE.search(dest_text):
            new_text = BLOCK_RE.sub(lambda _: block, dest_text, count=1)
        else:
            new_text = block + "\n\n" + dest_text
    else:
        new_text = block + "\n"
    dest_path.write_text(new_text, encoding="utf-8")


def open_pr_number(repo: str) -> str:
    """Number of the open ops-sync PR, or "" when there is none."""
    return run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            BRANCH,
            "--state",
            "open",
            "--json",
            "number",
            "--jq",
            ".[0].number // empty",
        ]
    )


def sync_repo(
    repo: str,
    items: list[dict],
    dry_run: bool,
    auto_merge_repos: set[str] | None = None,
) -> str:
    """Sync one repo; return a one-line result for the summary."""
    with tempfile.TemporaryDirectory(prefix="ops-sync-") as tmp:
        repo_dir = Path(tmp) / "repo"
        run(["gh", "repo", "clone", repo, str(repo_dir), "--", "--depth=1"])
        default_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
        run(["git", "checkout", "-B", BRANCH], cwd=repo_dir)

        for item in items:
            apply_file(item, repo_dir)

        status = run(["git", "status", "--porcelain"], cwd=repo_dir)
        if not status:
            return f"{repo}: in sync, nothing to do"
        changed = [line[3:] for line in status.splitlines()]
        if dry_run:
            return f"{repo}: would open/update PR ({', '.join(changed)})"

        sha = ops_sha()
        run(["git", "add", "-A"], cwd=repo_dir)
        run(
            ["git", "commit", "-m", commit_message(sha)],
            cwd=repo_dir,
        )
        run(["git", "push", "--force", "origin", BRANCH], cwd=repo_dir)

        number = open_pr_number(repo)
        if number:
            # Rewrite the body as well as the branch. A PR opened under an
            # older body format would otherwise carry that text forever,
            # failing a body check it can never pass on its own.
            run(
                [
                    "gh",
                    "pr",
                    "edit",
                    "--repo",
                    repo,
                    number,
                    "--title",
                    PR_TITLE,
                    "--body",
                    pr_body(sha, [item["dest"] for item in items]),
                ]
            )
            outcome = "updated existing PR branch and body"
        else:
            run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--repo",
                    repo,
                    "--head",
                    BRANCH,
                    "--base",
                    default_branch,
                    "--title",
                    PR_TITLE,
                    "--body",
                    pr_body(sha, [item["dest"] for item in items]),
                ]
            )
            # Ask for the number rather than parsing it out of the URL
            # gh printed, so a warning line on stdout cannot mangle it.
            number = open_pr_number(repo)
            outcome = "opened PR"

    opted_in = auto_merge_repos or set()
    if repo not in opted_in:
        return f"{repo}: {outcome}"
    eligible, why = auto_merge_decision(
        repo,
        changed,
        opted_in,
        required_checks(repo, default_branch),
        dry_run,
    )
    if not eligible:
        return f"{repo}: {outcome}, auto-merge skipped ({why})"
    error = enable_auto_merge(repo, number)
    if error:
        return f"{repo}: {outcome}, auto-merge refused ({error})"
    return f"{repo}: {outcome}, auto-merge armed ({why})"


def drift_repo(repo: str, items: list[dict]) -> str:
    """Report one repo's default branch as a markdown table row."""
    with tempfile.TemporaryDirectory(prefix="ops-drift-") as tmp:
        repo_dir = Path(tmp) / "repo"
        run(["gh", "repo", "clone", repo, str(repo_dir), "--", "--depth=1"])
        for item in items:
            apply_file(item, repo_dir)
        status = run(["git", "status", "--porcelain"], cwd=repo_dir)
    if not status:
        return f"| {repo} | in sync | |"
    open_prs = run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            BRANCH,
            "--state",
            "open",
            "--json",
            "number",
            "--jq",
            "length",
        ]
    )
    state = "PR open" if open_prs != "0" else "drifted"
    changed = ", ".join(line[3:] for line in status.splitlines())
    return f"| {repo} | {state} | {changed} |"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="print the grouped plan without cloning anything",
    )
    parser.add_argument(
        "--drift-report",
        action="store_true",
        help="markdown table of each repo's default branch vs ground truth",
    )
    parser.add_argument("--repo", help="sync only this owner/name target", default=None)
    args = parser.parse_args()

    by_repo = load_manifest()
    if args.drift_report:
        print("| Repo | State | Pending files |")
        print("|---|---|---|")
        failures = 0
        for repo, items in sorted(by_repo.items()):
            try:
                print(drift_repo(repo, items))
            except subprocess.CalledProcessError as e:
                failures += 1
                print(f"| {repo} | ERROR | {e.stderr.strip() or e} |")
        return 1 if failures else 0
    if args.plan_only:
        for repo, items in sorted(by_repo.items()):
            print(f"{repo}:")
            for item in items:
                print(f"  {item['src']} -> {item['dest']} ({item['mode']})")
        return 0
    if args.repo:
        if args.repo not in by_repo:
            raise SystemExit(f"{args.repo} is not in sync/manifest.yml")
        by_repo = {args.repo: by_repo[args.repo]}

    auto_merge_repos = load_auto_merge()
    failures = 0
    for repo, items in sorted(by_repo.items()):
        try:
            print(sync_repo(repo, items, args.dry_run, auto_merge_repos))
        except subprocess.CalledProcessError as e:
            failures += 1
            print(f"{repo}: FAILED — {e.stderr.strip() or e}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
