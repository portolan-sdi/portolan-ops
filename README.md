# portolan-ops

We build Portolan quickly, mostly with agents. This repo keeps that work consistent. Anything that should be standard across repos, such as CI logic, docs, norms, branding, and policies, lives here and propagates downstream. Cross-repo work is tracked here too, so [open an issue](https://github.com/portolan-sdi/portolan-ops/issues/new) for anything without a repo of its own.

## What you can do

- **Stand up a new repo.** Run the [`setup-repo`](.claude/skills/setup-repo) skill from inside it. It applies org standards and registers the repo in [`sync/manifest.yml`](sync/manifest.yml).
- **Change a shared file everywhere.** Edit it here (for example [VOICE.md](VOICE.md), a policy, or an issue template) and merge. Sync carries it to every repo that uses it.
- **Change shared CI.** Edit the reusable workflow in [`.github/workflows/`](.github/workflows/), confirm `ci-selftest.yml` passed, move the `v1` tag.
- **Add an existing repo to sync.** Add its entries to [`sync/manifest.yml`](sync/manifest.yml) and push.

## How changes propagate

When a change merges to `main` here, the sync workflow opens pull requests in all affected repos, as defined in [`sync/manifest.yml`](sync/manifest.yml). Most of those pull requests merge automatically once the repo's own CI passes. The rest must be merged by hand.

There are two exceptions. First, two files are generated from a source, and CI fails if you edit the source without regenerating:

```bash
python3 scripts/build_agents_block.py   # after editing AGENTS.md
python3 brand/emit_css.py --write       # after editing brand/brand.json
```

Second, shared CI workflows don't propagate on merge. Downstream repos run them directly from this repo, pinned to the `v1` tag, so a CI change reaches nobody until you move the tag. [norms/ci.md](norms/ci.md#releasing-a-ci-change) has the commands.

Before merging, `python3 scripts/sync.py --dry-run --plan-only` prints which repos your change would reach.

## What lives here

| Directory | What it governs | Who reads it |
|---|---|---|
| [VOICE.md](VOICE.md) | How Portolan sounds | Anyone writing anything for the org |
| [AGENTS.md](AGENTS.md) | Agent norms | Every repo, as a synced block |
| [copy/](copy/) | How Portolan is described, canonical URLs, org profile | Website, announcements, docs |
| [brand/](brand/) | Colors, fonts, logos, and the CSS generator | Website and browser |
| [policies/](policies/) | Code of conduct, contributing, AI policy, security | The org `.github` repo, and through it every repo |
| [norms/](norms/) | How repos, docs, and CI are expected to look | Maintainers and agents |
| [ci/](ci/) | Thin caller workflows | Repos, by CI family |
| [templates/](templates/) | Issue and PR templates, new-repo skeleton files | New and existing repos |
| [sync/](sync/) | `manifest.yml`, which files sync to which repos | The sync workflow |
| [.github/](.github/) | Reusable CI workflows, sync, scheduled jobs | Every repo's CI |
| [.claude/skills/](.claude/skills/) | `setup-repo` | Whoever stands up a new repo |

## Maintaining it

There is no Makefile. Every check is a script, and CI runs the same ones:

```bash
uvx prek run --all-files
python3 scripts/check_manifest.py
python3 scripts/build_agents_block.py --check
python3 brand/check.py
python3 scripts/sync.py --dry-run --plan-only
```

Three jobs run weekly and open pull requests: [`bump-tools.yml`](.github/workflows/bump-tools.yml) raises tool versions Dependabot cannot see, [`auto-update.yml`](.github/workflows/auto-update.yml) bumps pre-commit hook versions, and [`sync-drift.yml`](.github/workflows/sync-drift.yml) reports repos whose synced files have drifted.

## License

[Apache-2.0](LICENSE).
