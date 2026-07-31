# CI norms

CI logic lives in reusable workflows here. Downstream repos carry thin callers that reference them by tag. This means a CI change is one pull request here instead of one per repo.

## Workflow families

Python packages (rashid, portolan-cli) use [`reusable-python-ci.yml`](../.github/workflows/reusable-python-ci.yml). STAC extensions (stac-partition-extension, stac-iceberg-extension, stac-osi-extension) use [`reusable-stac-ext.yml`](../.github/workflows/reusable-stac-ext.yml). Web apps (portolan-sdi.org, portolan-browser, portolan-nl-demo) use [`reusable-web-ci.yml`](../.github/workflows/reusable-web-ci.yml). Each family has a caller template in `ci/` that repos copy to their own workflows directory.

The [repo checks](#the-repo-checks) run on every repo. The [security audit](#the-security-audit) is optional; Python repos opt in by copying [`ci/python-package/security-audit.yml`](../ci/python-package/security-audit.yml).

A repo with needs beyond its family (release workflows, deploys, e2e suites) keeps those as its own workflows alongside the caller. The family covers the shared floor: lint, quality gates, security audit, tests with coverage.

portolan-registry keeps its own workflows because it holds JSON schemas and a catalog of catalogs, not a package.

## Changing and releasing CI

Edit the reusable workflow here. CI validates workflow syntax with `check.yml` and runs the Python floor end to end against `tests/fixture-package` with `ci-selftest.yml`.

Merge the change to main. The change reaches the fleet when the major tag moves, not at merge. This leaves room to test on one repo first before rolling out everywhere.

To release: confirm `ci-selftest.yml` is green on the merge commit, point one downstream repo at `@main` and let a real run go green, then revert it to `@v1`. Cut an immutable tag and move the major tag:

```bash
git tag -a v1.1.0 -m "prek 0.4.12, wider test matrix" <sha>
git push origin v1.1.0
git tag -f v1 v1.1.0
git push -f origin v1
```

Moving `v1` overwrites where it used to point. The fixed tag gives each release a permanent name, and a bad release is rolled back by moving `v1` onto the previous tag.

A change that breaks callers ships as `v2`. Downstream repos keep running `@v1` until they opt in to move. Each family caller travels with a `dependabot.yml` so updates arrive automatically.

The tag move is easy to forget, and a forgotten move means the fleet enforces stale rules while this repo believes the fix shipped. [`tag-guard.yml`](../.github/workflows/tag-guard.yml) runs `scripts/check_release_tag.py` after any merge touching the enforcement files and fails until `v1` carries them. The weekly run keeps a tracking issue open while the lag persists.

## Adding a repo to a family

Copy the family's caller from `ci/` into `.github/workflows/ci.yml`. Copy `dependabot.yml` into `.github/dependabot.yml`. Copy `templates/repo/zizmor.yml` into `zizmor.yml`, or add the repo to `sync/manifest.yml` and let sync open the PR.

If the repo already has a Dependabot config, reconcile the ecosystems first. Delete superseded inline workflows after confirming the caller run is green.

The family caller itself is not synced. Repos need different inputs and sync replaces files wholesale; a synced caller would overwrite settings on every run. Copy it once and let the repo own it. Changes to shared logic still arrive through the tag.

The zizmor policy is required. Without it the lint job fails on the caller's tag.

The first run will probably fail. Switching on strict rules against existing code surfaces whatever accumulated before.

## Python quality floor

The reusable Python workflow enforces one floor across the family. Repos declare the floor's tools as dev dependencies: pytest, pytest-cov, pytest-xdist, diff-cover, mypy, vulture, xenon, deptry, bandit, pip-audit, and import-linter where contracts are declared.

The synced `.pre-commit-config.yaml` holds every lint and quality rule. Commit stage runs ruff-check, ruff-format, codespell, actionlint, zizmor, and file hygiene. Pre-push stage runs mypy, vulture, xenon, deptry, and import-linter. CI runs both stages with `uvx prek`, so an unhooked clone meets the same gate. commitizen runs at commit-msg but not in CI, since squash-merge makes the pull request title the commit message that lands.

deptry finds unused, missing, and transitive imports with no per-repo configuration needed. import-linter runs where a repo declares `[tool.importlinter]` contracts and skips where it does not; a repo turns the gate on by writing its first contract.

bandit and pip-audit run on every PR. Ignores live in `.pip-audit-ignores` with a mandatory expiry date and reason; expired entries fail CI automatically. xenon is the hard gate at pre-push and measures code complexity. wily reports complexity trends on PRs in a non-blocking job.

pytest writes `coverage.xml` and Codecov receives it over OIDC with no token secrets. `diff-cover` requires 90% coverage on changed lines in PRs.

Pull requests run the test matrix on ubuntu alone (`os-pull-request`). Schedule, push, and dispatch runs use ubuntu, macos, and windows. Path handling breaks on Windows, and a package on PyPI must work on all three. Keep ubuntu in `os-pull-request` because Codecov and diff-cover gate only there.

Mutation testing runs nightly when a repo opts in with `mutation: true` on its caller. See [Mutation testing](#mutation-testing).

`fast-tests` stays repo-local. It is a no-op unless a developer exports `ENABLE_PRE_PUSH_TESTS=1`, and CI runs the suite anyway regardless.

## CI rules

Pin actions to a full commit SHA with a version comment (`uses: actions/checkout@9c091bb2... # v7.0.0`). Floating tags are a supply-chain hole. This repo's reusable workflows are the exception; callers pin them to a major tag. zizmor enforces hash pinning and rejects that tag, so every repo with a caller needs `zizmor.yml` from `templates/repo/` to grant this repo alone ref-pinning.

Pin tool versions everywhere else: `uvx prek@X.Y.Z`, exact hook `rev`s, `--with pyyaml==X.Y.Z`.

Set `permissions: contents: read` at the top of every workflow. Grant more only per job, only when needed (e.g., `id-token: write` for Codecov OIDC on the test job alone).

Set `persist-credentials: false` on checkout unless the job pushes.

Use concurrency groups to cancel superseded runs on the same ref.

Use `uv` for Python tooling. Installs use `uv sync --locked`. A stale lockfile fails the build instead of silently re-resolving.

Nightly schedules catch dependency drift. Pick a distinct cron minute per repo. A scheduled security failure is an upstream CVE, not a regression. Use `continue-on-error` on schedule so the badge stays green.

Set timeouts on every job: 15 minutes for lint and audit, 20 minutes for test matrices unless measured otherwise.

## Repo checks

Every repo runs [`reusable-repo-checks.yml`](../.github/workflows/reusable-repo-checks.yml). The pull-request job reads the body and fails when prose runs past 200 words outside code blocks, when a section runs past six lines, when a required section is missing or empty, or when a behavior change claims verification with nothing pasted. A pull request that changes no behavior waives the evidence rule with the template's checkbox.

The issue job applies the same rules and applies `needs-rewrite` with a comment instead of failing (issues have no status check). The caller grants `issues: write`.

The layout job fails when `AGENTS.md` is missing or its synced block is gone, when `CLAUDE.md` is missing or does not import `AGENTS.md`, or when `CLAUDE.md` carries content of its own. Sync overwrites `CLAUDE.md`, so anything kept there is lost on the next run.

The rules live in `scripts/lint_body.py` and `scripts/check_repo_layout.py` (standard library only). The workflow fetches them. Changing the budget is one pull request rather than twelve.

Layout checks structure, not bytes. A repo sitting between an ops release and its sync pull request is behind, not broken. It should not fail for drift that sync exists to fix.

This caller is the exception to "callers are not synced." It takes no repo-specific inputs, so replacement overwrites nothing a repo owns. One file keeps rules comparable across the org. `zizmor.yml` ships with it because the caller names `@v1`, which zizmor rejects without the policy.

Branch protection makes a check required, not a file. Turn it on once a repo has run the checks green a few times.

## Sync distribution

[`sync/manifest.yml`](../sync/manifest.yml) drives the fan-out. [`sync.yml`](../.github/workflows/sync.yml) opens or updates one `ops-sync` pull request per affected repo. The managed file set is small on purpose.

Community health files (org profile, code of conduct, contributing guide, security policy, issue and PR templates) go to the [`.github`](https://github.com/portolan-sdi/.github) repo. GitHub applies these to every repo that lacks its own.

`LICENSE` (Apache-2.0) goes to every active repo because GitHub does not inherit licenses.

Thin CI caller workflows go to repos by family. The logic lives in reusable workflows here; callers reference them by tag.

An `AGENTS.md` pointer block goes to the top of each downstream `AGENTS.md`. Repo-specific content below the block is never touched. A matching `CLAUDE.md` bridge (one import line) goes to every active repo. See [Why AGENTS.md and CLAUDE.md both exist](#why-agentsmd-and-claudemd-both-exist).

The repo checks caller and zizmor policy go to every active repo. They hold bodies to 200 words with pasted evidence and keep the two agent files in shape.

`_brand-vars.css` (generated from `brand/brand.json` by `brand/emit_css.py`) is planned for website and browser but not yet in the manifest.

Sync refuses to push when the `ops-sync` branch carries a commit sync did not write, since the force-push would discard that person's work. Land or drop the foreign commits, then re-run.

The first sync to a repo is merged by hand. It always delivers `.github/workflows/repo-checks.yml`, which disqualifies auto-merge, and the layout check that would flag the missing agent files arrives in the same pull request. Expect the repo's own linters to complain about the synced files on that first pass; fix the ignores in that repo and merge.

[`sync-drift.yml`](../.github/workflows/sync-drift.yml) compares the fleet to ground truth weekly. Drift, a clone error, or an active org repo the manifest sends nothing to fails the run and keeps a tracking issue open here until the fleet converges.

## Auto-merging sync pull requests

A repo can hand the merge decision to its own checks by adding its name to `auto_merge` in [`sync/manifest.yml`](../sync/manifest.yml):

```yaml
auto_merge:
  - portolan-sdi/stac-partition-extension
```

Sync runs `gh pr merge --auto --squash` and GitHub merges when required checks pass. Sync never merges directly. A repo left off the list waits for a human.

Two conditions must hold. The base branch needs required status checks; otherwise auto-merge merges on the spot and the check signal is lost. The repo needs `allow_auto_merge` on; without it the command fails.

A run that writes anything under `.github/workflows/` skips auto-merge for that repo because a malformed workflow file breaks every event including the checks that would catch it.

Dry runs skip auto-merge because they push nothing to merge.

## AGENTS.md and CLAUDE.md

`AGENTS.md` is canonical and holds org norms and repo-specific rules below the marker. Claude Code does not read `AGENTS.md` and would show Claude Code nothing if it were the only file. `CLAUDE.md` holds one import line and nothing else, which is the pattern the Claude Code docs prescribe. A symlink would fail for Windows contributors and could not carry sync markers.

The block carries norms in full rather than linking because an agent loads what a file says and does not fetch URLs. `scripts/build_agents_block.py` generates `templates/repo/AGENTS.md` from this repo's `AGENTS.md`. `check.yml` fails when the two drift.

## Security audit

The family workflow runs bandit and pip-audit and a finding turns the PR red. [`reusable-security-audit.yml`](../.github/workflows/reusable-security-audit.yml) runs pip-audit nightly and keeps one tracking issue in sync, opening it on a finding and closing it when clean.

A scheduled security failure is an upstream CVE, so the badge stays green. A red run sits in Actions. An issue lands where work is tracked.

It is separate from the family workflow because the audit needs `issues: write`. GitHub validates a called workflow's permissions even for jobs that never run. Folding it in would force the permission on every caller and cost a major version.

Opt in by copying [`ci/python-package/security-audit.yml`](../ci/python-package/security-audit.yml) and picking a distinct cron minute. A repo without triage habits should leave it off because an unread issue is noise.

## Mutation testing

Mutation testing asks whether tests notice when code changes. mutmut alters the source one edit at a time and reruns the suite. A mutant that survives means no test objected. The sweep is slow, so it runs nightly instead of on pull requests. A repo opts in by setting `mutation: true` on its caller and adding a `[tool.mutmut]` block in `pyproject.toml` naming the paths to mutate.

Scoring lives in one place, `scripts/mutation_score.py`, which syncs from `templates/repo/scripts/`. Before this existed, rashid and portolan-cli each computed kill rates their own way and the numbers were not comparable.

```
killed_total = killed + timeout + suspicious
testable     = killed_total + survived
kill_rate    = killed_total / testable
```

A timeout or suspicious result means the suite reacted, so both count as kills. Mutants with no covering test are excluded rather than counted as failures because coverage measures that gap. Zero testable mutants fails the run.

Each repo keeps its own floor in `.mutation-baseline`, a single number. Ratchet it up as the suite improves. Lowering it needs justification in the pull request.

### Sharding mutation tests

A repo whose full sweep no longer fits the timeout sets `mutation-shards` to a number above zero. Each night mutates one slice, chosen by day of year, and the whole tree is covered every `mutation-shards` nights.

Shard membership comes from a hash of each file's path, not its position in a sorted list. Adding a module moves only that module, leaving recorded per-shard rates valid.

A single slice's kill rate depends on which modules land in it. Measured slices in portolan-cli ranged from 18% to 95%, so one repo-wide floor either flaps or gates nothing. A repo that shards should record each slice's own rate in `.mutation-shards.json`. The scorer enforces it alongside the repo-wide floor.

## Tool versions

`prek` and `pyyaml` repeat across workflows. Both read org-level Actions variables `PREK_VERSION` and `PYYAML_VERSION`. Setting one variable bumps the tool everywhere in a single edit:

```yaml
env:
  PREK_VERSION: ${{ vars.PREK_VERSION || '0.4.11' }}
```

The literal after `||` is a fallback. Inside a reusable workflow, `vars` resolves against the caller's repository, not this one. A fork or caller outside the org sees no variable and would otherwise run bare.

Changing the variable takes effect across every repo with no pull request and no review. Treat it as a deployment.

`wily` stays pinned inline because a `uvx wily@X.Y.Z` argument has no `env:` value to read.

Dependabot does not see `env:` values or `uvx` arguments, so fallbacks go stale without maintenance. `bump-tools.yml` runs weekly, asks PyPI for the newest prek, pyyaml, and wily, rewrites every literal that moved, and opens a pull request. CI runs the new versions before anyone merges.

The job writes files under `.github/workflows`. `GITHUB_TOKEN` may not do that at any permission level, so the job mints an app token with `workflows: write`.

A bumper that stops matching its patterns fails quietly. `scripts/test_bump_tools.py` tests the rewrite. `check.yml` runs `bump_tools.py --check`, which fails when a pattern no longer matches.

An org variable overrides the literal. While one is set, the bumper's pull request changes nothing on its own; the pull request body prints the command to update the variable.
