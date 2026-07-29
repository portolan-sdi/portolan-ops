#!/usr/bin/env python3
"""Tests for the hook set in templates/repo/.pre-commit-config.yaml.

That file is the fleet's code standard. Nothing else in CI runs it: the
lint job runs each repo's own config, so a hook that is missing here, or
one whose id drifted, would reach every repo before anyone noticed.

The import-linter guard gets a real run rather than a string comparison.
`lint-imports` exits non-zero when a repo declares no contracts, so the
guard is what keeps the hook shippable fleet-wide, and a guard that
inverts is worse than no guard: it would skip the check in exactly the
repos that wrote contracts.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "repo" / ".pre-commit-config.yaml"
OPS_CONFIG = ROOT / ".pre-commit-config.yaml"
FIXTURE = ROOT / "tests" / "fixture-package" / ".pre-commit-config.yaml"

CONTRACT_BLOCK = """\
[project]
name = "demo"

[tool.importlinter]
root_package = "demo"
"""

NO_CONTRACT = """\
[project]
name = "demo"
"""


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def hooks_by_id(config: dict) -> dict[str, dict]:
    return {
        hook["id"]: hook for repo in config["repos"] for hook in repo.get("hooks", [])
    }


def repo_rev(config: dict, url_fragment: str) -> str | None:
    for repo in config["repos"]:
        if url_fragment in repo.get("repo", ""):
            return repo.get("rev")
    return None


class TemplateHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load(TEMPLATE)
        self.hooks = hooks_by_id(self.config)

    def test_commitizen_runs_at_commit_msg(self) -> None:
        # Any other stage never sees the message, so the hook would pass
        # on every commit and enforce nothing.
        self.assertEqual(self.hooks["commitizen"]["stages"], ["commit-msg"])

    def test_dependency_and_contract_hooks_run_pre_push(self) -> None:
        for hook_id in ("deptry", "import-linter"):
            self.assertEqual(self.hooks[hook_id]["stages"], ["pre-push"], hook_id)

    def test_ruff_uses_the_current_hook_id(self) -> None:
        # The bare `ruff` id is the deprecated alias.
        self.assertIn("ruff-check", self.hooks)
        self.assertNotIn("ruff", self.hooks)

    def test_whole_project_hooks_do_not_take_filenames(self) -> None:
        # deptry and lint-imports read the project, not a file list. Left
        # on, prek would pass changed paths and the tools would scan the
        # wrong thing.
        for hook_id in ("deptry", "import-linter"):
            self.assertIs(self.hooks[hook_id]["pass_filenames"], False, hook_id)

    def test_ops_pins_commitizen_to_the_version_it_ships(self) -> None:
        # This repo drifting from the template it hands out is the same
        # bug as a repo drifting from the template.
        self.assertEqual(
            repo_rev(self.config, "commitizen-tools/commitizen"),
            repo_rev(load(OPS_CONFIG), "commitizen-tools/commitizen"),
        )


class FixtureMirrorTest(unittest.TestCase):
    """The self-test only proves the template if it runs the same hooks.

    Entries and paths differ on purpose (the fixture narrows mypy and
    xenon to its own layout), so this compares the hook set rather than
    the file.
    """

    def setUp(self) -> None:
        self.template = hooks_by_id(load(TEMPLATE))
        self.fixture = hooks_by_id(load(FIXTURE))

    def test_the_fixture_runs_every_hook_the_template_ships(self) -> None:
        missing = sorted(set(self.template) - set(self.fixture))
        self.assertEqual(missing, [], "fixture is missing template hooks")

    def test_hooks_run_at_the_same_stage_in_both(self) -> None:
        for hook_id, hook in self.template.items():
            self.assertEqual(
                self.fixture[hook_id].get("stages"),
                hook.get("stages"),
                hook_id,
            )


class ImportLinterGuardTest(unittest.TestCase):
    """Run the shipped entry with a stub `uv` and see whether it fires."""

    def setUp(self) -> None:
        self.entry = hooks_by_id(load(TEMPLATE))["import-linter"]["entry"]

    def run_guard(self, pyproject: str) -> tuple[int, bool]:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "pyproject.toml").write_text(pyproject, encoding="utf-8")
            marker = work / "ran"
            stub_dir = work / "bin"
            stub_dir.mkdir()
            stub = stub_dir / "uv"
            stub.write_text(f'#!/bin/sh\ntouch "{marker}"\n', encoding="utf-8")
            stub.chmod(0o755)
            env = dict(os.environ, PATH=f"{stub_dir}{os.pathsep}{os.environ['PATH']}")
            result = subprocess.run(
                shlex.split(self.entry), cwd=work, env=env, check=False
            )
            return result.returncode, marker.exists()

    def test_a_repo_without_contracts_passes_and_skips(self) -> None:
        code, ran = self.run_guard(NO_CONTRACT)
        self.assertEqual(code, 0)
        self.assertFalse(ran, "lint-imports ran without any contracts")

    def test_a_repo_with_contracts_runs_the_linter(self) -> None:
        code, ran = self.run_guard(CONTRACT_BLOCK)
        self.assertEqual(code, 0)
        self.assertTrue(ran, "contracts declared but lint-imports never ran")


if __name__ == "__main__":
    unittest.main(verbosity=2)
