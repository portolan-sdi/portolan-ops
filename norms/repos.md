# Repo norms

Every active portolan-sdi repo uses the shared files and patterns in this document. The [setup-repo skill](../.claude/skills/setup-repo/SKILL.md) can set them up for you.

## Required files and structure

Every repo needs `LICENSE` with Apache-2.0, synced from ops. Write a `README.md` per repo following [prose.md](prose.md). Use the skeleton in [`templates/repo/`](../templates/repo/). Create an `AGENTS.md` file with the synced ops norms block at the top, then add repo-specific instructions below it. This is the only place for repo-specific agent rules.

Set up CI in `.github/workflows/` as a thin caller for your repo's family (see [ci.md](ci.md)). Copy `.github/dependabot.yml` from [`templates/repo/`](../templates/repo/). Copy `.github/workflows/repo-checks.yml` from [`ci/repo-checks.yml`](../ci/repo-checks.yml). Copy `zizmor.yml` from [`templates/repo/`](../templates/repo/).

The `CLAUDE.md` file contains one import line, synced from [`templates/repo/`](../templates/repo/). Claude Code does not read `AGENTS.md`, so this file acts as a bridge. Do not add anything else to it. Sync will overwrite it, so any additional content gets lost.

Issue forms must have required fields, and blank issues must be off. A ticket then opens with a reproduction or a stated way to confirm it done. See [AGENTS.md](../AGENTS.md#pull-requests-and-issues) for the issue form requirements.

Do not copy community health files into each repo. Code of conduct, contributing guide, security policy, issue and PR templates should live in [`policies/`](../policies/) and [`templates/`](../templates/) here and sync to the org [`.github`](https://github.com/portolan-sdi/.github) repo. GitHub applies these files automatically. Add a repo-local copy only if the repo needs to override the org default.

## License

Use Apache-2.0 for all repos. portolan-browser and portolan-nl-demo use ISC for upstream code, which they took from the stac-browser fork. The license for new code in those repos remains an open decision, so both repos remain ISC for now.

## Naming

Repo names should be lowercase and hyphenated. Prefix org tools with `portolan-` (like portolan-registry). Prefix STAC extensions with `stac-` (like stac-partition-extension).

Do not commit binaries to git. Put versioned assets such as brand logos and fonts in ops' `brand/`. Everything else goes to object storage or Drive.

Archive repos instead of deleting them. Remove archived repos from the org profile.

## Releases and commits

Enforce Conventional Commits using the commitizen hook from the synced `.pre-commit-config.yaml`. Install hooks with `--hook-type commit-msg` alongside the other stages. Repos that publish a package should configure the bump in `[tool.commitizen]` with `tag_format = "v$version"`. This repo has a `.cz.toml` with the format check alone, because it releases CI by moving a tag rather than by bumping a version.

Use squash-merge for pull requests so the PR title becomes the commit message.

Python packages should release via bump-commit-triggered workflows with PyPI trusted publishing. Look at portolan-cli's release setup as the reference implementation.

STAC extensions should publish versioned JSON schemas to GitHub Pages on release.

## Issue labels and milestones

Issue tracking works only if a query means the same thing in every repo. The
label set and milestone names are fixed. Each issue goes on the
[Portolan Releases](https://github.com/orgs/portolan-sdi/projects/1) board.
A workflow enforces these rules. Whoever triages decides what matters.

### Labels

Each issue needs exactly one type label. Issue forms apply it, so an issue
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

`urgent` is the only priority signal, and a person applies it by hand. There is no
P0 through P3 ladder, because a ladder invites argument about rungs. An issue
is either the thing to drop everything for or it is not.

Some repos add a label of their own. portolan-registry adds
`catalog-feedback`. portolan-data adds `dataset`. portolan-spec adds
`schemas`, `spec-sync`, and `no-validator-change`. portolan-cli adds
`nightly-network-failure`.

Anything else is removed automatically, with a comment saying what went. To
add a label, change
[`issue-governance/allowed-labels.json`](../issue-governance/allowed-labels.json)
and update this table in the same pull request. A label created in a repo and
left out of that file does not survive the next issue event, and nothing warns
whoever created it, so run
[`scripts/check_label_config.py`](../scripts/check_label_config.py) after
adding a label anywhere. It reports any repo whose labels the set would strip.

### Project status

A board item has one of three statuses.

| Status | Meaning |
| --- | --- |
| `Ready` | The work can start |
| `In progress` | Work has started |
| `Done` | Work is complete |

New issues and human pull requests enter as `Ready`. The board has no backlog
status. An item that is not ready does not belong on the releases board.

### Milestones

Milestones mark when the work is needed, not how large it is. An issue can have
no milestone or one of these two:

| Milestone | Due | Meaning |
| --- | --- | --- |
| `v1.0` | 2026-12-30 | Required for 1.0 |
| `Post-v1.0` | none | Wanted, and not blocking 1.0 |

The workflow removes any other milestone from an issue. Closed per-version
milestones in portolan-cli, such as `v0.7.0`, remain closed as release history.

### The enforcement workflow

[`reusable-issue-governance.yml`](../.github/workflows/reusable-issue-governance.yml)
holds the rules, and [`scripts/issue_governance.py`](../scripts/issue_governance.py)
carries the two that touch the issue itself. Every repo with issues enabled
runs a caller synced from [`ci/issue-governance.yml`](../ci/issue-governance.yml),
pinned to `@v1` like the other shared workflows.
It runs when an issue opens, reopens, transfers, changes, or receives a milestone. It
adds the issue to the project board, sets its initial status to `Ready`, and
strips labels or milestones outside the sets above.

The workflow adds no type label, never touches `urgent`, and does not comment about a missing label.

The board write needs more reach than `GITHUB_TOKEN` has, so it requests a token
from the `portolan-ops-sync` app and needs `OPS_SYNC_APP_CLIENT_ID` and
`OPS_SYNC_APP_KEY` visible as organization secrets. Without them the label and
milestone rules still run and the board step logs a warning.

## The pull request board

Every pull request a person opens goes on the same
[Portolan Releases](https://github.com/orgs/portolan-sdi/projects/1) board as
the issues. One rule applies. The workflow leaves the milestone and the labels on a pull
request alone, because the review itself already records the state that matters.

Bot pull requests stay off the board. Dependabot, the ops sync app, and the
registry bot open work that merges on its own checks, so a row for it adds
noise. The workflow tests the author type that GitHub reports on the event,
not a list of names, so a new bot needs no change.

[`reusable-pr-board.yml`](../.github/workflows/reusable-pr-board.yml) holds the
rule. Every active repo runs a caller synced from
[`ci/pr-board.yml`](../ci/pr-board.yml), pinned to `@v1` like the other shared
workflows. It runs when somebody opens or reopens a pull request.

The caller uses `pull_request_target` rather than `pull_request`. A fork pull
request runs `pull_request` without the org secret, so the board add fails for
exactly the outside contributor who most needs tracking. The risk that comes
with `pull_request_target` is a checkout of the contributor's branch. This
workflow checks out nothing and runs no code from the pull request. It reads
the author type and the pull request number, and calls one API. Both callers
carry a `zizmor: ignore[dangerous-triggers]` comment that records this.

The board write needs more reach than `GITHUB_TOKEN` has, so it requests a token
from the `portolan-ops-sync` app and needs `OPS_SYNC_APP_CLIENT_ID` and
`OPS_SYNC_APP_KEY` visible as organization secrets. Without them the run logs
a warning and adds nothing.

The workflow ignores a pull request that was open before it existed. Run
[`scripts/backfill_pr_board.py`](../scripts/backfill_pr_board.py) to add those,
and to repair the board after a run that failed. It reports what it would add
and changes nothing until you pass `--apply`. The add is idempotent, so a
second run costs nothing.

## Recording decisions

Org-wide decisions should go in this file or in an issue in portolan-ops linked from here.

Repo-specific architecture decisions should go in ADRs kept in the repo. portolan-cli's `context/shared/adr/` is the reference pattern.
