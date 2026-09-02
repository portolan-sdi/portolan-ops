# Prose

Portolan sounds calm, direct, and definite. It states facts without a sales
pitch and names limits without apology. This page defines that voice and maps
the checks that support it.

## Write for the reader

Lead with the outcome. Explain the mechanism only when it helps the reader
judge or use the result. Link to implementation detail instead of narrating a
workflow file in prose.

Support each claim with a mechanism or a checkable fact. Name the format, tool,
comparison, cost, or constraint that makes the claim true. When a claim is
relative, state what Portolan changes and what the alternative requires.

Scope claims to facts that will remain true. Avoid absolutes about every tool,
publisher, cost, or future implementation. Describe Portolan as an evolving
open-source specification and state current gaps directly.

Use verbs that match the system. People query remote data rather than load it
into Portolan. Publishers store files rather than run a Portolan server.

## Cut formulaic prose

Vary sentence length and structure. Do not use one grammatical frame across
adjacent sentences or paragraphs. In particular, avoid a sequence of
"The X does A, B, and C" explanations followed by a neat consequence clause.

Do not turn two related facts into a mirrored slogan. Do not add a three-part
list for rhythm when the subject does not require three items. Avoid stock
transitions, dramatic colons, aphorisms, metaphors, and closing summaries.

Keep one subject per paragraph. Most paragraphs need two or three sentences.
End on the final substantive point instead of restating it.

Technical terms can remain unexplained when the audience knows them. Keep the
surrounding language plain, and never use jargon to make ordinary behavior
sound important.

<!-- vale Portolan-Terms.AiReady = NO -->
Portolan is AI-ready, not AI-first.
<!-- vale Portolan-Terms.AiReady = YES -->
Name people and agents together. Treat agent access as a means to serve people.

These rules judge the text, not its author. A human can write formulaic prose,
and an agent can write clean prose. Report the pattern that needs revision and
do not claim that a tool identified who wrote it.

## Automated checks

The Vale rules live in [`styles/`](../styles/), and [`.vale.ini`](../.vale.ini)
configures them. Each rule explains its purpose in its `message` field.

## The three layers

Three shared styles apply to every prose file.

<!-- vale Portolan-Terms.AiReady = NO -->

| Style | Holds |
|---|---|
| `Portolan-Terms` | The project lexicon. Portolan is a specification. The validator is `rashid`. Portolan is AI-ready, not AI-first. Hype words are errors. |
| `Portolan-Mechanics` | Punctuation and capitalization. Headings use sentence case. An em dash carries spaces around it and appears at most three times per file. |
| `Portolan-Voice` | Formulaic constructions that Vale can identify with useful precision. |
<!-- vale Portolan-Terms.AiReady = YES -->

`Portolan-Terms` derives from [`copy/messaging.md`](../copy/messaging.md) and
[`copy/urls.md`](../copy/urls.md). Change those files first, then the rules.

One surface style also applies per path.

| Style | Applies to | Sentence limit |
|---|---|---|
| `Portolan-Docs` | READMEs, docs pages, specifications | 26 words |
| `Portolan-Web` | Website copy, extracted from `messages/en.json` | 30 words |
| `Portolan-Blog` | Blog posts | 45 words |

`Portolan-Docs` also extends the Google developer documentation style, pinned
to a release. Proselint checks a small set of clichés, redundant phrases,
hedges, and commercial language that Vale does not own.

## Running it

```bash
vale sync
vale .
vale --minAlertLevel=error .
uvx --from proselint==0.16.0 proselint check \
  --config proselint.json \
  README.md docs
```

CI decides what fails. Error-level findings block portolan-ops. Downstream pull
requests cannot add new errors, but existing errors remain visible until each
repo is clean.

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

## What automation does not check

The tools match words, punctuation, and a small set of structural patterns.
They cannot decide whether a claim has enough evidence or whether a paragraph
serves its reader. Read the text before publication.

Development writing follows a separate rule set. Issue bodies, pull request
bodies, and commit message bodies use Simplified Technical English, checked by
[`.claude/hooks/writing_check.py`](../.claude/hooks/writing_check.py).
