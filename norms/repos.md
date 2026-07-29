# Repo norms

What every active portolan-sdi repo carries, and how repos behave. The [setup-repo skill](../.claude/skills/setup-repo/SKILL.md) scaffolds all of this for a new repo.

## Required files

| File | Source |
|---|---|
| `LICENSE` | Apache-2.0, synced from ops. No exceptions for new repos (see [License](#license) for the two fork exceptions). |
| `README.md` | Written per repo, following [VOICE.md](../VOICE.md). Skeleton in [`templates/repo/`](../templates/repo/). |
| `AGENTS.md` | Ops norms block (synced) + repo-specific instructions below it. The only home for repo-specific agent rules. |
| `.github/workflows/` | A thin caller for the repo's CI family (see [ci.md](ci.md)). |
| `.github/dependabot.yml` | From [`templates/repo/`](../templates/repo/). |
| `CLAUDE.md` | One import line, synced from [`templates/repo/`](../templates/repo/). Claude Code never reads `AGENTS.md`, so this file is the bridge. Put nothing else in it. |
| `.github/workflows/repo-checks.yml` | The repo checks caller, synced from [`ci/repo-checks.yml`](../ci/repo-checks.yml). |
| `zizmor.yml` | Synced from [`templates/repo/`](../templates/repo/). Travels with the repo checks caller, which names a tag. |

Issue forms carry required fields, and blank issues are off, so every ticket arrives with a reproduction or a stated way to confirm it done. The budget and the evidence rule are in [AGENTS.md](../AGENTS.md#writing-issues-and-pull-requests).

The two agent files divide as follows. `AGENTS.md` is canonical and holds everything: the synced org norms, then whatever the repo needs below the marker. `CLAUDE.md` exists because Claude Code does not read `AGENTS.md`, and holds the import that bridges them. Sync overwrites `CLAUDE.md`, so content kept there is lost on the next run. [`norms/ci.md`](ci.md#why-agentsmd-and-claudemd-both-exist) has the reasoning, and the `layout` check enforces it.

Community health files (code of conduct, contributing guide, security policy, issue and PR templates) are **not** copied into each repo. They live in [`policies/`](../policies/) and [`templates/`](../templates/) here and sync to the org [`.github`](https://github.com/portolan-sdi/.github) repo, which GitHub applies to every repo automatically. Add a repo-local copy only when the repo needs to override the org default.

## License

Apache-2.0 everywhere. Two documented exceptions, inherited from the upstream stac-browser fork: **portolan-browser** and **portolan-nl-demo** carry ISC for upstream code. Resolution for new code in those repos is an open decision. Until it's made, they keep ISC, and this paragraph is the record of why.

## Naming and structure

- Repo names: lowercase, hyphenated, `portolan-` prefix for org tools (`portolan-registry`), `stac-` prefix for STAC extensions (`stac-partition-extension`).
- Keep binaries out of git. Assets that must be versioned (brand logos, fonts) live in ops' `brand/`. Everything else goes to object storage or Drive.
- Archive repos instead of deleting them, and remove archived repos from the org profile.

## Releases and commits

- Conventional Commits, enforced by the commitizen hook the synced `.pre-commit-config.yaml` ships. It runs at commit-msg, so install hooks with `--hook-type commit-msg` alongside the other two stages. Repos that publish a package configure the bump in `[tool.commitizen]` with `tag_format = "v$version"`; this repo carries a `.cz.toml` with the format check alone, since it ships CI by moving a tag.
- Squash-merge, so the PR title becomes the commit message.
- Python packages release via bump-commit-triggered workflows with PyPI trusted publishing (see portolan-cli's release setup as the reference).
- STAC extensions publish versioned JSON schemas to GitHub Pages on release.

## Where decisions get recorded

- Org-wide decisions: this file, or an issue in portolan-ops linked from here.
- Repo-specific architecture decisions: ADRs in the repo (portolan-cli's `context/shared/adr/` is the reference pattern).
