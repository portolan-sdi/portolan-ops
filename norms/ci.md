# CI Norms

Shared CI logic lives in reusable workflows. Downstream repos use thin caller workflows that reference these reusable ones by tag. This approach means you change CI in one place instead of updating every repo.

## Workflow Families

Three workflow families handle different repo types. Python packages like rashid and portolan-cli use `reusable-python-ci.yml`. STAC extensions like stac-partition-extension and stac-iceberg-extension use `reusable-stac-ext.yml`. Web apps like portolan-sdi.org and portolan-browser use `reusable-web-ci.yml`.

Each family includes a caller template in the `ci/` directory. Repos copy this caller into their own `.github/workflows/` directory once.

All repos run repo checks automatically. Python repos can optionally enable security audits by copying `ci/python-package/security-audit.yml`.

Repos with specialized needs keep those workflows alongside the shared caller. Release workflows, deploys, and end-to-end test suites live as repo-local files. The shared caller provides the baseline: linting, quality gates, security audits, and test coverage.

The portolan-registry repo is different. It stores JSON schemas and a catalog index, not a package. It maintains its own workflows.

## Changing and Releasing CI

Edit the reusable workflow in this repo. Two validation workflows run automatically. `check.yml` validates workflow syntax. `ci-selftest.yml` runs the Python floor end to end against a fixture package.

Merge your change to main. The change reaches other repos only when you move the major version tag, not at merge. This gives you a window to test the change on one repo first.

To release: confirm `ci-selftest.yml` is green on your merge commit. Point one downstream repo at `@main` and let it run. When that run is green, point it back to `@v1`. Now cut an immutable tag and move the major tag.

```bash
git tag -a v1.1.0 -m "prek 0.4.12, wider test matrix" <sha>
git push origin v1.1.0
git tag -f v1 v1.1.0
git push -f origin v1
```

Moving `v1` to the new tag gives all repos the update. The immutable tag `v1.1.0` becomes the release record. If something breaks, move `v1` back to the previous tag to roll back the change.

A breaking change ships as `v2`. Downstream repos keep using `@v1` until they explicitly update. Each family caller includes a `dependabot.yml` so updates can arrive automatically.

A script called `tag-guard.yml` runs after any merge that touches enforcement files. It checks that `v1` points to the current code and fails if the tag is stale. This prevents the fleet from running old rules while this repo believes new ones have shipped. The script also opens a tracking issue if the lag persists.

## Adding a Repo to a Family

Copy the family's caller workflow from `ci/` into the new repo's `.github/workflows/ci.yml`. Copy `dependabot.yml` into `.github/dependabot.yml`. Copy `templates/repo/zizmor.yml` into `zizmor.yml`, or add the repo to `sync/manifest.yml` and let the sync process open a pull request.

If the repo already has a Dependabot config, reconcile the ecosystems first. Delete any old workflows after the new caller runs green.

Don't sync the caller workflow itself. Repos have different inputs. Syncing would overwrite repo-specific settings on every run. Copy it once and let the repo maintain it. Updates to shared logic still arrive through the major version tag.

The zizmor policy file is required. Without it, the lint job will fail on the caller's tag reference.

The first run will probably fail. Enabling strict rules against existing code often surfaces accumulated issues. Fix linter ignores as needed.

## Python Quality Floor

The Python workflow enforces one quality floor across all Python repos. Repos declare these tools as dev dependencies: pytest, pytest-cov, pytest-xdist, diff-cover, mypy, vulture, xenon, deptry, bandit, pip-audit, and import-linter.

The synced `.pre-commit-config.yaml` holds every lint and quality rule. At commit stage, ruff-check, ruff-format, codespell, actionlint, zizmor, and file checks run. At pre-push stage, mypy, vulture, xenon, deptry, and import-linter run. CI runs both stages with `uvx prek`, so even an unhooked clone meets the same gate.

commitizen runs at commit-msg but not in CI. Squash-merge makes the pull request title become the commit message, so the tool adds no value in CI.

deptry finds unused, missing, and transitive imports with no per-repo configuration. import-linter runs only in repos that declare `[tool.importlinter]` contracts. A repo turns this gate on by writing its first contract.

bandit and pip-audit run on every pull request. Ignores live in `.pip-audit-ignores` with a mandatory expiry date and reason. Expired entries fail CI automatically.

xenon measures code complexity. It is a hard gate at pre-push. wily reports complexity trends on pull requests but does not block merges.

pytest writes `coverage.xml` and Codecov receives it over OIDC without token secrets. `diff-cover` requires 90% coverage on changed lines in pull requests.

Pull requests run tests on Ubuntu only. Scheduled, push, and manual dispatch runs use Ubuntu, macOS, and Windows. Path handling breaks on Windows, and packages on PyPI must work on all three. Keep Ubuntu in the PR job because Codecov and diff-cover gate only there.

Mutation testing runs nightly when a repo opts in. See the Mutation testing section below.

`fast-tests` stays repo-local. It is a no-op unless a developer sets `ENABLE_PRE_PUSH_TESTS=1`. CI runs the full suite regardless.

## CI Rules

Pin actions to a full commit SHA with a version comment: `uses: actions/checkout@9c091bb2... # v7.0.0`. Floating tags are a supply-chain risk.

This repo's reusable workflows are the exception. Callers pin them to a major tag. zizmor enforces hash pinning and rejects that tag, so every repo with a caller needs `zizmor.yml` from `templates/repo/` to allow this repo's tag.

Pin tool versions everywhere else. Use exact hook `rev`s and exact versions in uvx and pip commands like `--with pyyaml==X.Y.Z`.

Set `permissions: contents: read` at the top of every workflow. Grant more only per job, only when needed. The test job needs `id-token: write` for Codecov OIDC. The sync job needs `contents: write` to push.

Never filter `pull_request` by branch. GitHub matches `branches:` under `pull_request` against the base branch, so a workflow that names `main` there queues nothing for a pull request into any other branch, and a release branch merges unchecked. Keep the filter on `push`, where a push to a side branch is not a merge. `scripts/check_workflow_triggers.py` fails `check.yml` when the filter returns, in this repo's workflows and in the caller templates under `ci/`.

Set `persist-credentials: false` on checkout unless the job pushes.

Use concurrency groups to cancel superseded runs on the same ref.

Use `uv` for Python tooling. Run installs with `uv sync --locked`. A stale lockfile fails the build instead of silently resolving dependencies again.

Nightly schedules catch dependency drift. Pick a distinct cron minute per repo. A scheduled security failure is an upstream CVE, not a regression. Use `continue-on-error` on schedule so the badge stays green.

Set timeouts on every job. Lint and audit jobs get 15 minutes. Test matrices get 20 minutes unless you measure something longer.

## Repo Checks

Every repo runs `reusable-repo-checks.yml`. The pull-request job reads the PR body. It fails when a required section is missing or empty, when no issue is referenced, or when a behavior change claims verification with nothing pasted. A pull request that changes no behavior can skip the evidence rule by checking the template's checkbox.

This job checks structure, not writing. It counts nothing. A long body full of evidence and implementation detail is what a reviewer and an agent both need, and CI must never push an author to compress it.

There is no issue job. Writing quality is handled before a body is filed, not labelled after. The `needs-rewrite` label is gone.

The layout job fails when `AGENTS.md` is missing, when its synced block is gone, when `CLAUDE.md` is missing, when `CLAUDE.md` does not import `AGENTS.md`, or when `CLAUDE.md` carries its own content. The sync process overwrites `CLAUDE.md`, so content kept there is lost on the next run. It also fails when `.claude/settings.json` wires no writing hook.

The rules live in `scripts/lint_body.py` and `scripts/check_repo_layout.py`, which use only the standard library. Changing one means one pull request here instead of twelve across all repos.

## Branch Protection

`sync/protection.yml` records the checks each branch requires. One entry per protected branch: the repo, the branch, the regime, and the contexts. Every entry names `checks / layout` and `checks / pull-request`, which `repo-checks.yml` posts in every repo, plus whatever that repo runs of its own.

GitHub holds the gate in one of two places, and they share no state. Classic branch protection answers `repos/{owner}/{repo}/branches/{branch}/protection`, and reading it needs `administration:read`. A repository ruleset answers `repos/{owner}/{repo}/rules/branches/{branch}` from `contents:read`. A repo that moves from one to the other keeps none of its old contexts. portolan-cli lost both org checks that way, and nothing reported it.

`scripts/check_protection.py` reads the record, reads the live setting, and prints one row per branch with what is missing and what is extra. It exits non-zero on any difference, and on a branch it cannot read. `protection-audit.yml` runs it every Monday and keeps one tracking issue open in ops while the fleet differs.

Nothing applies these settings automatically. A person does, with the endpoint that edits the check list alone:

```bash
gh api -X PATCH \
  repos/OWNER/REPO/branches/main/protection/required_status_checks \
  -f 'contexts[]=checks / layout' \
  -f 'contexts[]=checks / pull-request'
```

`PUT .../protection` replaces the whole protection object, so a call that names only the checks drops the review rules with it.

Add a repo to the record once it has run its checks green a few times. Require only checks that report on a pull request. A job that runs on push or on a schedule never reports on one, so requiring it leaves the pull request waiting forever.

## The Writing Hook

The rules are an output style. `.claude/output-styles/simplified-technical-english.md` holds Simplified Technical English (ASD-STE100). It is the one canonical copy.

`.claude/hooks/writing_check.py` runs as a Claude Code hook in every repo. At session start it prints that output style as context, which activates it for the repo. This mirrors how a personal `prose-style-activate.js` hook activates a style globally. Before `gh issue create` or `gh pr create`, the same file reads the body and denies the call when it finds a blocking problem, and it names the line and the fix.

The blocking rules are the STE rules that a machine can check. Verb form carries most of the weight: STE allows the infinitive, the imperative, and the simple present, past, and future. A gerund, a present participle, a passive, and a perfect tense each fail. A sentence over 20 words fails, which is the STE limit. The word rules ban filler, hype, and a word where a simpler approved word exists.

Article dropping and noun clusters need part-of-speech data, so they advise or are absent.

An author overrides a wrong call with `<!-- ste-ok: RULE_ID reason -->` on the line above. The reason is required and stays in the diff, so `grep -c 'ste-ok'` measures how hard people are fighting a rule. A rule people fight should be retired.

The hook matches word lists and punctuation. It does not read tone, and it cannot tell padding or self-justifying prose from useful detail, so a body can pass it and still read badly. Passing is not evidence that a body is well written, and reviewers should not treat it that way.

Two other limits are worth knowing. A body written through a heredoc rather than `--body` or `--body-file` is not seen, because the hook does not evaluate shell. A contributor using the GitHub web form is bound by the templates and the CI structural check only.

`.claude/settings.json` syncs in `merge-json` mode rather than `copy`. A repo may wire hooks of its own, and a wholesale copy would delete them. The merge rewrites only the entries whose command names `writing_check.py` and leaves everything else alone, so a second run produces no diff.

This caller is the exception to the "callers are not synced" rule. It takes no repo-specific inputs, so replacement changes nothing the repo owns. One file keeps rules comparable across the organization.

Branch protection makes a check required at the GitHub level, not in the file. Record it in `sync/protection.yml` and apply it once a repo has run the checks green a few times. See Branch Protection above.

## Sync Distribution

`sync/manifest.yml` drives the fan-out. `sync.yml` opens or updates one `ops-sync` pull request per affected repo. The managed file set is small on purpose.

Community health files live in the [`.github`](https://github.com/portolan-sdi/.github) repo. GitHub applies these to every repo that lacks its own. These include the org profile, code of conduct, contributing guide, security policy, and issue and pull request templates.

`LICENSE` (Apache-2.0) goes to every active repo. GitHub does not inherit licenses.

CI caller workflows go to repos by family. The logic lives in reusable workflows. Callers reference them by tag.

An `AGENTS.md` pointer block goes to the top of each downstream `AGENTS.md`. Repo-specific content below the block is never touched. A matching `CLAUDE.md` file (one import line) goes to every active repo. See the section on AGENTS.md and CLAUDE.md below.

The repo checks caller and zizmor policy go to every active repo. They enforce the 200-word body limit with pasted evidence and keep the two agent files in shape.

`_brand-vars.css` is generated from `brand/brand.json` by `brand/emit_css.py`. It is planned for the website and browser but not yet in the manifest.

Sync refuses to push when the `ops-sync` branch carries a commit that sync did not write. The force-push would discard that person's work. Land or drop foreign commits, then re-run sync.

The first sync to a repo is merged by hand. It always delivers `.github/workflows/repo-checks.yml`, which disqualifies auto-merge. The layout check that flags missing agent files arrives in the same pull request. Expect the repo's own linters to complain about synced files on that first pass. Fix the ignores in that repo and merge.

`sync-drift.yml` compares the fleet to ground truth weekly. It fails and keeps a tracking issue open if drift is found, if a clone failed, or if the manifest sends nothing to an active org repo. It never reports portolan-ops itself, which holds the originals and cannot be a target of its own fan-out.

Sync writes a repo's default branch and nothing else. A long-lived release branch therefore keeps whatever synced files it forked with, which is how portolan-cli's `release/v1.0.0b0` came to carry `.claude/settings.json` without `.claude/hooks/writing_check.py` and fail its own layout check. Name such a branch under `extra_branches` in `sync/manifest.yml` and the weekly report reads it as its own row:

```yaml
extra_branches:
  portolan-sdi/portolan-cli:
    - release/v1.0.0b0
```

That makes the drift visible. It delivers nothing. The repo cherry-picks the missing files itself.

## Auto-Merging Sync Pull Requests

A repo can hand merge decisions to its own checks. Add the repo name to `auto_merge` in `sync/manifest.yml`:

```yaml
auto_merge:
  - portolan-sdi/stac-partition-extension
```

Sync runs `gh pr merge --auto --squash`. GitHub merges when required checks pass. Sync never merges directly.

Two conditions must hold. The base branch needs required status checks. Without them, auto-merge merges immediately and the check signal is lost. The repo needs `allow_auto_merge` enabled. The command fails without it.

A run that writes anything under `.github/workflows/` skips auto-merge for that repo. A malformed workflow file breaks every event, including the checks that would catch the error.

Dry runs skip auto-merge because they push nothing to merge.

## AGENTS.md and CLAUDE.md

`AGENTS.md` is canonical. It holds org norms and repo-specific rules below a marker block. Claude Code does not read `AGENTS.md`, so the file alone would show Claude Code nothing. `CLAUDE.md` holds one import line and nothing else. This matches the pattern the Claude Code docs prescribe.

A symlink would fail for Windows contributors and could not carry sync markers. The block carries norms in full instead of linking because agents load what a file says and do not fetch URLs.

`scripts/build_agents_block.py` generates `templates/repo/AGENTS.md` from this repo's `AGENTS.md`. `check.yml` fails if the two drift.

## Security Audit

The Python family workflow runs bandit and pip-audit. A finding turns the pull request red.

`reusable-security-audit.yml` runs pip-audit nightly and keeps one tracking issue in sync. It opens the issue on a finding and closes it when clean.

A scheduled security failure is an upstream CVE, so the badge stays green. The red run sits in Actions. The issue tracks where work happens.

This workflow is separate from the family workflow because it needs `issues: write`. GitHub validates called workflow permissions even for jobs that never run. Folding it in would force the permission on every caller and require a major version bump.

Opt in by copying `ci/python-package/security-audit.yml` and picking a distinct cron minute. A repo without triage habits should skip this because an unread issue is noise.

## Mutation Testing

Mutation testing checks whether tests notice when code changes. mutmut edits the source one change at a time and reruns the suite. A mutant that survives means no test objected. The sweep is slow, so it runs nightly instead of on pull requests.

A repo opts in by setting `mutation: true` on its caller and adding a `[tool.mutmut]` block in `pyproject.toml` that names the paths to mutate.

Scoring lives in one place: `scripts/mutation_score.py`. Before this existed, rashid and portolan-cli each computed kill rates their own way. The numbers were not comparable.

The formula is:

```
killed_total = killed + timeout + suspicious
testable     = killed_total + survived
kill_rate    = killed_total / testable
```

A timeout or suspicious result means the suite reacted, so both count as kills. Mutants with no covering test are excluded rather than counted as failures because coverage measures that gap. Zero testable mutants fails the run.

Each repo keeps its own floor in `.mutation-baseline`. Ratchet it up as the suite improves. Lowering it needs justification in the pull request.

### Sharding Mutation Tests

A repo whose full sweep no longer fits the timeout can set `mutation-shards` to a number above zero. Each night mutates one slice, chosen by day of year. The whole tree is covered every `mutation-shards` nights.

Shard membership comes from a hash of each file's path, not its position in a sorted list. Adding a module moves only that module. Recorded per-shard rates stay valid.

A single slice's kill rate depends on which modules land in it. Measured slices in portolan-cli ranged from 18% to 95%. A single repo-wide floor either flaps or gates nothing. A repo that shards should record each slice's own rate in `.mutation-shards.json`. The scorer enforces it alongside the repo-wide floor.

## Tool Versions

`prek` and `pyyaml` repeat across workflows. Both are read from org-level Actions variables `PREK_VERSION` and `PYYAML_VERSION`. Setting one variable bumps the tool everywhere in a single edit:

```yaml
env:
  PREK_VERSION: ${{ vars.PREK_VERSION || '0.4.11' }}
```

The value after `||` is a fallback. Inside a reusable workflow, `vars` resolves against the caller's repository, not this one. A fork or caller outside the org sees no variable and uses the fallback.

Changing the variable takes effect across every repo with no pull request and no review. Treat it as a deployment.

`wily` stays pinned inline because a `uvx wily@X.Y.Z` argument has no `env:` value to read.

Dependabot does not see `env:` values or `uvx` arguments, so fallbacks go stale without maintenance. `bump-tools.yml` runs weekly. It asks PyPI for the newest prek, pyyaml, and wily. It rewrites every literal that moved and opens a pull request. CI runs the new versions before anyone merges.

The job writes files under `.github/workflows`. `GITHUB_TOKEN` cannot do this at any permission level, so the job mints an app token with `workflows: write`.

A bumper that stops matching its patterns fails quietly. `scripts/test_bump_tools.py` tests the rewrite. `check.yml` runs `bump_tools.py --check`, which fails when a pattern no longer matches.

An org variable overrides the literal. While one is set, the bumper's pull request changes nothing on its own. The pull request body prints the command to update the variable.
