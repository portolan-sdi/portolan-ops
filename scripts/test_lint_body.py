#!/usr/bin/env python3
"""Unit tests for lint_body.py.

Run directly (check.yml does):

    python3 scripts/test_lint_body.py

Covers each rule in both directions, and checks that the shipped templates
behave: filled in they pass, submitted untouched they fail.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lint_body

ROOT = Path(__file__).resolve().parent.parent
PR_TEMPLATE = ROOT / "templates" / "PULL_REQUEST_TEMPLATE.md"

GOOD_PR = """\
## What this changes

`portolan check` now reports a partition mismatch instead of exiting zero.

## Why

Closes #42.

## Verification

Ran it against the Overture buildings catalog:

```console
$ portolan check https://data.example.org/overture/catalog.json
error: partition key "quadkey" absent from 3 of 210 items
```

- [ ] This change does not alter behavior (docs, chore, or CI only).

## Related issues

#42
"""


def problems(body, kind="pr", **kw):
    return lint_body.check(body, kind, **kw)


def joined(body, kind="pr", **kw):
    return " ".join(problems(body, kind, **kw))


class GoodBodyTest(unittest.TestCase):
    def test_filled_template_passes(self):
        self.assertEqual(problems(GOOD_PR), [])

    def test_shipped_template_untouched_fails(self):
        found = joined(PR_TEMPLATE.read_text(encoding="utf-8"))
        self.assertIn("is empty", found)

    def test_empty_body_fails(self):
        self.assertIn("empty", joined("   \n\n"))


class RequiredSectionTest(unittest.TestCase):
    def test_missing_section_named(self):
        body = GOOD_PR.replace("## Verification", "## Testing")
        self.assertIn('Missing the "Verification" section', joined(body))

    def test_empty_section_named(self):
        body = GOOD_PR.replace("Closes #42.", "")
        self.assertIn('"Why" is empty', joined(body))

    def test_heading_match_ignores_trailing_punctuation(self):
        body = GOOD_PR.replace("## Why", "## Why:")
        self.assertNotIn("Missing", joined(body))

    def test_issue_kind_requires_no_headings(self):
        body = (
            "### What happened?\n\nIt broke.\n\n```\n$ run /data/x.parquet\nboom\n```\n"
        )
        self.assertEqual(problems(body, kind="issue"), [])


class WordBudgetTest(unittest.TestCase):
    def test_over_budget_reports_count_and_section(self):
        padded = GOOD_PR.replace("Closes #42.", "word " * 300)
        found = joined(padded)
        self.assertIn("the budget is 200", found)
        self.assertIn('"Why"', found)

    def test_code_blocks_do_not_count(self):
        body = GOOD_PR.replace(
            "boom", "\n".join("output line here" for _ in range(200))
        )
        self.assertNotIn("budget", joined(body))

    def test_html_comments_do_not_count(self):
        body = GOOD_PR.replace("Closes #42.", "<!-- " + "word " * 300 + " -->")
        self.assertNotIn("budget", joined(body))

    def test_multiline_comment_does_not_count(self):
        comment = "<!--\n" + ("word " * 60 + "\n") * 5 + "-->"
        body = GOOD_PR.replace("Closes #42.", "Closes #42.\n" + comment)
        self.assertNotIn("budget", joined(body))

    def test_budget_is_configurable(self):
        self.assertIn("the budget is 5", joined(GOOD_PR, max_words=5))


class SectionLengthTest(unittest.TestCase):
    def test_long_section_reported(self):
        body = GOOD_PR.replace("Closes #42.", "\n".join("line" for _ in range(9)))
        found = joined(body)
        self.assertIn('"Why" runs 9 lines', found)

    def test_blank_lines_do_not_count(self):
        body = GOOD_PR.replace("Closes #42.", "\n\n".join("line" for _ in range(6)))
        self.assertNotIn("runs", joined(body))

    def test_code_lines_do_not_count(self):
        long_block = "\n".join(f"line {i}" for i in range(40))
        body = GOOD_PR.replace("boom", long_block)
        self.assertNotIn("runs", joined(body))


class EvidenceTest(unittest.TestCase):
    def test_no_pasted_output_reported(self):
        body = GOOD_PR.split("```console")[0] + "\n## Related issues\n\n#42\n"
        self.assertIn("pastes no output", joined(body))

    def test_tests_pass_alone_is_not_evidence(self):
        body = GOOD_PR.replace(
            "Ran it against the Overture buildings catalog:", "CI is green."
        )
        body = body.split("```console")[0] + "\n## Related issues\n\n#42\n"
        self.assertIn("pastes no output", joined(body))

    def test_empty_fence_is_not_evidence(self):
        body = GOOD_PR.replace(
            "$ portolan check https://data.example.org/overture/catalog.json\n"
            'error: partition key "quadkey" absent from 3 of 210 items\n',
            "\n",
        )
        self.assertIn("pastes no output", joined(body))

    def test_unnamed_source_reported(self):
        body = GOOD_PR.replace(
            "$ portolan check https://data.example.org/overture/catalog.json",
            "$ portolan check",
        )
        self.assertIn("names no data source", joined(body))

    def test_local_path_counts_as_a_source(self):
        body = GOOD_PR.replace(
            "https://data.example.org/overture/catalog.json",
            "tests/data/overture.parquet",
        )
        self.assertEqual(problems(body), [])

    def test_object_store_url_counts_as_a_source(self):
        body = GOOD_PR.replace(
            "https://data.example.org/overture/catalog.json",
            "s3://portolan-demo/overture/catalog.json",
        )
        self.assertEqual(problems(body), [])

    def test_ticked_waiver_skips_evidence(self):
        body = GOOD_PR.split("## Verification")[0] + (
            "## Verification\n\n"
            "- [x] This change does not alter behavior (docs, chore, or CI only).\n\n"
            "## Related issues\n\n#42\n"
        )
        self.assertEqual(problems(body), [])

    def test_waiver_does_not_skip_the_budget(self):
        body = GOOD_PR.split("## Verification")[0] + (
            "## Verification\n\n"
            "- [x] This change does not alter behavior (docs, chore, or CI only).\n\n"
            "## Related issues\n\n" + "word " * 300
        )
        self.assertIn("budget", joined(body))

    def test_unticked_waiver_still_demands_evidence(self):
        body = GOOD_PR.split("```console")[0] + (
            "- [ ] This change does not alter behavior (docs, chore, or CI only).\n\n"
            "## Related issues\n\n#42\n"
        )
        self.assertIn("pastes no output", joined(body))

    def test_issue_without_anything_pasted_reported(self):
        body = "### What needs doing?\n\nRename the thing everywhere.\n"
        self.assertIn("Nothing is pasted", joined(body, kind="issue"))


class CliTest(unittest.TestCase):
    def test_exit_codes(self):
        import io

        for body, expected in ((GOOD_PR, 0), ("### x\n\nnope\n", 1)):
            with self.subTest(expected=expected):
                sys.stdin = io.StringIO(body)
                try:
                    self.assertEqual(lint_body.main(["--kind", "pr"]), expected)
                finally:
                    sys.stdin = sys.__stdin__


if __name__ == "__main__":
    unittest.main(verbosity=2)
