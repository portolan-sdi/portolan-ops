# Prose

## Public copy

Portolan's copy is defined in [copy](/copy/). Use it for any public-facing copy, such as portolan-sdi.org. Agents: do not invent your own phrasing.

## Technical guides

Technical documentation for humans, such as guides and tutorials, should use the [Google Developer voice guide](https://developers.google.com/style/highlights).

## Development language

Agents writing GitHub tickets, PRs, commit messages, etc. must use Simplified Technical English (ASD-STE100). This is enforced by [`.claude/hooks/writing_check.py`](../.claude/hooks/writing_check.py).

## Portolan conventions

Most of these are checked by the Vale hook. Some specific things to be aware of:

- Use sentence-case headlines. `Portolan-Mechanics.Headings` reports the exceptions.
- Do not use emoji in docs or headlines. Mono symbols like `→` are fine.
- "Portolan" refers to the standard. Name a specific tool (portolan-cli, the browser) when you mean the tool.
- Command examples must be real, copy-pasteable, and tested against the released CLI. An org profile once advertised a `portolan ingest` command that did not exist.
- Use absolute dates (`2026-07-24`), never relative ones ("last month").
- Link to canonical homes rather than restating them. Pull URLs from [`copy/urls.md`](../copy/urls.md), policies from [`policies/`](../policies/), and brand values from [`brand/brand.json`](../brand/brand.json).

## Vale hooks

We use Vale to enforce Portolan's branding and language norms. It also tries to mitigate the worst excess of AI slop (alas, often unsuccessfully). Unfortunately, it's an imperfect tool, so: humans, feel free to override it for your own hand-written prose. Agents: knock it off with your BS.

The Vale rules live in [`styles/`](../styles/), and [`.vale.ini`](../.vale.ini).

<!-- vale Portolan-Terms.AiReady = NO -->
Portolan is AI-ready, not AI-first.
<!-- vale Portolan-Terms.AiReady = YES -->
Name people and agents together. Treat agent access as a means to serve people.

### Style layers

These shared styles apply to every prose file.

<!-- vale Portolan-Terms.AiReady = NO -->

| Style | Holds |
|---|---|
| `Portolan-Terms` | The project lexicon. Portolan is a specification, and `rashid` is the validator. Portolan is AI-ready, not AI-first. Hype words are errors. |
| `Portolan-Mechanics` | Punctuation and capitalization. Headings use sentence case. An em dash needs spaces around it and appears at most three times per file. |
| `Portolan-Voice` | Formulaic constructions that Vale can identify with useful precision. |
<!-- vale Portolan-Terms.AiReady = YES -->

`Portolan-Terms` derives from [`copy/messaging.md`](../copy/messaging.md) and
[`copy/urls.md`](../copy/urls.md). Change those files first, then the rules.

One surface style also applies per path.

| Style | Applies to | Sentence limit |
|---|---|---|
| `Portolan-Docs` | READMEs, docs pages, specifications | 30 words |
| `Portolan-Web` | Website copy, extracted from `messages/en.json` | 30 words |
| `Portolan-Blog` | Blog posts | 45 words |

`Portolan-Docs` also extends pinned Google and Microsoft style packages. The
Microsoft package adds rules for clear and direct technical writing. Local
rules replace package rules that conflict with Portolan conventions.

The `ai-tells` package from
[tbhb/vale-ai-tells](https://github.com/tbhb/vale-ai-tells) reports the
patterns this file forbids but the Portolan styles cannot match: figurative
language, hype words, and filler. It applies to docs, blog posts, and website
copy. Six of its rules are off, and `.vale.ini` states the reason for each.

| Rule | Why it is off |
|---|---|
| `EmDashUsage` | It bans the em dash. `Portolan-Mechanics.EmDash` defines the em dash rule and requires spaces around it. |
| `SemicolonUsage` | `Google.Semicolons` warns on the semicolon. Keep one rule for it. |
| `NegatedObject` | Its message gives a contraction as the fix. Contraction rules are off here. |
| `FormalRegister` | It reports "implements". A tool implements the specification. The word is exact. |
| `ColonUsage` | It reports a run-in bold label, which the docs use to open a paragraph. |
| `DoubleHyphen` | Every match is a CLI flag inside a code span. Vale reports the token at the raw position inside the mask. |

Vale skips the block between the `ops-sync` markers. A sync run overwrites that
text in a downstream repo, so an edit there does not last. The source text is in this
repo, where the file has no markers, so Vale checks the canonical version here.

The `ai-tells` pin stays manual. `scripts/bump_tools.py` reads PyPI and the
workflow files. Move the release URL in `.vale.ini` by hand, then run the
checks below.

`scripts/vale_sync.sh` fetches the packages and retries a failed download.
GitHub answers a release download with 504 often enough to fail a correct pull
request. The script tries three times, and the wait doubles after each failure.
`VALE_SYNC_ATTEMPTS` and `VALE_SYNC_WAIT` override both numbers.

The Readability package reports the Automated Readability Index and Flesch
Reading Ease for docs. Both findings are suggestions. Use them to compare a
document before and after an edit. Technical names can keep sound prose outside
the package's general targets. Improve the prose by unpacking abstractions and
making relationships clear. Do not replace precise terms only to improve a
score.

Proselint checks a small set of clichés, redundant phrases, hedges, and
commercial language that Vale does not own.

### Running Vale

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

Downstream repos store no copy of the rules. `ci/vale.yml` calls
`reusable-vale.yml`, which checks out portolan-ops and lints against the
`.vale.ini` here. To run the same check by hand from another repo, point Vale
at a checkout of ops:

```bash
vale --config ../portolan-ops/.vale.ini --output=line .
```

The reusable workflow accepts a `glob` input to exclude vendored prose.
Set `glob: '!tests/fixtures/**'` under the caller's `with` block to skip
upstream fixtures. The same glob applies to the base report and the proposed
change, including the reports that enforce the error gate. The default `*`
selects all paths, while Proselint uses its separate file list.

Website copy that lives in `messages/en.json` is not Markdown, so
`scripts/vale_messages.py` extracts it first:

```bash
python3 scripts/vale_messages.py extract messages/en.json
vale --output=JSON .vale-web/messages.md \
  | python3 scripts/vale_messages.py remap
```

`remap` rewrites each location back to the JSON key.

### Suppressing a rule

Prefer a narrow suppression when Vale is wrong.

```markdown
<!-- vale Portolan-Mechanics.Headings = NO -->
## A Heading That Must Keep Its Case
<!-- vale Portolan-Mechanics.Headings = YES -->
```

Turn a rule off for a whole file with `<!-- vale RuleName = NO -->` at the top.
Turn every rule off with `<!-- vale off -->`.

A comment toggle works on a local style only. Vale ignores it for a rule from a
package, such as `ai-tells` or `Google`. Suppress one of those with a path
section in `.vale.ini`, and put the reason in a comment above the section.

Do not suppress a finding only to make the check pass.

### Two traps

A term listed in `styles/config/vocabularies/Portolan/accept.txt` is skipped by
every other check. Adding "Portolan" there silently disabled the rule that
reports "Portolan standard". Keep a word out of `accept.txt` when a rule must
match on it.

`BasedOnStyles` does not accumulate across glob sections. The most specific
match replaces the others. Every section in `.vale.ini` names each
style it needs.
