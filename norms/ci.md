# CI norms

Reusable workflows in portolan-ops hold the shared CI logic. Repos call them by the `v1` tag. These are the rules for any CI change in any repo. The workflows and scripts are the record of what CI does, so read them for the details.

Maintainers who release CI, add repos, or change branch protection follow [maintaining-ci.md](../docs/maintaining-ci.md).

## Workflow families

| Repo type | Workflow | Examples |
|---|---|---|
| Python packages | `reusable-python-ci.yml` | rashid, portolan-cli |
| STAC extensions | `reusable-stac-ext.yml` | stac-partition-extension, stac-iceberg-extension |
| Web apps | `reusable-web-ci.yml` | portolan-sdi.org, portolan-browser |

Every repo also runs `reusable-repo-checks.yml`. Release, deployment, and end-to-end workflows stay in each repo beside the shared caller.

## Workflow rules

Pin actions to a full commit SHA with a version comment:

```yaml
uses: actions/checkout@9c091bb2... # v7.0.0
```

The portolan-ops reusable workflows are the one exception. Callers reference them by major tag, and `templates/repo/zizmor.yml` allows it.

Pin other tools to exact versions. This covers hook `rev` values and tools installed through uvx or pip, such as `--with pyyaml==X.Y.Z`.

Renovate reads hook `rev` values and action pins on its own. A workflow `env` value or a `uvx tool@X.Y.Z` argument needs a comment on the line above it:

```yaml
# renovate: datasource=pypi depName=prek
PREK_VERSION: ${{ vars.PREK_VERSION || '0.5.6' }}
```

Set `permissions: contents: read` at workflow level. Grant extra permissions only to the job that needs them.

Set `persist-credentials: false` on checkout unless the job pushes.

Never filter `pull_request` events by branch. GitHub applies that filter to the target branch, so `branches: [main]` leaves pull requests into release branches unchecked. Branch filters on `push` are fine. `scripts/check_workflow_triggers.py` enforces this.

Use concurrency groups to cancel superseded runs on the same ref.

Use `uv` for Python tooling and `uv sync --locked` for installs. A stale lockfile must fail the build.

Set a timeout on every job. Lint and audit jobs get 15 minutes. Test matrices get 20 minutes unless measurements justify longer.

## Python repos

`templates/repo/.pre-commit-config.yaml` lists the lint and quality hooks. CI runs its commit and push stages, so local hooks are optional.

- `diff-cover` requires 90% coverage on the lines a pull request changes.
- Codecov statuses are informational. Never make `codecov/*` a required check.
- Each exception in `.pip-audit-ignores` needs a reason and an expiry date. An expired exception fails CI.
- Raise `.mutation-baseline` as tests improve. Explain any reduction in the pull request.
- Keep Ubuntu in the test matrix for pull requests. Codecov and diff-cover run only there.

## Dependency updates

Renovate updates dependencies. `renovate.yml` runs it every hour as the portolan-renovate app, and `renovate/default.json5` holds the policy for every repo.

- Every update merges when the required checks pass, majors included. The checks are the gate.
- Non-major updates open as one grouped pull request early on Monday (UTC). Each major opens on its own.
- A release must be 7 days old before Renovate proposes it.
- Security fixes skip the schedule and the 7-day delay.
- A daily lock-file refresh moves transitive dependencies. It clears a `pip-audit` failure that comes from a transitive pin.
- Each repo has a Dependency Dashboard issue that lists pending and held updates.

A repo that needs an exception adds a `renovate.json5` with only the exception, and a comment that gives the reason. To review one package by hand before it merges, set `automerge: false` in a `packageRules` entry for it.

## Pull request check

The check fails when a required section is missing or empty, when the body references no issue, or when a behavior change has no pasted evidence.

The template offers two waivers. Tick at most one.

| Waiver | Use it when |
|---|---|
| No behavior change | The change covers docs, chores, or CI and alters no behavior. |
| Previously reviewed changes | The pull request merges a release branch, and each change in it was verified on its own. |

A waiver removes the issue and evidence requirements. Every section is still required. A checkbox inside a fenced code block does not count.

The check enforces structure, not quality or length. Never compress evidence to make a body shorter.

## Writing hook

`.claude/hooks/writing_check.py` checks the body before `gh issue create` and `gh pr create`. To override a wrong finding, put this comment on the line before it:

```html
<!-- ste-ok: RULE_ID reason -->
```

The reason is required. The hook reads `--body` and `--body-file` but cannot see a body passed through a heredoc. A pass means the body has none of the patterns the hook matches. It says nothing about tone or padding.

## Prose and links

Vale and proselint check Markdown. See [prose.md](prose.md).

lychee checks relative links and anchors on every push and pull request, and checks external URLs weekly. To check locally, run this from a repo with portolan-ops checked out beside it:

```bash
../portolan-ops/scripts/lychee.sh --offline .
```

Put repo exceptions in `lychee.toml` under `exclude_path` or in `.lycheeignore`, one pattern per line. Give a reason for each. A repo can add exclusions but cannot remove the ones in `lychee/org.toml`.

A site with a build step adds a `site-links` job that passes the built site to `reusable-links.yml`. That workflow's header explains the inputs.

## Workflow and script reference

| Topic | Read |
|---|---|
| Which files sync to which repos | `sync/manifest.yml`, `scripts/sync.py` |
| Sync auto-merge and retired files | `sync/manifest.yml`, `scripts/sync.py` |
| Workflow and setting repair | `automation-reconcile.yml` |
| Nightly security audit | `reusable-security-audit.yml` |
| Mutation scores and shards | `templates/repo/scripts/mutation_score.py`, `templates/repo/scripts/shard_select.py` |
| Dependency and tool version updates | `renovate.yml`, `renovate/default.json5`, `renovate/global.json5` |
| Agent file layout | `scripts/check_repo_layout.py`, `scripts/build_agents_block.py` |
