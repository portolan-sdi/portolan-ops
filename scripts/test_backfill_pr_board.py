#!/usr/bin/env python3
"""Unit tests for backfill_pr_board.py."""

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backfill_pr_board as backfill


class BackfillTest(unittest.TestCase):
    def setUp(self):
        self.original_gh = backfill.gh
        self.calls = []

    def tearDown(self):
        backfill.gh = self.original_gh

    def install(self, pulls=None):
        if pulls is None:
            pulls = [
                {
                    "number": 7,
                    "node_id": "PR_human",
                    "title": "Fix the check",
                    "user": {"type": "User"},
                },
                {
                    "number": 8,
                    "node_id": "PR_bot",
                    "title": "Bump a pin",
                    "user": {"type": "Bot"},
                },
            ]

        def fake(args, stdin=None):
            self.calls.append(args)
            if args[:2] == ["api", "graphql"]:
                query = next(a for a in args if a.startswith("query="))
                if "projectV2" in query:
                    return {"data": {"organization": {"projectV2": {"id": "PVT_1"}}}}
                return {"data": {"addProjectV2ItemById": {"item": {"id": "I_1"}}}}
            path = args[-1]
            if path.startswith("orgs/"):
                return [
                    {"full_name": "org/repo", "archived": False, "disabled": False},
                    {"full_name": "org/old", "archived": True, "disabled": False},
                    {"full_name": "org/off", "archived": False, "disabled": True},
                ]
            if path.startswith("repos/org/repo/pulls"):
                return pulls
            raise AssertionError(path)

        backfill.gh = fake

    def run_backfill(self, apply=False):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = backfill.backfill("org", 1, apply)
        return code, output.getvalue()

    def mutations(self):
        return [
            args
            for args in self.calls
            if args[:2] == ["api", "graphql"]
            and any("addProjectV2ItemById" in a for a in args)
        ]

    def test_the_dry_run_writes_nothing(self):
        self.install()
        code, output = self.run_backfill(apply=False)
        self.assertEqual(code, 0)
        self.assertIn("would add", output)
        self.assertEqual(self.mutations(), [])

    def test_apply_adds_the_human_pull_request(self):
        self.install()
        code, output = self.run_backfill(apply=True)
        self.assertEqual(code, 0)
        self.assertIn("added", output)
        self.assertEqual(len(self.mutations()), 1)
        self.assertTrue(
            any("content=PR_human" in a for a in self.mutations()[0]),
            self.mutations(),
        )

    def test_a_bot_pull_request_stays_off_the_board(self):
        self.install()
        _, output = self.run_backfill(apply=True)
        self.assertIn("org/repo#7", output)
        self.assertNotIn("org/repo#8", output)

    def test_an_archived_or_disabled_repo_is_skipped(self):
        self.install()
        self.run_backfill()
        listed = [a[-1] for a in self.calls if a[-1].startswith("repos/")]
        self.assertEqual(listed, ["repos/org/repo/pulls?state=open&per_page=100"])

    def test_no_open_pull_requests_reports_and_exits_zero(self):
        self.install(pulls=[])
        code, output = self.run_backfill()
        self.assertEqual(code, 0)
        self.assertIn("No open pull requests", output)

    def test_a_missing_project_reports_an_error(self):
        self.install()
        original = backfill.gh

        def fake(args, stdin=None):
            if args[:2] == ["api", "graphql"] and any("projectV2" in a for a in args):
                return {"data": {"organization": {"projectV2": None}}}
            return original(args, stdin)

        backfill.gh = fake
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            code = backfill.main(["--org", "org", "--project", "9"])
        self.assertEqual(code, 1)
        self.assertIn("no project number 9", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
