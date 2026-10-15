#!/usr/bin/env python3
"""Unit tests for check_python_ci_shell.py.

Run directly (check.yml does):

    uv run --no-project --with pyyaml==6.0.3 python \
        scripts/test_check_python_ci_shell.py
"""

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_python_ci_shell as guard

CLEAN = """
on:
  workflow_call:
    inputs:
      test-command:
        type: string
        default: >-
          uv run pytest
          --cov=$COVERAGE_TARGET
jobs:
  lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        shell: bash
        working-directory: .
    steps:
      - run: echo ok
  test:
    runs-on: ${{ matrix.os }}-latest
    defaults:
      run:
        shell: bash
    steps:
      - name: Run tests
        run: bash -c "$TEST_COMMAND"
  called:
    uses: ./.github/workflows/other.yml
"""

NO_DEFAULTS = """
jobs:
  test:
    runs-on: windows-latest
    steps:
      - run: echo "$TEST_COMMAND"
"""

PWSH = """
jobs:
  test:
    runs-on: windows-latest
    defaults:
      run:
        shell: pwsh
    steps:
      - run: echo ok
"""

DIR_ONLY = """
jobs:
  test:
    runs-on: windows-latest
    defaults:
      run:
        working-directory: src
    steps:
      - shell: bash
        run: echo ok
"""


class JobsWithoutBashTest(unittest.TestCase):
    def test_clean_workflow_passes(self) -> None:
        self.assertEqual(guard.jobs_without_bash(guard.load(CLEAN)), [])

    def test_job_with_no_defaults_fails(self) -> None:
        self.assertEqual(guard.jobs_without_bash(guard.load(NO_DEFAULTS)), ["test"])

    def test_job_with_another_shell_fails(self) -> None:
        self.assertEqual(guard.jobs_without_bash(guard.load(PWSH)), ["test"])

    def test_step_shell_does_not_excuse_the_job(self) -> None:
        # The next step added to the job would run in pwsh again.
        self.assertEqual(guard.jobs_without_bash(guard.load(DIR_ONLY)), ["test"])


class ExtractTest(unittest.TestCase):
    def test_reads_the_test_step(self) -> None:
        self.assertEqual(guard.test_step(guard.load(CLEAN)), 'bash -c "$TEST_COMMAND"')

    def test_missing_test_step_raises(self) -> None:
        with self.assertRaises(KeyError):
            guard.test_step(guard.load(NO_DEFAULTS))

    def test_reads_the_folded_default_command(self) -> None:
        self.assertEqual(
            guard.default_test_command(guard.load(CLEAN)),
            "uv run pytest --cov=$COVERAGE_TARGET",
        )


class RealWorkflowTest(unittest.TestCase):
    """The shipped workflow, which every Python repo in the fleet runs."""

    def setUp(self) -> None:
        self.data = guard.load(guard.WORKFLOW.read_text(encoding="utf-8"))

    def test_every_job_runs_in_bash(self) -> None:
        self.assertEqual(guard.jobs_without_bash(self.data), [])

    def test_default_command_measures_coverage(self) -> None:
        self.assertIn("--cov=$COVERAGE_TARGET", guard.default_test_command(self.data))

    def _run_step(self, command: str) -> subprocess.CompletedProcess[str]:
        # The flags GitHub passes for `shell: bash`.
        return subprocess.run(
            [
                "bash",
                "--noprofile",
                "--norc",
                "-eo",
                "pipefail",
                "-c",
                guard.test_step(self.data),
            ],
            env={
                "PATH": "/usr/bin:/bin",
                "TEST_COMMAND": command,
                "COVERAGE_TARGET": "src/pkg",
            },
            capture_output=True,
            text=True,
            check=False,
        )

    def test_empty_command_fails_the_step(self) -> None:
        result = self._run_step("")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("test-command is empty", result.stderr)

    def test_command_runs_with_the_coverage_target(self) -> None:
        result = self._run_step('echo "ran $COVERAGE_TARGET"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ran src/pkg")

    def test_command_failure_fails_the_step(self) -> None:
        self.assertEqual(self._run_step("exit 3").returncode, 3)


if __name__ == "__main__":
    unittest.main()
