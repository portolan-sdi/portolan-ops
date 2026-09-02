#!/usr/bin/env python3
"""Fail when the current Vale report adds error-level findings."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
from typing import Any

Fingerprint = tuple[str, str, str, str]


def read_report(path: pathlib.Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        raise ValueError(f"{path} does not exist")
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise ValueError(f"{path} is empty")
    report = json.loads(raw)
    if not isinstance(report, dict):
        raise ValueError(f"{path} does not contain a Vale report")
    return report


def fingerprints(
    report: dict[str, list[dict[str, Any]]],
) -> collections.Counter[Fingerprint]:
    found: collections.Counter[Fingerprint] = collections.Counter()
    for path, alerts in report.items():
        normalized = pathlib.PurePosixPath(path.replace("\\", "/")).as_posix()
        for alert in alerts:
            item = (
                normalized.removeprefix("./"),
                str(alert.get("Check", "")),
                str(alert.get("Match", "")),
                str(alert.get("Message", "")),
            )
            found[item] += 1
    return found


def new_findings(
    base: dict[str, list[dict[str, Any]]],
    current: dict[str, list[dict[str, Any]]],
) -> collections.Counter[Fingerprint]:
    return fingerprints(current) - fingerprints(base)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=pathlib.Path)
    parser.add_argument("current", type=pathlib.Path)
    args = parser.parse_args(argv)

    try:
        added = new_findings(read_report(args.base), read_report(args.current))
    except (OSError, ValueError, json.JSONDecodeError) as err:
        print(f"Cannot compare Vale reports: {err}", file=sys.stderr)
        return 2
    if not added:
        print("No new Vale errors.")
        return 0

    print("This change adds Vale errors:", file=sys.stderr)
    for (path, check, match, message), count in sorted(added.items()):
        suffix = f" ({count} occurrences)" if count > 1 else ""
        print(
            f"  {path}: {check}: {message} [matched: {match!r}]{suffix}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
