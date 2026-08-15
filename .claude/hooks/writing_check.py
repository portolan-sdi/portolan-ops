#!/usr/bin/env python3
"""Check that an issue or pull request body reads well before it is filed.

This is a Claude Code hook. It runs two ways:

    writing_check.py --print-rules        SessionStart: print the rules
    writing_check.py                      PreToolUse: read hook JSON on stdin

It also runs by hand, which is how the tests drive it:

    gh pr view 40 --json body -q .body | writing_check.py --kind pr --stdin

The rules live in this file and nowhere else, so the text an agent reads and
the checks that run cannot drift apart. VOICE.md governs public-facing copy.
These rules govern development writing: issue bodies, pull request bodies, and
commit message bodies.

A rule blocks only when it is a closed list of exact strings or a single
punctuation mark. Anything needing part-of-speech data advises instead. The
checker denies only when it affirmatively found a blocking hit; every other
path exits zero and silent, because a false positive must never stop a person
from filing an issue.

Standard library only: it runs in every repo with no install step.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import shlex
import sys
from pathlib import Path

MASK = "\x00"  # Not prose. Never matched by a rule.
KEEP = "\x01"  # Opaque, but counts as one word.

RULES = """\
WRITING RULES - issue bodies, pull request bodies, commit message bodies.

VOICE.md governs public-facing copy: the website, announcements, and docs.
These rules govern development writing. Follow these for issues and pull
requests.

TWO LAYERS

Write the human layer first. State what is wrong or missing, why it matters,
and what should happen instead. A reader who did not follow the investigation
understands it in about one minute.

Then write the agent layer: evidence, implementation detail, constraints, edge
cases, and verification.

Length is not a fault. Compression into dense prose is. A 700-word issue is
good when the first 150 words make the outcome obvious. A 150-word issue is
bad when it hides the outcome.

SENTENCES

- Keep a sentence under about 20 words. Over 32 words is blocked.
- Put one idea in one sentence.
- Write in the active voice. Name who does the action.
- Start an instruction with the verb.
- Do not use an em dash, a semicolon, or a dramatic mid-sentence colon. A
  colon before a list is correct.

WORDS

- Use the simple word. Write "use", not "utilize". Write "before", not "prior
  to". Write "about", not "regarding".
- Do not write "leverage", "facilitate", or "utilize". Name the action.
- Cut filler: just, really, actually, simply, basically, of course.
- Cut hype: powerful, seamless, robust, blazing-fast. State the measured
  behavior instead.
- Do not use idioms or metaphors.

STRUCTURE

- Put the outcome first and the detail after.
- Describe the current state. Do not narrate failed approaches unless that
  history changes the current design.
- Use bullets for parallel items and numbered lists for steps.
- End on the last technical point.

NEVER CHANGED

- Code, commands, file paths, identifiers, error text, and quoted output stay
  exact.
- Technical precision wins. Simplify the language, not the content.

EXAMPLES

  Bad:  This creates a persistent remote-state divergence.
  Good: The old files remain on the server.

  Bad:  The PMTiles source resolution pathway lacks propagation semantics.
  Good: The generator does not write the PMTiles URL.

  Bad:  The graduated-only case ultimately collapses into an invalid
        symbolizer state.
  Good: If every rule is graduated, conversion fails.

A hook checks bodies at `gh issue create` and `gh pr create`. Suppress a false
positive with `<!-- ste-ok: RULE_ID why this is fine -->` on the line above.
"""

# Each entry is one required section. The first spelling is canonical and is
# what messages name; the rest are accepted so that pull requests opened
# against the older template keep passing while the fleet converges.
PR_REQUIRED: tuple[tuple[str, ...], ...] = (
    ("What changed", "What this changes"),
    ("Why",),
    ("Verification",),
)


# --------------------------------------------------------------------------
# Masking
# --------------------------------------------------------------------------

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_COMMENT_TAIL_RE = re.compile(r"<!--(?!.*?-->).*\Z", re.DOTALL)
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM_RE = re.compile(r"^ {0,3}(?:[-*+]|\d{1,9}[.)])\s+")
QUOTE_RE = re.compile(r"^ {0,3}>")
INDENTED_RE = re.compile(r"^ {4,}\S")
TABLE_RE = re.compile(r"^[^|\n]*\|[^|\n]*\|")

INLINE_MASKS = (
    re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", re.DOTALL),  # inline code
    re.compile(r"<[a-zA-Z][^>\s]*://[^>]*>"),  # autolink
    re.compile(r"(?:https?|s3|gs|az|abfss?|file|ftp)://\S+"),  # bare URL
    re.compile(r"(?<=\])\([^)\s]+(?:\s+\"[^\"]*\")?\)"),  # link destination
    re.compile(r"^\s{0,3}\[[^\]]+\]:\s*\S+.*$", re.MULTILINE),  # link def
    re.compile(r"&[#\w]{1,10};"),  # HTML entity
    re.compile(r"(?<![\w/])[\w.-]+/[\w.-]+#\d+"),  # cross-repo ref
    re.compile(r"(?<![\w&])#\d+\b"),  # issue ref
    re.compile(r"(?<![\w/])@[\w-]+"),  # handle
    re.compile(r"\b[0-9a-f]{7,40}\b"),  # SHA
    re.compile(r"(?<![\w-])[~.]?/?[\w.-]+(?:/[\w.-]+)+(?![\w-])"),  # path
    re.compile(
        r"(?<![\w-])[\w-]+\.(?:md|py|ya?ml|json|toml|txt|csv|tiff?|parquet"
        r"|geojson|html|css|js|ts|tsx|sh|cfg|ini|lock|rs|go|sql|pmtiles|cog)"
        r"(?![\w-])"
    ),  # filename
)

# Tokens that carry a period but do not end a sentence.
PROTECT = (
    re.compile(
        r"\b(?:e\.g\.|i\.e\.|etc\.|cf\.|vs\.|approx\.|est\.|al\.|Fig\.|No\."
        r"|Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.|St\.|Inc\.|Ltd\.|Jr\.|Sr\."
        r"|Ph\.D\.|U\.S\.|a\.m\.|p\.m\.)",
        re.IGNORECASE,
    ),
    re.compile(r"\bv?\d+(?:\.\d+)+\b"),  # v1.2.3, 0.16.0
    re.compile(r"\.{2,}"),  # ellipsis
    re.compile(r"\b[A-Z]\."),  # initial
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]*[A-Z0-9])")


class Doc:
    """A body split into lines, with a masked twin of the same shape."""

    def __init__(self, text: str) -> None:
        self.text = text.replace("\r\n", "\n")
        self.starts = [0]
        for i, ch in enumerate(self.text):
            if ch == "\n":
                self.starts.append(i + 1)
        flags = [False] * len(self.text)
        self._mask_comments(flags)
        self.kinds = self._mask_lines(flags)
        self._mask_inline(flags)
        self.masked = "".join(
            ch if ch == "\n" or not f else MASK for ch, f in zip(self.text, flags)
        )

    # -- construction helpers ------------------------------------------
    def _fill(self, flags: list[bool], start: int, end: int) -> None:
        for i in range(start, min(end, len(flags))):
            flags[i] = True

    def _mask_comments(self, flags: list[bool]) -> None:
        for pattern in (HTML_COMMENT_RE, HTML_COMMENT_TAIL_RE):
            for m in pattern.finditer(self.text):
                self._fill(flags, m.start(), m.end())

    def _line_span(self, n: int) -> tuple[int, int]:
        start = self.starts[n]
        end = self.starts[n + 1] if n + 1 < len(self.starts) else len(self.text)
        return start, end

    def _mask_lines(self, flags: list[bool]) -> list[str]:
        """Classify every line and mask the ones that are not prose."""
        kinds: list[str] = []
        fence: str | None = None
        for n in range(len(self.starts)):
            start, end = self._line_span(n)
            raw = self.text[start:end].rstrip("\n")
            masked_out = all(flags[start:end]) if end > start else False

            if fence is not None:
                kinds.append("code")
                self._fill(flags, start, end)
                if raw.strip().startswith(fence):
                    fence = None
                continue

            opened = FENCE_OPEN_RE.match(raw)
            if opened and not masked_out:
                fence = opened.group(1)
                kinds.append("code")
                self._fill(flags, start, end)
                continue

            if masked_out or not raw.strip():
                kinds.append("blank")
                continue
            if HEADING_RE.match(raw):
                kinds.append("heading")
                continue
            if INDENTED_RE.match(raw) or QUOTE_RE.match(raw) or TABLE_RE.match(raw):
                kinds.append("code")
                self._fill(flags, start, end)
                continue
            if LIST_ITEM_RE.match(raw):
                kinds.append("list_item")
                continue
            kinds.append("prose")
        return kinds

    def _mask_inline(self, flags: list[bool]) -> None:
        live = "".join(
            ch if (ch == "\n" or not f) else MASK for ch, f in zip(self.text, flags)
        )
        for pattern in INLINE_MASKS:
            for m in pattern.finditer(live):
                self._fill(flags, m.start(), m.end())

    # -- lookups -------------------------------------------------------
    def line_of(self, offset: int) -> int:
        return bisect.bisect_right(self.starts, offset)

    def col_of(self, offset: int) -> int:
        return offset - self.starts[self.line_of(offset) - 1] + 1

    def excerpt(self, start: int, end: int, width: int = 22) -> str:
        left = max(0, start - width)
        right = min(len(self.text), end + width)
        head = self.text[left:start].replace("\n", " ")
        body = self.text[start:end].replace("\n", " ")
        tail = self.text[end:right].replace("\n", " ")
        out = f"{'...' if left else ''}{head}>>{body}<<{tail}"
        return " ".join(out.split())

    def headings(self) -> list[tuple[int, str]]:
        out = []
        for n, kind in enumerate(self.kinds):
            if kind != "heading":
                continue
            start, end = self._line_span(n)
            m = HEADING_RE.match(self.text[start:end].rstrip("\n"))
            if m:
                out.append((n, m.group(2).strip()))
        return out

    def section_bounds(self) -> list[tuple[str, int, int]]:
        marks = self.headings()
        out = []
        for i, (line_no, title) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else len(self.kinds)
            out.append((title, line_no, end))
        return out

    def is_live(self, offset: int) -> bool:
        return self.masked[offset] not in (MASK, "\n")


# --------------------------------------------------------------------------
# Sentences
# --------------------------------------------------------------------------


class Sentence:
    def __init__(self, start: int, text: str) -> None:
        self.start = start
        self.text = text

    def words(self) -> int:
        return len(re.findall(r"\S+", self.text.replace(MASK, "x")))


def sentences(doc: Doc) -> list[Sentence]:
    """Split prose into sentences, with offsets into the original text."""
    out: list[Sentence] = []
    block: list[int] = []

    def flush(single: bool = False) -> None:
        if not block:
            return
        start = doc.starts[block[0]]
        last = block[-1]
        end = doc.starts[last + 1] if last + 1 < len(doc.starts) else len(doc.masked)
        chunk = doc.masked[start:end]
        if single:
            # A list item is one unit. Its internal periods are usually
            # abbreviations or a clipped clause, not sentence ends.
            if chunk.strip(MASK + " \t\n"):
                out.append(Sentence(start, chunk))
            block.clear()
            return
        guard = list(chunk)
        for pattern in PROTECT:
            for m in pattern.finditer(chunk):
                for i in range(m.start(), m.end()):
                    guard[i] = KEEP
        guarded = "".join(guard)
        offset = 0
        for piece in SENTENCE_SPLIT_RE.split(guarded):
            if piece.strip(MASK + KEEP + " \t\n"):
                out.append(
                    Sentence(start + offset, chunk[offset : offset + len(piece)])
                )
            offset += len(piece)
            # Re-align past the whitespace the split consumed.
            while offset < len(guarded) and guarded[offset] in " \t\n\"')]":
                offset += 1
        block.clear()

    for n, kind in enumerate(doc.kinds):
        if kind == "prose":
            block.append(n)
            continue
        flush()
        if kind == "list_item":
            block.append(n)
            flush(single=True)
    flush()
    return out


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------


def _words(*items: str) -> re.Pattern[str]:
    body = "|".join(items)
    return re.compile(rf"(?<![\w-])(?:{body})(?![\w-])", re.IGNORECASE)


def _phrases(*items: str) -> re.Pattern[str]:
    body = "|".join(i.replace(" ", r"\s+") for i in items)
    return re.compile(rf"(?<![\w-])(?:{body})(?![\w-])", re.IGNORECASE)


VOCAB: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "FILLER",
        _words(
            "just",
            "really",
            "simply",
            "basically",
            "actually",
            "truly",
            "obviously",
            "of course",
        ),
        "delete it",
    ),
    (
        "HYPE",
        _phrases(
            "powerful",
            "seamless",
            "seamlessly",
            "effortless",
            "robust",
            "blazing.fast",
            "lightning.fast",
            "cutting.edge",
            "world.class",
            "best.in.class",
            "rock.solid",
            "state.of.the.art",
            "game.changing",
            "revolutionary",
            "supercharge",
            "unleash",
            "delve",
            "elevate",
        ),
        "show the behavior",
    ),
    (
        "VAGUE_VERB",
        _words(
            "leverage",
            "leverages",
            "leveraged",
            "leveraging",
            "facilitate",
            "facilitates",
            "facilitated",
            "utilize",
            "utilizes",
            "utilized",
            "utilizing",
            "utilization",
        ),
        "name the action",
    ),
    (
        "WORDY",
        _phrases(
            "prior to",
            "in order to",
            "due to the fact that",
            "at this point in time",
            "at the present time",
            "in the event that",
            "subsequent to",
            "has the ability to",
            "is able to",
            "are able to",
            "make use of",
            "a large number of",
        ),
        "use the short form",
    ),
    (
        "IDIOM",
        _phrases(
            "at the end of the day",
            "low.hanging fruit",
            "silver bullet",
            "rabbit hole",
            "heavy lifting",
            "boils down to",
            "in the weeds",
            "moving parts",
            "bread and butter",
            "tip of the iceberg",
        ),
        "say it plainly",
    ),
    (
        "QUALIFIER",
        _words("very", "quite", "somewhat", "fairly"),
        "delete it",
    ),
)

FILLER_TEMPORAL_RE = re.compile(
    r"just\s+(?:before|after|under|over|below|above|\d)", re.IGNORECASE
)
ROBUST_STATS_RE = re.compile(
    r"robust\s+(?:to|against|regression|estimator|standard\s+errors)",
    re.IGNORECASE,
)
RATHER_THAN_RE = re.compile(r"rather\s+than", re.IGNORECASE)

CLOSING_TAIL_RE = _phrases(
    "and that.s it",
    "that.s all you need to know",
    "now you.re ready to",
    "it.s that simple",
    "in conclusion",
    "to summarize",
    "to sum up",
    "hope this helps",
)

EM_DASH_RE = re.compile(r"—|–|(?<= )--(?=[ ])")
DIGIT_RANGE_RE = re.compile(r"\d\s*–\s*\d")
SEMICOLON_RE = re.compile(r";")
MID_COLON_RE = re.compile(r"(?<=[a-z]) *: +(?=[a-z])")
LABEL_COLON_RE = re.compile(r"^\s*\*{0,2}[A-Z][\w ]{0,24}\*{0,2}:")
PASSIVE_RE = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?(\w+(?:ed|en))\b\s+by\b",
    re.IGNORECASE,
)
PASSIVE_OK = frozenset(
    {
        "deprecated",
        "required",
        "based",
        "located",
        "supported",
        "documented",
        "expected",
        "related",
        "involved",
        "interested",
        "dedicated",
        "sophisticated",
        "caused",
        "followed",
        "accompanied",
    }
)

BLOCK_MAX_WORDS = 32
ADVISE_MAX_WORDS = 25
ADVISE_MAX_SENTENCES = 6

SUPPRESS_RE = re.compile(
    r"<!--\s*ste-ok:\s*([A-Z_]+(?:\s+[A-Z_]+)*)\s+(.{8,}?)\s*-->", re.DOTALL
)
SKIP_RE = re.compile(r"<!--\s*ste-skip:\s*(.{8,}?)\s*-->", re.DOTALL)


class Finding:
    def __init__(
        self,
        rule: str,
        line: int,
        col: int,
        fix: str,
        excerpt: str,
        blocking: bool = True,
    ) -> None:
        self.rule = rule
        self.line = line
        self.col = col
        self.fix = fix
        self.excerpt = excerpt
        self.blocking = blocking

    def format(self) -> str:
        where = f"L{self.line}:{self.col}"
        return f"{where:<8} {self.rule:<13} {self.fix:<28} {self.excerpt}"


def _blank_fences(text: str) -> str:
    """Blank fenced lines, keeping length and line breaks.

    A marker inside a fence is quoted material, not a claim about this body.
    The waiver checkbox in lint_body.py already works this way.
    """
    out: list[str] = []
    fence: str | None = None
    for line in text.split("\n"):
        opened = FENCE_OPEN_RE.match(line)
        if fence is not None:
            out.append(" " * len(line))
            if line.strip().startswith(fence):
                fence = None
            continue
        if opened:
            fence = opened.group(1)
            out.append(" " * len(line))
            continue
        out.append(line)
    return "\n".join(out)


def _suppressions(text: str) -> tuple[bool, dict[int, set[str]], list[str]]:
    """Return whole-body skip, per-line rule suppressions, and their labels."""
    text = _blank_fences(text.replace("\r\n", "\n"))
    doc_starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]

    def line_at(offset: int) -> int:
        return bisect.bisect_right(doc_starts, offset)

    if SKIP_RE.search(text):
        return True, {}, ["whole body"]

    per_line: dict[int, set[str]] = {}
    labels: list[str] = []
    lines = text.split("\n")
    for m in SUPPRESS_RE.finditer(text):
        rules = set(m.group(1).split())
        here = line_at(m.start())
        target = here
        # End-of-line marker applies to its own line; otherwise the next
        # line that holds something.
        if lines[here - 1].strip().startswith("<!--"):
            target = here + 1
            while target <= len(lines) and not lines[target - 1].strip():
                target += 1
        per_line.setdefault(target, set()).update(rules)
        labels.extend(f"{r} L{target}" for r in sorted(rules))
    return False, per_line, labels


def review(body: str, kind: str) -> tuple[list[Finding], list[str]]:
    """Return findings and the suppressions that were honored."""
    skip_all, per_line, labels = _suppressions(body)
    if skip_all:
        return [], labels

    doc = Doc(body)
    found: list[Finding] = []

    def add(rule: str, start: int, end: int, fix: str, blocking: bool = True) -> None:
        line = doc.line_of(start)
        if rule in per_line.get(line, set()):
            return
        found.append(
            Finding(
                rule, line, doc.col_of(start), fix, doc.excerpt(start, end), blocking
            )
        )

    live = doc.masked
    if not live.replace(MASK, "").strip():
        found.append(Finding("EMPTY_BODY", 1, 1, "use the template", "", True))
        return found, labels

    # Vocabulary.
    for rule, pattern, fix in VOCAB:
        for m in pattern.finditer(live):
            word = live[m.start() : m.end()]
            if rule == "FILLER" and FILLER_TEMPORAL_RE.match(live[m.start() :]):
                continue
            if rule == "HYPE" and ROBUST_STATS_RE.match(live[m.start() :]):
                continue
            add(rule, m.start(), m.end(), f'"{word}" -> {fix}')
    for m in _words("rather").finditer(live):
        if RATHER_THAN_RE.match(live[m.start() :]):
            continue
        add("QUALIFIER", m.start(), m.end(), '"rather" -> delete it')

    # Punctuation.
    for m in EM_DASH_RE.finditer(live):
        if DIGIT_RANGE_RE.search(live[max(0, m.start() - 3) : m.end() + 3]):
            continue
        add("EM_DASH", m.start(), m.end(), "split into two sentences")
    for m in SEMICOLON_RE.finditer(live):
        add("SEMICOLON", m.start(), m.end(), "split into two sentences")
    for m in MID_COLON_RE.finditer(live):
        line_no = doc.line_of(m.start())
        raw = body.split("\n")[line_no - 1]
        if LABEL_COLON_RE.match(raw):
            continue
        after = live[m.end() : doc.starts[line_no - 1] + len(raw)]
        if len(re.findall(r"\S+", after.replace(MASK, "x"))) < 4:
            continue
        if line_no < len(doc.kinds) and doc.kinds[line_no] in ("list_item", "code"):
            continue
        add("MID_COLON", m.start(), m.end(), "use a period, not a colon")

    # Sentences.
    for sentence in sentences(doc):
        count = sentence.words()
        if count > BLOCK_MAX_WORDS:
            add(
                "LONG_SENTENCE",
                sentence.start,
                sentence.start + min(len(sentence.text), 40),
                f"{count} words; split it",
            )
        elif count > ADVISE_MAX_WORDS:
            add(
                "SENTENCE_LONG",
                sentence.start,
                sentence.start + min(len(sentence.text), 40),
                f"{count} words; consider splitting",
                blocking=False,
            )

    # Passive voice, advisory only.
    for m in PASSIVE_RE.finditer(live):
        if m.group(1).lower() in PASSIVE_OK:
            continue
        add("PASSIVE", m.start(), m.end(), "name who acts", blocking=False)

    # Closing tails, only near the end of a section.
    bounds = doc.section_bounds() or [("", 0, len(doc.kinds))]
    for _title, first, last in bounds:
        span_start = doc.starts[first]
        span_end = doc.starts[last] if last < len(doc.starts) else len(live)
        segment = live[span_start:span_end]
        for m in CLOSING_TAIL_RE.finditer(segment):
            tail = segment[m.end() :]
            if len(re.findall(r"\S+", tail.replace(MASK, ""))) > 25:
                continue
            add(
                "CLOSING_TAIL",
                span_start + m.start(),
                span_start + m.end(),
                "end on the last point",
            )

    # Structure.
    found.extend(_structure(doc, kind, per_line))
    found.sort(key=lambda f: (f.line, f.col))
    return found, labels


def _has_content(doc: Doc, first: int, last: int) -> bool:
    """Whether lines [first, last) hold prose or pasted output.

    A fence marker on its own is punctuation, not content. Everything a
    reader would see counts, so an empty section really is empty.
    """
    for n in range(first, min(last, len(doc.kinds))):
        kind = doc.kinds[n]
        if kind == "blank":
            continue
        start, end = doc._line_span(n)
        raw = doc.text[start:end].strip()
        if kind == "code":
            if raw and not FENCE_OPEN_RE.match(raw):
                return True
            continue
        if doc.masked[start:end].replace(MASK, "").strip():
            return True
    return False


def _structure(doc: Doc, kind: str, per_line: dict[int, set[str]]) -> list[Finding]:
    if kind != "pr":
        return []
    titles = [t for _n, t in doc.headings()]
    if not titles:
        return [Finding("HEADING_MISSING", 1, 1, "use the pull request template", "")]
    out: list[Finding] = []
    norm = [t.casefold().rstrip("?:") for t in titles]
    seen: list[int] = []
    for names in PR_REQUIRED:
        keys = [n.casefold().rstrip("?:") for n in names]
        here = [norm.index(k) for k in keys if k in norm]
        if not here:
            out.append(
                Finding(
                    "HEADING_MISSING",
                    1,
                    1,
                    f'"## {names[0]}" is missing',
                    "",
                )
            )
        else:
            seen.append(min(here))
    if len(seen) == len(PR_REQUIRED) and seen != sorted(seen):
        out.append(
            Finding(
                "HEADING_ORDER",
                1,
                1,
                "outcome first: " + ", ".join(n[0] for n in PR_REQUIRED),
                "",
            )
        )
    wanted = {n.casefold().rstrip("?:") for names in PR_REQUIRED for n in names}
    for title, first, last in doc.section_bounds():
        if title.casefold().rstrip("?:") not in wanted:
            continue
        if not _has_content(doc, first + 1, last) and (
            "HEADING_EMPTY" not in per_line.get(first + 1, set())
        ):
            out.append(
                Finding("HEADING_EMPTY", first + 1, 1, f'"## {title}" is empty', "")
            )
    return out


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

MAX_SHOWN = 10


def report(findings: list[Finding], labels: list[str], kind: str) -> str:
    blocking = [f for f in findings if f.blocking]
    advisory = [f for f in findings if not f.blocking]
    noun = "pull request" if kind == "pr" else "issue"
    plural = "" if len(blocking) == 1 else "s"
    headline = (
        f"Writing review: {len(blocking)} blocking problem{plural} "
        f"in this {noun} body. Fix and retry."
    )
    lines = [headline, ""]
    lines.extend(f.format() for f in blocking[:MAX_SHOWN])
    if len(blocking) > MAX_SHOWN:
        lines.append(f"... and {len(blocking) - MAX_SHOWN} more.")
    if advisory:
        note = ", ".join(f"{f.rule} L{f.line}" for f in advisory[:6])
        lines += ["", f"Advisory, not blocking: {len(advisory)} ({note})."]
    if labels:
        lines += ["", f"Suppressions honored: {', '.join(labels)}."]
    lines += [
        "",
        "Suppress a false positive with a comment on the line above:",
        "  <!-- ste-ok: RULE_ID why this one is correct -->",
        "Rules: writing_check.py --print-rules",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Hook adapter
# --------------------------------------------------------------------------

GH_RE = re.compile(r"\bgh\s+(issue|pr)\s+(create|edit)\b")
SHELL_UNSAFE_RE = re.compile(r"<<|\$\(|`")


def body_from_command(command: str) -> tuple[str, str] | None:
    """Return (kind, body) for a gh call that carries a literal body."""
    m = GH_RE.search(command)
    if not m:
        return None
    kind = "pr" if m.group(1) == "pr" else "issue"
    if SHELL_UNSAFE_RE.search(command):
        return None
    try:
        argv = shlex.split(command)
    except ValueError:
        return None
    for i, token in enumerate(argv):
        nxt = argv[i + 1] if i + 1 < len(argv) else None
        if token in ("--body", "-b") and nxt:
            return kind, nxt
        if token.startswith("--body="):
            return kind, token.split("=", 1)[1]
        if token in ("--body-file", "-F") and nxt:
            if nxt == "-":
                return None
            return kind, Path(nxt).read_text(encoding="utf-8")
    return None


def run_hook() -> int:
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return 0
    command = payload.get("tool_input", {}).get("command", "")
    found = body_from_command(command)
    if not found:
        return 0
    kind, body = found
    findings, labels = review(body, kind)
    if not any(f.blocking for f in findings):
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": report(findings, labels, kind),
                }
            }
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a body's writing.")
    parser.add_argument("--print-rules", action="store_true")
    parser.add_argument("--kind", choices=("pr", "issue"))
    parser.add_argument("--stdin", action="store_true")
    args = parser.parse_args(argv)

    if args.print_rules:
        print(RULES)
        return 0

    if args.stdin:
        findings, labels = review(sys.stdin.read(), args.kind or "issue")
        blocking = [f for f in findings if f.blocking]
        if blocking:
            print(report(findings, labels, args.kind or "issue"), file=sys.stderr)
            return 1
        extra = f" ({len(labels)} suppressions)" if labels else ""
        print(f"Writing review passed{extra}.")
        return 0

    return run_hook()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - fail open, never block the author.
        sys.exit(0)
