# Portolan agent norms

Canonical rules for AI agents working in any portolan-sdi repo. Downstream repos carry a synced pointer block at the top of their own `AGENTS.md` that links here; repo-specific instructions live below that block. When a repo-specific rule conflicts with this file, the repo-specific rule wins for that repo.

## Voice and prose

- All collective public-facing copy (website, announcements, docs, presentations) follows [VOICE.md](VOICE.md). Read it before writing any of those.
- All written artifacts (READMEs, PR and issue bodies, docs, commit message bodies, lasting code comments) follow [STYLE.md](STYLE.md). Apply it while drafting, not as a cleanup pass.
- Both are mandatory. "Agents MUST abide" is the operative phrase in each.

## Org-wide facts

- License is Apache-2.0 in every repo. Never introduce code under another license without a human decision recorded in `norms/repos.md`.
- The canonical homepage is https://www.portolan-sdi.org/. Canonical URLs live in [copy/urls.md](copy/urls.md); do not hardcode variants.
- Community discussion happens in the [Portolan Google Group](https://groups.google.com/g/portolan). Planning lives in [org-level GitHub projects](https://github.com/orgs/portolan-sdi/projects/1).
- The [portolan-spec](https://github.com/portolan-sdi/portolan-spec) repo is the ground truth for the Portolan standard. The CLI, the validator, the registry, and every other tool implement the spec and are downstream of it. Never describe the CLI as the source of truth for the spec. Propose spec changes in portolan-spec.

## Contribution rules

- The [AI policy](policies/AI_POLICY.md) applies to every contribution. A human must have read, reviewed, and understood any change before review is requested. Agents never open PRs, post comments, or take action in shared spaces without human approval.
- Follow the [contributing guide](policies/CONTRIBUTING.md) and the [code of conduct](policies/CODE_OF_CONDUCT.md).
- Conventional commits. Squash-merge means the PR title is the commit message; write it in conventional form.
- Never bypass pre-commit hooks or CI gates. Green means green.

## Ground truth discipline

- One canonical home per fact; link, don't duplicate. If a value (a color, a URL, a policy line) exists in this repo, reference it rather than copying it.
- Shared files reach downstream repos through `sync/manifest.yml` and the sync workflow, never by hand-copying. To change a synced file in a downstream repo, change it here.
- Brand values come from `brand/brand.json`. Regenerate derived files (`brand/emit_css.py`) rather than editing them.
