#!/usr/bin/env python3
"""Unit tests for check_protection.py.

Run directly (check.yml does):

    uv run --no-project --with pyyaml==6.0.3 python \
        scripts/test_check_protection.py

The API payloads are recorded, so no test reaches the network.
"""

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_protection as audit

# GET repos/{repo}/branches/{branch}/protection/required_status_checks
PROTECTION = {
    "strict": False,
    "contexts": ["checks / layout", "check"],
    "checks": [
        {"context": "checks / layout", "app_id": None},
        {"context": "check", "app_id": None},
    ],
}

# GET repos/{repo}/rules/branches/{branch}
RULES = [
    {"type": "deletion"},
    {
        "type": "required_status_checks",
        "parameters": {
            "required_status_checks": [
                {"context": "CI Success"},
                {"context": "codecov/patch"},
            ]
        },
    },
]


class ProtectionContextsTest(unittest.TestCase):
    def call(self, payload, error=""):
        original = audit.gh_api
        audit.gh_api = lambda path: (payload, error)
        try:
            return audit.protection_contexts("org/a", "main")
        finally:
            audit.gh_api = original

    def test_merges_contexts_and_checks_without_duplicates(self):
        names, error = self.call(PROTECTION)
        self.assertEqual(names, ["check", "checks / layout"])
        self.assertEqual(error, "")

    def test_unprotected_branch_reports_the_error(self):
        names, error = self.call(None, "gh: Branch not protected (HTTP 404)")
        self.assertIsNone(names)
        self.assertIn("404", error)


class RulesetContextsTest(unittest.TestCase):
    def call(self, payload, error=""):
        original = audit.gh_api
        audit.gh_api = lambda path: (payload, error)
        try:
            return audit.ruleset_contexts("org/a", "main")
        finally:
            audit.gh_api = original

    def test_reads_the_status_check_rule_only(self):
        names, _ = self.call(RULES)
        self.assertEqual(names, ["CI Success", "codecov/patch"])

    def test_branch_with_no_rules_has_no_contexts(self):
        names, error = self.call([])
        self.assertEqual(names, [])
        self.assertEqual(error, "")


class LiveContextsTest(unittest.TestCase):
    def test_regime_picks_the_endpoint(self):
        seen = []
        original = audit.gh_api

        def record(path):
            seen.append(path)
            return [], ""

        audit.gh_api = record
        try:
            audit.live_contexts("org/a", "main", "ruleset")
            audit.live_contexts("org/a", "main", "protection")
        finally:
            audit.gh_api = original
        self.assertIn("rules/branches/main", seen[0])
        self.assertIn("protection/required_status_checks", seen[1])


class CompareTest(unittest.TestCase):
    def test_match_reports_nothing(self):
        self.assertEqual(audit.compare(["a", "b"], ["b", "a"]), ([], []))

    def test_missing_context_is_reported(self):
        self.assertEqual(audit.compare(["a", "b"], ["a"]), (["b"], []))

    def test_extra_context_is_reported(self):
        # An extra gate is not a failure of the fleet, but the record
        # must name every check a merge waits on.
        self.assertEqual(audit.compare(["a"], ["a", "z"]), ([], ["z"]))


class AuditTest(unittest.TestCase):
    def run_audit(self, entries, answers):
        original = audit.live_contexts
        audit.live_contexts = lambda repo, branch, regime: answers[(repo, branch)]
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = audit.audit(entries)
        finally:
            audit.live_contexts = original
        return code, out.getvalue()

    def test_matching_fleet_exits_zero(self):
        entries = [{"repo": "org/a", "branch": "main", "contexts": ["test"]}]
        code, _ = self.run_audit(entries, {("org/a", "main"): (["test"], "")})
        self.assertEqual(code, 0)

    def test_difference_exits_nonzero(self):
        entries = [{"repo": "org/a", "branch": "main", "contexts": ["test"]}]
        code, out = self.run_audit(entries, {("org/a", "main"): ([], "")})
        self.assertEqual(code, 1)
        self.assertIn("test", out)

    def test_unreadable_branch_exits_nonzero(self):
        # A token without administration:read reads nothing and must not
        # report a clean fleet.
        entries = [{"repo": "org/a", "branch": "main", "contexts": ["test"]}]
        answers = {("org/a", "main"): (None, "HTTP 403")}
        code, out = self.run_audit(entries, answers)
        self.assertEqual(code, 1)
        self.assertIn("UNREADABLE", out)


class RecordTest(unittest.TestCase):
    def test_every_entry_is_well_formed(self):
        entries = audit.load_record()
        for entry in entries:
            self.assertIn("/", entry["repo"])
            self.assertTrue(entry["branch"])
            self.assertIn(entry["regime"], audit.REGIMES)
            self.assertTrue(entry["contexts"])

    def test_every_branch_requires_both_org_checks_or_says_why(self):
        # repo-checks.yml posts these two in every repo. A branch that
        # does not require them merges without the layout and body gates,
        # so it has to carry a note that says why.
        org = {"checks / layout", "checks / pull-request"}
        for entry in audit.load_record():
            if org <= set(entry["contexts"]):
                continue
            note = entry.get("note", "")
            self.assertTrue(note, f"{entry['repo']} {entry['branch']}: no note")
            self.assertGreater(len(note.split()), 5)

    def test_no_repo_and_branch_pair_repeats(self):
        pairs = [(e["repo"], e["branch"]) for e in audit.load_record()]
        self.assertEqual(len(pairs), len(set(pairs)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
