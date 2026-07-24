# Docs norms

How documentation is written and organized across portolan-sdi repos.

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
