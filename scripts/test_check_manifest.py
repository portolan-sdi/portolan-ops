#!/usr/bin/env python3
"""Tests for the retired section of scripts/check_manifest.py.

Run directly (check.yml does):

    uv run --no-project --with pyyaml==6.0.3 python scripts/test_check_manifest.py
"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_manifest

SYNC = [{"src": "LICENSE", "targets": [{"repo": "org/a", "dest": "LICENSE"}]}]


def run_check(manifest: dict) -> tuple[int, str]:
    """Run the check on a manifest; return the exit code and stderr."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "manifest.yml"
        path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        original = check_manifest.MANIFEST
        check_manifest.MANIFEST = path
        err = io.StringIO()
        try:
            with (
                contextlib.redirect_stderr(err),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                code = check_manifest.main()
        finally:
            check_manifest.MANIFEST = original
    return code, err.getvalue()


class RetiredTest(unittest.TestCase):
    def test_a_valid_retirement_passes(self):
        retired = [{"path": ".github/dependabot.yml", "repos": ["org/a"]}]
        self.assertEqual(run_check({"sync": SYNC, "retired": retired})[0], 0)

    def test_no_retired_section_passes(self):
        self.assertEqual(run_check({"sync": SYNC})[0], 0)

    def test_a_path_the_sync_still_writes_fails(self):
        retired = [{"path": "LICENSE", "repos": ["org/a"]}]
        code, err = run_check({"sync": SYNC, "retired": retired})
        self.assertEqual(code, 1)
        self.assertIn("sync still writes org/a:LICENSE", err)

    def test_a_path_outside_the_repo_fails(self):
        retired = [{"path": "../escape.yml", "repos": ["org/a"]}]
        code, err = run_check({"sync": SYNC, "retired": retired})
        self.assertEqual(code, 1)
        self.assertIn("bad path", err)

    def test_an_entry_without_repos_fails(self):
        code, err = run_check({"sync": SYNC, "retired": [{"path": "old.yml"}]})
        self.assertEqual(code, 1)
        self.assertIn("non-empty list of repos", err)

    def test_a_bad_repo_name_fails(self):
        retired = [{"path": "old.yml", "repos": ["not-a-repo"]}]
        code, err = run_check({"sync": SYNC, "retired": retired})
        self.assertEqual(code, 1)
        self.assertIn("bad repo", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
