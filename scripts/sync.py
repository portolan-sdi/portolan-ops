#!/usr/bin/env python3
"""Fan out synced files to downstream repos as ops-sync pull requests.

Reads sync/manifest.yml, groups entries by target repo, and for each repo:
clones it shallowly, applies the file copies (or block splices), and, when
the result differs from the default branch, force-pushes an `ops-sync`
branch and ensures a single open PR for it. Re-runs update the same branch
and PR; nothing is ever pushed to a default branch.

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
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "sync" / "manifest.yml"
BRANCH = "ops-sync"
BLOCK_RE = re.compile(
    r"<!-- ops-sync:begin.*?-->.*?<!-- ops-sync:end -->", re.DOTALL
)
PR_TITLE = "chore: sync shared files from portolan-ops"
PR_BODY = (
    "Automated sync from"
    " [portolan-ops](https://github.com/portolan-sdi/portolan-ops).\n\n"
    "These files are org ground truth; to change them, open a PR in"
    " portolan-ops instead of editing them here. Re-runs of the sync"
    " update this same branch."
)


def run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd, cwd=cwd, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


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


def extract_block(text: str) -> str:
    m = BLOCK_RE.search(text)
    if not m:
        raise SystemExit(
            "source file has no ops-sync block markers; cannot splice"
        )
    return m.group(0)


def apply_file(item: dict, repo_dir: Path) -> None:
    src_path = ROOT / item["src"]
    dest_path = repo_dir / item["dest"]
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if item["mode"] == "copy":
        shutil.copyfile(src_path, dest_path)
        return
    # mode "block": replace the delimited region, keep the rest.
    block = extract_block(src_path.read_text(encoding="utf-8"))
    if dest_path.exists():
        dest_text = dest_path.read_text(encoding="utf-8")
        if BLOCK_RE.search(dest_text):
            new_text = BLOCK_RE.sub(lambda _: block, dest_text, count=1)
        else:
            new_text = block + "\n\n" + dest_text
    else:
        new_text = src_path.read_text(encoding="utf-8")
    dest_path.write_text(new_text, encoding="utf-8")


def sync_repo(repo: str, items: list[dict], dry_run: bool) -> str:
    """Sync one repo; return a one-line result for the summary."""
    with tempfile.TemporaryDirectory(prefix="ops-sync-") as tmp:
        repo_dir = Path(tmp) / "repo"
        run(["gh", "repo", "clone", repo, str(repo_dir), "--", "--depth=1"])
        default_branch = run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir
        )
        run(["git", "checkout", "-B", BRANCH], cwd=repo_dir)

        for item in items:
            apply_file(item, repo_dir)

        status = run(["git", "status", "--porcelain"], cwd=repo_dir)
        if not status:
            return f"{repo}: in sync, nothing to do"
        if dry_run:
            changed = ", ".join(line[3:] for line in status.splitlines())
            return f"{repo}: would open/update PR ({changed})"

        run(["git", "add", "-A"], cwd=repo_dir)
        run(
            ["git", "commit", "-m", PR_TITLE],
            cwd=repo_dir,
        )
        run(["git", "push", "--force", "origin", BRANCH], cwd=repo_dir)

        open_prs = run(
            [
                "gh", "pr", "list",
                "--repo", repo,
                "--head", BRANCH,
                "--state", "open",
                "--json", "number",
                "--jq", "length",
            ]
        )
        if open_prs == "0":
            run(
                [
                    "gh", "pr", "create",
                    "--repo", repo,
                    "--head", BRANCH,
                    "--base", default_branch,
                    "--title", PR_TITLE,
                    "--body", PR_BODY,
                ]
            )
            return f"{repo}: opened PR"
        return f"{repo}: updated existing PR branch"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="print the grouped plan without cloning anything",
    )
    parser.add_argument(
        "--repo", help="sync only this owner/name target", default=None
    )
    args = parser.parse_args()

    by_repo = load_manifest()
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

    failures = 0
    for repo, items in sorted(by_repo.items()):
        try:
            print(sync_repo(repo, items, args.dry_run))
        except subprocess.CalledProcessError as e:
            failures += 1
            print(f"{repo}: FAILED — {e.stderr.strip() or e}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
