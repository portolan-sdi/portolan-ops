#!/usr/bin/env python3
"""Unit tests for compare_vale.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare_vale


def report(*alerts):
    result = {}
    for path, check, match, message in alerts:
        result.setdefault(path, []).append(
            {"Check": check, "Match": match, "Message": message}
        )
    return result


class NewFindingsTest(unittest.TestCase):
    def test_unchanged_finding_is_not_new(self):
        item = ("docs/a.md", "Portolan.Rule", "bad", "Rewrite it.")
        self.assertFalse(compare_vale.new_findings(report(item), report(item)))

    def test_line_moves_do_not_change_the_fingerprint(self):
        base = {
            "docs/a.md": [
                {"Check": "Rule", "Match": "bad", "Message": "Fix.", "Line": 1}
            ]
        }
        current = {
            "./docs/a.md": [
                {"Check": "Rule", "Match": "bad", "Message": "Fix.", "Line": 20}
            ]
        }
        self.assertFalse(compare_vale.new_findings(base, current))

    def test_extra_occurrence_is_new(self):
        item = ("docs/a.md", "Portolan.Rule", "bad", "Rewrite it.")
        added = compare_vale.new_findings(report(item), report(item, item))
        self.assertEqual(sum(added.values()), 1)

    def test_new_rule_finding_is_new(self):
        old = ("docs/a.md", "Portolan.Old", "bad", "Rewrite it.")
        new = ("docs/a.md", "Portolan.New", "bad", "Rewrite it.")
        added = compare_vale.new_findings(report(old), report(old, new))
        self.assertEqual(sum(added.values()), 1)


class ReadReportTest(unittest.TestCase):
    def test_empty_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "is empty"):
                compare_vale.read_report(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
