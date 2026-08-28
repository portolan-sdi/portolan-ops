# Repo norms

Every active portolan-sdi repo carries certain files and follows certain patterns. The [setup-repo skill](../.claude/skills/setup-repo/SKILL.md) can set them up for you.

## Required files and structure

Every repo carries `LICENSE` with Apache-2.0, synced from ops. Write a `README.md` per repo following [VOICE.md](../VOICE.md). Use the skeleton in [`templates/repo/`](../templates/repo/). Create an `AGENTS.md` file with the synced ops norms block at the top, then add repo-specific instructions below it. This is the only place for repo-specific agent rules.

Set up CI in `.github/workflows/` as a thin caller for your repo's family (see [ci.md](ci.md)). Copy `.github/dependabot.yml` from [`templates/repo/`](../templates/repo/). Copy `.github/workflows/repo-checks.yml` from [`ci/repo-checks.yml`](../ci/repo-checks.yml). Copy `zizmor.yml` from [`templates/repo/`](../templates/repo/).

The `CLAUDE.md` file holds one import line, synced from [`templates/repo/`](../templates/repo/). Claude Code does not read `AGENTS.md`, so this file acts as a bridge. Do not add anything else to it. Sync will overwrite it, so any additional content gets lost.

Issue forms must carry required fields and blank issues must be off. This ensures every ticket arrives with a reproduction or a stated way to confirm it done. See [AGENTS.md](../AGENTS.md#pull-requests-and-issues) for the issue form requirements.

Do not copy community health files into each repo. Code of conduct, contributing guide, security policy, issue and PR templates should live in [`policies/`](../policies/) and [`templates/`](../templates/) here and sync to the org [`.github`](https://github.com/portolan-sdi/.github) repo. GitHub applies these files automatically. Add a repo-local copy only if the repo needs to override the org default.

## License

Use Apache-2.0 for all repos. Two exceptions come from the upstream stac-browser fork. portolan-browser and portolan-nl-demo carry ISC for upstream code. The decision about what new code in those repos should carry remains open, so they stay ISC for now.

## Naming

Repo names should be lowercase and hyphenated. Prefix org tools with `portolan-` (like portolan-registry). Prefix STAC extensions with `stac-` (like stac-partition-extension).

Do not commit binaries to git. Assets that must be versioned, such as brand logos and fonts, should live in ops' `brand/`. Everything else goes to object storage or Drive.

Archive repos instead of deleting them. Remove archived repos from the org profile.

## Releases and commits

Enforce Conventional Commits using the commitizen hook from the synced `.pre-commit-config.yaml`. Install hooks with `--hook-type commit-msg` alongside the other stages. Repos that publish a package should configure the bump in `[tool.commitizen]` with `tag_format = "v$version"`. This repo carries a `.cz.toml` with the format check alone because it ships CI by moving a tag rather than releasing a version.

Use squash-merge for pull requests so the PR title becomes the commit message.

Python packages should release via bump-commit-triggered workflows with PyPI trusted publishing. Look at portolan-cli's release setup as the reference implementation.

STAC extensions should publish versioned JSON schemas to GitHub Pages on release.

## Issue labels and milestones

Issue tracking works only if a query means the same thing in every repo. So
the label set is fixed, every issue carries a milestone, and every issue sits
on the [Portolan Releases](https://github.com/orgs/portolan-sdi/projects/1)
board. A workflow enforces all three. What it cannot decide is what matters,
which stays with whoever triages.

### Labels

Every issue carries exactly one type label. Issue forms apply it, so an issue
opened through a form already has one.

| Label | Use it for |
| --- | --- |
| `bug` | Something behaves against its documented contract |
| `enhancement` | A new capability, or a change to existing behavior |
| `documentation` | Docs, README, or spec prose |
| `task` | Chore, refactor, CI, or maintenance work |

Beyond the type, these are available in every repo. All are optional.

| Label | Meaning |
| --- | --- |
| `urgent` | Drop everything. It blocks a release or production. |
| `blocked` | Waiting on another issue or an outside party |
| `needs-rewrite` | Body is over budget or missing evidence |
| `automated` | Opened by a CI workflow |
| `good first issue`, `help wanted` | Invitations to contributors |
| `question`, `duplicate`, `invalid`, `wontfix` | Triage outcomes |
| `dependencies`, `github_actions` | Dependabot's own labels |

`urgent` is the only priority signal, and only a person applies it. There is no
P0 through P3 ladder, because a ladder invites argument about rungs. An issue
is either the thing to drop everything for or it is not.

Four repos add a label of their own: `catalog-feedback` in portolan-registry,
`dataset` in portolan-data, `schemas`, `spec-sync`, and `no-validator-change`
in portolan-spec, and `nightly-network-failure` in portolan-cli.

Anything else is removed automatically, with a comment saying what went. To
add a label, change
[`issue-governance/allowed-labels.json`](../issue-governance/allowed-labels.json)
and update this table in the same pull request. A label created in a repo and
left out of that file does not survive the next issue event.

### Milestones

Every repo carries the same four milestones. They mark when the work is
needed, not how large it is.

| Milestone | Due | Meaning |
| --- | --- | --- |
| `Beta` | 2026-09-29 | Required for the beta release |
| `v1.0` | 2026-12-30 | Required for 1.0 |
| `Post-v1.0` | none | Wanted, and not blocking 1.0 |
| `Backlog` | none | Not yet scheduled |

A new issue with no milestone lands on `Backlog`, so nothing sits untracked
while it waits for triage. Moving it out of `Backlog` is a person's decision
and the workflow never reverses it. Closed per-version milestones in
portolan-cli, such as `v0.7.0`, stay closed as release history.

### The enforcement workflow

[`reusable-issue-governance.yml`](../.github/workflows/reusable-issue-governance.yml)
holds the rules, and [`scripts/issue_governance.py`](../scripts/issue_governance.py)
carries the two that touch the issue itself. Every repo with issues enabled
runs a caller synced from [`ci/issue-governance.yml`](../ci/issue-governance.yml),
pinned to `@v1` like the other shared workflows.
It runs when an issue is opened, edited, or labeled, and does three things:
adds the issue to the project board, sets `Backlog` when a newly opened issue
has no milestone, and strips labels outside the set above.

It leaves everything else alone. It adds no type label, never touches
`urgent`, does not comment about a missing label, and does not move a
milestone somebody already set.

The board write needs more reach than `GITHUB_TOKEN` has, so it mints a token
from the `portolan-ops-sync` app and needs `OPS_SYNC_APP_CLIENT_ID` and
`OPS_SYNC_APP_KEY` visible as organization secrets. Without them the label and
milestone rules still run and the board step logs a warning.

## Recording decisions

Org-wide decisions should go in this file or in an issue in portolan-ops linked from here.

Repo-specific architecture decisions should go in ADRs kept in the repo. portolan-cli's `context/shared/adr/` is the reference pattern.
