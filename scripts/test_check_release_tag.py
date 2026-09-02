#!/usr/bin/env python3
"""Unit tests for check_release_tag.py.

Run directly (check.yml does):

    python3 scripts/test_check_release_tag.py

Git is stubbed, so the tests run anywhere.
"""

import subprocess
import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_release_tag


def fake_git(rev_parse_rc=0, diff_out="", diff_rc=0, diff_err=""):
    def run(args):
        if args[0] == "rev-parse":
            return subprocess.CompletedProcess(args, rev_parse_rc, "", "")
        if args[0] == "diff":
            return subprocess.CompletedProcess(args, diff_rc, diff_out, diff_err)
        raise AssertionError(f"unexpected git call: {args}")

    return run


class ChangedSinceTest(unittest.TestCase):
    def test_clean_tag_reports_nothing(self):
        found = check_release_tag.changed_since(
            "v1", check_release_tag.GUARDED, run=fake_git()
        )
        self.assertEqual(found, [])

    def test_changed_files_listed(self):
        run = fake_git(diff_out="scripts/lint_body.py\n")
        found = check_release_tag.changed_since(
            "v1", check_release_tag.GUARDED, run=run
        )
        self.assertEqual(found, ["scripts/lint_body.py"])

    def test_missing_tag_raises(self):
        with self.assertRaises(RuntimeError) as caught:
            check_release_tag.changed_since(
                "v1", check_release_tag.GUARDED, run=fake_git(rev_parse_rc=1)
            )
        self.assertIn("Fetch tags", str(caught.exception))

    def test_diff_failure_raises(self):
        run = fake_git(diff_rc=128, diff_err="fatal: bad revision")
        with self.assertRaises(RuntimeError):
            check_release_tag.changed_since("v1", check_release_tag.GUARDED, run=run)


class GuardedPathsTest(unittest.TestCase):
    def test_guarded_files_exist(self):
        root = Path(__file__).resolve().parent.parent
        for path in check_release_tag.GUARDED:
            target = path.removesuffix("/**")
            self.assertTrue((root / target).exists(), path)


class MainTest(unittest.TestCase):
    def run_main(self, run):
        original = check_release_tag.run_git
        check_release_tag.changed_since.__defaults__ = (run,)
        try:
            return check_release_tag.main([])
        finally:
            check_release_tag.changed_since.__defaults__ = (original,)

    def test_exit_zero_when_current(self):
        self.assertEqual(self.run_main(fake_git()), 0)

    def test_exit_one_when_stale(self):
        run = fake_git(diff_out=".github/workflows/reusable-repo-checks.yml\n")
        self.assertEqual(self.run_main(run), 1)

    def test_exit_one_when_tag_missing(self):
        self.assertEqual(self.run_main(fake_git(rev_parse_rc=1)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TagGuardPathsTest(unittest.TestCase):
    """The guard runs on push. Its paths must match the guarded list.

    A file in GUARDED but not in the workflow's paths is guarded by the
    weekly run alone, so a push that changes it reports nothing that day.
    """

    def test_the_workflow_paths_match_guarded(self):
        root = Path(__file__).resolve().parent.parent
        text = (root / ".github/workflows/tag-guard.yml").read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        triggers = data.get("on", data.get(True))
        paths = set(triggers["push"]["paths"])
        # The guard's own script is not a file the fleet consumes, so it is
        # not in GUARDED. Everything else must appear in both.
        self.assertEqual(
            paths - {"scripts/check_release_tag.py"}, set(check_release_tag.GUARDED)
        )
