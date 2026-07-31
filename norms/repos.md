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

## Recording decisions

Org-wide decisions should go in this file or in an issue in portolan-ops linked from here.

Repo-specific architecture decisions should go in ADRs kept in the repo. portolan-cli's `context/shared/adr/` is the reference pattern.
