#!/usr/bin/env python3
"""Check that a pull request or issue body is structured and carries evidence.

Reads the body on stdin. Exits non-zero when a required section is missing or
empty, when a behavior change claims verification with nothing pasted, or when
no issue is referenced.

    gh pr view 18 --json body -q .body | python3 scripts/lint_body.py --kind pr

This file checks structure only. It does not judge writing, and it does not
count words. A long body full of useful detail is good. The writing itself is
checked at authoring time by `.claude/hooks/writing_check.py`, which runs
before `gh pr create` and reports specific problems.

A pull request that changes no behavior waives the evidence rule by ticking
the waiver checkbox the template ships. The waiver only counts in prose. A
checkbox pasted inside a fence is quoted material, not a claim. A pull request
that does change behavior must reference the issue it verifies, because the
issue holds the reproduction the evidence should re-run.

Standard library only: the reusable workflow runs this with no install step.
"""

from __future__ import annotations

import argparse
import re
import sys

# Authors whose bodies are generated, so there is no writer to hold to the
# budget and nothing a rewrite would survive: Dependabot restates its release
# notes on every rebase, and the ops sync app regenerates its body from
# scripts/sync.py on every run. GitHub reserves [bot] logins, so a fork
# cannot claim the exemption. Keep the list short and add nothing a person
# could be behind.
BOT_AUTHORS = frozenset({"dependabot[bot]", "portolan-ops-sync[bot]"})

# One entry per required section. The first spelling is canonical and is what
# a failure names. The rest are accepted so a pull request opened against the
# older template keeps passing while the fleet converges on the new one.
PR_REQUIRED_SECTIONS: tuple[tuple[str, ...], ...] = (
    ("What changed", "What this changes"),
    ("Why",),
    ("Verification",),
)
EVIDENCE_SECTION = "Verification"

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
COMMENT_OPEN_RE = re.compile(r"<!--")
COMMENT_CLOSE_RE = re.compile(r"-->")
WAIVER_RE = re.compile(r"^\s*[-*]\s*\[[xX]\].*does not alter behavior", re.MULTILINE)

# An issue reference: #N, or a GitHub issue URL.
ISSUE_RE = re.compile(r"(?<![\w&])#\d+\b|github\.com/[\w.-]+/[\w.-]+/issues/\d+")

# A named source: an object-store or web URL, or a path with a file extension.
SOURCE_RE = re.compile(
    r"(?:https?|s3|gs|az|abfss?|file)://\S+"
    r"|(?:^|[\s\"'(`])[~.]?/?[\w.-]+(?:/[\w.-]+)+\.\w{2,9}\b"
)


class Section:
    """One heading and the lines beneath it, split by kind."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.prose: list[str] = []
        self.code: list[str] = []

    @property
    def prose_text(self) -> str:
        return "\n".join(self.prose)

    @property
    def code_text(self) -> str:
        return "\n".join(self.code)

    def is_empty(self) -> bool:
        return not self.prose_text.strip() and not self.code_text.strip()


def strip_comments(text: str) -> str:
    """Drop HTML comments, including the unclosed tail of a truncated one."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return re.sub(r"<!--.*\Z", "", text, flags=re.DOTALL)


def parse(body: str) -> list[Section]:
    """Split a body into sections, separating prose from fenced code."""
    sections = [Section("")]
    fence: str | None = None
    in_comment = False

    for raw in body.replace("\r\n", "\n").split("\n"):
        line = raw

        if fence is not None:
            sections[-1].code.append(line)
            if FENCE_RE.match(line) and line.strip().startswith(fence):
                fence = None
            continue

        if in_comment:
            close = COMMENT_CLOSE_RE.search(line)
            sections[-1].prose.append(line[close.end() :] if close else "")
            in_comment = close is None
            continue

        opened = FENCE_RE.match(line)
        if opened:
            fence = opened.group(1)
            sections[-1].code.append(line)
            continue

        heading = HEADING_RE.match(line)
        if heading:
            sections.append(Section(heading.group(2).strip()))
            continue

        if COMMENT_OPEN_RE.search(line) and not COMMENT_CLOSE_RE.search(line):
            in_comment = True
            sections[-1].prose.append(strip_comments(line))
            continue

        sections[-1].prose.append(strip_comments(line))

    return sections


def find(sections: list[Section], title: str) -> Section | None:
    wanted = title.casefold().rstrip("?:")
    for section in sections:
        if section.title.casefold().rstrip("?:") == wanted:
            return section
    return None


def has_evidence(section: Section) -> tuple[bool, bool]:
    """Return whether the section pastes output and whether it names a source."""
    body = "\n".join(ln for ln in section.code if not FENCE_RE.match(ln)).strip()
    pasted = bool(body)
    named = bool(SOURCE_RE.search(section.code_text + "\n" + section.prose_text))
    return pasted, named


def is_generated(author: str) -> bool:
    """Whether the body came from an automated author rather than a person."""
    return author.strip() in BOT_AUTHORS


def check(
    body: str,
    kind: str,
    author: str = "",
) -> list[str]:
    """Return one problem per line, empty when the body passes."""
    if is_generated(author):
        return []

    if not body.strip():
        return ["The body is empty. Use the template."]

    sections = parse(body)
    problems: list[str] = []

    if kind == "pr":
        for names in PR_REQUIRED_SECTIONS:
            section = next(
                (s for s in (find(sections, n) for n in names) if s is not None),
                None,
            )
            if section is None:
                problems.append(f'Missing the "{names[0]}" section.')
            elif section.is_empty():
                problems.append(f'"{section.title}" is empty. Fill it in or cut it.')

    # A waiver only counts in prose. Inside a fence it is quoted material,
    # not a claim about this change.
    waived = any(WAIVER_RE.search(s.prose_text) for s in sections)

    if kind == "pr" and not waived:
        referenced = any(ISSUE_RE.search(s.prose_text) for s in sections)
        if not referenced:
            problems.append(
                "No issue is referenced. Name the issue this change verifies "
                "(#N or its URL); its reproduction is what the evidence "
                "should re-run. A change that alters no behavior ticks the "
                "waiver instead."
            )

    if not waived:
        evidence = find(sections, EVIDENCE_SECTION)
        if kind == "pr" and evidence is None:
            pass  # Already reported as a missing required section.
        elif evidence is not None:
            pasted, named = has_evidence(evidence)
            if not pasted:
                problems.append(
                    f'"{EVIDENCE_SECTION}" pastes no output. Add the command you '
                    f"ran and what it printed, in a fenced block."
                )
            if not named:
                problems.append(
                    f'"{EVIDENCE_SECTION}" names no data source. Give the URL or '
                    f"catalog path the command read."
                )
        elif kind == "issue":
            pasted = any(
                "\n".join(ln for ln in s.code if not FENCE_RE.match(ln)).strip()
                for s in sections
            )
            if not pasted:
                problems.append(
                    "Nothing is pasted. Show the command and its output, run "
                    "against real data."
                )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("pr", "issue"), required=True)
    parser.add_argument(
        "--author",
        default="",
        help="Login of the author. A generated body is exempt.",
    )
    args = parser.parse_args(argv)

    if is_generated(args.author):
        print(f"Body check skipped: {args.author.strip()} generates its bodies.")
        return 0

    body = sys.stdin.read()
    problems = check(body, args.kind, args.author)

    if problems:
        noun = "pull request" if args.kind == "pr" else "issue"
        print(f"This {noun} body needs work:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nThe structure and the evidence rule are in the org norms:\n"
            "https://github.com/portolan-sdi/portolan-ops/blob/main/AGENTS.md",
            file=sys.stderr,
        )
        return 1

    print("Body check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
