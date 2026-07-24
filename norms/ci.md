# CI norms

CI logic lives in this repo as reusable workflows. Downstream repos carry thin callers that reference them, so a CI change is one PR here instead of one per repo.

## The three families

| Family | Repos | Reusable workflow | Caller template |
|---|---|---|---|
| Python package | reis, portolan-cli, portolan-registry | [`reusable-python-ci.yml`](../.github/workflows/reusable-python-ci.yml) | [`ci/python-package/ci.yml`](../ci/python-package/ci.yml) |
| STAC extension | stac-partition-extension, stac-iceberg-extension, stac-osi-extension | [`reusable-stac-ext.yml`](../.github/workflows/reusable-stac-ext.yml) | [`ci/stac-extension/ci.yml`](../ci/stac-extension/ci.yml) |
| Web app | portolan-sdi.org, portolan-browser, portolan-nl-demo | [`reusable-web-ci.yml`](../.github/workflows/reusable-web-ci.yml) | [`ci/web-app/ci.yml`](../ci/web-app/ci.yml) |

A repo with needs beyond its family (release workflows, deploys, e2e suites) keeps those as its own workflows alongside the caller. The family covers the shared floor: lint, test, audit.

## Rules

- **Pin actions to a full commit SHA** with a version comment (`uses: actions/checkout@9c091bb2... # v7.0.0`). Floating tags are a supply-chain hole.
- **`permissions: contents: read`** at the top of every workflow. Grant more only per job, only when needed.
- **`persist-credentials: false`** on checkout unless the job pushes.
- **Concurrency groups** cancel superseded runs on the same ref.
- **Python tooling is `uv`** (`astral-sh/setup-uv` with cache). Lint is ruff via pre-commit, and tests are pytest.
- **Nightly schedules** catch dependency drift on idle repos. A scheduled security failure is a new upstream CVE, not a repo regression, and must not turn the badge red (`continue-on-error` on schedule).
- **Timeouts on every job.** 15 minutes for lint/audit, 20 for test matrices, unless measured otherwise.

## Changing CI

1. Edit the reusable workflow here.
2. CI on this repo validates workflow syntax (`check.yml`).
3. Merged changes take effect in every downstream repo on its next run. Callers pin `@main`. Pin a tag instead if a repo needs isolation from ops changes.

## Adding a repo to a family

Copy the family's caller from `ci/` into the repo's `.github/workflows/ci.yml` (or add the repo to `sync/manifest.yml` and let sync open the PR). Delete the repo's superseded inline workflows in the same PR, after confirming the caller run is green.
