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

# GET repos/{repo}/branches/{branch}/protection
PROTECTION = {
    "required_status_checks": {
        "strict": False,
        "contexts": ["checks / layout", "check"],
        "checks": [
            {"context": "checks / layout", "app_id": None},
            {"context": "check", "app_id": None},
        ],
    },
    # The shape a branch with no review rule answers with.
    "required_pull_request_reviews": None,
    "allow_force_pushes": {"enabled": False},
}

PROTECTION_WITH_REVIEWS = {
    "required_status_checks": {"strict": False, "contexts": ["test"], "checks": []},
    "required_pull_request_reviews": {
        "required_approving_review_count": 2,
        "dismiss_stale_reviews": False,
    },
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
    {"type": "pull_request", "parameters": {"required_approving_review_count": 0}},
]

# Two rulesets covering one branch. GitHub returns their rules in one
# list, and a merge waits for both.
STACKED_RULES = RULES + [
    {"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
]


class ProtectionGateTest(unittest.TestCase):
    def call(self, payload, error=""):
        original = audit.gh_api
        audit.gh_api = lambda path: (payload, error)
        try:
            return audit.protection_gate("org/a", "main")
        finally:
            audit.gh_api = original

    def test_merges_contexts_and_checks_without_duplicates(self):
        gate, error = self.call(PROTECTION)
        self.assertEqual(gate.contexts, ["check", "checks / layout"])
        self.assertEqual(error, "")

    def test_null_review_rule_reads_as_no_reviews(self):
        gate, _ = self.call(PROTECTION)
        self.assertEqual(gate.reviews, 0)

    def test_review_count_is_read(self):
        gate, _ = self.call(PROTECTION_WITH_REVIEWS)
        self.assertEqual(gate.reviews, 2)
        self.assertEqual(gate.contexts, ["test"])

    def test_unprotected_branch_reports_the_error(self):
        gate, error = self.call(None, "gh: Branch not protected (HTTP 404)")
        self.assertIsNone(gate)
        self.assertIn("404", error)


class RulesetGateTest(unittest.TestCase):
    def call(self, payload, error=""):
        original = audit.gh_api
        audit.gh_api = lambda path: (payload, error)
        try:
            return audit.ruleset_gate("org/a", "main")
        finally:
            audit.gh_api = original

    def test_reads_the_status_check_rule(self):
        gate, _ = self.call(RULES)
        self.assertEqual(gate.contexts, ["CI Success", "codecov/patch"])

    def test_a_pull_request_rule_asking_no_review_reads_as_zero(self):
        gate, _ = self.call(RULES)
        self.assertEqual(gate.reviews, 0)

    def test_stacked_rulesets_take_the_strictest_count(self):
        # Two rulesets cover the branch. A merge waits for both, so the
        # branch demands the larger of the two.
        gate, _ = self.call(STACKED_RULES)
        self.assertEqual(gate.reviews, 1)

    def test_branch_with_no_rules_has_no_gate(self):
        gate, error = self.call([])
        self.assertEqual(gate.contexts, [])
        self.assertEqual(gate.reviews, 0)
        self.assertEqual(error, "")


class LiveGateTest(unittest.TestCase):
    def test_regime_picks_the_endpoint(self):
        seen = []
        original = audit.gh_api

        def record(path):
            seen.append(path)
            return [], ""

        audit.gh_api = record
        try:
            audit.live_gate("org/a", "main", "ruleset")
            audit.live_gate("org/a", "main", "protection")
        finally:
            audit.gh_api = original
        self.assertIn("rules/branches/main", seen[0])
        self.assertTrue(seen[1].endswith("branches/main/protection"))


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
        original = audit.live_gate
        audit.live_gate = lambda repo, branch, regime: answers[(repo, branch)]
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = audit.audit(entries)
        finally:
            audit.live_gate = original
        return code, out.getvalue()

    def entry(self, **kw):
        base = {"repo": "org/a", "branch": "main", "contexts": ["test"], "reviews": 0}
        base.update(kw)
        return [base]

    def gate(self, contexts=("test",), reviews=0):
        return {("org/a", "main"): (audit.Gate(list(contexts), reviews), "")}

    def test_matching_fleet_exits_zero(self):
        code, _ = self.run_audit(self.entry(), self.gate())
        self.assertEqual(code, 0)

    def test_difference_exits_nonzero(self):
        code, out = self.run_audit(self.entry(), self.gate(contexts=()))
        self.assertEqual(code, 1)
        self.assertIn("test", out)

    def test_an_unrecorded_review_requirement_exits_nonzero(self):
        # The rule that blocked portolan-cli#777. The checks matched, and
        # a review requirement nobody recorded held the merge.
        code, out = self.run_audit(self.entry(), self.gate(reviews=1))
        self.assertEqual(code, 1)
        self.assertIn("0/1", out)

    def test_a_recorded_review_requirement_is_no_difference(self):
        code, out = self.run_audit(self.entry(reviews=1), self.gate(reviews=1))
        self.assertEqual(code, 0)
        self.assertIn("1/1", out)

    def test_unreadable_branch_exits_nonzero(self):
        # A token without administration:read reads nothing and must not
        # report a clean fleet.
        answers = {("org/a", "main"): (None, "HTTP 403")}
        code, out = self.run_audit(self.entry(), answers)
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
            self.assertIsInstance(entry["reviews"], int)

    def test_no_branch_waits_for_a_review(self):
        # The checks are the gate. A branch that waits for a review
        # stalls its own sync pull request, because auto-merge cannot use
        # the admin bypass. Raise this here first if that ever changes.
        for entry in audit.load_record():
            self.assertEqual(entry["reviews"], 0, entry["repo"])

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

    def test_no_branch_requires_an_external_coverage_status(self):
        # diff-cover is the merge gate. A missing Codecov callback cannot
        # leave a pull request in a pending state.
        for entry in audit.load_record():
            contexts = entry["contexts"]
            self.assertFalse(
                any(context.startswith("codecov/") for context in contexts),
                entry["repo"],
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
