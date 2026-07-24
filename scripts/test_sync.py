#!/usr/bin/env python3
"""Unit tests for the pure functions in sync.py.

Run directly (check.yml does):

    uv run --no-project --with pyyaml==6.0.2 python scripts/test_sync.py

Covers manifest grouping and file application. The git/gh plumbing in
sync_repo stays untested here; the sync workflow's dry-run exercises it.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import sync  # noqa: E402

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
        sync.apply_file(
            {"src": "src.md", "dest": "dest.md", "mode": mode}, self.repo
        )
        return dest.read_text(encoding="utf-8")

    def test_copy_replaces_dest_wholesale(self):
        result = self._apply(
            "canonical\n", "copy", dest_text="stale local edits\n"
        )
        self.assertEqual(result, "canonical\n")

    def test_block_splices_into_marked_dest(self):
        dest = f"# Repo title\n\n{MARKED}\n\nlocal content\n"
        result = self._apply(f"header\n{BLOCK}\n", "block", dest_text=dest)
        self.assertEqual(
            result, f"# Repo title\n\n{BLOCK}\n\nlocal content\n"
        )

    def test_block_creates_missing_dest_with_block_only(self):
        result = self._apply(
            f"template header, not synced\n{BLOCK}\n", "block"
        )
        self.assertEqual(result, BLOCK + "\n")

    def test_block_prepends_when_dest_has_no_markers(self):
        result = self._apply(
            f"x\n{BLOCK}\n", "block", dest_text="# Existing readme\n"
        )
        self.assertEqual(result, f"{BLOCK}\n\n# Existing readme\n")

    def test_block_resync_is_idempotent(self):
        first = self._apply(f"x\n{BLOCK}\n", "block")
        second = self._apply(f"x\n{BLOCK}\n", "block", dest_text=first)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
