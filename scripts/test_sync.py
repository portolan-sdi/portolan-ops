#!/usr/bin/env python3
"""Unit tests for the pure functions in sync.py.

Run directly (check.yml does):

    uv run --no-project --with pyyaml==6.0.2 python scripts/test_sync.py

Covers manifest grouping, file application, and the auto-merge decision.
The git/gh plumbing in sync_repo stays untested here. The sync workflow's
dry-run exercises it.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lint_body

import sync

# A repo receiving many files must still get a valid body, since the
# list lives in a fenced block that the budget does not count.
MANY_DESTS = [f"docs/page-{i}.md" for i in range(30)]
MARKED = (
    "<!-- ops-sync:begin managed by portolan-ops -->\n"
    "old managed text\n"
    "<!-- ops-sync:end -->"
)
BLOCK = (
    "<!-- ops-sync:begin managed by portolan-ops -->\n"
    "new managed text\n"
    "<!-- ops-sync:end -->"
)


class LoadManifestTest(unittest.TestCase):
    def test_groups_targets_by_repo(self):
        manifest = {
            "sync": [
                {
                    "src": "LICENSE",
                    "targets": [
                        {"repo": "org/a", "dest": "LICENSE"},
                        {"repo": "org/b", "dest": "LICENSE"},
                    ],
                },
                {
                    "src": "templates/repo/AGENTS.md",
                    "mode": "block",
                    "targets": [{"repo": "org/a", "dest": "AGENTS.md"}],
                },
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yml"
            import yaml

            path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
            original = sync.MANIFEST
            sync.MANIFEST = path
            try:
                by_repo = sync.load_manifest()
            finally:
                sync.MANIFEST = original
        self.assertEqual(sorted(by_repo), ["org/a", "org/b"])
        self.assertEqual(
            by_repo["org/a"],
            [
                {"src": "LICENSE", "dest": "LICENSE", "mode": "copy"},
                {
                    "src": "templates/repo/AGENTS.md",
                    "dest": "AGENTS.md",
                    "mode": "block",
                },
            ],
        )


OPTED_IN = {"org/a"}


class AutoMergeDecisionTest(unittest.TestCase):
    def decide(self, repo="org/a", changed=None, checks=None, dry_run=False):
        return sync.auto_merge_decision(
            repo,
            ["LICENSE"] if changed is None else changed,
            OPTED_IN,
            ["ci / test"] if checks is None else checks,
            dry_run,
        )

    def test_opted_in_repo_with_required_checks_is_eligible(self):
        eligible, why = self.decide()
        self.assertTrue(eligible)
        self.assertIn("ci / test", why)

    def test_repo_not_opted_in_is_skipped(self):
        eligible, why = self.decide(repo="org/b")
        self.assertFalse(eligible)
        self.assertEqual(why, "not opted in")

    def test_workflow_write_blocks_auto_merge(self):
        eligible, why = self.decide(
            changed=["LICENSE", ".github/workflows/repo-checks.yml"]
        )
        self.assertFalse(eligible)
        self.assertIn(".github/workflows/repo-checks.yml", why)

    def test_branch_without_required_checks_blocks_auto_merge(self):
        eligible, why = self.decide(checks=[])
        self.assertFalse(eligible)
        self.assertIn("no required status checks", why)

    def test_dry_run_never_arms_auto_merge(self):
        eligible, why = self.decide(dry_run=True)
        self.assertFalse(eligible)
        self.assertEqual(why, "dry run")

    def test_opt_out_wins_over_every_other_signal(self):
        eligible, _ = self.decide(repo="org/b", changed=[], checks=[], dry_run=True)
        self.assertFalse(eligible)


class UpdatePathTest(unittest.TestCase):
    """A re-run rewrites the body, not only the branch.

    git and gh are replaced by a stub that answers the few reads
    sync_repo makes, so the assertion is about the commands issued.
    """

    def sync(self, number):
        calls = []

        def fake_run(cmd, cwd=None):
            calls.append(cmd)
            if cmd[:2] == ["git", "rev-parse"] and "--abbrev-ref" in cmd:
                return "main"
            if cmd[:2] == ["git", "status"]:
                return " M LICENSE"
            return ""

        original_run, original_number = sync.run, sync.open_pr_number
        sync.run = fake_run
        sync.open_pr_number = lambda repo: number
        try:
            summary = sync.sync_repo(
                "org/a",
                [{"src": "LICENSE", "dest": "LICENSE", "mode": "copy"}],
                dry_run=False,
            )
        finally:
            sync.run, sync.open_pr_number = original_run, original_number
        return summary, calls

    def edit_body(self, calls):
        for cmd in calls:
            if cmd[:3] == ["gh", "pr", "edit"]:
                return cmd[cmd.index("--body") + 1]
        return None

    def test_existing_pr_gets_a_fresh_body(self):
        summary, calls = self.sync("7")
        body = self.edit_body(calls)
        self.assertIsNotNone(body)
        self.assertEqual(
            lint_body.check(body, "pr", author="portolan-ops-sync[bot]"), []
        )
        self.assertIn("LICENSE", body)
        self.assertIn("body", summary)

    def test_new_pr_is_created_rather_than_edited(self):
        _, calls = self.sync("")
        self.assertIsNone(self.edit_body(calls))
        self.assertTrue(any(cmd[:3] == ["gh", "pr", "create"] for cmd in calls))


MODIFIED = "GraphQL: Base branch was modified. Review and try the merge again."
PENDING = "GraphQL: 3 of 3 required status checks are expected."
DISABLED = "GraphQL: Auto merge is not allowed for this repository"


class EnableAutoMergeTest(unittest.TestCase):
    """The retry path, with gh replaced by a scripted list of outcomes."""

    def arm(self, outcomes, attempts=3):
        calls = []
        pauses = []

        def fake_run(cmd, cwd=None):
            calls.append(cmd)
            outcome = outcomes[len(calls) - 1]
            if outcome:
                raise subprocess.CalledProcessError(1, cmd, stderr=outcome)
            return ""

        original = sync.run
        sync.run = fake_run
        try:
            error = sync.enable_auto_merge(
                "org/a", "7", attempts=attempts, sleep=pauses.append
            )
        finally:
            sync.run = original
        return error, calls, pauses

    def test_first_attempt_succeeds(self):
        error, calls, pauses = self.arm([""])
        self.assertEqual(error, "")
        self.assertEqual(len(calls), 1)
        self.assertEqual(pauses, [])

    def test_transient_refusal_is_attempted_again(self):
        error, calls, _ = self.arm([MODIFIED, ""])
        self.assertEqual(error, "")
        self.assertEqual(len(calls), 2)

    def test_pending_checks_are_transient_too(self):
        error, calls, _ = self.arm([PENDING, PENDING, ""])
        self.assertEqual(error, "")
        self.assertEqual(len(calls), 3)

    def test_exhausted_attempts_report_the_last_error(self):
        error, calls, _ = self.arm([MODIFIED, MODIFIED, PENDING])
        self.assertEqual(error, PENDING)
        self.assertEqual(len(calls), 3)

    def test_standing_refusal_is_reported_once(self):
        error, calls, pauses = self.arm([DISABLED, ""])
        self.assertEqual(error, DISABLED)
        self.assertEqual(len(calls), 1)
        self.assertEqual(pauses, [])

    def test_pauses_widen_between_attempts(self):
        _, _, pauses = self.arm([MODIFIED, MODIFIED, PENDING])
        self.assertEqual(len(pauses), 2)
        self.assertLess(pauses[0], pauses[1])

    def test_transient_patterns_match_the_refusals_github_sends(self):
        for error in (MODIFIED, PENDING):
            with self.subTest(error=error):
                self.assertTrue(sync.is_transient_auto_merge_error(error))
        self.assertFalse(sync.is_transient_auto_merge_error(DISABLED))


class LoadAutoMergeTest(unittest.TestCase):
    def _load(self, manifest):
        import yaml

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yml"
            path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
            original = sync.MANIFEST
            sync.MANIFEST = path
            try:
                return sync.load_auto_merge()
            finally:
                sync.MANIFEST = original

    def test_reads_the_opt_in_list(self):
        self.assertEqual(
            self._load({"sync": [], "auto_merge": ["org/a", "org/b"]}),
            {"org/a", "org/b"},
        )

    def test_missing_key_means_nobody_opted_in(self):
        self.assertEqual(self._load({"sync": []}), set())


class ProvenanceTest(unittest.TestCase):
    def test_commit_message_embeds_ops_sha(self):
        msg = sync.commit_message("abc123def456")
        self.assertTrue(msg.startswith(sync.PR_TITLE))
        self.assertIn("portolan-sdi/portolan-ops@abc123def456", msg)

    def test_pr_body_embeds_ops_sha_and_dests(self):
        body = sync.pr_body("abc123def456", ["LICENSE", "CLAUDE.md"])
        self.assertIn("portolan-sdi/portolan-ops@abc123def456", body)
        self.assertIn(f"{sync.OPS_COMMIT_URL}/abc123def456", body)
        self.assertIn("LICENSE", body)
        self.assertIn("Copies 2 files", body)

    def test_pr_body_passes_the_body_check(self):
        # The repo checks read every sync PR body. The sync app's login is
        # exempt as a generated body, which covers the issue-reference
        # rule (sync has no ticket). The shape rules still hold: assert
        # the body would pass for a person, missing reference aside, so a
        # regression in the shape turns up here and not in twelve
        # downstream pull requests.
        for dests in (["LICENSE"], ["LICENSE", "CLAUDE.md"], MANY_DESTS):
            with self.subTest(count=len(dests)):
                body = sync.pr_body("abc123def456", dests)
                self.assertEqual(
                    lint_body.check(body, "pr", author="portolan-ops-sync[bot]"),
                    [],
                )
                shape_problems = [
                    p
                    for p in lint_body.check(body, "pr")
                    if "No issue is referenced" not in p
                ]
                self.assertEqual(shape_problems, [])

    def test_ops_sha_reports_a_short_hash(self):
        sha = sync.ops_sha()
        self.assertRegex(sha, r"^([0-9a-f]{12}|unknown)$")


class ForeignCommitTest(unittest.TestCase):
    def test_sync_commits_are_not_foreign(self):
        subjects = [sync.PR_TITLE, f"{sync.PR_TITLE} (retry)"]
        self.assertEqual(sync.foreign_commit_subjects(subjects), [])

    def test_human_commits_are_foreign(self):
        subjects = [sync.PR_TITLE, "fix: satisfy prettier on synced files"]
        self.assertEqual(
            sync.foreign_commit_subjects(subjects),
            ["fix: satisfy prettier on synced files"],
        )

    def test_missing_branch_means_nothing_foreign(self):
        self.assertEqual(sync.foreign_commit_subjects([]), [])

    def test_sync_repo_refuses_to_overwrite_a_persons_work(self):
        def fake_run(cmd, cwd=None):
            if cmd[:2] == ["git", "rev-parse"] and "--abbrev-ref" in cmd:
                return "main"
            if cmd[:2] == ["git", "status"]:
                return " M LICENSE"
            return ""

        original_run = sync.run
        original_subjects = sync.branch_commit_subjects
        sync.run = fake_run
        sync.branch_commit_subjects = lambda repo, base: ["fix: hand edit"]
        try:
            with self.assertRaises(sync.SyncError) as caught:
                sync.sync_repo(
                    "org/a",
                    [{"src": "LICENSE", "dest": "LICENSE", "mode": "copy"}],
                    dry_run=False,
                )
        finally:
            sync.run = original_run
            sync.branch_commit_subjects = original_subjects
        self.assertIn("fix: hand edit", str(caught.exception))


class DriftReportTest(unittest.TestCase):
    def report(self, rows, missing=(), extra=None):
        import contextlib
        import io

        original_repo = sync.drift_repo
        original_missing = sync.unmanaged_repos
        original_extra = sync.load_extra_branches
        sync.drift_repo = lambda repo, items, branch=None: rows[(repo, branch)]
        sync.unmanaged_repos = lambda managed: list(missing)
        sync.load_extra_branches = lambda: dict(extra or {})
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = sync.drift_report({repo: [] for repo, _ in rows})
        finally:
            sync.drift_repo = original_repo
            sync.unmanaged_repos = original_missing
            sync.load_extra_branches = original_extra
        return code, out.getvalue()

    def test_clean_fleet_exits_zero(self):
        code, _ = self.report({("org/a", None): "| org/a | in sync | |"})
        self.assertEqual(code, 0)

    def test_drift_exits_nonzero(self):
        code, out = self.report({("org/a", None): "| org/a | drifted | AGENTS.md |"})
        self.assertEqual(code, 1)
        self.assertIn("drifted", out)

    def test_unmanaged_repo_exits_nonzero(self):
        code, out = self.report(
            {("org/a", None): "| org/a | in sync | |"}, missing=["org/new-repo"]
        )
        self.assertEqual(code, 1)
        self.assertIn("org/new-repo", out)

    def test_extra_branch_gets_its_own_row(self):
        rows = {
            ("org/a", None): "| org/a | in sync | |",
            ("org/a", "release/v1"): "| org/a (release/v1) | drifted | hook.py |",
        }
        code, out = self.report(rows, extra={"org/a": ["release/v1"]})
        self.assertEqual(code, 1)
        self.assertIn("org/a (release/v1)", out)
        self.assertIn("hook.py", out)

    def test_clean_extra_branch_keeps_the_run_green(self):
        rows = {
            ("org/a", None): "| org/a | in sync | |",
            ("org/a", "release/v1"): "| org/a (release/v1) | in sync | |",
        }
        code, _ = self.report(rows, extra={"org/a": ["release/v1"]})
        self.assertEqual(code, 0)


class UnmanagedReposTest(unittest.TestCase):
    def unmanaged(self, active, managed):
        original = sync._gh_api_lines
        sync._gh_api_lines = lambda path, jq: list(active)
        try:
            return sync.unmanaged_repos(set(managed))
        finally:
            sync._gh_api_lines = original

    def test_reports_a_repo_the_manifest_misses(self):
        found = self.unmanaged(["org/a", "org/new"], ["org/a"])
        self.assertEqual(found, ["org/new"])

    def test_never_reports_the_source_repo(self):
        # Ops holds the originals, so it cannot sync to itself. Reporting
        # it would keep the weekly run red on a line no edit can clear.
        active = ["portolan-sdi/portolan-ops", "org/a"]
        self.assertEqual(self.unmanaged(active, ["org/a"]), [])


class LoadExtraBranchesTest(unittest.TestCase):
    def load(self, text):
        original = sync.MANIFEST
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.yml"
            path.write_text(text, encoding="utf-8")
            sync.MANIFEST = path
            try:
                return sync.load_extra_branches()
            finally:
                sync.MANIFEST = original

    def test_reads_the_map(self):
        text = "extra_branches:\n  org/a:\n    - release/v1\nsync: []\n"
        self.assertEqual(self.load(text), {"org/a": ["release/v1"]})

    def test_absent_key_reads_as_empty(self):
        self.assertEqual(self.load("sync: []\n"), {})


class ExtractBlockTest(unittest.TestCase):
    def test_extracts_delimited_region(self):
        text = f"before\n{BLOCK}\nafter\n"
        self.assertEqual(sync.extract_block(text), BLOCK)

    def test_missing_markers_fails_loudly(self):
        with self.assertRaises(SystemExit):
            sync.extract_block("no markers here\n")


class ApplyFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "ops"
        self.repo = Path(self._tmp.name) / "repo"
        self.root.mkdir()
        self.repo.mkdir()
        self._original_root = sync.ROOT
        sync.ROOT = self.root
        self.addCleanup(self._restore_root)

    def _restore_root(self):
        sync.ROOT = self._original_root

    def _apply(self, src_text, mode, dest_text=None):
        (self.root / "src.md").write_text(src_text, encoding="utf-8")
        dest = self.repo / "dest.md"
        if dest_text is not None:
            dest.write_text(dest_text, encoding="utf-8")
        sync.apply_file({"src": "src.md", "dest": "dest.md", "mode": mode}, self.repo)
        return dest.read_text(encoding="utf-8")

    def test_copy_replaces_dest_wholesale(self):
        result = self._apply("canonical\n", "copy", dest_text="stale local edits\n")
        self.assertEqual(result, "canonical\n")

    def test_block_splices_into_marked_dest(self):
        dest = f"# Repo title\n\n{MARKED}\n\nlocal content\n"
        result = self._apply(f"header\n{BLOCK}\n", "block", dest_text=dest)
        self.assertEqual(result, f"# Repo title\n\n{BLOCK}\n\nlocal content\n")

    def test_block_creates_missing_dest_with_block_only(self):
        result = self._apply(f"template header, not synced\n{BLOCK}\n", "block")
        self.assertEqual(result, BLOCK + "\n")

    def test_block_prepends_when_dest_has_no_markers(self):
        result = self._apply(f"x\n{BLOCK}\n", "block", dest_text="# Existing readme\n")
        self.assertEqual(result, f"{BLOCK}\n\n# Existing readme\n")


OPS_SETTINGS = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": "python3 writing_check.py"}],
            }
        ]
    }
}

REPO_SETTINGS = {
    "permissions": {"allow": ["Bash(uv run *)"]},
    "hooks": {
        "PostToolUse": [
            {
                "matcher": "Read",
                "hooks": [{"type": "command", "command": "./inject-docs.sh"}],
            }
        ]
    },
}


class PorcelainPathsTest(unittest.TestCase):
    """run() strips, so the first line arrives without its leading space."""

    def test_stripped_first_line_keeps_its_whole_path(self):
        status = "M .claude/settings.json\n ?? .github/x.yml"
        self.assertEqual(
            sync.porcelain_paths(status),
            [".claude/settings.json", ".github/x.yml"],
        )

    def test_unstripped_lines_parse(self):
        status = " M AGENTS.md\n?? .claude/hooks/writing_check.py"
        self.assertEqual(
            sync.porcelain_paths(status),
            ["AGENTS.md", ".claude/hooks/writing_check.py"],
        )

    def test_path_with_a_space_survives(self):
        self.assertEqual(sync.porcelain_paths("?? my file.md"), ["my file.md"])

    def test_rename_reports_the_new_name(self):
        self.assertEqual(sync.porcelain_paths("R  old.md -> new.md"), ["new.md"])

    def test_empty_status_is_empty(self):
        self.assertEqual(sync.porcelain_paths(""), [])


class MergeHooksTest(unittest.TestCase):
    """A repo's own hooks and settings must survive the merge."""

    def test_foreign_hook_survives(self):
        merged = sync.merge_hooks(OPS_SETTINGS, REPO_SETTINGS)
        self.assertIn("PostToolUse", merged["hooks"])
        self.assertIn("PreToolUse", merged["hooks"])

    def test_unrelated_keys_survive(self):
        merged = sync.merge_hooks(OPS_SETTINGS, REPO_SETTINGS)
        self.assertEqual(merged["permissions"], {"allow": ["Bash(uv run *)"]})

    def test_creates_hooks_from_nothing(self):
        merged = sync.merge_hooks(OPS_SETTINGS, {})
        self.assertEqual(len(merged["hooks"]["PreToolUse"]), 1)

    def test_stale_ops_entry_is_replaced_not_doubled(self):
        stale = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 old/writing_check.py",
                            }
                        ],
                    }
                ]
            }
        }
        merged = sync.merge_hooks(OPS_SETTINGS, stale)
        commands = [
            h["command"] for g in merged["hooks"]["PreToolUse"] for h in g["hooks"]
        ]
        self.assertEqual(commands, ["python3 writing_check.py"])

    def test_second_run_produces_no_change(self):
        once = sync.merge_hooks(OPS_SETTINGS, REPO_SETTINGS)
        twice = sync.merge_hooks(OPS_SETTINGS, once)
        self.assertEqual(once, twice)

    def test_group_keeps_its_other_entries(self):
        mixed = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "python3 writing_check.py"},
                            {"type": "command", "command": "./repo-guard.sh"},
                        ],
                    }
                ]
            }
        }
        merged = sync.merge_hooks(OPS_SETTINGS, mixed)
        commands = [
            h["command"] for g in merged["hooks"]["PreToolUse"] for h in g["hooks"]
        ]
        self.assertEqual(commands, ["./repo-guard.sh", "python3 writing_check.py"])


class MergeJsonModeTest(ApplyFileTest):
    def _apply_json(self, source, dest_text=None):
        (self.root / "settings.json").write_text(json.dumps(source), encoding="utf-8")
        dest = self.repo / "out.json"
        if dest_text is not None:
            dest.write_text(dest_text, encoding="utf-8")
        sync.apply_file(
            {"src": "settings.json", "dest": "out.json", "mode": "merge-json"},
            self.repo,
        )
        return json.loads(dest.read_text(encoding="utf-8"))

    def test_writes_a_missing_file(self):
        got = self._apply_json(OPS_SETTINGS)
        self.assertEqual(len(got["hooks"]["PreToolUse"]), 1)

    def test_preserves_the_repo_hook(self):
        got = self._apply_json(OPS_SETTINGS, json.dumps(REPO_SETTINGS))
        self.assertIn("PostToolUse", got["hooks"])

    def test_empty_file_is_not_a_parse_error(self):
        got = self._apply_json(OPS_SETTINGS, "   \n")
        self.assertIn("PreToolUse", got["hooks"])

    def test_block_resync_is_idempotent(self):
        first = self._apply(f"x\n{BLOCK}\n", "block")
        second = self._apply(f"x\n{BLOCK}\n", "block", dest_text=first)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
