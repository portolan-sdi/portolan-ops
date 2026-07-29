#!/usr/bin/env python3
"""Generate templates/repo/AGENTS.md from this repo's AGENTS.md.

Downstream repos carry the org norms as text rather than as links, because
Claude Code loads what a file says and never follows a URL to find out. This
wraps the canonical AGENTS.md in ops-sync markers and rewrites its relative
links to absolute ops URLs, which is all that differs between the two.

    python3 scripts/build_agents_block.py            # write the template
    python3 scripts/build_agents_block.py --check    # fail if it is stale

check.yml runs --check, so editing AGENTS.md without regenerating fails there
rather than drifting downstream unnoticed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "AGENTS.md"
TEMPLATE = ROOT / "templates" / "repo" / "AGENTS.md"

BLOB = "https://github.com/portolan-sdi/portolan-ops/blob/main/"

BEGIN = (
    "<!-- ops-sync:begin — synced from portolan-sdi/portolan-ops. "
    "Edit there, not here. -->"
)
END = "<!-- ops-sync:end -->"

FOOTER = """\
# Repo-specific instructions

<!-- Add instructions for this repo below. The block above is overwritten by
     sync. This file is the only home for repo-specific agent rules: CLAUDE.md
     carries the import and nothing else. -->
"""

# A markdown link whose target is neither absolute nor a bare anchor.
RELATIVE_LINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\((?!https?://|#|mailto:)([^)]+)\)")


def absolutize(text: str) -> str:
    """Point every relative link at ops, since the text lands in other repos."""
    return RELATIVE_LINK_RE.sub(rf"[\1]({BLOB}\2)", text)


def render(source_text: str) -> str:
    body = absolutize(source_text).strip()
    return f"{BEGIN}\n{body}\n{END}\n\n{FOOTER}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when the template is out of date; write nothing.",
    )
    args = parser.parse_args(argv)

    rendered = render(SOURCE.read_text(encoding="utf-8"))

    if args.check:
        current = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else ""
        if current != rendered:
            print(
                f"{TEMPLATE.relative_to(ROOT)} is stale.\n"
                "Run: python3 scripts/build_agents_block.py",
                file=sys.stderr,
            )
            return 1
        print(f"{TEMPLATE.relative_to(ROOT)} is current.")
        return 0

    TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATE.write_text(rendered, encoding="utf-8")
    print(f"wrote {TEMPLATE.relative_to(ROOT)} ({len(rendered.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
