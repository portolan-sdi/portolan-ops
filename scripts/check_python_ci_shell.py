#!/usr/bin/env python3
"""Hold reusable-python-ci.yml to bash on every OS.

A job with no shell set runs its `run:` steps in pwsh on a Windows
runner. pwsh reads "$TEST_COMMAND" as its own variable, which is not
set, so the test step ran `bash -c ""` and passed with no test run
(portolan-ops#132). Every job must set `shell: bash` under
`defaults.run`.

    python3 scripts/check_python_ci_shell.py           # check the shell
    python3 scripts/check_python_ci_shell.py test-step  # print the test step
    python3 scripts/check_python_ci_shell.py test-command

The two print modes let ci-selftest.yml run the real test step on a
Windows runner, with the real default command, rather than a copy.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "reusable-python-ci.yml"
TEST_JOB = "test"
TEST_STEP = "Run tests"


def load(text: str) -> dict[str, Any]:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise TypeError("workflow is not a mapping")
    return data


def jobs_without_bash(data: dict[str, Any]) -> list[str]:
    """Jobs whose `run:` steps would not all run in bash. Empty when clean.

    A job that calls another workflow has no steps of its own, so it is
    skipped. A step that sets its own shell still counts against its job:
    the default is what keeps the next step correct.
    """
    found: list[str] = []
    for name, job in (data.get("jobs") or {}).items():
        if not isinstance(job, dict) or "uses" in job:
            continue
        shell = ((job.get("defaults") or {}).get("run") or {}).get("shell")
        if shell != "bash":
            found.append(name)
    return found


def test_step(data: dict[str, Any]) -> str:
    """The `run:` body of the test job's test step."""
    for step in data["jobs"][TEST_JOB]["steps"]:
        if step.get("name") == TEST_STEP:
            return str(step["run"])
    raise KeyError(f"no step named {TEST_STEP!r} in job {TEST_JOB!r}")


def default_test_command(data: dict[str, Any]) -> str:
    """The default of the test-command input that callers inherit.

    PyYAML reads the bare `on:` key as the boolean True (YAML 1.1).
    """
    triggers = data.get("on", data.get(True))
    return str(triggers["workflow_call"]["inputs"]["test-command"]["default"])


def main(argv: list[str]) -> int:
    # Windows writes CRLF to a redirected stdout. The test step lands
    # in a file that bash runs, and bash reads a CR as part of a word.
    sys.stdout.reconfigure(newline="\n")  # type: ignore[union-attr]
    data = load(WORKFLOW.read_text(encoding="utf-8"))
    mode = argv[0] if argv else "check"
    if mode == "test-step":
        print(test_step(data))
        return 0
    if mode == "test-command":
        print(default_test_command(data))
        return 0
    if mode != "check":
        print(f"unknown mode {mode!r}", file=sys.stderr)
        return 2

    rel = WORKFLOW.relative_to(ROOT)
    missing = jobs_without_bash(data)
    for name in missing:
        print(
            f"{rel}: job {name!r} sets no `shell: bash` under defaults.run. "
            f"On Windows its steps run in pwsh, and env references "
            f"such as $TEST_COMMAND expand to nothing.",
            file=sys.stderr,
        )
    if missing:
        return 1
    print(f"{rel}: every job runs its steps in bash")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
