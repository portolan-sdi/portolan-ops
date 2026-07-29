#!/usr/bin/env python3
"""Unit tests for the pure functions in sync.py.

Run directly (check.yml does):

    uv run --no-project --with pyyaml==6.0.2 python scripts/test_sync.py

Covers manifest grouping, file application, and the auto-merge decision.
The git/gh plumbing in sync_repo stays untested here. The sync workflow's
dry-run exercises it.
"""

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
        # The repo checks read every sync PR body, so a body that fails
        # here turns twelve downstream pull requests red.
        for dests in (["LICENSE"], ["LICENSE", "CLAUDE.md"], MANY_DESTS):
            with self.subTest(count=len(dests)):
                body = sync.pr_body("abc123def456", dests)
                self.assertEqual(lint_body.check(body, "pr"), [])

    def test_ops_sha_reports_a_short_hash(self):
        sha = sync.ops_sha()
        self.assertRegex(sha, r"^([0-9a-f]{12}|unknown)$")


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

    def test_block_resync_is_idempotent(self):
        first = self._apply(f"x\n{BLOCK}\n", "block")
        second = self._apply(f"x\n{BLOCK}\n", "block", dest_text=first)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
