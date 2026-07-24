# portolan-ops

Ground truth for the [Portolan](https://github.com/portolan-sdi) organization. Copy, branding, docs norms, policies, CI configuration, and repo templates live here. Downstream repos pull from this repo instead of drifting.

Portolan builds specs. This repo is the spec for the specs: it defines how the organization's repos get built, what they share, and how the shared parts stay in sync. It is also the coordination board for work that has no repo of its own: infrastructure, promotion, events, and cross-repo efforts. [Open an issue](https://github.com/portolan-sdi/portolan-ops/issues/new) for anything in that category.

## Read order

1. **[VOICE.md](VOICE.md)** — how Portolan sounds in public copy. Required for anyone (human or agent) writing for the organization.
2. **[STYLE.md](STYLE.md)** — the prose rubric. Required before drafting any written artifact.
3. **[AGENTS.md](AGENTS.md)** — canonical norms for AI agents working in any org repo.
4. **[norms/](norms/)** — how repos, docs, and CI are expected to look.
5. **[policies/](policies/)** — code of conduct, contributing, AI policy, security.
6. **[copy/](copy/)** and **[brand/](brand/)** — canonical language and visual identity.

## How sync works

Content here fans out through one workflow, [`sync.yml`](.github/workflows/sync.yml), driven by an explicit manifest, [`sync/manifest.yml`](sync/manifest.yml). On a push to `main` that touches synced files, the workflow opens or updates a single `ops-sync` pull request in each affected repo. Downstream repos review and merge; nothing lands silently.

The fan-out is deliberately small:

| What | Where it goes | Why |
|---|---|---|
| Org profile, code of conduct, contributing guide, security policy, issue and PR templates | The [`.github`](https://github.com/portolan-sdi/.github) repo | GitHub applies community health files from `.github` to every repo that lacks its own. One sync target covers the whole org. |
| `LICENSE` (Apache-2.0) | Every active repo | GitHub does not inherit licenses. |
| Thin CI caller workflows | Repos, per CI family | The logic lives in this repo's reusable workflows. Callers reference them (`uses: portolan-sdi/portolan-ops/.github/workflows/...@main`) and rarely change. |
| `AGENTS.md` pointer block | Every active repo | A delimited block at the top of each downstream `AGENTS.md` links back here. Repo-specific content below the block is never touched. |
| `_brand-vars.css` | Website and browser | Generated from `brand/brand.json` by `brand/emit_css.py`. |

To add a repo to the fan-out, add it to `sync/manifest.yml`. That is the whole procedure.

## Map of the org

| Repo | Role |
|---|---|
| [portolan-spec](https://github.com/portolan-sdi/portolan-spec) | The Portolan specification. Ground truth for the standard; every implementation is downstream of it. |
| [portolan-cli](https://github.com/portolan-sdi/portolan-cli) | CLI. Implements the spec. |
| [portolan-sdi.org](https://github.com/portolan-sdi/portolan-sdi.org) | Website — [portolan-sdi.org](https://www.portolan-sdi.org/) |
| [reis](https://github.com/portolan-sdi/reis) | Validator |
| [portolan-registry](https://github.com/portolan-sdi/portolan-registry) | Catalog registry |
| [portolan-browser](https://github.com/portolan-sdi/portolan-browser) | Catalog browser (stac-browser fork) |
| [portolan-skills](https://github.com/portolan-sdi/portolan-skills) | Claude Code skills |
| [stac-partition-extension](https://github.com/portolan-sdi/stac-partition-extension), [stac-iceberg-extension](https://github.com/portolan-sdi/stac-iceberg-extension), [stac-osi-extension](https://github.com/portolan-sdi/stac-osi-extension) | Incubated STAC extensions |
| [portolan-ops](https://github.com/portolan-sdi/portolan-ops) | This repo |

Roadmap and planning live in [org-level GitHub projects](https://github.com/orgs/portolan-sdi/projects/1). Community discussion lives in the [Portolan Google Group](https://groups.google.com/g/portolan).

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
