# Portolan agent norms

Canonical rules for AI agents working in any portolan-sdi repo. Downstream repos carry this text verbatim as a synced block at the top of their own `AGENTS.md`, so the rules are in context rather than a link away. Repo-specific instructions live below that block, and when one conflicts with the block, the repo-specific rule wins in that repo.

Claude Code does not read `AGENTS.md`. Each repo therefore carries a one-line `CLAUDE.md` that imports it. Put repo-specific instructions in `AGENTS.md`, never in `CLAUDE.md`, which the sync overwrites.

## Ground rules

- The [portolan-spec](https://github.com/portolan-sdi/portolan-spec) repo is the ground truth for the Portolan standard. The CLI, the validator, the registry, and every other tool implement the spec and are downstream of it. Never describe the CLI as the source of truth for the spec. Propose spec changes in portolan-spec.
- Before documenting any command, flag, or API, verify it exists in the shipped tool. A fabricated example outlives the session that wrote it.
- License is Apache-2.0 in every repo except portolan-browser and portolan-nl-demo, which are ISC forks (recorded in [norms/repos.md](norms/repos.md)). Never introduce code under another license without a human decision recorded there.
- Never bypass pre-commit hooks or CI gates. Green means green.
- Conventional commits. Squash-merge makes the pull request title the commit message, so write the title in conventional form.

## Pull requests and issues

A reviewer should finish a pull request body in under a minute and know what changed, why, and that it works. CI lints every body on each push and edit. The contract it checks:

- The sections `## What this changes`, `## Why`, and `## Verification` exist and are filled in.
- 200 words outside code blocks, no section longer than six lines. Fenced blocks are uncapped, so evidence never competes with the budget.
- The prose references the issue the change resolves, as `#N` or its URL.
- Verification pastes the command you ran and its output in a fenced block under `## Verification`, and names the data it read: a URL or a catalog path.
- A change that alters no behavior ticks the waiver checkbox instead. Keep its wording intact, since the check matches the phrase "does not alter behavior" outside code blocks.

Weak evidence proves a command exits zero. Strong evidence re-runs the reproduction from the linked issue against real data and shows the reported behavior changed. A wall of `pytest` output is weak. The failing command from the ticket, now succeeding against the same catalog, is strong.

Issues carry the same budget. A bug report needs the reproduction that triggered it, a feature request needs the transcript showing where current behavior falls short, and a task needs the command that will prove it done. Every repo runs the org issue forms, and blank issues are off. The check fails the pull request; on an issue it applies `needs-rewrite` and comments once. Dependabot is exempt, since its body is generated release notes that it restates on every rebase.

## Documentation

Agents writing or restructuring documentation follow the two sources named in [norms/docs.md](norms/docs.md): [obstore](https://github.com/developmentseed/obstore) is the exemplar for shape and layering, and [scaffold-docs-skill](https://github.com/dbreunig/scaffold-docs-skill) is the method, drafting top-down in layers with human review between them. Do not draft a README from a generic template or from memory of what READMEs look like.

Three rules apply to every docs change: sentence-case headings without emoji, absolute dates ("in July 2026", never "recently"), and command examples that were actually run against the shipped tool.

## Voice and messaging

Every written artifact follows [VOICE.md](VOICE.md): READMEs, PR and issue bodies, commit message bodies, docs, and lasting code comments. Apply it while drafting, not as a cleanup pass. The rules that catch the most agent prose:

- Write flat, declarative sentences, mostly under twenty words, and vary their texture.
- Every claim needs a mechanism or a checkable fact near it. Praise without proof gets cut.
- No mirrored phrases, no rule of three, no aphoristic headers. Plain and descriptive, every time.
- Cut hype adjectives such as powerful or seamless. Keep functional ones such as standardized or cloud-optimized.
- Scope claims to what stays true. Before writing an absolute, ask what future fact would falsify it.
- Portolan is AI-ready, not AI-first. Agents are the means, people are the ends.

How Portolan is described comes from [copy/messaging.md](copy/messaging.md) alone. The one-liner: "Publish geospatial data as plain files in your own storage, connected into a searchable network." Standard is the governing noun, and "ecosystem" describes the result, never the thing. The parts are the standard, the validator, the CLI, the registry, and the browser. Name people and agents together.

Before drafting substantial public copy such as a README, a docs page, or an announcement, fetch and read [VOICE.md](VOICE.md) and [copy/messaging.md](copy/messaging.md) in full. If you cannot fetch them, say so and stop rather than writing from memory.

## Org-wide facts

- The canonical homepage is https://www.portolan-sdi.org/. Canonical URLs live in [copy/urls.md](copy/urls.md). Do not hardcode variants.
- Community discussion happens in the [Portolan Google Group](https://groups.google.com/g/portolan) and the [Portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in the Cloud-Native Geo Slack. Planning lives in [org-level GitHub projects](https://github.com/orgs/portolan-sdi/projects/1).

## Contribution rules

- The [AI policy](policies/AI_POLICY.md) applies to every contribution. An agent may draft the diff and the pull request body. A human must read, understand, and approve both before review is requested. Agents never open PRs, post comments, or take action in shared spaces without human approval.
- Follow the [contributing guide](policies/CONTRIBUTING.md) and the [code of conduct](policies/CODE_OF_CONDUCT.md).

## Sync discipline

- Files between `ops-sync` markers are synced from [portolan-ops](https://github.com/portolan-sdi/portolan-ops) and overwritten on every sync run. To change one, change it in portolan-ops, never in place.
- One canonical home per fact. If a value such as a color, a URL, or a policy line exists in portolan-ops, link to it rather than copying it.
