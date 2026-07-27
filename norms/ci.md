# CI norms

CI logic lives in this repo as reusable workflows. Downstream repos carry thin callers that reference them, so a CI change is one PR here instead of one per repo.

## The three families

| Family | Repos | Reusable workflow | Caller template |
|---|---|---|---|
| Python package | reis, portolan-cli | [`reusable-python-ci.yml`](../.github/workflows/reusable-python-ci.yml) | [`ci/python-package/ci.yml`](../ci/python-package/ci.yml) |
| STAC extension | stac-partition-extension, stac-iceberg-extension, stac-osi-extension | [`reusable-stac-ext.yml`](../.github/workflows/reusable-stac-ext.yml) | [`ci/stac-extension/ci.yml`](../ci/stac-extension/ci.yml) |
| Web app | portolan-sdi.org, portolan-browser, portolan-nl-demo | [`reusable-web-ci.yml`](../.github/workflows/reusable-web-ci.yml) | [`ci/web-app/ci.yml`](../ci/web-app/ci.yml) |

A repo with needs beyond its family (release workflows, deploys, e2e suites) keeps those as its own workflows alongside the caller. The family covers the shared floor: lint, quality gates, security audit, tests with coverage.

portolan-registry belongs to no family. It holds JSON schemas and a catalog of catalogs rather than a package, so the Python floor does not apply. It keeps its own workflows.

## The Python quality floor

The reusable Python workflow enforces one floor across the family:

- **Hooks via prek, both stages.** The synced `.pre-commit-config.yaml` holds every lint and quality rule. Commit stage: ruff, ruff-format, codespell, actionlint, zizmor, file hygiene. Pre-push stage: mypy, vulture, xenon. CI runs both stages with `uvx prek`, so an unhooked clone meets the same gate.
- **Security**: bandit plus pip-audit. Ignores live in `.pip-audit-ignores` with a mandatory expiry date and reason. Expired entries fail CI again automatically (`scripts/pip_audit_ignores.py`).
- **Coverage**: pytest writes `coverage.xml`, Codecov receives it over OIDC (no token secrets), and `diff-cover` requires 90% coverage on changed lines in PRs.
- **Complexity**: xenon is the hard gate (pre-push hook). wily reports the trend on PRs in a non-blocking job.
- **Mutation**: off by default. A repo turns it on with `mutation: true` on its caller, and the sweep then runs nightly. See "Mutation testing" below.

Repos in the family declare the tools the floor runs as dev dependencies: pytest, pytest-cov, pytest-xdist, diff-cover, mypy, vulture, xenon, bandit, pip-audit.

## Rules

- **Pin actions to a full commit SHA** with a version comment (`uses: actions/checkout@9c091bb2... # v7.0.0`). Floating tags are a supply-chain hole. This repo's own reusable workflows are the exception, and callers pin them to a major tag. See "Releasing a CI change" below.
- **Pin tool versions** everywhere else too: `uvx prek@X.Y.Z`, exact hook `rev`s, `--with pyyaml==X.Y.Z`.
- **`permissions: contents: read`** at the top of every workflow. Grant more only per job, only when needed (`id-token: write` for Codecov OIDC lives on the test job alone).
- **`persist-credentials: false`** on checkout unless the job pushes.
- **Concurrency groups** cancel superseded runs on the same ref.
- **Python tooling is `uv`**, and installs are `uv sync --locked`. A stale lockfile fails the build instead of silently re-resolving.
- **Nightly schedules** catch dependency drift on idle repos. Pick a distinct cron minute per repo. A scheduled security failure is a new upstream CVE, not a repo regression, and must not turn the badge red (`continue-on-error` on schedule).
- **Timeouts on every job.** 15 minutes for lint/audit, 20 for test matrices, unless measured otherwise.

## Mutation testing

Every other gate confirms the code runs. Mutation testing asks whether the tests notice when the code changes. mutmut alters the source one edit at a time and reruns the suite, and a mutant that survives means no test objected.

The sweep is slow, so it runs nightly rather than on pull requests. A repo opts in by setting `mutation: true` on its caller. Doing so adds mutmut to the dev-dependency contract, and the repo also needs a `[tool.mutmut]` block in `pyproject.toml` naming the paths to mutate.

Scoring lives in one place, `scripts/mutation_score.py`, which syncs from `templates/repo/scripts/`. Before this job existed, reis and portolan-cli each computed a kill rate their own way, and the two numbers were not comparable.

```
killed_total = killed + timeout + suspicious
testable     = killed_total + survived
kill_rate    = killed_total / testable
```

A timeout or a suspicious result still means the suite reacted, so both count as kills. Mutants with no covering test at all are excluded rather than counted as failures, because coverage measures that gap already. Zero testable mutants fails the run, since it means mutmut generated or parsed nothing.

Each repo keeps its own floor in `.mutation-baseline`, a single number. Ratchet it up as the suite improves. Lowering it needs a justification in the pull request that does so.

### Sharding

A repo whose full sweep no longer fits the timeout sets `mutation-shards` to a number above zero. Each night then mutates one slice, chosen by day of year, and the whole tree is covered every `mutation-shards` nights.

Shard membership comes from a hash of each file's path rather than its position in a sorted list. Adding a module therefore moves only that module, leaving every recorded per-shard rate still valid.

A single slice's kill rate depends on which modules land in it. Measured slices in portolan-cli ranged from 18% to 95%, so one repo-wide floor either flaps or gates nothing. A repo that shards should also record each slice's own rate in `.mutation-shards.json`, which the scorer enforces alongside the repo-wide floor.

## Tool versions

Two pins repeat across several workflows and drift apart when bumped by hand: `prek` and `pyyaml`. Both read org-level Actions variables named `PREK_VERSION` and `PYYAML_VERSION`. Setting one of those variables bumps the tool everywhere in a single edit.

```yaml
env:
  PREK_VERSION: ${{ vars.PREK_VERSION || '0.4.11' }}
```

The literal after `||` is a fallback rather than a second source of truth. Inside a reusable workflow, the `vars` context resolves against the **caller's** repository rather than this one. A fork, or any caller outside the org, sees no variable and would otherwise run `uvx prek@` bare.

Changing the variable takes effect across every repo with no pull request and no review. Treat it as a deployment rather than an edit.

`wily` stays pinned inline in one file. A `uvx wily@X.Y.Z` argument has no `env:` value to read.

### Keeping the literals fresh

No tool bumps a pinned version on its own. Dependabot reads action references, which leaves an `env:` value and a `uvx tool@version` argument invisible to it. Left alone, the fallbacks go stale.

`bump-tools.yml` runs weekly. It asks PyPI for the newest prek, pyyaml, and wily, rewrites every literal that moved, and opens a pull request. CI runs the new versions on that pull request before anyone merges it.

The job writes files under `.github/workflows`. `GITHUB_TOKEN` may not do that at any permission level, so the job mints an app token with `workflows: write` instead. Nothing else separates it from `auto-update.yml`.

A bumper that stops matching its patterns fails quietly, and the pins then rot unnoticed. Two guards cover that. `scripts/test_bump_tools.py` tests the rewrite, and `check.yml` runs `bump_tools.py --check`, which fails when a pattern no longer matches the real workflows.

An org variable overrides the literal in the workflow. While one is set, the bumper's pull request changes nothing on its own. The pull request body detects this and prints the command to update the variable.

## Changing CI

1. Edit the reusable workflow here.
2. CI on this repo validates workflow syntax (`check.yml`), and `ci-selftest.yml` runs the Python floor end to end against `tests/fixture-package`.
3. Merge. The change reaches the fleet when the major tag moves, not at merge.

## Releasing a CI change

Callers pin `@v1`, a tag that moves with each release. Merging here changes nothing downstream until the tag moves, which leaves room to test the change on one repo first.

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

Moving `v1` overwrites where it used to point. The fixed tag gives each release a name that stays put, and a bad release is rolled back by moving `v1` onto the previous one.

A change that breaks callers ships as `v2`, leaving `v1` alone. Downstream repos keep running `v1` until they choose to move, and Dependabot opens the pull request asking them to. Each family caller travels with a `dependabot.yml` for that reason. Without the `github-actions` ecosystem enabled, a major release stays invisible downstream.

## Adding a repo to a family

Copy the family's caller from `ci/` into the repo's `.github/workflows/ci.yml`, and its `dependabot.yml` into `.github/dependabot.yml` (or add the repo to `sync/manifest.yml` and let sync open the PR). A repo that already has a Dependabot config gets it replaced, so reconcile the ecosystems first. Delete the repo's superseded inline workflows in the same PR, after confirming the caller run is green.
