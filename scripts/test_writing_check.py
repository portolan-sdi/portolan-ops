#!/usr/bin/env python3
"""Tests for the writing hook.

The test that matters most is CorpusTest. It runs the checker over bodies that
are already good and asserts nothing blocks. A rule that trips it is wrong,
because the hook stops an author from filing. Demote the rule rather than tune
the corpus.

    python3 scripts/test_writing_check.py
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude" / "hooks" / "writing_check.py"

_spec = importlib.util.spec_from_file_location("writing_check", HOOK)
assert _spec and _spec.loader
wc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wc)


def blocking(body: str, kind: str = "issue") -> list[str]:
    findings, _labels = wc.review(body, kind)
    return [f.rule for f in findings if f.blocking]


def advisory(body: str, kind: str = "issue") -> list[str]:
    findings, _labels = wc.review(body, kind)
    return [f.rule for f in findings if not f.blocking]


# The fixture is written in Simplified Technical English, because the checker
# it exercises enforces STE. Short sentences. Active voice. Simple verbs.
GOOD_PR = """\
## What changed

`portolan check` now rejects a `partition:glob` URL that it cannot expand.

## Why

Closes #761. A catalog passed the check but no reader could open it.

## Verification

The command from the issue now reports the error.

```console
$ portolan check s3://example-bucket/catalog.json
error: partition:glob has no matching objects
```
"""


class MaskingTest(unittest.TestCase):
    def test_fenced_code_is_not_prose(self) -> None:
        body = "Text here.\n\n```\nvery robust; leverage --\n```\n"
        self.assertEqual(blocking(body), [])

    def test_inline_code_is_not_prose(self) -> None:
        self.assertEqual(blocking("Set `--simply-really` on the call."), [])

    def test_html_comments_are_not_prose(self) -> None:
        self.assertEqual(blocking("Text.\n<!-- just really powerful -->\n"), [])

    def test_urls_are_not_prose(self) -> None:
        body = "See https://example.com/a;b?just=1 for the data."
        self.assertEqual(blocking(body), [])

    def test_table_rows_are_not_prose(self) -> None:
        body = "Text.\n\n| a | b |\n|---|---|\n| just | robust; |\n"
        self.assertEqual(blocking(body), [])

    def test_blockquotes_are_not_prose(self) -> None:
        self.assertEqual(blocking("Text.\n\n> it is just really powerful\n"), [])

    def test_masking_keeps_line_numbers(self) -> None:
        body = "```\ncode\n```\n\nThis is just wrong.\n"
        findings, _ = wc.review(body, "issue")
        self.assertEqual([f.line for f in findings if f.blocking], [5])


class SentenceTest(unittest.TestCase):
    def split(self, text: str) -> list[str]:
        return [s.text.strip() for s in wc.sentences(wc.Doc(text))]

    def test_abbreviation_does_not_split(self) -> None:
        self.assertEqual(len(self.split("Use a store, e.g. S3, for this.")), 1)

    def test_version_does_not_split(self) -> None:
        self.assertEqual(len(self.split("We pin v1.2.3 for the build.")), 1)

    def test_decimal_does_not_split(self) -> None:
        self.assertEqual(len(self.split("Ruff moved to 0.16.0 last week.")), 1)

    def test_filename_does_not_split(self) -> None:
        self.assertEqual(len(self.split("Read catalog.json from the root.")), 1)

    def test_two_sentences_split(self) -> None:
        self.assertEqual(len(self.split("The parser fails. The check passes.")), 2)

    def test_list_item_is_one_unit(self) -> None:
        body = "- One thing. Another thing.\n- A third thing.\n"
        self.assertEqual(len(self.split(body)), 2)


class VocabularyTest(unittest.TestCase):
    def test_filler_blocks(self) -> None:
        self.assertIn("FILLER", blocking("The parser simply drops the row."))

    def test_temporal_just_passes(self) -> None:
        self.assertEqual(blocking("The job runs just before midnight."), [])

    def test_hyphenated_just_passes(self) -> None:
        self.assertEqual(blocking("The reader uses just-in-time reads."), [])

    def test_hype_blocks(self) -> None:
        self.assertIn("HYPE", blocking("The new parser is powerful."))

    def test_statistical_robust_passes(self) -> None:
        self.assertEqual(blocking("The estimate is robust to outliers."), [])

    def test_vague_verb_blocks(self) -> None:
        self.assertIn("VAGUE_VERB", blocking("We leverage the cache here."))

    def test_address_and_enable_pass(self) -> None:
        body = "Set the IP address. Enable the flag. Provide the token."
        self.assertEqual(blocking(body), [])

    def test_wordy_phrase_blocks(self) -> None:
        self.assertIn("WORDY", blocking("Run the check prior to the merge."))

    def test_idiom_blocks(self) -> None:
        self.assertIn("IDIOM", blocking("This is the low-hanging fruit."))

    def test_qualifier_blocks(self) -> None:
        self.assertIn("QUALIFIER", blocking("The scan is very slow."))

    def test_rather_than_passes(self) -> None:
        self.assertEqual(blocking("Use a URL rather than a local path."), [])

    def test_closing_tail_blocks(self) -> None:
        self.assertIn("CLOSING_TAIL", blocking("The fix lands. Hope this helps."))


class VerbFormTest(unittest.TestCase):
    """STE allows simple tenses and the active voice. This is the core rule."""

    def test_gerund_blocks(self) -> None:
        self.assertIn("GERUND", blocking("The check stops counting words."))

    def test_present_participle_blocks(self) -> None:
        self.assertIn("GERUND", blocking("The parser is reporting an error."))

    def test_noun_ending_in_ing_passes(self) -> None:
        body = "The setting holds a string. The warning names the heading."
        self.assertEqual(blocking(body), [])

    def test_passive_blocks(self) -> None:
        self.assertIn("PASSIVE", blocking("The body is checked before filing."))

    def test_predicate_adjective_passes(self) -> None:
        self.assertEqual(blocking("The flag is required for the run."), [])

    def test_perfect_tense_blocks(self) -> None:
        self.assertIn("PERFECT_TENSE", blocking("The label has accumulated."))

    def test_simple_tense_passes(self) -> None:
        body = "The check reads the body. It reports the line. It exits."
        self.assertEqual(blocking(body), [])


class PunctuationTest(unittest.TestCase):
    def test_em_dash_blocks(self) -> None:
        self.assertIn("EM_DASH", blocking("The parser fails — it reads late."))

    def test_numeric_en_dash_passes(self) -> None:
        self.assertEqual(blocking("The range is 10–20 rows."), [])

    def test_double_hyphen_flag_passes(self) -> None:
        self.assertEqual(blocking("Pass `--body-file` to the command."), [])

    def test_semicolon_blocks(self) -> None:
        self.assertIn("SEMICOLON", blocking("Copies drift; synced ones do not."))

    def test_mid_colon_blocks(self) -> None:
        body = "The command fails for one reason: the parser reads the URL late."
        self.assertIn("MID_COLON", blocking(body))

    def test_label_colon_passes(self) -> None:
        self.assertEqual(blocking("**Note:** the parser reads the URL late."), [])

    def test_colon_before_list_passes(self) -> None:
        body = "The check reads three things:\n\n- one\n- two\n"
        self.assertEqual(blocking(body), [])

    def test_short_tail_colon_passes(self) -> None:
        self.assertEqual(blocking("It printed one line: results below."), [])


class LengthTest(unittest.TestCase):
    def test_long_sentence_blocks(self) -> None:
        body = "The " + "word " * 40 + "ends."
        self.assertIn("LONG_SENTENCE", blocking(body))

    def test_medium_sentence_advises_only(self) -> None:
        body = "The " + "word " * 17 + "ends."
        self.assertEqual(blocking(body), [])
        self.assertIn("SENTENCE_LONG", advisory(body))

    def test_ste_limit_is_twenty_words(self) -> None:
        self.assertEqual(blocking("The " + "word " * 18 + "ends."), [])
        self.assertIn("LONG_SENTENCE", blocking("The " + "word " * 20 + "ends."))

    def test_long_url_counts_as_one_word(self) -> None:
        url = "https://example.com/" + "a" * 300
        self.assertEqual(blocking(f"Read the catalog at {url} first."), [])

    def test_long_document_passes(self) -> None:
        para = "The parser reads the URL. The check reports the failure.\n\n"
        self.assertEqual(blocking(para * 60), [])


class StructureTest(unittest.TestCase):
    def test_good_pr_passes(self) -> None:
        self.assertEqual(blocking(GOOD_PR, "pr"), [])

    def test_missing_section_blocks(self) -> None:
        body = GOOD_PR.replace("## Why", "## Background")
        self.assertIn("HEADING_MISSING", blocking(body, "pr"))

    def test_old_heading_spelling_still_passes(self) -> None:
        body = GOOD_PR.replace("## What changed", "## What this changes")
        self.assertEqual(blocking(body, "pr"), [])

    def test_empty_section_blocks(self) -> None:
        body = "## What changed\n\n## Why\n\nCloses #1.\n\n## Verification\n\n```\nok\n```\n"
        self.assertIn("HEADING_EMPTY", blocking(body, "pr"))

    def test_code_only_section_is_not_empty(self) -> None:
        self.assertEqual(blocking(GOOD_PR, "pr"), [])

    def test_out_of_order_blocks(self) -> None:
        body = (
            "## Verification\n\n```\nok\n```\n\n"
            "## What changed\n\nIt reads the URL.\n\n"
            "## Why\n\nCloses #1.\n"
        )
        self.assertIn("HEADING_ORDER", blocking(body, "pr"))

    def test_issue_without_headings_is_not_structured(self) -> None:
        self.assertEqual(blocking("The parser reads the URL late."), [])

    def test_empty_body_blocks(self) -> None:
        self.assertIn("EMPTY_BODY", blocking("   \n\n"))


class SuppressionTest(unittest.TestCase):
    def test_marker_suppresses_next_line(self) -> None:
        body = "<!-- ste-ok: FILLER quoting the user report -->\nIt is just wrong.\n"
        self.assertEqual(blocking(body), [])

    def test_marker_does_not_suppress_other_rules(self) -> None:
        body = "<!-- ste-ok: FILLER quoting the user report -->\nIt is powerful.\n"
        self.assertIn("HYPE", blocking(body))

    def test_marker_does_not_suppress_other_lines(self) -> None:
        body = (
            "<!-- ste-ok: FILLER quoting the report -->\n"
            "It is just wrong.\n\nIt is just broken.\n"
        )
        self.assertEqual(blocking(body).count("FILLER"), 1)

    def test_marker_without_reason_is_ignored(self) -> None:
        self.assertIn("FILLER", blocking("<!-- ste-ok: FILLER -->\nIt is just wrong."))

    def test_skip_suppresses_everything(self) -> None:
        body = "<!-- ste-skip: pasted from the vendor report -->\nIt is just powerful."
        self.assertEqual(blocking(body), [])

    def test_marker_inside_a_fence_does_not_suppress(self) -> None:
        body = "```\n<!-- ste-skip: not a real waiver -->\n```\n\nIt is just wrong.\n"
        self.assertIn("FILLER", blocking(body))


class CommandTest(unittest.TestCase):
    def test_body_flag(self) -> None:
        got = wc.body_from_command("gh pr create --title x --body 'It works.'")
        self.assertEqual(got, ("pr", "It works."))

    def test_body_equals_form(self) -> None:
        got = wc.body_from_command("gh issue create --body='It works.'")
        self.assertEqual(got, ("issue", "It works."))

    def test_body_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("It works.")
            name = fh.name
        self.assertEqual(
            wc.body_from_command(f"gh pr create -F {name}"), ("pr", "It works.")
        )
        Path(name).unlink()

    def test_heredoc_is_skipped(self) -> None:
        self.assertIsNone(wc.body_from_command('gh pr create --body "$(cat f)"'))

    def test_unrelated_command_is_skipped(self) -> None:
        self.assertIsNone(wc.body_from_command("gh pr list --state open"))

    def test_missing_file_fails_open(self) -> None:
        with self.assertRaises(OSError):
            wc.body_from_command("gh pr create -F /nonexistent/path.md")


class HookTest(unittest.TestCase):
    def drive(self, payload: dict) -> str:
        stdin, stdout = sys.stdin, sys.stdout
        sys.stdin = io.StringIO(json.dumps(payload))
        sys.stdout = io.StringIO()
        try:
            wc.run_hook()
            return sys.stdout.getvalue()
        finally:
            sys.stdin, sys.stdout = stdin, stdout

    def test_bad_body_denies(self) -> None:
        out = self.drive(
            {
                "tool_name": "Bash",
                "tool_input": {"command": "gh issue create --body 'It is just wrong.'"},
            }
        )
        payload = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        self.assertIn("FILLER", payload["permissionDecisionReason"])

    def test_good_body_is_silent(self) -> None:
        out = self.drive(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "gh issue create --body 'The parser reads it.'"
                },
            }
        )
        self.assertEqual(out, "")

    def test_other_tools_are_ignored(self) -> None:
        self.assertEqual(self.drive({"tool_name": "Read", "tool_input": {}}), "")


class OutputStyleTest(unittest.TestCase):
    """The hook activates the output style. It does not restate it."""

    def test_the_style_file_ships(self) -> None:
        style = ROOT / ".claude" / "output-styles" / ("simplified-technical-english.md")
        self.assertTrue(style.is_file())
        self.assertIn("ASD-STE100", style.read_text("utf-8"))

    def test_injected_text_is_the_style_file(self) -> None:
        text = wc.rules_text()
        self.assertIn("SIMPLIFIED TECHNICAL ENGLISH ACTIVE", text)
        self.assertIn("20 words maximum", text)
        self.assertIn("norms/prose.md", text)

    def test_frontmatter_is_stripped(self) -> None:
        self.assertNotIn("description:", wc.rules_text())

    def test_a_missing_style_file_still_prints_rules(self) -> None:
        original = wc.STYLE
        wc.STYLE = ROOT / "no" / "such" / "file.md"
        try:
            self.assertIn("20 words maximum", wc.rules_text())
        finally:
            wc.STYLE = original


class CorpusTest(unittest.TestCase):
    """Good writing must never block. A rule that trips this is wrong."""

    def test_good_pr_passes(self) -> None:
        self.assertEqual(blocking(GOOD_PR, "pr"), [])

    def test_long_detailed_body_passes(self) -> None:
        body = """\
## What changed

`portolan check` now rejects a `partition:glob` URL that expands to nothing.

## Why

Closes #761. A catalog could pass validation and still fail to read.

## Implementation notes

The check runs in `src/portolan/check/partition.py`. It lists the prefix once
and stops at the first match, so a wide glob costs one request.

Three cases need care:

- A glob with no wildcard is a plain URL. The check skips it.
- A glob over an empty prefix returns nothing. The check reports the prefix.
- A glob the store cannot list raises. The check reports the store error.

## Verification

```console
$ portolan check s3://example-bucket/catalog.json
error: partition:glob has no matching objects under s3://example-bucket/p/
```

## Related issues

Closes #761.
"""
        self.assertEqual(blocking(body, "pr"), [])

    def test_shipped_pr_template_has_no_prose_faults(self) -> None:
        text = (ROOT / "templates" / "PULL_REQUEST_TEMPLATE.md").read_text("utf-8")
        rules = [r for r in blocking(text, "pr") if r != "EMPTY_BODY"]
        self.assertEqual([r for r in rules if r != "HEADING_EMPTY"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
