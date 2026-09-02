# Prose

Portolan prose follows rules that Vale enforces. The rules live in
[`styles/`](../styles/) and the configuration lives in
[`.vale.ini`](../.vale.ini). This page is the map. The rules themselves are
the `.yml` files, and each one states its reason in its `message` field.

## The three layers

Two layers apply to every prose file.

<!-- vale Portolan-Terms.AiReady = NO -->

| Style | Holds |
|---|---|
| `Portolan-Terms` | The project lexicon. Portolan is a specification. The validator is `rashid`. Portolan is AI-ready, not AI-first. Hype words are errors. |
| `Portolan-Mechanics` | Punctuation and capitalization. Headings use sentence case. An em dash carries spaces around it and appears at most three times per file. |

<!-- vale Portolan-Terms.AiReady = YES -->

`Portolan-Terms` derives from [`copy/messaging.md`](../copy/messaging.md) and
[`copy/urls.md`](../copy/urls.md). Change those files first, then the rules.

One voice layer applies per path.

| Style | Applies to | Sentence limit |
|---|---|---|
| `Portolan-Docs` | READMEs, docs pages, specifications | 26 words |
| `Portolan-Web` | Website copy, extracted from `messages/en.json` | 30 words |
| `Portolan-Blog` | Blog posts | 45 words |

`Portolan-Voice` holds the rules all three share, such as the closing tail and
the mirrored phrase. `Portolan-Docs` also extends the Google developer
documentation style, pinned to a release.

## Running it

```bash
vale sync          # fetch the pinned Google package, once
vale .             # everything, including suggestions
vale --minAlertLevel=error .
```

CI decides what fails. `MinAlertLevel` in `.vale.ini` sets what prints and
also sets the exit code, so the workflow passes `--minAlertLevel` rather than
the file changing per repo.

Downstream repos hold no copy of the rules. `ci/vale.yml` calls
`reusable-vale.yml`, which checks out portolan-ops and lints against the
`.vale.ini` here. To run the same check by hand from another repo, point Vale
at a checkout of ops:

```bash
vale --config ../portolan-ops/.vale.ini --output=line .
```

Website copy that lives in `messages/en.json` is not Markdown, so
`scripts/vale_messages.py` extracts it first:

```bash
python3 scripts/vale_messages.py extract messages/en.json
vale --output=JSON .vale-web/messages.md \
  | python3 scripts/vale_messages.py remap
```

`remap` rewrites each location back to the JSON key.

## Suppressing a rule

Wrap the text when Vale is wrong about it.

```markdown
<!-- vale Portolan-Mechanics.Headings = NO -->
## A Heading That Must Keep Its Case
<!-- vale Portolan-Mechanics.Headings = YES -->
```

Turn a rule off for a whole file with `<!-- vale RuleName = NO -->` at the top.
Turn every rule off with `<!-- vale off -->`.

## Two traps

A term listed in `styles/config/vocabularies/Portolan/accept.txt` is skipped by
every other check. Adding "Portolan" there silently disabled the rule that
reports "Portolan standard". Keep a word out of `accept.txt` when a rule must
match on it.

`BasedOnStyles` does not accumulate across glob sections. The most specific
match replaces the others. Every section in `.vale.ini` therefore names each
style it needs.

## What Vale does not check

Vale matches words and punctuation. It cannot see tone, padding, or prose that
spends its length arguing for the work it describes. Read what you wrote before
you publish it, and cut the sentences that exist to make the change sound good.

Development writing follows a separate rule set. Issue bodies, pull request
bodies, and commit message bodies use Simplified Technical English, checked by
[`.claude/hooks/writing_check.py`](../.claude/hooks/writing_check.py).
