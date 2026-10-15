# Docs norms

Docs are written and organized consistently across all Portolan repos. Read this when writing or restructuring any project documentation.

Build docs with Zensical and deploy to GitHub pages. Most of our docs are heavily LLM-generated. To avoid drift, bloat, and AI slop, we try to enforce the following norms.

1. Human readers must have a quick entrypoint to understanding what a tool is and does. Usually this is the README plus one or two real world tutorials. We really like Drew Bruening's [scaffold-docs-skill](https://github.com/dbreunig/scaffold-docs-skill) for this.
2. READMEs must be concise and human-written. The [Portolan CLI](https://github.com/portolan-sdi/portolan-cli) is a good example.
3. Pretty much all documentation must be tested and/or auto-generated to make sure that it doesn't drift. Be on guard against agents and their tendency to append a bunch of BS without checking if it's true/helpful.
4. Be concise. Even in docstrings.
5. Ruthlessly deduplicate. Use pointers/symlinks whenever possible, and watch out for agents copy-and-pasting across sections.
6. Humans and agents must follow the prose guide laid out in [prose.md](prose.md) and the Vale hook. Humans and agents are strongly encouraged to use the [Google Developer voice guide](https://developers.google.com/style/highlights) for tutorials and guides. Humans are warned that (at least as of October 2026) Claude Opus and Fable write like crap, and docs often benefit from a cleanup pass with Codex.
7. Do not accumulate drift-prone pseudo-documentation, like ADRs written entirely by agents. It's hard to maintain and tends to just cause confusion. Our goal is an absolute minimum of text that is not either human-maintained (e.g., the spec) or tested/auto-generated (e.g., tutorials, docstrings).
8. Seriously, be concise.
