# portolan-ops

The shared parts of every [Portolan](https://github.com/portolan-sdi) repo: CI logic, docs and repo norms, branding, copy, policies, and new-repo templates. Change one of them here and the sync workflow carries it to every repo that uses it.

Portolan is a lot of repos, built quickly, mostly with agents. Two of them hold the human attention. [portolan-spec](https://github.com/portolan-sdi/portolan-spec) defines the standard, and this repo defines how the org's repos get built. Everything else is downstream of those two, which is what makes it safe to move fast downstream. Think of it as spec-driven development pointed at operations instead of at the product.

This repo is also where cross-repo work gets tracked, so [open an issue](https://github.com/portolan-sdi/portolan-ops/issues/new) for anything without a repo of its own.

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
| [sync/](sync/) | `manifest.yml`, the fan-out map | The sync workflow |
| [.github/](.github/) | Reusable CI workflows, sync, scheduled jobs | Every repo's CI |
| [.claude/skills/](.claude/skills/) | `setup-repo` | Whoever stands up a new repo |

## What you can do

### Stand up a new repo

Run the `setup-repo` skill from inside the new repo, either by asking for it ("set this repo up to org standards") or with `/setup-repo`. It reads this repo as ground truth and applies the license, the README skeleton, the `AGENTS.md` block, the family CI caller, the repo checks, dependabot, the pre-commit hooks, and the Python dependency groups. It finishes by registering the repo in [`sync/manifest.yml`](sync/manifest.yml), which is what puts it on the fan-out.

### Change a shared file everywhere

Edit the file here and merge. Sync opens a single `ops-sync` pull request in each affected repo, and most repos merge that by hand. Two files are generated rather than written:

```bash
python3 scripts/build_agents_block.py   # after editing AGENTS.md
python3 brand/emit_css.py --write       # after editing brand/brand.json
```

CI fails if you skip either one.

### Add a repo to the fan-out

Add its entries to [`sync/manifest.yml`](sync/manifest.yml) and push. Listing the repo under `auto_merge` hands the merge decision to its own CI instead of to a reviewer. See [norms/ci.md](norms/ci.md#auto-merging-the-sync-pull-request) for what that requires.

### Change brand values

Edit [`brand/brand.json`](brand/brand.json), regenerate the CSS, then check it:

```bash
python3 brand/emit_css.py --write
python3 brand/check.py
```

### Change shared CI

Edit the reusable workflow in [`.github/workflows/`](.github/workflows/), confirm `ci-selftest.yml` passed, then move the `v1` tag. Downstream callers pin a tag, so a merge to `main` alone reaches nobody. [norms/ci.md](norms/ci.md#releasing-a-ci-change) has the commands and the reasoning.

## Maintaining it

There is no Makefile. Every check is a script you run directly, and CI runs the same ones.

```bash
uvx prek run --all-files
python3 scripts/check_manifest.py
python3 scripts/build_agents_block.py --check
python3 brand/check.py
python3 scripts/sync.py --dry-run --plan-only
```

The dry run prints which repos each changed file would reach, which is the fastest way to see the blast radius of an edit before merging it.

Three jobs run weekly and open pull requests you review like any other. [`bump-tools.yml`](.github/workflows/bump-tools.yml) raises the pinned versions of prek, pyyaml, and wily, which Dependabot cannot see. [`auto-update.yml`](.github/workflows/auto-update.yml) bumps hook versions in the pre-commit configs. [`sync-drift.yml`](.github/workflows/sync-drift.yml) reports repos whose synced files no longer match this one.

## License

[Apache-2.0](LICENSE).
