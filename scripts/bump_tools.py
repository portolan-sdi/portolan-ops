#!/usr/bin/env python3
"""Bump pinned tool versions in this repo's workflows to the latest release.

Three tools are pinned by literal version string across .github/workflows:
prek, pyyaml, and wily. Nothing bumps them on its own — Dependabot reads
`uses:` refs, not `env:` values or `uvx tool@version` arguments — so the
pins rot until someone notices. `bump-tools.yml` runs this weekly and
opens a PR with whatever moved.

Run with --check to report drift without writing (used by check.yml to
prove the patterns still match what the workflows contain).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

WORKFLOWS = Path(".github/workflows")
PYPI = "https://pypi.org/pypi/{name}/json"


@dataclass(frozen=True)
class Tool:
    """A pinned tool and the regex that finds its version in a workflow.

    The pattern must capture the version as group "version"; everything
    around it is preserved verbatim on rewrite.
    """

    name: str
    pypi: str
    pattern: str

    def regex(self) -> re.Pattern[str]:
        return re.compile(self.pattern)


TOOLS = (
    # env: PREK_VERSION: ${{ vars.PREK_VERSION || '0.4.11' }}
    Tool(
        name="prek",
        pypi="prek",
        pattern=r"vars\.PREK_VERSION \|\| '(?P<version>[^']+)'",
    ),
    # env: PYYAML_VERSION: ${{ vars.PYYAML_VERSION || '6.0.2' }}
    Tool(
        name="pyyaml",
        pypi="PyYAML",
        pattern=r"vars\.PYYAML_VERSION \|\| '(?P<version>[^']+)'",
    ),
    # run: uvx wily@1.25.0 build ...
    Tool(
        name="wily",
        pypi="wily",
        pattern=r"uvx wily@(?P<version>[0-9][^\s]*)",
    ),
)


def latest_version(pypi_name: str) -> str:
    """Return the newest non-yanked release of a package on PyPI."""
    url = PYPI.format(name=pypi_name)
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    return str(payload["info"]["version"])


def current_versions(tool: Tool, root: Path) -> dict[Path, set[str]]:
    """Map each workflow file to the versions of `tool` pinned in it."""
    found: dict[Path, set[str]] = {}
    for path in sorted((root / WORKFLOWS).glob("*.yml")):
        matches = tool.regex().finditer(path.read_text())
        versions = {match.group("version") for match in matches}
        if versions:
            found[path] = versions
    return found


def rewrite(tool: Tool, root: Path, target: str) -> list[Path]:
    """Point every pin of `tool` at `target`. Returns the files changed."""
    changed = []
    for path, versions in current_versions(tool, root).items():
        if versions == {target}:
            continue
        original = path.read_text()
        updated = tool.regex().sub(
            lambda match: match.group(0).replace(match.group("version"), target),
            original,
        )
        if updated != original:
            path.write_text(updated)
            changed.append(path)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report drift without writing. Fails if a pin is unmatched.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root. Defaults to the working directory.",
    )
    args = parser.parse_args()

    unmatched = [tool.name for tool in TOOLS if not current_versions(tool, args.root)]
    if unmatched:
        # A pin that no longer matches is worse than a stale pin: the
        # bumper goes quiet and the version rots unnoticed.
        print(
            "no workflow pins matched for: " + ", ".join(unmatched),
            file=sys.stderr,
        )
        return 1

    if args.check:
        for tool in TOOLS:
            for path, versions in current_versions(tool, args.root).items():
                pinned = ", ".join(sorted(versions))
                print(f"{tool.name} {pinned} in {path}")
        return 0

    summary = []
    for tool in TOOLS:
        pinned = {
            version
            for versions in current_versions(tool, args.root).values()
            for version in versions
        }
        target = latest_version(tool.pypi)
        changed = rewrite(tool, args.root, target)
        if changed:
            was = ", ".join(sorted(pinned))
            files = ", ".join(str(path) for path in changed)
            summary.append(f"- `{tool.name}` {was} -> {target} ({files})")

    if not summary:
        print("All tool pins current.")
        return 0

    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
