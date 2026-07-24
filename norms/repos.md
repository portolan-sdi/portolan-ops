# Repo norms

What every active portolan-sdi repo carries, and how repos behave. The [setup-repo skill](../.claude/skills/setup-repo/SKILL.md) scaffolds all of this for a new repo.

## Required files

| File | Source |
|---|---|
| `LICENSE` | Apache-2.0, synced from ops. No exceptions for new repos (see [License](#license) for the two fork exceptions). |
| `README.md` | Written per repo, following [STYLE.md](../STYLE.md). Skeleton in [`templates/repo/`](../templates/repo/). |
| `AGENTS.md` | Ops pointer block (synced) + repo-specific instructions below it. |
| `.github/workflows/` | A thin caller for the repo's CI family (see [ci.md](ci.md)). |
| `.github/dependabot.yml` | From [`templates/repo/`](../templates/repo/). |

Community health files (code of conduct, contributing guide, security policy, issue and PR templates) are **not** copied into each repo. They live in [`policies/`](../policies/) and [`templates/`](../templates/) here and sync to the org [`.github`](https://github.com/portolan-sdi/.github) repo, which GitHub applies to every repo automatically. Add a repo-local copy only when the repo needs to override the org default.

## License

Apache-2.0 everywhere. Two documented exceptions, inherited from the upstream stac-browser fork: **portolan-browser** and **portolan-nl-demo** carry ISC for upstream code. Resolution for new code in those repos is an open decision; until it's made, they keep ISC and this paragraph is the record of why.

## Naming and structure

- Repo names: lowercase, hyphenated, `portolan-` prefix for org tools (`portolan-registry`), `stac-` prefix for STAC extensions (`stac-partition-extension`).
- Keep binaries out of git. Assets that must be versioned (brand logos, fonts) live in ops' `brand/`; everything else goes to object storage or Drive.
- Archive repos instead of deleting them, and remove archived repos from the org profile.

## Releases and commits

- Conventional Commits, enforced where tooling exists (commitizen in Python repos).
- Squash-merge; PR title becomes the commit message.
- Python packages release via bump-commit-triggered workflows with PyPI trusted publishing (see portolan-cli's release setup as the reference).
- STAC extensions publish versioned JSON schemas to GitHub Pages on release.

## Where decisions get recorded

- Org-wide decisions: this file, or an issue in portolan-ops linked from here.
- Repo-specific architecture decisions: ADRs in the repo (portolan-cli's `context/shared/adr/` is the reference pattern).
