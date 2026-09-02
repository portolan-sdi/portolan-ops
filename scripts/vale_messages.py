#!/usr/bin/env python3
"""Lint website copy that lives in a next-intl message catalogue.

Vale reads Markdown, not JSON, so `extract` writes every leaf string of
`messages/en.json` to `.vale-web/messages.md`, one per line, next to a
sidecar map from output line to JSON key path. `remap` reads Vale's JSON
output and rewrites each location back to the key a person can find.

    python scripts/vale_messages.py extract messages/en.json
    vale --output=JSON .vale-web/messages.md \
      | python scripts/vale_messages.py remap

Rich-text tags such as <cli>...</cli> and <m>...</m> are markup, not prose,
so `extract` strips them. ICU placeholders such as {count} stay, because
they read as part of the sentence.

Standard library only, so it runs wherever the CI workflow runs.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

OUT_DIR = pathlib.Path(".vale-web")
OUT_FILE = OUT_DIR / "messages.md"
MAP_FILE = OUT_DIR / "messages.map.json"

TAG = re.compile(r"</?[a-zA-Z][\w]*/?>")


def leaves(node: object, path: str = "") -> list[tuple[str, str]]:
    """Return every (key path, string) pair under `node`, depth first."""
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            out.extend(leaves(value, f"{path}.{key}" if path else key))
    elif isinstance(node, str):
        out.append((path, node))
    return out


def extract(source: pathlib.Path) -> int:
    data = json.loads(source.read_text(encoding="utf-8"))
    pairs = leaves(data)

    lines: list[str] = []
    mapping: dict[str, str] = {}
    for key, raw in pairs:
        text = TAG.sub("", raw).strip()
        if not text:
            continue
        # One string per line keeps the line number a stable address. A
        # blank line between them stops Vale joining two strings into one
        # sentence or one paragraph.
        lines.append(text)
        mapping[str(len(lines))] = key
        lines.append("")
        mapping[str(len(lines))] = key

    OUT_DIR.mkdir(exist_ok=True)
    OUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    MAP_FILE.write_text(
        json.dumps({"source": str(source), "lines": mapping}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{OUT_FILE}: {len(mapping) // 2} strings from {source}")
    return 0


def remap(stream: object) -> int:
    """Rewrite Vale JSON locations from the extract file back to key paths."""
    if not MAP_FILE.exists():
        print(f"{MAP_FILE} is missing. Run extract first.", file=sys.stderr)
        return 2

    side = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    source, lines = side["source"], side["lines"]

    raw = stream.read()
    if not raw.strip():
        return 0
    report = json.loads(raw)

    count = 0
    for alerts in report.values():
        for alert in alerts:
            key = lines.get(str(alert["Line"]), "?")
            print(f"{source} → {key}:{alert['Check']}:{alert['Message']}")
            count += 1
    return 1 if count else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    ex = sub.add_parser("extract", help="write .vale-web/messages.md")
    ex.add_argument("source", type=pathlib.Path, help="path to messages/en.json")

    sub.add_parser("remap", help="rewrite Vale JSON locations, read from stdin")

    args = parser.parse_args(argv)
    if args.command == "extract":
        return extract(args.source)
    return remap(sys.stdin)


if __name__ == "__main__":
    sys.exit(main())
