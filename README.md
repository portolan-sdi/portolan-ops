# portolan-ops

Ground truth for the [Portolan](https://github.com/portolan-sdi) organization. Copy, branding, docs norms, policies, CI configuration, and repo templates live here. Downstream repos pull from this repo instead of drifting.

Portolan builds specs. This repo is the spec for the specs. It defines how the organization's repos get built, what they share, and how the shared parts stay in sync. It is also the coordination board for work that has no repo of its own: infrastructure, promotion, events, and cross-repo efforts. [Open an issue](https://github.com/portolan-sdi/portolan-ops/issues/new) for anything in that category.

## Read order

1. **[VOICE.md](VOICE.md)** — how Portolan sounds in public copy. Required for anyone (human or agent) writing for the organization.
2. **[STYLE.md](STYLE.md)** — the prose rubric. Required before drafting any written artifact.
3. **[AGENTS.md](AGENTS.md)** — canonical norms for AI agents working in any org repo.
4. **[norms/](norms/)** — how repos, docs, and CI are expected to look.
5. **[policies/](policies/)** — code of conduct, contributing, AI policy, security.
6. **[copy/messaging.md](copy/messaging.md)** — how Portolan is described. Still provisional, but it wins over older copy.
7. **[copy/](copy/)** and **[brand/](brand/)** — canonical language and visual identity.

## How sync works

Content here fans out through one workflow, [`sync.yml`](.github/workflows/sync.yml), driven by an explicit manifest, [`sync/manifest.yml`](sync/manifest.yml). On a push to `main` that touches synced files, the workflow opens or updates a single `ops-sync` pull request in each affected repo. Downstream repos review and merge. Nothing lands silently.

The fan-out is deliberately small:

| What | Where it goes | Why |
|---|---|---|
| Org profile, code of conduct, contributing guide, security policy, issue and PR templates | The [`.github`](https://github.com/portolan-sdi/.github) repo | GitHub applies community health files from `.github` to every repo that lacks its own. One sync target covers the whole org. |
| `LICENSE` (Apache-2.0) | Every active repo | GitHub does not inherit licenses. |
| Thin CI caller workflows | Repos, per CI family | The logic lives in this repo's reusable workflows. Callers reference them (`uses: portolan-sdi/portolan-ops/.github/workflows/...@v1`) and rarely change. See [How shared CI works](#how-shared-ci-works). |
| `AGENTS.md` pointer block | Every active repo | A delimited block at the top of each downstream `AGENTS.md` links back here. Repo-specific content below the block is never touched. |
| `CLAUDE.md` bridge | Every active repo | One import line. Claude Code does not read `AGENTS.md`, so without this file it sees no org norms. See [Why both exist](norms/ci.md#why-agentsmd-and-claudemd-both-exist). |
| Repo checks caller and zizmor policy | Every active repo | Holds bodies to 200 words with pasted evidence, and keeps the two agent files in shape. It takes no repo-specific inputs, so one synced file serves the org. See [The repo checks](norms/ci.md#the-repo-checks). |
| `_brand-vars.css` | Website and browser (planned) | Generated from `brand/brand.json` by `brand/emit_css.py`. Not yet in the manifest. The website and browser keep their own tokens until branding lands (see [brand/PATTERN.md](brand/PATTERN.md), "Current state"). |

Adding a repo to the fan-out is one edit to `sync/manifest.yml`.

## How shared CI works

Repos across the org should hold the same quality bar. Copying a CI configuration into each one guarantees they drift apart, so this repo holds the logic and the others call it. [`norms/ci.md`](norms/ci.md) lists the three families and which repos belong to each.

A repo that joins a family receives two files. The first is a short workflow that calls the shared logic. The second is `.pre-commit-config.yaml`, which names the rules the repo runs: ruff, codespell, commitizen, mypy, vulture, xenon, deptry, import-linter, and the file hygiene checks.

A Python repo can add a third, `ci/python-package/security-audit.yml`. That caller runs pip-audit nightly and keeps a tracking issue in step with the result, opening it on a finding and closing it when the audit goes clean. It is optional because an issue nobody triages is noise. See [The security audit](norms/ci.md#the-security-audit).

The rules live in the hook config, not the workflow. CI runs both hook stages, which means a clone without hooks installed faces the same checks as one with them.

### Why callers name a version

A caller points at a tag rather than a branch.

```yaml
uses: portolan-sdi/portolan-ops/.github/workflows/reusable-python-ci.yml@v1
```

GitHub reads the workflow from this repo at that tag every time a downstream repo runs CI. Merging a change to `main` therefore reaches nobody. The change ships when the `v1` tag moves onto the new commit.

That gap is deliberate. Under the old arrangement, callers named `main`, and a merge that broke CI broke it in every repo at once with no chance to test first.

Each release also gets a fixed tag such as `v1.0.0`. The `v1` tag moves and overwrites where it used to point. The fixed tag gives every release a name that stays put, which is what makes a rollback possible.

A change that breaks callers ships as `v2`, leaving `v1` alone. Repos keep running the old version until they choose to move. Dependabot opens the pull request that asks them to, which is why each family caller travels with a `dependabot.yml`.

### Releasing a CI change

1. Edit the reusable workflow and merge it.
2. Confirm `ci-selftest.yml` passed. It runs the Python floor against `tests/fixture-package` before any real repo sees the change.
3. Move the tag. [`norms/ci.md`](norms/ci.md) has the commands.

Forgetting step 3 leaves the change sitting in `main` with no effect anywhere.

### Adding a repo to a family

Uncomment that repo's entries in `sync/manifest.yml` and push. Sync opens a pull request carrying the hook config and the supporting files for pip-audit. Copy the family caller from `ci/` by hand, since repos need different inputs and sync would overwrite them.

The zizmor policy arrives earlier, with the repo checks caller that every repo carries. It is required rather than optional. zizmor demands a hash pin on every action reference, so without it the repo's own lint job rejects any caller's tag.

The repo needs the dev dependencies the workflow runs: pytest, pytest-cov, pytest-xdist, diff-cover, mypy, vulture, xenon, bandit, and pip-audit. Expect the first run to fail. Switching on strict rules against an existing codebase surfaces whatever accumulated before them.

### Pinned tool versions

Three tools are pinned by version string across the workflows here: prek, pyyaml, and wily. Dependabot cannot see those pins, because it reads action references rather than plain strings.

[`bump-tools.yml`](.github/workflows/bump-tools.yml) covers the gap. It checks PyPI each week and opens a pull request when a version moves, so CI runs the new version before anyone merges it.

## Map of the org

| Repo | Role |
|---|---|
| [portolan-spec](https://github.com/portolan-sdi/portolan-spec) | The Portolan specification. Ground truth for the standard. Every implementation is downstream of it. |
| [portolan-cli](https://github.com/portolan-sdi/portolan-cli) | CLI. Implements the spec. |
| [portolan-sdi.org](https://github.com/portolan-sdi/portolan-sdi.org) | Website: [portolan-sdi.org](https://www.portolan-sdi.org/) |
| [rashid](https://github.com/portolan-sdi/rashid) | Validator |
| [portolan-registry](https://github.com/portolan-sdi/portolan-registry) | Catalog registry |
| [portolan-browser](https://github.com/portolan-sdi/portolan-browser) | Catalog browser (stac-browser fork) |
| [portolan-data](https://github.com/portolan-sdi/portolan-data) | Tracking and coordination for official Portolan catalogs and mirrors |
| [portolan-skills](https://github.com/portolan-sdi/portolan-skills) | Claude Code skills |
| [stac-partition-extension](https://github.com/portolan-sdi/stac-partition-extension), [stac-iceberg-extension](https://github.com/portolan-sdi/stac-iceberg-extension), [stac-osi-extension](https://github.com/portolan-sdi/stac-osi-extension) | Incubated STAC extensions |
| [portolan-ops](https://github.com/portolan-sdi/portolan-ops) | This repo |

Roadmap and planning live in [org-level GitHub projects](https://github.com/orgs/portolan-sdi/projects/1). Community discussion lives in the [Portolan Google Group](https://groups.google.com/g/portolan) and the [Portolan channel](https://cloudnativegeo.slack.com/archives/C0A1JBH9529) in the Cloud-Native Geo Slack.

## Repo layout

```
VOICE.md          Portolan voice — governs collective public copy
STYLE.md          prose rubric — governs all written artifacts
AGENTS.md         canonical agent norms; downstream repos point here
brand/            brand kit: brand.json, logos, fonts, validator, CSS generator
copy/             canonical language: messaging, URLs, org profile source
policies/         code of conduct, contributing, AI policy, security
norms/            repo, docs, and CI conventions
ci/               thin caller workflows that downstream repos receive
templates/        issue/PR templates and new-repo skeleton files
sync/             manifest.yml — the fan-out map
.github/          sync + check workflows, reusable CI workflows
.claude/skills/   setup-repo — scaffolds a new org repo from this repo
```

## License

[Apache-2.0](LICENSE), like every Portolan repo.
