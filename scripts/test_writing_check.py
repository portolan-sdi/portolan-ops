#!/usr/bin/env python3
"""Tests for the writing hook.

The test that matters most is CorpusTest. It runs the checker over bodies that
are already good and asserts nothing blocks. A rule that trips it is wrong,
because the hook stops an author from filing. Demote the rule rather than tune
the corpus.

    uv run --no-project --with pyyaml python scripts/test_writing_check.py

PyYAML is the reference the form parser is compared with. The hook itself
runs without it.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

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


FORMS_DIR = ROOT / "templates" / "ISSUE_TEMPLATE"
ORG_FORMS = ("bug_report.yml", "feature_request.yml", "task.yml", "docs_issue.yml")
PUBLIC_FORMS = (
    "portolan-registry/dataset-problem.yml",
    "portolan-registry-qgis/plugin-problem.yml",
)


P0_ANSWER = (
    "P0: Fix now. Data loss, a leaked secret, wrong published data with no "
    "warning, or a broken release."
)
REAL_FORMS_FOR = wc.forms_for


def org_forms() -> list:
    return [wc.parse_form((FORMS_DIR / n).read_text("utf-8"), n) for n in ORG_FORMS]


def shape(form) -> tuple:
    if form is None:
        return ()
    fields = tuple(
        (f.label, f.required, tuple(f.options), f.multiple) for f in form.fields
    )
    return tuple(form.labels), fields


GOOD_BUG = """\
### What happened?

`portolan push` deletes an object that the remote version still uses.

### Why it matters

A reader of the catalog gets a 404 for the data asset.

### Priority

{P0_ANSWER}

### How to reproduce

```console
$ portolan push s3://example-bucket/catalog
```

### Implementation notes

_No response_

### How to confirm the fix

Run the push twice. The second run deletes nothing.

### Version

0.7.0
""".replace("{P0_ANSWER}", P0_ANSWER)


class FormParseTest(unittest.TestCase):
    """The stdlib parser must read every form the way GitHub does."""

    def test_every_shipped_form_matches_pyyaml(self) -> None:
        files = sorted(FORMS_DIR.rglob("*.yml"))
        self.assertGreater(len(files), 5)
        for path in files:
            with self.subTest(form=path.name):
                text = path.read_text("utf-8")
                mine = wc.parse_form(text, path.name)
                ref = wc.form_from_data(yaml.safe_load(text), path.name)
                self.assertEqual(shape(mine), shape(ref))

    def test_config_is_not_a_form(self) -> None:
        self.assertIsNone(wc.parse_form((FORMS_DIR / "config.yml").read_text("utf-8")))

    def test_org_forms_ask_the_same_priority_question(self) -> None:
        asked = []
        for form in org_forms():
            field = next(f for f in form.fields if f.label == wc.PRIORITY_HEADING)
            self.assertTrue(field.required, form.name)
            asked.append(tuple(field.options))
        self.assertEqual(len(set(asked)), 1)
        keys = tuple(wc._option_key(o) for o in asked[0])
        self.assertEqual(keys, wc.PRIORITIES)

    def test_public_forms_leave_priority_to_triage(self) -> None:
        for name in PUBLIC_FORMS:
            form = wc.parse_form((FORMS_DIR / name).read_text("utf-8"), name)
            labels = [f.label for f in form.fields]
            self.assertNotIn(wc.PRIORITY_HEADING, labels, name)

    def test_plain_scalar_continues_on_deeper_lines(self) -> None:
        text = "a: one\n  two\nb: [x, 'y z']\n"
        self.assertEqual(wc._yaml_load(text), {"a": "one two", "b": ["x", "y z"]})


class FormCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.forms = org_forms()
        qgis = FORMS_DIR / PUBLIC_FORMS[1]
        self.forms.append(wc.parse_form(qgis.read_text("utf-8"), qgis.name))

    def problems(self, body: str, labels: list[str]) -> list[str]:
        return wc.form_problems(body, labels, self.forms)

    def test_a_complete_bug_body_passes(self) -> None:
        self.assertEqual(self.problems(GOOD_BUG, ["bug"]), [])

    def test_a_short_priority_answer_passes(self) -> None:
        body = GOOD_BUG.replace(P0_ANSWER, "P0")
        self.assertEqual(self.problems(body, ["bug", "P0"]), [])

    def test_a_missing_priority_fails(self) -> None:
        start = GOOD_BUG.index("### Priority")
        end = GOOD_BUG.index("### How to reproduce")
        body = GOOD_BUG[:start] + GOOD_BUG[end:]
        got = self.problems(body, ["bug"])
        self.assertTrue(any('"### Priority" is missing' in p for p in got), got)

    def test_a_truncated_priority_answer_passes(self) -> None:
        body = GOOD_BUG.replace(P0_ANSWER, "P0: Fix now.")
        self.assertEqual(self.problems(body, ["bug"]), [])

    def test_a_priority_key_needs_a_boundary(self) -> None:
        got = self.problems(GOOD_BUG.replace(P0_ANSWER, "P01"), ["bug"])
        self.assertTrue(any("must be one of" in p for p in got), got)

    def test_an_unknown_priority_fails(self) -> None:
        got = self.problems(GOOD_BUG.replace(P0_ANSWER, "High"), ["bug"])
        self.assertTrue(any("must be one of: P0, P1, P2, P3" in p for p in got), got)

    def test_no_response_counts_as_empty(self) -> None:
        body = GOOD_BUG.replace("0.7.0\n", "_No response_\n")
        got = self.problems(body, ["bug"])
        self.assertTrue(any('"### Version" is empty' in p for p in got), got)

    def test_a_heading_inside_a_fence_does_not_count(self) -> None:
        body = GOOD_BUG.replace(
            "### Version\n\n0.7.0\n", "```\n### Version\n0.7.0\n```\n"
        )
        got = self.problems(body, ["bug"])
        self.assertTrue(any('"### Version" is missing' in p for p in got), got)

    def test_heading_level_and_question_mark_do_not_matter(self) -> None:
        body = GOOD_BUG.replace("### What happened?", "## What happened")
        self.assertEqual(self.problems(body, ["bug"]), [])

    def test_any_form_with_the_label_can_satisfy_it(self) -> None:
        """The QGIS plugin form also sets `bug` and asks no priority."""
        qgis = self.forms[-1]
        body = "".join(f"### {f.label}\n\nThe plugin stops.\n\n" for f in qgis.fields)
        self.assertEqual(self.problems(body, ["bug"]), [])

    def test_no_type_label_names_the_choices(self) -> None:
        got = self.problems(GOOD_BUG, [])
        self.assertEqual(len(got), 1)
        self.assertIn("bug, documentation, enhancement, task", got[0])

    def test_problems_name_the_closest_form(self) -> None:
        got = self.problems("### What happened?\n\nIt fails.\n", ["bug"])
        self.assertTrue(got)
        self.assertTrue(
            all(p.startswith(("bug_report.yml", "plugin-problem.yml")) for p in got)
        )

    def test_priority_from_body(self) -> None:
        self.assertEqual(wc.priority_from_body(GOOD_BUG), "P0")
        self.assertIsNone(wc.priority_from_body("### Priority\n\nsoon\n"))
        self.assertIsNone(wc.priority_from_body("It fails.\n"))


class LocalFormsTest(unittest.TestCase):
    def test_reads_the_repo_forms_from_a_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            forms = root / ".github" / "ISSUE_TEMPLATE"
            forms.mkdir(parents=True)
            (forms / "bug_report.yml").write_text(
                (FORMS_DIR / "bug_report.yml").read_text("utf-8")
            )
            (forms / "config.yml").write_text("blank_issues_enabled: false\n")
            nested = root / "src" / "pkg"
            nested.mkdir(parents=True)
            got = wc.local_forms(nested)
            self.assertEqual([f.name for f in got], ["bug_report.yml"])

    def test_stops_at_the_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / ".git").mkdir()
            self.assertEqual(wc.local_forms(Path(directory)), [])


class HookTest(unittest.TestCase):
    def setUp(self) -> None:
        forms = org_forms()
        original = wc.forms_for
        wc.forms_for = lambda flags: forms
        self.addCleanup(setattr, wc, "forms_for", original)

    def drive(self, payload: dict) -> str:
        stdin, stdout = sys.stdin, sys.stdout
        sys.stdin = io.StringIO(json.dumps(payload))
        sys.stdout = io.StringIO()
        try:
            wc.run_hook()
            return sys.stdout.getvalue()
        finally:
            sys.stdin, sys.stdout = stdin, stdout

    def command(self, command: str) -> str:
        return self.drive({"tool_name": "Bash", "tool_input": {"command": command}})

    def denial(self, command: str) -> str:
        out = self.command(command)
        self.assertTrue(out, f"not denied: {command}")
        payload = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(payload["permissionDecision"], "deny")
        return payload["permissionDecisionReason"]

    def body_file(self, body: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(body)
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_bad_body_denies(self) -> None:
        reason = self.denial("gh issue create --label bug --body 'It is just wrong.'")
        self.assertIn("FILLER", reason)

    def test_good_form_body_is_silent(self) -> None:
        path = self.body_file(GOOD_BUG)
        self.assertEqual(self.command(f"gh issue create -t x -l bug -F {path}"), "")

    def test_a_body_without_its_form_denies_and_lists_headings(self) -> None:
        path = self.body_file("The parser reads the URL late.\n")
        reason = self.denial(
            f"gh issue create --title x --label bug --body-file {path}"
        )
        self.assertIn('"### What happened?" is missing', reason)
        self.assertIn("### Priority", reason)

    def test_a_missing_type_label_denies(self) -> None:
        path = self.body_file(GOOD_BUG)
        reason = self.denial(f"gh issue create --title x --body-file {path}")
        self.assertIn("--label", reason)

    def test_comma_separated_labels_count(self) -> None:
        path = self.body_file(GOOD_BUG)
        self.assertEqual(
            self.command(f"gh issue create -t x --label=P0,bug -F {path}"), ""
        )

    def test_a_heredoc_body_denies(self) -> None:
        reason = self.denial(
            'gh issue create --label bug --body "$(cat <<EOF\nx\nEOF\n)"'
        )
        self.assertIn("--body-file", reason)

    def test_a_pr_heredoc_body_denies(self) -> None:
        self.assertIn("--body-file", self.denial('gh pr create --body "$(cat f)"'))

    def test_a_missing_body_file_denies(self) -> None:
        reason = self.denial("gh issue create --label bug -F /nonexistent/path.md")
        self.assertIn("cannot read", reason)

    def test_web_creation_is_left_to_the_form(self) -> None:
        self.assertEqual(self.command("gh issue create --web"), "")

    def test_an_edit_without_a_body_is_silent(self) -> None:
        self.assertEqual(self.command("gh issue edit 5 --add-label P1"), "")

    def test_api_issue_creation_denies(self) -> None:
        for command in (
            "gh api repos/o/r/issues -f title=x -f body=y",
            "gh api -X POST repos/o/r/issues --input body.json",
            "gh api graphql -f query='mutation { createIssue(input: {}) { issue { id } } }'",
        ):
            with self.subTest(command=command):
                self.assertIn("gh api", self.denial(command))

    def test_api_reads_and_comments_are_silent(self) -> None:
        for command in (
            "gh api repos/o/r/issues",
            "gh api repos/o/r/issues -X GET -f state=open",
            "gh api repos/o/r/issues/5/comments -f body=ok",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.command(command), "")

    def test_unreadable_forms_deny(self) -> None:
        wc.forms_for = lambda flags: []
        path = self.body_file(GOOD_BUG)
        self.assertIn("issue forms", self.denial(f"gh issue create -l bug -F {path}"))

    def test_the_repo_flag_selects_remote_forms(self) -> None:
        self.addCleanup(setattr, wc, "remote_forms", wc.remote_forms)
        seen: list[str] = []
        wc.remote_forms = lambda repo: seen.append(repo) or []
        REAL_FORMS_FOR(["--label", "bug", "-R", "o/r"])
        self.assertEqual(seen, ["o/r"])

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
