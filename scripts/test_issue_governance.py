#!/usr/bin/env python3
"""Unit tests for issue_governance.py.

Run directly (check.yml does):

    python3 scripts/test_issue_governance.py

Every call the rules make to GitHub goes through `issue_governance.request`,
so the fake below stands in for the whole API. Each test asserts on the calls
recorded, which is what a rule is: what got written, and what did not. Both
directions of each rule are covered, because a rule that never declines to
act is not a rule.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import issue_governance

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "issue-governance" / "allowed-labels.json"

ALLOWED = {"bug", "enhancement", "task", "urgent"}
NORMS = "https://example.invalid/norms"


class FakeApi:
    """Records every write and answers reads from a canned issue."""

    def __init__(self, labels=None, milestone=None, comments=None, milestones=None):
        self.issue = {
            "number": 7,
            "labels": [{"name": name} for name in (labels or [])],
            "milestone": milestone,
        }
        self.comments = list(comments or [])
        self.milestones = list(milestones or [])
        self.calls = []

    def __call__(self, method, path, token, body=None):
        self.calls.append((method, path, body))
        if method == "GET" and "comments" in path:
            return self.comments if "page=1" in path else []
        if method == "GET" and "milestones" in path:
            return self.milestones if "page=1" in path else []
        if method == "GET":
            return self.issue
        if method == "POST" and "comments" in path:
            self.comments.append({"body": body["body"]})
            return {"id": 1}
        return {}

    def writes(self, method):
        return [(path, body) for verb, path, body in self.calls if verb == method]


class GovernanceTest(unittest.TestCase):
    def install(self, **kwargs):
        """Swap the API for a fake and hand it back."""
        fake = FakeApi(**kwargs)
        original = issue_governance.request
        issue_governance.request = fake
        self.addCleanup(setattr, issue_governance, "request", original)
        return fake


class AllowedLabels(GovernanceTest):
    def test_repo_additions_are_merged_in(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allowed.json"
            path.write_text(
                json.dumps(
                    {
                        "org_wide": sorted(ALLOWED),
                        "per_repo": {"portolan-spec": ["schemas"]},
                    }
                )
            )
            self.assertEqual(
                issue_governance.allowed_labels(str(path), "portolan-spec"),
                ALLOWED | {"schemas"},
            )
            self.assertNotIn(
                "schemas", issue_governance.allowed_labels(str(path), "rashid")
            )

    def test_the_shipped_config_is_coherent(self):
        """The file the workflow reads parses, and no repo repeats a label."""
        config = json.loads(CONFIG_FILE.read_text())
        self.assertIn("bug", config["org_wide"])
        self.assertIn("urgent", config["org_wide"])
        for repo, extras in config["per_repo"].items():
            with self.subTest(repo=repo):
                self.assertTrue(extras, "lists no additional labels")
                self.assertFalse(set(extras) & set(config["org_wide"]))


class StripLabels(GovernanceTest):
    def test_removes_labels_outside_the_set_and_comments_once(self):
        fake = self.install(labels=["bug", "roadmap:mvp", "spec-sprint"])
        removed = issue_governance.strip_labels("o/r", 7, "t", ALLOWED, NORMS)

        self.assertEqual(removed, 2)
        deleted = [path for path, _ in fake.writes("DELETE")]
        self.assertTrue(any("roadmap%3Amvp" in path for path in deleted))
        self.assertTrue(any("spec-sprint" in path for path in deleted))

        posted = fake.writes("POST")
        self.assertEqual(len(posted), 1)
        self.assertIn("`roadmap:mvp`", posted[0][1]["body"])
        self.assertIn(issue_governance.MARKER, posted[0][1]["body"])

    def test_leaves_a_clean_issue_alone(self):
        fake = self.install(labels=["bug", "urgent"])
        self.assertEqual(
            issue_governance.strip_labels("o/r", 7, "t", ALLOWED, NORMS), 0
        )
        self.assertEqual(fake.writes("DELETE"), [])
        self.assertEqual(fake.writes("POST"), [])

    def test_does_not_repeat_an_identical_comment(self):
        body = issue_governance.comment_body(["roadmap:mvp"], NORMS)
        fake = self.install(labels=["roadmap:mvp"], comments=[{"body": body}])

        self.assertEqual(
            issue_governance.strip_labels("o/r", 7, "t", ALLOWED, NORMS), 1
        )
        self.assertEqual(fake.writes("POST"), [])

    def test_comments_again_when_a_different_label_appears(self):
        old = issue_governance.comment_body(["roadmap:mvp"], NORMS)
        fake = self.install(labels=["spec-sprint"], comments=[{"body": old}])

        issue_governance.strip_labels("o/r", 7, "t", ALLOWED, NORMS)
        self.assertEqual(len(fake.writes("POST")), 1)


class DefaultMilestone(GovernanceTest):
    def test_sets_backlog_on_a_new_issue_with_none(self):
        fake = self.install(
            milestones=[
                {"title": "Beta", "number": 1},
                {"title": "Backlog", "number": 4},
            ]
        )
        issue_governance.default_milestone("o/r", 7, "t", "opened")
        self.assertEqual(
            fake.writes("PATCH"), [("/repos/o/r/issues/7", {"milestone": 4})]
        )

    def test_never_overrides_a_milestone_a_person_set(self):
        fake = self.install(
            milestone={"title": "Beta", "number": 1},
            milestones=[{"title": "Backlog", "number": 4}],
        )
        issue_governance.default_milestone("o/r", 7, "t", "opened")
        self.assertEqual(fake.writes("PATCH"), [])

    def test_ignores_events_other_than_opened(self):
        fake = self.install(milestones=[{"title": "Backlog", "number": 4}])
        issue_governance.default_milestone("o/r", 7, "t", "edited")
        self.assertEqual(fake.calls, [])

    def test_skips_quietly_when_the_repo_has_no_backlog(self):
        fake = self.install(milestones=[{"title": "Beta", "number": 1}])
        issue_governance.default_milestone("o/r", 7, "t", "opened")
        self.assertEqual(fake.writes("PATCH"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
