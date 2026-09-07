# Docs norms

Documentation is written and organized the same way across portolan-sdi repos. Read this before you write a README or restructure a docs site.

## Reference models

LLMs generate and read most docs. A human who opens a page must still understand quickly what the tool is and what it does. Docs have to serve both readers, and that requirement shapes everything we build.

To keep docs maintainable and resistant to drift, we prioritize testable and auto-generated docs whenever possible. Handwritten prose gets written once and then rots. Docs that rebuild themselves match the code they describe.

Humans are responsible for identifying which docs are primarily read by humans and which by agents. The README is the main human surface. Make sure a person can read the human-facing docs and use them. Be kind to maintainers who have to update them and users who have to read them.

These two sources govern how we build docs, READMEs above all. Agents must consult both before writing or restructuring documentation in any org repo. Humans should too.

[obstore](https://github.com/developmentseed/obstore) is the exemplar for shape and register. Fetch its README and docs layout before drafting and match its structure. The landing page covers what the tool is and why it exists. It then shows how to install the tool. A minimal working example follows, with links to deeper docs. Work divides across three layers. The README orients the reader and gives the quick start. The docs site gives depth. The generated API reference gives completeness. No layer restates another. Each section justifies its length with concrete claims and runnable code, not feature adjectives. The generated parts (API docs) and the hand-maintained parts (README, guides) differ on purpose.

[scaffold-docs-skill](https://github.com/dbreunig/scaffold-docs-skill) documents the method. Draft top-down in layers, with review between each layer. Write the section structure first. Add the headers, then the topic sentences, then the full paragraphs. Do not emit a finished page in one pass. Each layer is a checkpoint for human review. [prose.md](prose.md) applies at every layer. Building docs this way makes them easier for LLMs to parse and regenerate, and easier for humans to spot where something has drifted.

Drafting a README from a generic template or from memory of what READMEs usually look like is a norms violation.

## Writing process

Every doc follows [prose.md](prose.md). The prose is calm and plain. It states decisions without hesitation. Show behavior instead of praise. Cut filler, hype adjectives, and victory-lap closings.

Read the completed page before publication. Check its claims, examples, structure, and tone.

## README and structure

The README answers three questions in order. It says what the tool is. It shows how to install or use the tool in under a minute. It points to the full docs. A reader should finish it in one sitting, and depth goes in the docs site.

Python repos use mkdocs-material, built strict in CI (`mkdocs build --strict`), and deployed to GitHub Pages. Contributing docs live in `docs/contributing.md` and are linked (not duplicated) from the README.

STAC extensions follow the upstream stac-extensions README layout: overview, fields table, examples, and `CHANGELOG.md`.

[portolan-spec](https://github.com/portolan-sdi/portolan-spec) holds the specification, the ground truth for the standard. Docs in implementation repos link to it rather than restating normative language.

## Writing conventions

Use sentence-case headlines. `Portolan-Mechanics.Headings` reports the exceptions.

Do not use emoji in docs or headlines. Mono symbols like `→` are fine.

"Portolan" refers to the standard. Name a specific tool (portolan-cli, the browser) when you mean the tool.

Command examples must be real, copy-pasteable, and tested against the released CLI. An org profile once advertised a `portolan ingest` command that did not exist.

Use absolute dates (`2026-07-24`), never relative ones ("last month").

Link to canonical homes rather than restating them. Pull URLs from [`copy/urls.md`](../copy/urls.md), policies from [`policies/`](../policies/), and brand values from [`brand/brand.json`](../brand/brand.json).
