#!/usr/bin/env python3
"""Unit tests for reconcile_repo_automation.py."""

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import reconcile_repo_automation as automation


class ReconcileTest(unittest.TestCase):
    def setUp(self):
        self.original_api = automation.gh_api
        self.calls = []

    def tearDown(self):
        automation.gh_api = self.original_api

    def install(self, *, auto_merge=True, actions=True, workflow_state="active"):
        def fake(path, method="GET", body=None):
            self.calls.append((path, method, body))
            if path.startswith("orgs/"):
                return [
                    {
                        "full_name": "org/repo",
                        "archived": False,
                        "disabled": False,
                    },
                    {"full_name": "org/old", "archived": True, "disabled": False},
                ]
            if path == "repos/org/repo":
                return {"allow_auto_merge": auto_merge}
            if path.endswith("actions/permissions"):
                return {"enabled": actions, "allowed_actions": "all"}
            if path.endswith("actions/workflows?per_page=100"):
                return {
                    "workflows": [
                        {
                            "id": 17,
                            "path": ".github/workflows/check.yml",
                            "state": workflow_state,
                        }
                    ]
                }
            if path.endswith("/enable"):
                return None
            raise AssertionError(path)

        automation.gh_api = fake

    def run_reconcile(self, apply=False):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = automation.reconcile("org", apply)
        return code, output.getvalue()

    def test_clean_fleet_exits_zero(self):
        self.install()
        code, output = self.run_reconcile()
        self.assertEqual(code, 0)
        self.assertIn("match the automation policy", output)

    def test_audit_reports_each_disabled_control(self):
        self.install(auto_merge=False, actions=False, workflow_state="disabled_fork")
        code, output = self.run_reconcile()
        self.assertEqual(code, 1)
        self.assertIn("auto-merge", output)
        self.assertIn("Actions", output)
        self.assertIn(".github/workflows/check.yml", output)
        self.assertFalse(any(method != "GET" for _, method, _ in self.calls))

    def test_apply_repairs_each_disabled_control(self):
        self.install(auto_merge=False, actions=False, workflow_state="disabled_fork")
        code, output = self.run_reconcile(apply=True)
        self.assertEqual(code, 0)
        self.assertEqual(output.count("repaired"), 3)
        writes = [
            (path, method, body) for path, method, body in self.calls if method != "GET"
        ]
        self.assertIn(
            ("repos/org/repo", "PATCH", {"allow_auto_merge": True}),
            writes,
        )
        self.assertIn(
            (
                "repos/org/repo/actions/permissions",
                "PUT",
                {"enabled": True, "allowed_actions": "all"},
            ),
            writes,
        )
        self.assertIn(
            ("repos/org/repo/actions/workflows/17/enable", "PUT", None),
            writes,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
