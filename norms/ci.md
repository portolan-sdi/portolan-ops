# CI norms

CI logic lives in this repo as reusable workflows. Downstream repos carry thin callers that reference them, so a CI change is one PR here instead of one per repo.

## The three families

| Family | Repos | Reusable workflow | Caller template |
|---|---|---|---|
| Python package | rashid, portolan-cli | [`reusable-python-ci.yml`](../.github/workflows/reusable-python-ci.yml) | [`ci/python-package/ci.yml`](../ci/python-package/ci.yml) |
| STAC extension | stac-partition-extension, stac-iceberg-extension, stac-osi-extension | [`reusable-stac-ext.yml`](../.github/workflows/reusable-stac-ext.yml) | [`ci/stac-extension/ci.yml`](../ci/stac-extension/ci.yml) |
| Web app | portolan-sdi.org, portolan-browser, portolan-nl-demo | [`reusable-web-ci.yml`](../.github/workflows/reusable-web-ci.yml) | [`ci/web-app/ci.yml`](../ci/web-app/ci.yml) |

Two workflows sit outside the families. The [repo checks](#the-repo-checks) run everywhere. The [security audit](#the-security-audit) is optional, and Python repos opt in by copying [`ci/python-package/security-audit.yml`](../ci/python-package/security-audit.yml).

A repo with needs beyond its family (release workflows, deploys, e2e suites) keeps those as its own workflows alongside the caller. The family covers the shared floor: lint, quality gates, security audit, tests with coverage.

portolan-registry belongs to no family. It holds JSON schemas and a catalog of catalogs rather than a package, so the Python floor does not apply. It keeps its own workflows.

## The Python quality floor

The reusable Python workflow enforces one floor across the family:

- **Hooks via prek, both stages.** The synced `.pre-commit-config.yaml` holds every lint and quality rule. Commit stage: ruff-check, ruff-format, codespell, actionlint, zizmor, file hygiene. Pre-push stage: mypy, vulture, xenon, deptry, import-linter. CI runs both stages with `uvx prek`, so an unhooked clone meets the same gate. commitizen runs at commit-msg, which CI does not run: squash-merge makes the pull request title the commit message that lands.
- **Dependency hygiene**: deptry finds unused, missing, and transitive imports. It needs no per-repo configuration, which is why it belongs in the shared floor rather than in one repo's config.
- **Import contracts**: import-linter runs where a repo declares `[tool.importlinter]` contracts and skips where it does not. `lint-imports` exits non-zero with no config, so the hook is guarded. A repo turns the gate on by writing its first contract, with no edit to the template.
- **Security**: bandit plus pip-audit. Ignores live in `.pip-audit-ignores` with a mandatory expiry date and reason. Expired entries fail CI again automatically (`scripts/pip_audit_ignores.py`).
- **Coverage**: pytest writes `coverage.xml`, Codecov receives it over OIDC (no token secrets), and `diff-cover` requires 90% coverage on changed lines in PRs.
- **Complexity**: xenon is the hard gate (pre-push hook). wily reports the trend on PRs in a non-blocking job.
- **Mutation**: off by default. A repo turns it on with `mutation: true` on its caller, and the sweep then runs nightly. See "Mutation testing" below.

- **Test matrix**: pull requests run `os-pull-request`, which is ubuntu alone. Schedule, push, and dispatch runs use `os`, which is ubuntu, macos, and windows. Path handling is where Windows breaks, and a package on PyPI gets installed on all three, so the coverage is worth having. Paying for it on every review iteration is not. Keep ubuntu in `os-pull-request`: the Codecov upload and the diff-cover gate run there and nowhere else.

Repos in the family declare the tools the floor runs as dev dependencies: pytest, pytest-cov, pytest-xdist, diff-cover, mypy, vulture, xenon, deptry, bandit, pip-audit. Add import-linter where the repo declares contracts.

`fast-tests` stays repo-local by decision. It is a no-op unless a developer exports `ENABLE_PRE_PUSH_TESTS=1`, and CI runs the suite anyway, so it adds nothing to a shared floor. A repo that wants it keeps it in its own config.

## Rules

- **Pin actions to a full commit SHA** with a version comment (`uses: actions/checkout@9c091bb2... # v7.0.0`). Floating tags are a supply-chain hole. This repo's own reusable workflows are the exception, and callers pin them to a major tag. See "Releasing a CI change" below. zizmor enforces hash pinning and rejects that tag, so every repo with a caller also needs `zizmor.yml` from `templates/repo/`, which grants ref-pinning to this repo alone.
- **Pin tool versions** everywhere else too: `uvx prek@X.Y.Z`, exact hook `rev`s, `--with pyyaml==X.Y.Z`.
- **`permissions: contents: read`** at the top of every workflow. Grant more only per job, only when needed (`id-token: write` for Codecov OIDC lives on the test job alone).
- **`persist-credentials: false`** on checkout unless the job pushes.
- **Concurrency groups** cancel superseded runs on the same ref.
- **Python tooling is `uv`**, and installs are `uv sync --locked`. A stale lockfile fails the build instead of silently re-resolving.
- **Nightly schedules** catch dependency drift on idle repos. Pick a distinct cron minute per repo. A scheduled security failure is a new upstream CVE, not a repo regression, and must not turn the badge red (`continue-on-error` on schedule).
- **Timeouts on every job.** 15 minutes for lint/audit, 20 for test matrices, unless measured otherwise.

## The repo checks

Every repo runs [`reusable-repo-checks.yml`](../.github/workflows/reusable-repo-checks.yml), whatever family it belongs to. Three jobs:

- **`pull-request`** reads the body and fails when the prose runs past 200 words outside code blocks, when a section runs past six lines, when a required section is missing or empty, or when a behavior change claims verification with nothing pasted and no data source named. A pull request that changes no behavior waives the evidence rule with the template's checkbox.
- **`issue`** applies the same body rules. An issue has no status check to fail, so it applies `needs-rewrite` and comments once instead, which is why the caller grants `issues: write`.
- **`layout`** fails when `AGENTS.md` is missing or its synced block is gone, when `CLAUDE.md` is missing or does not import `AGENTS.md`, or when `CLAUDE.md` carries content of its own. Sync overwrites that file, so anything kept there is lost on the next run and invisible to agents that read `AGENTS.md` in the meantime.

The rules live in `scripts/lint_body.py` and `scripts/check_repo_layout.py` here, standard library only, and the workflow fetches them. Changing the budget is one pull request rather than twelve.

`layout` checks structure, not bytes. A repo sitting between an ops release and its sync pull request is behind, not broken, and should not go red for it. Drift in the managed text is what sync exists to fix.

This caller is the one exception to "callers are not synced," below. It takes no repo-specific inputs, so a wholesale replacement overwrites nothing a repo owns, and one file keeps the rules comparable across the org. `zizmor.yml` ships with it: the caller names `@v1`, which zizmor rejects without the policy.

Making a check *required* is per-repo branch protection and no file can set it. Turn it on once a repo has run the checks green a few times.

## Auto-merging the sync pull request

Sync opens the same reviewed diff in thirteen repos. Reading it thirteen more times finds nothing; the per-repo CI signal is what the downstream pull request is for. So a repo can hand the merge decision to its own checks by adding its name to `auto_merge` in [`sync/manifest.yml`](../sync/manifest.yml):

```yaml
auto_merge:
  - portolan-sdi/stac-partition-extension
```

Sync then runs `gh pr merge --auto --squash` after opening or updating the pull request, and GitHub merges it when the required checks pass. Sync never merges anything directly. A repo left off the list keeps waiting for a human, which is the default.

Two conditions have to hold, and `scripts/sync.py` checks both rather than assuming them.

- **The base branch needs required status checks.** Without them GitHub's auto-merge merges on the spot, which throws away the signal the pull request exists for. Sync reads the branch's protection and rulesets, and skips the repo when the context list comes back empty. Classic branch protection answers only to `administration:read`; rulesets answer to the `contents:read` the sync token already holds, so a repo gated by rulesets needs no token change.
- **The repo needs `allow_auto_merge` on.** Without it the command fails. Sync reports that on the repo's summary line and carries on with the rest of the fan-out.

A run that writes anything under `.github/workflows/` skips auto-merge for that repo whatever else is true. A malformed workflow file breaks every event in a repo, including the checks that would have caught it, and that has happened here once already.

Dry runs skip auto-merge, since they push nothing to merge.

## Why AGENTS.md and CLAUDE.md both exist

`AGENTS.md` is canonical. It holds the org norms as text and any repo-specific rules below the marker.

Claude Code [does not read `AGENTS.md`](https://code.claude.com/docs/en/memory.md). A repo carrying it alone shows Claude Code nothing at all. `CLAUDE.md` therefore holds one import line and nothing else, which is the pattern the Claude Code docs prescribe. A symlink would work on Linux and macOS and fail for Windows contributors, and it could not carry the sync markers.

The block carries the norms in full rather than linking to them, because an agent loads what a file says and does not fetch URLs to find out. `scripts/build_agents_block.py` generates `templates/repo/AGENTS.md` from this repo's own `AGENTS.md`, and `check.yml` fails when the two drift.

## The security audit

The family workflow holds the gate: its security job runs bandit and pip-audit, and a finding turns the pull request red. [`reusable-security-audit.yml`](../.github/workflows/reusable-security-audit.yml) holds the notification. It runs pip-audit nightly and keeps one tracking issue in step with the result, opening it on a finding and closing it with a comment when the audit goes clean.

The split follows from the rule above: a scheduled security failure is an upstream CVE, so the badge stays green and the finding needs somewhere else to land. A red run sits in the Actions tab. An issue lands where the work is already tracked.

It is a separate workflow rather than another job in the family because the audit needs `issues: write`. GitHub validates a called workflow's requested permissions even for jobs that never run, so folding it in would force the permission on every caller in the family and cost a major version.

Opt in by copying [`ci/python-package/security-audit.yml`](../ci/python-package/security-audit.yml) and picking a distinct cron minute. A repo without triage habits should leave it off, since an issue nobody reads is noise rather than signal.

## Mutation testing

Every other gate confirms the code runs. Mutation testing asks whether the tests notice when the code changes. mutmut alters the source one edit at a time and reruns the suite, and a mutant that survives means no test objected.

The sweep is slow, so it runs nightly rather than on pull requests. A repo opts in by setting `mutation: true` on its caller. Doing so adds mutmut to the dev-dependency contract, and the repo also needs a `[tool.mutmut]` block in `pyproject.toml` naming the paths to mutate.

Scoring lives in one place, `scripts/mutation_score.py`, which syncs from `templates/repo/scripts/`. Before this job existed, rashid and portolan-cli each computed a kill rate their own way, and the two numbers were not comparable.

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

Copy the family's caller from `ci/` into the repo's `.github/workflows/ci.yml`, its `dependabot.yml` into `.github/dependabot.yml`, and `templates/repo/zizmor.yml` into `zizmor.yml` (or add the repo to `sync/manifest.yml` and let sync open the PR). A repo that already has a Dependabot config gets it replaced, so reconcile the ecosystems first. Delete the repo's superseded inline workflows in the same PR, after confirming the caller run is green.

The family caller itself is not synced. Repos need different inputs, and sync replaces files wholesale, so a synced caller would overwrite them on every run. Copy it once and let the repo own it. Changes to the shared logic still arrive through the tag. The repo checks caller is the exception, for the reason given above.

The zizmor policy is not optional. Without it, the repo's own lint job fails on the caller's tag.
