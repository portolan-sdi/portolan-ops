#!/usr/bin/env python3
"""Tests for the tool-version bumper.

The regexes here are the whole risk: a pin that stops matching makes the
bumper go quiet, and a stale version is then invisible. `--check` guards
that against the real workflows in CI; these cover the rewrite itself.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bump_tools import TOOLS, current_versions, rewrite

PREK, PYYAML, WILY = TOOLS

REUSABLE = """\
env:
  PREK_VERSION: ${{ vars.PREK_VERSION || '0.4.11' }}

jobs:
  lint:
    steps:
      - run: uvx prek@"$PREK_VERSION" run --all-files
      - run: |
          uvx wily@1.25.0 build --max-revisions 30 src
          uvx wily@1.25.0 diff src --no-detail
"""

SYNC = """\
env:
  PYYAML_VERSION: ${{ vars.PYYAML_VERSION || '6.0.2' }}

jobs:
  sync:
    steps:
      - run: uv run --with "pyyaml==$PYYAML_VERSION" python x.py
"""


class BumpToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        workflows = self.root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "reusable.yml").write_text(REUSABLE)
        (workflows / "sync.yml").write_text(SYNC)

    def read(self, name: str) -> str:
        return (self.root / ".github" / "workflows" / name).read_text()

    def test_finds_the_fallback_literal(self) -> None:
        found = current_versions(PREK, self.root)
        self.assertEqual(
            {path.name: versions for path, versions in found.items()},
            {"reusable.yml": {"0.4.11"}},
        )

    def test_finds_repeated_pins_in_one_file(self) -> None:
        found = current_versions(WILY, self.root)
        self.assertEqual(list(found.values()), [{"1.25.0"}])

    def test_rewrite_replaces_every_occurrence(self) -> None:
        changed = rewrite(WILY, self.root, "1.26.0")
        self.assertEqual([path.name for path in changed], ["reusable.yml"])
        self.assertNotIn("wily@1.25.0", self.read("reusable.yml"))
        self.assertEqual(self.read("reusable.yml").count("wily@1.26.0"), 2)

    def test_rewrite_leaves_the_shell_variable_alone(self) -> None:
        # `uvx prek@"$PREK_VERSION"` reads the env var; only the literal
        # inside the `vars` fallback may move.
        rewrite(PREK, self.root, "0.5.0")
        body = self.read("reusable.yml")
        self.assertIn("vars.PREK_VERSION || '0.5.0'", body)
        self.assertIn('uvx prek@"$PREK_VERSION"', body)

    def test_rewrite_is_idempotent(self) -> None:
        rewrite(PYYAML, self.root, "6.0.3")
        self.assertEqual(rewrite(PYYAML, self.root, "6.0.3"), [])

    def test_rewrite_skips_files_without_the_pin(self) -> None:
        changed = rewrite(PYYAML, self.root, "6.0.3")
        self.assertEqual([path.name for path in changed], ["sync.yml"])
        self.assertIn("PREK_VERSION || '0.4.11'", self.read("reusable.yml"))

    def test_unmatched_tool_reports_nothing(self) -> None:
        empty = Path(self.tmp.name) / "empty"
        (empty / ".github" / "workflows").mkdir(parents=True)
        self.assertEqual(current_versions(PREK, empty), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
