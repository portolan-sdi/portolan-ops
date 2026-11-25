#!/usr/bin/env python3
"""Unit tests for next_release.py.

Run directly (check.yml does):

    python3 scripts/test_next_release.py

Each test builds a throwaway git repo, so the tests need git and no network.
"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import next_release


class RepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self.cwd)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "tag.gpgSign", "false")
        self.git("config", "commit.gpgSign", "false")
        self.commit("chore: start")
        self.git("tag", "-a", "v1.4.2", "-m", "v1.4.2")

    def git(self, *args):
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    def commit(self, message):
        self.git("commit", "-q", "--allow-empty", "-m", message)

    def plan(self, bump="auto"):
        return next_release.plan("HEAD", bump)


class PlanTest(RepoTest):
    def test_nothing_since_the_tag(self):
        self.assertIsNone(self.plan())

    def test_fix_bumps_patch(self):
        self.commit("fix: one")
        self.commit("docs: two")
        self.assertEqual(self.plan(), ("v1.4.3", ["fix: one", "docs: two"]))

    def test_feat_bumps_minor(self):
        self.commit("fix: one")
        self.commit("feat(sync): two")
        self.assertEqual(self.plan()[0], "v1.5.0")

    def test_non_conventional_subject_is_patch(self):
        self.commit("Update README")
        self.assertEqual(self.plan()[0], "v1.4.3")

    def test_bang_is_breaking(self):
        self.commit("ci!: drop inputs")
        with self.assertRaises(next_release.ReleaseError) as caught:
            self.plan()
        self.assertIn("ci!: drop inputs", str(caught.exception))
        self.assertIn("bump=minor", str(caught.exception))

    def test_scoped_bang_is_breaking(self):
        self.commit("feat(api)!: rename")
        with self.assertRaises(next_release.ReleaseError):
            self.plan()

    def test_footer_is_breaking(self):
        self.commit("fix: one\n\nBREAKING CHANGE: the input is gone")
        with self.assertRaises(next_release.ReleaseError):
            self.plan()

    def test_breaking_in_prose_is_not_a_footer(self):
        self.commit("fix: one\n\nThis is not a BREAKING CHANGE: honest")
        self.assertEqual(self.plan()[0], "v1.4.3")

    def test_override_skips_the_breaking_check(self):
        self.commit("ci!: drop inputs")
        self.assertEqual(self.plan("minor")[0], "v1.5.0")
        self.assertEqual(self.plan("patch")[0], "v1.4.3")

    def test_newest_ancestor_tag_wins(self):
        self.commit("fix: one")
        self.git("tag", "-a", "v1.10.0", "-m", "v1.10.0")
        self.git("tag", "v1")
        self.commit("fix: two")
        self.assertEqual(self.plan(), ("v1.10.1", ["fix: two"]))

    def test_stale_run_after_a_newer_release(self):
        self.commit("fix: one")
        old = self.git("rev-parse", "HEAD")
        self.commit("fix: two")
        self.git("tag", "-a", "v1.4.3", "-m", "v1.4.3")
        self.assertIsNone(next_release.plan(old, "auto"))

    def test_next_tag_on_another_branch_fails(self):
        self.git("checkout", "-q", "-b", "side")
        self.commit("fix: side")
        self.git("tag", "-a", "v1.4.3", "-m", "v1.4.3")
        self.git("checkout", "-q", "main")
        self.commit("fix: main")
        with self.assertRaises(next_release.ReleaseError) as caught:
            self.plan()
        self.assertIn("already exists", str(caught.exception))

    def test_no_tag_fails(self):
        self.git("tag", "-d", "v1.4.2")
        with self.assertRaises(next_release.ReleaseError):
            self.plan()


class MainTest(RepoTest):
    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = next_release.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_release_prints_tag_and_subjects(self):
        self.commit("feat: one")
        self.assertEqual(self.run_main(), (0, "v1.5.0\n- feat: one\n", ""))

    def test_nothing_to_release_exits_zero_with_empty_stdout(self):
        self.assertEqual(self.run_main(), (0, "", "nothing to release\n"))

    def test_breaking_exits_one(self):
        self.commit("ci!: drop inputs")
        code, out, err = self.run_main()
        self.assertEqual((code, out), (1, ""))
        self.assertIn("v2", err)

    def test_bump_flag(self):
        self.commit("ci!: drop inputs")
        self.assertEqual(self.run_main("--bump", "minor")[1].splitlines()[0], "v1.5.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
