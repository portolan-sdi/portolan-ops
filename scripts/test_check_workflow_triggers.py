#!/usr/bin/env python3
"""Unit tests for check_workflow_triggers.py.

Run directly (check.yml does):

    uv run --no-project --with pyyaml==6.0.3 python \
        scripts/test_check_workflow_triggers.py
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_workflow_triggers as guard

CLEAN = """
name: Check
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
"""

FILTERED = """
name: Check
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
permissions:
  contents: read
"""

IGNORED = """
name: Check
on:
  pull_request:
    branches-ignore: [wip/**]
"""

TARGET = """
name: Check
on:
  pull_request_target:
    branches: [main]
"""

PATHS_ONLY = """
name: Check
on:
  pull_request:
    paths:
      - src/**
"""

LIST_FORM = """
name: Check
on: [push, pull_request]
"""


class BranchFiltersTest(unittest.TestCase):
    def test_pull_request_without_a_filter_passes(self):
        self.assertEqual(guard.branch_filters(CLEAN), [])

    def test_push_filter_alone_passes(self):
        # The push filter is correct and must stay.
        self.assertNotIn("push", guard.branch_filters(CLEAN))

    def test_branches_filter_is_reported(self):
        self.assertEqual(guard.branch_filters(FILTERED), ["branches"])

    def test_branches_ignore_is_reported(self):
        self.assertEqual(guard.branch_filters(IGNORED), ["branches-ignore"])

    def test_pull_request_target_is_reported(self):
        self.assertEqual(guard.branch_filters(TARGET), ["branches"])

    def test_paths_filter_passes(self):
        # A path filter narrows which changes run, not which base branch.
        self.assertEqual(guard.branch_filters(PATHS_ONLY), [])

    def test_list_form_trigger_passes(self):
        self.assertEqual(guard.branch_filters(LIST_FORM), [])

    def test_empty_document_passes(self):
        self.assertEqual(guard.branch_filters(""), [])


class WorkflowFilesTest(unittest.TestCase):
    def test_finds_both_suffixes_under_both_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "ci" / "python-package").mkdir(parents=True)
            (root / ".github" / "workflows" / "a.yml").write_text(CLEAN)
            (root / "ci" / "python-package" / "b.yaml").write_text(CLEAN)
            (root / "ci" / "notes.md").write_text("not a workflow")
            names = [p.name for p in guard.workflow_files(root)]
        self.assertEqual(names, ["a.yml", "b.yaml"])

    def test_missing_directory_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(guard.workflow_files(Path(tmp)), [])


class RepoTest(unittest.TestCase):
    def test_this_repo_is_clean(self):
        # The guard runs against ROOT in CI. Prove it passes here too.
        self.assertEqual(guard.main(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
