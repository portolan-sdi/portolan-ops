# Docs norms

How documentation is written and organized across portolan-sdi repos.

## Reference models (mandatory for agents)

Two sources govern how we build docs, READMEs especially. Agents MUST consult both before writing or restructuring documentation in any org repo; humans should too.

**[obstore](https://github.com/developmentseed/obstore) — the exemplar.** The target for shape and register. Before drafting, fetch its README and docs layout and match:

- What the landing page covers, and in what order: what it is, why it exists, install, a minimal working example, links out to deeper docs.
- How the work divides across layers: README for orientation and quick-start, docs site for depth, generated API reference for completeness. No layer restates another.
- How much each section says. obstore's README earns its length with concrete claims and runnable code, not feature adjectives.

**[scaffold-docs-skill](https://github.com/dbreunig/scaffold-docs-skill) — the method.** Draft top-down in layers, with review between each:

1. Section structure (what sections exist, what each is for)
2. Headers
3. Topic sentences
4. Full paragraphs

Do not emit a finished docs page in one pass; each layer is a checkpoint for human review. Our [STYLE.md](../STYLE.md) is adapted from this skill's prose reference and applies at every layer.

Drafting a README from a generic template, or from memory of what READMEs usually look like, is a norms violation.

## Prose

Every doc follows [STYLE.md](../STYLE.md). Public-facing docs (anything a user reads on the website or in a README) also follow [VOICE.md](../VOICE.md). The short version: calm, plain, definite. Show behavior, don't praise it. No filler, no hype adjectives, no victory-lap closings.

## Structure

- **README.md** answers, in order: what this is, how to install or use it in under a minute, where the full docs are. Keep it short enough to read in one sitting; depth goes in the docs site.
- **Python repos** use mkdocs-material, built strict in CI (`mkdocs build --strict`), deployed to GitHub Pages. Contributing docs live in `docs/contributing.md` and are linked (not duplicated) from the README.
- **STAC extensions** follow the upstream stac-extensions README layout: overview, fields table, examples, `CHANGELOG.md`.
- **The spec** lives in [portolan-spec](https://github.com/portolan-sdi/portolan-spec), the ground truth for the standard. Docs in implementation repos link to it rather than restating normative language.

## Conventions

- Sentence-case headlines. Title case only for proper nouns and product names.
- No emoji in docs or headlines (mono symbols like `→` are fine).
- "Portolan" refers to the standard. Name a specific tool (`portolan-cli`, the browser) when you mean the tool.
- Command examples must be real: copy-pasteable and tested against the shipped CLI. The org profile once advertised a `portolan ingest` command that didn't exist; that class of drift is what this rule prevents.
- Dates absolute (`2026-07-24`), never relative ("last month").
- Link to canonical homes rather than restating them: URLs from [`copy/urls.md`](../copy/urls.md), policies from [`policies/`](../policies/), brand values from [`brand/brand.json`](../brand/brand.json).
