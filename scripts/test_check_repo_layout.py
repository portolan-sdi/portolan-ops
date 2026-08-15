#!/usr/bin/env python3
"""Unit tests for check_repo_layout.py.

Run directly (check.yml does):

    python3 scripts/test_check_repo_layout.py

Each rule is covered in both directions, and the shipped templates are checked
against the rules they exist to satisfy.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_repo_layout as crl

ROOT = Path(__file__).resolve().parent.parent
AGENTS_TEMPLATE = ROOT / "templates" / "repo" / "AGENTS.md"
CLAUDE_TEMPLATE = ROOT / "templates" / "repo" / "CLAUDE.md"

BEGIN = "<!-- ops-sync:begin — synced from portolan-sdi/portolan-ops. -->"
END = "<!-- ops-sync:end -->"

GOOD_AGENTS = f"{BEGIN}\n# Norms\n\nBe brief.\n{END}\n"
GOOD_CLAUDE = f"{BEGIN}\n@AGENTS.md\n{END}\n"


GOOD_SETTINGS = json.dumps(
    {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {"type": "command", "command": "python3 writing_check.py"}
                    ],
                }
            ]
        }
    }
)


def repo_with(agents=GOOD_AGENTS, claude=GOOD_CLAUDE, settings=GOOD_SETTINGS, hook="x"):
    """Build a temp repo; None means the file is absent."""
    tmp = tempfile.mkdtemp(prefix="layout-")
    path = Path(tmp)
    if agents is not None:
        (path / "AGENTS.md").write_text(agents, encoding="utf-8")
    if claude is not None:
        (path / "CLAUDE.md").write_text(claude, encoding="utf-8")
    (path / ".claude" / "hooks").mkdir(parents=True)
    if settings is not None:
        (path / ".claude" / "settings.json").write_text(settings, encoding="utf-8")
    if hook is not None:
        (path / ".claude" / "hooks" / "writing_check.py").write_text(
            hook, encoding="utf-8"
        )
    return path


def joined(**kw):
    return " ".join(crl.check(repo_with(**kw)))


class PassingTest(unittest.TestCase):
    def test_correct_repo_passes(self):
        self.assertEqual([], crl.check(repo_with()))

    def test_repo_specific_content_below_agents_block_is_fine(self):
        agents = GOOD_AGENTS + "\n# Repo-specific\n\nUse plan mode here.\n"
        self.assertEqual([], crl.check(repo_with(agents=agents)))

    def test_comments_outside_the_claude_block_are_fine(self):
        claude = GOOD_CLAUDE + "\n<!-- a note for humans -->\n"
        self.assertEqual([], crl.check(repo_with(claude=claude)))


class WritingHookTest(unittest.TestCase):
    def test_missing_script_reported(self):
        self.assertIn("writing_check.py is missing", joined(hook=None))

    def test_missing_settings_reported(self):
        self.assertIn("settings.json is missing", joined(settings=None))

    def test_unwired_hook_reported(self):
        settings = json.dumps({"permissions": {"allow": []}})
        self.assertIn("wires no writing_check.py hook", joined(settings=settings))

    def test_broken_json_reported(self):
        self.assertIn("not readable JSON", joined(settings="{nope"))

    def test_repo_hooks_alongside_ours_pass(self):
        settings = json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Read",
                            "hooks": [{"type": "command", "command": "./own.sh"}],
                        }
                    ],
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python3 writing_check.py",
                                }
                            ],
                        }
                    ],
                }
            }
        )
        self.assertEqual([], crl.check(repo_with(settings=settings)))


class AgentsTest(unittest.TestCase):
    def test_missing_file_reported(self):
        self.assertIn("AGENTS.md is missing", joined(agents=None))

    def test_no_block_reported(self):
        self.assertIn("no ops-sync block", joined(agents="# Norms\n\nBe brief.\n"))

    def test_half_a_block_reported(self):
        self.assertIn("no ops-sync block", joined(agents=f"{BEGIN}\n# Norms\n"))

    def test_reversed_markers_reported(self):
        self.assertIn("wrong order", joined(agents=f"{END}\n# Norms\n{BEGIN}\n"))

    def test_empty_block_reported(self):
        self.assertIn("block is empty", joined(agents=f"{BEGIN}\n\n{END}\n"))

    def test_duplicate_blocks_reported(self):
        """The marker-deleted-then-resynced shape: sync prepends a fresh
        block and the stale copy sits below it."""
        agents = GOOD_AGENTS + GOOD_AGENTS
        self.assertIn("more than one ops-sync block", joined(agents=agents))


class ClaudeTest(unittest.TestCase):
    def test_missing_file_reported(self):
        found = joined(claude=None)
        self.assertIn("CLAUDE.md is missing", found)
        self.assertIn("never reads AGENTS.md", found)

    def test_no_block_reported(self):
        self.assertIn("no ops-sync block", joined(claude="@AGENTS.md\n"))

    def test_block_without_the_import_reported(self):
        claude = f"{BEGIN}\nSee AGENTS.md for the rules.\n{END}\n"
        self.assertIn("does not import AGENTS.md", joined(claude=claude))

    def test_content_outside_the_block_reported(self):
        claude = GOOD_CLAUDE + "\n## Project overview\n\nThis repo does things.\n"
        found = joined(claude=claude)
        self.assertIn("outside the ops-sync block", found)
        self.assertIn("Move it into AGENTS.md", found)

    def test_line_count_is_reported(self):
        claude = GOOD_CLAUDE + "\nline one\nline two\n\nline three\n"
        self.assertIn("carries 3 lines", joined(claude=claude))

    def test_duplicate_blocks_reported(self):
        claude = GOOD_CLAUDE + GOOD_CLAUDE
        self.assertIn("more than one ops-sync block", joined(claude=claude))

    def test_instructions_only_in_claude_is_the_headline_failure(self):
        """The portolan-cli shape: real content, no bridge."""
        found = joined(agents=None, claude="# Project\n\nUse STAC terms.\n")
        self.assertIn("AGENTS.md is missing", found)
        self.assertIn("no ops-sync block", found)


class ShippedTemplateTest(unittest.TestCase):
    def test_templates_satisfy_the_check(self):
        repo = repo_with(
            agents=AGENTS_TEMPLATE.read_text(encoding="utf-8"),
            claude=CLAUDE_TEMPLATE.read_text(encoding="utf-8"),
        )
        self.assertEqual([], crl.check(repo))

    def test_ops_itself_satisfies_the_check(self):
        self.assertEqual([], crl.check(ROOT, is_source=True))

    def test_ops_without_the_source_flag_is_flagged(self):
        """The source repo's AGENTS.md has no markers, and that is only ok
        because it writes them."""
        self.assertIn("no ops-sync block", " ".join(crl.check(ROOT)))


class CliTest(unittest.TestCase):
    def test_exit_codes(self):
        self.assertEqual(0, crl.main([str(repo_with())]))
        self.assertEqual(1, crl.main([str(repo_with(claude=None))]))
        self.assertEqual(2, crl.main([str(repo_with() / "nope")]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
