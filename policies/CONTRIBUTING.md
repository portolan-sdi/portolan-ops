# Contributing to Portolan

Thanks for contributing. This guide covers every repo in the portolan-sdi organization. A repo may add its own instructions in its `CONTRIBUTING.md` or docs, and those add to this guide rather than replacing it.

## The quality bar

Much of the code in this organization is written with AI agents, so the bar is set by **automation, not reviewer attention**. CI enforces the quality gates, and a PR earns trust by turning them green. AI-assisted contributions are welcome under our [AI policy](AI_POLICY.md), which requires a human in the loop who has read, reviewed, and understood the change before asking for review.

Before you ask for review, a PR should clear this bar:

- **Tests exercise real behavior.** New or changed product code ships with tests. Prefer a reproducible failing test as the starting point for a bug fix.
- **All CI is green.** Green means green. Nothing merges red, and hooks are never bypassed.
- **A human can explain it.** You can answer questions about any line in the diff.
- **Docs updated.** User-facing behavior changes come with doc changes.
- **The PR description is yours, and it is short.** Write it in your own words, capped at 200 words outside code blocks with no section over six lines. CI fails the check when a body runs long, and a verbose generated description gets the PR closed (see the AI policy).
- **Verification is pasted, not claimed.** Anything that changes behavior shows the command, its output, and the data it read: a URL or a catalog path. Green CI is not verification. Docs, chore, and CI-only changes tick the waiver checkbox in the template instead.

## Conventions

- **License.** Every contribution is Apache-2.0. You must have the right to contribute the code under that license.
- **Commits.** [Conventional Commits](https://www.conventionalcommits.org/). PRs are squash-merged, so the PR title becomes the commit message. Write it in conventional form (`feat(scope): ...`, `fix(scope): ...`).
- **Branches.** `feature/description`, `fix/description`, `docs/description`, `refactor/description`.
- **Prose.** Written artifacts follow the [Portolan voice](https://github.com/portolan-sdi/portolan-ops/blob/main/VOICE.md).

## Where things go

- **Spec changes.** The [portolan-spec](https://github.com/portolan-sdi/portolan-spec) repo is the ground truth for the Portolan standard. Open spec PRs there. Implementations (the CLI, the validator, the registry) follow the spec, never the reverse.
- **Org-wide files.** LICENSE, this guide, the code of conduct, CI templates, and branding are synced from [portolan-ops](https://github.com/portolan-sdi/portolan-ops). To change one, open a PR there, not in the repo that received the synced copy.
- **Cross-repo work.** Work with no obvious home gets an issue in [portolan-ops](https://github.com/portolan-sdi/portolan-ops/issues).

## Community

- Questions and discussion: the [Portolan Google Group](https://groups.google.com/g/portolan) and the [Portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in the Cloud-Native Geo Slack.
- Conduct: the [code of conduct](CODE_OF_CONDUCT.md) applies in all community spaces.
- Security issues: report privately per the [security policy](SECURITY.md), never in a public issue.
