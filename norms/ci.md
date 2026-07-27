# CI norms

CI logic lives in this repo as reusable workflows. Downstream repos carry thin callers that reference them, so a CI change is one PR here instead of one per repo.

## The three families

| Family | Repos | Reusable workflow | Caller template |
|---|---|---|---|
| Python package | reis, portolan-cli, portolan-registry | [`reusable-python-ci.yml`](../.github/workflows/reusable-python-ci.yml) | [`ci/python-package/ci.yml`](../ci/python-package/ci.yml) |
| STAC extension | stac-partition-extension, stac-iceberg-extension, stac-osi-extension | [`reusable-stac-ext.yml`](../.github/workflows/reusable-stac-ext.yml) | [`ci/stac-extension/ci.yml`](../ci/stac-extension/ci.yml) |
| Web app | portolan-sdi.org, portolan-browser, portolan-nl-demo | [`reusable-web-ci.yml`](../.github/workflows/reusable-web-ci.yml) | [`ci/web-app/ci.yml`](../ci/web-app/ci.yml) |

A repo with needs beyond its family (release workflows, deploys, e2e suites) keeps those as its own workflows alongside the caller. The family covers the shared floor: lint, quality gates, security audit, tests with coverage.

## The Python quality floor

The reusable Python workflow enforces one floor across the family:

- **Hooks via prek, both stages.** The synced `.pre-commit-config.yaml` holds every lint and quality rule. Commit stage: ruff, ruff-format, codespell, actionlint, zizmor, file hygiene. Pre-push stage: mypy, vulture, xenon. CI runs both stages with `uvx prek`, so an unhooked clone meets the same gate.
- **Security**: bandit plus pip-audit. Ignores live in `.pip-audit-ignores` with a mandatory expiry date and reason. Expired entries fail CI again automatically (`scripts/pip_audit_ignores.py`).
- **Coverage**: pytest writes `coverage.xml`, Codecov receives it over OIDC (no token secrets), and `diff-cover` requires 90% coverage on changed lines in PRs.
- **Complexity**: xenon is the hard gate (pre-push hook). wily reports the trend on PRs in a non-blocking job.

Repos in the family declare the tools the floor runs as dev dependencies: pytest, pytest-cov, pytest-xdist, diff-cover, mypy, vulture, xenon, bandit, pip-audit.

## Rules

- **Pin actions to a full commit SHA** with a version comment (`uses: actions/checkout@9c091bb2... # v7.0.0`). Floating tags are a supply-chain hole. The one exception is this repo's own reusable workflows, which callers pin to a major tag; see "Releasing a CI change" below.
- **Pin tool versions** everywhere else too: `uvx prek@X.Y.Z`, exact hook `rev`s, `--with pyyaml==X.Y.Z`.
- **`permissions: contents: read`** at the top of every workflow. Grant more only per job, only when needed (`id-token: write` for Codecov OIDC lives on the test job alone).
- **`persist-credentials: false`** on checkout unless the job pushes.
- **Concurrency groups** cancel superseded runs on the same ref.
- **Python tooling is `uv`**, and installs are `uv sync --locked`. A stale lockfile fails the build instead of silently re-resolving.
- **Nightly schedules** catch dependency drift on idle repos. Pick a distinct cron minute per repo. A scheduled security failure is a new upstream CVE, not a repo regression, and must not turn the badge red (`continue-on-error` on schedule).
- **Timeouts on every job.** 15 minutes for lint/audit, 20 for test matrices, unless measured otherwise.

## Tool versions

Two pins repeat across workflows and drift apart when bumped by hand: `prek` and `pyyaml`. Both now read org-level Actions variables, `PREK_VERSION` and `PYYAML_VERSION`, so a fleet-wide bump is one edit in org settings.

```yaml
env:
  PREK_VERSION: ${{ vars.PREK_VERSION || '0.4.11' }}
```

The literal after `||` is a fallback, not a second source of truth. It matters because the `vars` context inside a reusable workflow resolves against the **caller's** repository, not this one. A fork, or any caller outside the org, sees no variable at all and would otherwise run `uvx prek@` bare.

Two consequences worth knowing. Bumping the variable changes CI across the fleet with no PR and no review, so treat it like a deploy rather than an edit. And the fallback literals go stale silently, so refresh them when the variable moves a long way.

`wily` stays pinned inline. It appears in one file, so there is nothing for it to drift against.

## Changing CI

1. Edit the reusable workflow here.
2. CI on this repo validates workflow syntax (`check.yml`), and `ci-selftest.yml` runs the Python floor end to end against `tests/fixture-package`.
3. Merge. The change reaches the fleet when the major tag moves, not at merge.

## Releasing a CI change

Callers pin a moving major tag, `@v1`. The gap between merging here and moving the tag is the canary window: main can be wrong for an hour without taking every repo's CI down with it.

1. Merge the change to main.
2. Confirm `ci-selftest.yml` is green on the merge commit.
3. Point one downstream repo at `@main` and let a real run go green. Revert it to `@v1` afterward.
4. Cut an immutable tag and move the major tag onto it:

   ```bash
   git tag -a v1.1.0 -m "prek 0.4.12, wider test matrix" <sha>
   git push origin v1.1.0
   git tag -f v1 v1.1.0
   git push -f origin v1
   ```

The immutable tag is what makes a bad release recoverable: move `v1` back to the previous one.

A change that breaks callers ships as `v2` instead, with `v1` left where it is. Downstream repos then get a Dependabot PR bumping `@v1` to `@v2`, which they merge on their own schedule. That PR is the whole reason each family caller travels with a `dependabot.yml`; without the `github-actions` ecosystem enabled, a major release is invisible downstream.

## Adding a repo to a family

Copy the family's caller from `ci/` into the repo's `.github/workflows/ci.yml`, and its `dependabot.yml` into `.github/dependabot.yml` (or add the repo to `sync/manifest.yml` and let sync open the PR). A repo that already has a Dependabot config gets it replaced, so reconcile the ecosystems first. Delete the repo's superseded inline workflows in the same PR, after confirming the caller run is green.
