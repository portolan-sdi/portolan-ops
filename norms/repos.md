# Repo norms

Every active portolan-sdi repo follows these conventions. The [setup-repo skill](../.claude/skills/setup-repo/SKILL.md) can create the required files.

## Required files and structure

Use the [repo templates](../templates/repo/) to set up these files:

| File | Requirement |
|---|---|
| `LICENSE` | Apache-2.0, synced from ops, except as noted under [License](#license) |
| `README.md` | Repo-specific documentation following [prose.md](prose.md) |
| `AGENTS.md` | Synced ops norms block at the top, followed by repo-specific agent instructions |
| `CLAUDE.md` | One synced import line pointing to `AGENTS.md` |
| `.github/workflows/ci.yml` | Thin caller for the repo's workflow family; see [ci.md](ci.md) |
| `.github/dependabot.yml` | Copied from the repo templates |
| `.github/workflows/repo-checks.yml` | Copied from [`ci/repo-checks.yml`](../ci/repo-checks.yml) |
| `zizmor.yml` | Copied from the repo templates |

Keep repo-specific agent rules in `AGENTS.md`. Claude Code reads them through the import in `CLAUDE.md`. Sync overwrites `CLAUDE.md`, so additional content there will be lost.

Issue forms must require enough information to reproduce a problem or confirm completion, with blank issues disabled. See the [issue form requirements](../AGENTS.md#pull-requests-and-issues).

Community health files live in [`policies/`](../policies/) and [`templates/`](../templates/) and sync to the organization's [`.github` repo](https://github.com/portolan-sdi/.github). GitHub applies the code of conduct, contributing guide, security policy, and issue and pull request templates automatically. Add repo-local copies only when a repo needs to override an organization default.

## License

Use Apache-2.0 except in portolan-browser and portolan-nl-demo. Those repos inherited ISC-licensed code from the stac-browser fork and remain ISC while the license for new code is undecided.

## Naming and assets

Use lowercase, hyphenated repo names. Prefix organization tools with `portolan-`, as in `portolan-registry`, and STAC extensions with `stac-`, as in `stac-partition-extension`.

Keep versioned assets such as logos and fonts in portolan-ops' `brand/` directory. Other binaries belong in object storage or Drive. Archive retired repos and remove them from the organization profile.

## Releases and commits

Enforce [Conventional Commits](https://www.conventionalcommits.org) with the Commitizen hook in the synced `.pre-commit-config.yaml`. Include `--hook-type commit-msg` when installing hooks, and squash-merge pull requests so their titles become the commit messages.

Repos that publish packages should configure version bumps in `[tool.commitizen]` with `tag_format = "v$version"`. portolan-ops uses `.cz.toml` for commit-message checks because it releases CI by moving a tag.

Python packages should use bump-commit-triggered release workflows with PyPI trusted publishing, following portolan-cli's setup. STAC extensions should publish versioned JSON schemas to GitHub Pages on release.

## Issue labels and milestones

Use consistent labels and milestones so queries work across repos. Every issue goes on the [Portolan Releases board](https://github.com/orgs/portolan-sdi/projects/1). Automation enforces the allowed labels and milestones; the person who triages the issue decides its importance.

### Labels

Each issue needs exactly one type label, applied automatically by its issue form:

| Label | Use it for |
|---|---|
| `bug` | Behavior that violates the documented contract |
| `enhancement` | A new capability or a change to existing behavior |
| `documentation` | Documentation, README, or spec prose |
| `task` | Chores, refactoring, CI, or maintenance |

These additional labels are optional and available in every repo:

| Label | Meaning |
|---|---|
| `urgent` | Blocks a release or production and needs immediate attention |
| `blocked` | Waiting on another issue or an outside party |
| `needs-rewrite` | Body exceeds the word budget or lacks evidence |
| `automated` | Opened by a CI workflow |
| `good first issue`, `help wanted` | Invitations to contributors |
| `question`, `duplicate`, `invalid`, `wontfix` | Triage outcomes |
| `dependencies`, `github_actions` | Dependabot labels |

`urgent` is the only priority label and requires a person's judgment. Some repos also use these specialized labels:

| Repo | Labels |
|---|---|
| portolan-registry | `catalog-feedback` |
| portolan-data | `dataset` |
| portolan-spec | `schemas`, `spec-sync`, `no-validator-change` |
| portolan-cli | `nightly-network-failure` |

Automation removes unapproved labels from issues and comments with the removed names. To add a label, update [`issue-governance/allowed-labels.json`](../issue-governance/allowed-labels.json) and this document in the same pull request, then run [`scripts/check_label_config.py`](../scripts/check_label_config.py). The script reports repo labels that enforcement would remove. Labels created only in GitHub will be removed from issues on their next event, without warning the label's creator.

### Project status

The board uses three statuses:

| Status | Meaning |
|---|---|
| `Ready` | Work can start |
| `In progress` | Work has started |
| `Done` | Work is complete |

New issues and human-authored pull requests enter as `Ready`. Keep items off the releases board until they are ready to start.

### Milestones

Milestones record when work is needed. An issue can have no milestone or one of these:

| Milestone | Due date | Meaning |
|---|---|---|
| `v1.0` | 2026-12-30 | Required for 1.0 |
| `Post-v1.0` | None | Wanted, but does not block 1.0 |

Automation removes other milestones from issues. Closed per-version milestones, such as portolan-cli's `v0.7.0`, remain as release history.

### Enforcement

[`reusable-issue-governance.yml`](../.github/workflows/reusable-issue-governance.yml) defines the workflow, and [`scripts/issue_governance.py`](../scripts/issue_governance.py) enforces label and milestone rules. Every repo with issues enabled receives a caller from [`ci/issue-governance.yml`](../ci/issue-governance.yml), pinned to `@v1`.

When an issue opens, reopens, transfers, changes, or receives a milestone, the workflow adds it to the board with an initial status of `Ready` and removes unapproved labels and milestones. Type labels remain the responsibility of issue forms and triage. The workflow leaves `urgent` unchanged and skips comments about missing labels.

Board updates require a `portolan-ops-sync` app token, using the organization secrets `OPS_SYNC_APP_CLIENT_ID` and `OPS_SYNC_APP_KEY`. If either is unavailable, the board step logs a warning while label and milestone enforcement continues.

## The pull request board

Human-authored pull requests go on the [Portolan Releases board](https://github.com/orgs/portolan-sdi/projects/1), with their existing labels and milestones preserved. Bot pull requests stay off the board because Dependabot, ops sync, and registry updates merge through their required checks. The workflow identifies bots through GitHub's author type, so new bots need no configuration change.

[`reusable-pr-board.yml`](../.github/workflows/reusable-pr-board.yml) defines the workflow. Every active repo receives a caller from [`ci/pr-board.yml`](../ci/pr-board.yml), pinned to `@v1`, which runs when a pull request opens or reopens.

The caller uses `pull_request_target` to access organization credentials for fork contributions. It reads the author type and pull request number and calls the API without checking out or running contributor code. Both board callers include a `zizmor: ignore[dangerous-triggers]` comment explaining this use.

Board updates require a `portolan-ops-sync` app token and the organization secrets `OPS_SYNC_APP_CLIENT_ID` and `OPS_SYNC_APP_KEY`. If either secret is unavailable, the workflow logs a warning and skips the update.

Use [`scripts/backfill_pr_board.py`](../scripts/backfill_pr_board.py) to add pull requests opened before the workflow was installed or repair missed updates. The script previews changes by default; pass `--apply` to make them. Repeated runs leave existing board entries unchanged.

## Recording decisions

Record organization-wide decisions here or in a portolan-ops issue linked from this document. Keep repo-specific architecture decisions in that repo's ADRs, following portolan-cli's `context/shared/adr/` pattern.