# CI norms

Reusable workflows define shared CI logic. Repos call them by version tag, so a shared change reaches every caller without edits in each repo.

## Workflow families

Each repo type uses a workflow family:

| Repo type | Workflow | Examples |
|---|---|---|
| Python packages | `reusable-python-ci.yml` | rashid, portolan-cli |
| STAC extensions | `reusable-stac-ext.yml` | stac-partition-extension, stac-iceberg-extension |
| Web apps | `reusable-web-ci.yml` | portolan-sdi.org, portolan-browser |

Caller templates live in `ci/`. Copy the appropriate template into the repo's `.github/workflows/` directory.

Each family provides baseline linting, quality, security, and coverage checks. All repos also run repo checks. Python repos can opt into nightly security audits with `ci/python-package/security-audit.yml`.

Release, deployment, end-to-end, and other specialized workflows stay in each repo alongside the shared caller.

## Changing and releasing CI

Edit the reusable workflow in portolan-ops. Two workflows run automatically:

- `check.yml` validates workflow syntax.
- `ci-selftest.yml` runs the Python checks against a fixture package.

Merging to `main` does not update downstream repos. They receive the change when you move the major version tag.

To release:

1. Confirm that `ci-selftest.yml` passes on the merge commit.
2. Point one downstream caller at `@main` and confirm that its checks pass.
3. Return that caller to `@v1`.
4. Create an immutable release tag and move the major tag:

```bash
git tag -a v1.1.0 -m "prek 0.4.12, wider test matrix" <sha>
git push origin v1.1.0
git tag -f v1 v1.1.0
git push -f origin v1
```

The immutable tag records the release. Moving `v1` updates every repo that uses it. To roll back, move `v1` to the previous release tag.

Release breaking changes under `v2`. Existing callers stay on `@v1` until they update. Each family includes a `dependabot.yml` template to automate update pull requests.

After a merge that changes enforcement files, `tag-guard.yml` checks whether `v1` points to the current code. A stale tag fails the check because downstream repos still enforce older rules. The workflow opens a tracking issue if the lag persists.

## Adding a repo to a family

1. Copy the family's caller from `ci/` to `.github/workflows/ci.yml`.
2. Copy its `dependabot.yml` to `.github/dependabot.yml`. If a config already exists, combine the ecosystem entries.
3. Copy `templates/repo/zizmor.yml` to `zizmor.yml`, or add the repo to `sync/manifest.yml` and let sync open a pull request.
4. Fix any failures in the new checks, including linter ignores where needed.
5. Delete the old workflows after the new caller passes.

The zizmor policy is required: without it, linting rejects the caller's version tag.

Family callers are copied once and maintained by each repo. Do not sync them: repos use different inputs, and sync would overwrite those settings. Shared logic still updates through the major version tag.

Expect the first run to find problems in existing code.

## Python quality requirements

Python repos must declare these development dependencies:

```text
pytest
pytest-cov
pytest-xdist
diff-cover
mypy
vulture
xenon
deptry
bandit
pip-audit
import-linter
```

The synced `.pre-commit-config.yaml` defines the lint and quality checks:

| Stage | Checks |
|---|---|
| Commit | ruff, codespell, actionlint, zizmor, and file checks |
| Push | mypy, vulture, xenon, deptry, and import-linter |
| Commit message | Commitizen |

CI runs both commit and push stages with `uvx prek`, so the checks apply even without local hooks. Commitizen runs only locally. Squash merges use the pull request title as the commit message, so CI does not run it.

The tools have these roles:

- deptry detects unused, missing, and transitive imports without per-repo configuration.
- import-linter runs when a repo defines `[tool.importlinter]` contracts. Adding the first contract enables the check.
- bandit and pip-audit run on every pull request. Audit exceptions in `.pip-audit-ignores` require a reason and expiry date. Expired exceptions fail CI.
- xenon blocks pushes when complexity exceeds its limits. wily reports complexity trends on pull requests without blocking merges.

pytest writes `coverage.xml`, which Codecov receives through OIDC without a token secret. Codecov's project and patch statuses are informational. `diff-cover` enforces 90% coverage on changed lines in pull requests. Branch protection must not require `codecov/*` statuses.

Pull requests run tests on Ubuntu. Push, scheduled, and manual runs test Ubuntu, macOS, and Windows because published packages must work on all three, including Windows path handling. Keep Ubuntu in the pull request matrix: Codecov and diff-cover run only there.

Mutation testing is optional and runs nightly. See [Mutation testing](#mutation-testing).

The `fast-tests` hook stays repo-local and runs only when a developer sets `ENABLE_PRE_PUSH_TESTS=1`. CI always runs the full suite.

## CI rules

### Versions and permissions

Pin actions to a full commit SHA and include a version comment:

```yaml
uses: actions/checkout@9c091bb2... # v7.0.0
```

Floating action tags create a supply-chain risk. This repo's reusable workflows are the exception: callers reference a major tag. Each caller repo needs `templates/repo/zizmor.yml` to allow that tag.

Pin other tools to exact versions, including hook `rev` values and tools installed through uvx or pip, such as `--with pyyaml==X.Y.Z`.

Set `permissions: contents: read` at workflow level. Grant additional permissions only to jobs that need them. For example:

- The test job needs `id-token: write` for Codecov OIDC.
- The sync job needs `contents: write` to push.

Set `persist-credentials: false` on checkout unless the job pushes.

### Triggers and execution

Do not filter `pull_request` events by branch. GitHub applies that filter to the target branch, so `branches: [main]` leaves pull requests into release or integration branches unchecked.

Keep branch filters on `push`. `scripts/check_workflow_triggers.py` enforces this rule through `check.yml` for this repo's workflows and caller templates under `ci/`.

Use concurrency groups to cancel superseded runs on the same ref.

Use `uv` for Python tooling and `uv sync --locked` for installs. A stale lockfile must fail the build rather than trigger dependency resolution.

Run nightly checks to catch dependency drift, with a distinct cron minute per repo. Scheduled security findings report upstream CVEs; use `continue-on-error` on scheduled runs to keep the badge green.

Set a timeout on every job:

| Job type | Timeout |
|---|---|
| Lint and audit | 15 minutes |
| Test matrix | 20 minutes, unless measurements justify longer |

## Repo checks

Every repo runs `reusable-repo-checks.yml`.

### Pull request bodies

The pull request check fails when:

- A required section is missing or empty.
- The body references no issue.
- A behavior change claims verification without pasted evidence.

The template provides two waivers. Select at most one:

| Waiver | Use it when |
|---|---|
| No behavior change | The change covers docs, chores, or CI without changing behavior. |
| Previously reviewed changes | A release or integration branch collects changes already verified in individual pull requests. |

Either waiver removes the issue-reference and pasted-evidence requirements. All sections remain required. For a release or integration pull request, list the included pull requests under “What changed” so reviewers can inspect them.

Checkboxes inside fenced code blocks do not count as waivers.

Generated bodies from authors listed in `BOT_AUTHORS` in `scripts/lint_body.py` are exempt. Keep that list short. Editing those bodies is ineffective because the generating workflow overwrites them.

This check enforces structure, not writing quality or length. Detailed evidence and implementation notes are valid; CI must not force authors to compress them.

There is no issue-body check or `needs-rewrite` label. Review writing before filing an issue.

### Repository layout

The layout check requires:

- An `AGENTS.md` file with its synced block.
- A `CLAUDE.md` file containing only the import of `AGENTS.md`.
- A writing-hook configuration in `.claude/settings.json`.

Sync overwrites `CLAUDE.md`, so any other content there will be lost.

The checks live in `scripts/lint_body.py` and `scripts/check_repo_layout.py`. Both use only the Python standard library. Change the shared scripts here to update the checks across repos.

## Prose

Vale checks Markdown and English website copy against this repo's rules. Error-level findings block changes in portolan-ops. Downstream pull requests can retain existing errors but cannot add new ones.

Website diagnostics identify the original `messages/en.json` key. Proselint checks a small set of general English problems.

See [prose.md](prose.md) for rules, local commands, and suppressions.

## Links

[lychee](https://lychee.cli.rs) checks links in every repo with a working tree. Sync copies `ci/links.yml` to `.github/workflows/links.yml`, which calls `reusable-links.yml`.

Organization rules live in `lychee/org.toml`. `scripts/lychee.sh` runs the pinned binary with those rules.

| When | Scope | Network | Failure result |
|---|---|---|---|
| `lychee` pre-commit hook | Relative links and anchors in staged Markdown and HTML | None | Blocks the commit |
| `links / lychee` on pushes and pull requests | Relative links and anchors in all tracked files | None | Fails the check |
| Weekly `links / lychee` run | External URLs | Required | Updates “Broken external links” |

Relative links and anchors produce consistent results, so they can block merges. External checks cannot: remote hosts can time out, rate-limit requests, or go offline independently of a pull request.

The weekly run maintains one issue per repo and closes it when all links work. Repos with issues disabled receive the report in the job summary. Remote anchor checks are skipped because many sites generate anchors with JavaScript.

The pre-commit hook reads only staged files. A rename can therefore pass locally but fail in CI if it breaks a link in an unstaged file.

For absolute links such as `/img/a.png`, `scripts/lychee.sh` sets `--root-dir` to `public/` when that directory exists, matching Vite and Next.js. Otherwise, it uses the repo root.

### Exceptions

Keep repo-specific exceptions in these root-level files. Sync leaves both untouched.

| File | Contents |
|---|---|
| `lychee.toml` | Path exclusions under `exclude_path` |
| `.lycheeignore` | URL patterns, one regular expression per line |

Include a reason for each exception. lychee merges repo arrays with organization rules, so repos can add exclusions but cannot remove organization exclusions.

Organization rules exclude test fixtures, Slack links that require sign-in, and LinkedIn links that reject requests without a browser session.

### Built sites

Site generators can create broken links through routes, templates, or navigation files even when source links are correct. Add a link-checking job to the build workflow and pass the built site as an artifact:

```yaml
  site-links:
    needs: docs
    uses: portolan-sdi/portolan-ops/.github/workflows/reusable-links.yml@v1
    permissions:
      contents: read
      issues: write
    with:
      site-artifact: site
```

The reusable workflow declares `issues: write` for weekly runs. GitHub does not let a called workflow exceed its caller's permissions, so callers must grant it even for built-site checks.

The job reports as `site-links / lychee`. It checks relative links and anchors in built HTML, using the build output as the root.

portolan-cli, portolan-registry-qgis, and portolan-sdi.org run this check. portolan-browser and portolan-nl-demo are single-page apps whose links live in JavaScript; they use the source check because lychee has no built HTML links to inspect.

Upload plain site files with `actions/upload-artifact`. GitHub Pages artifacts contain a tarball, so Pages deployments need a separate upload for link checks.

Some generators need additional configuration:

- **Zensical and MkDocs:** Sites served under a path such as `/portolan-cli/` generate a `404.html` with absolute links that resolve only on the live host. Exclude it in `lychee.toml` with `'(^|/)404\.html$'`. Other pages use relative links to the same destinations and remain covered.
- **Next.js:** The `.next/` layout does not match public URLs. portolan-sdi.org starts the production server and uses `wget` to copy pages to their URL paths, starting from `sitemap.xml` and following internal links. Its `lychee.toml` sets `index_files = ["index.html", "."]` so links such as `/#how` resolve to the home-page anchor.

### Running locally

From a portolan-sdi repo with a portolan-ops checkout beside it, run:

```bash
../portolan-ops/scripts/lychee.sh --offline .
```

Remove `--offline` to check external URLs. Set `GITHUB_TOKEN` first to avoid rate limits on github.com links.

### Installing the hook

Add the hook to `.pre-commit-config.yaml` at a release tag:

```yaml
  - repo: https://github.com/portolan-sdi/portolan-ops
    rev: v1.12.0
    hooks:
      - id: lychee
```

On first use, the hook downloads lychee from its GitHub release, verifies the archive against a pinned SHA-256, and caches the binary under `~/.cache/portolan-lychee`.

Set `LYCHEE_BIN` to use an existing installation. The organization does not use the upstream hook because it installs through an unpinned remote script.

## Branch protection

`sync/protection.yml` records the required settings for each protected branch:

- Repository and branch.
- Protection type.
- Required check contexts.
- Number of approving reviews.

Every entry requires `checks / layout` and `checks / pull-request`, reported by `repo-checks.yml`, plus any repo-specific checks.

All branches currently set `reviews: 0`. Required checks block merges; approving reviews are not required. A sole maintainer cannot approve their own work, and GitHub auto-merge does not honor admin bypass rights. A review requirement can therefore leave an otherwise passing sync pull request waiting indefinitely, as happened in portolan-cli#777.

Review still happens through maintainers reading each other's work. To require approvals, update the recorded review count before changing GitHub settings so the audit and configuration agree.

### Protection types and audits

GitHub stores classic branch protection and repository rulesets separately:

| Protection type | Read endpoint | Required permission |
|---|---|---|
| Classic branch protection | `repos/{owner}/{repo}/branches/{branch}/protection` | `administration:read` |
| Repository ruleset | `repos/{owner}/{repo}/rules/branches/{branch}` | `contents:read` |

Moving between them does not preserve required checks. portolan-cli lost both organization checks during such a move without an alert.

`scripts/check_protection.py` compares recorded settings with GitHub. For each branch, it reports missing and extra checks and expected versus actual review counts. Any difference or unreadable branch causes a nonzero exit.

`protection-audit.yml` runs every Monday and keeps one tracking issue open in portolan-ops until all settings match.

### Applying settings

Apply settings manually. For classic protection, use the endpoint that updates only required checks:

```bash
gh api -X PATCH \
  repos/OWNER/REPO/branches/main/protection/required_status_checks \
  -f 'contexts[]=checks / layout' \
  -f 'contexts[]=checks / pull-request'
```

`PUT .../protection` replaces the entire protection object. Sending only checks through that endpoint also removes review rules.

Add a repo to the record after its checks have passed several times. Require only checks that run on pull requests. Requiring a push-only or scheduled job leaves pull requests waiting for a status that never arrives.

## The writing hook

`.claude/output-styles/simplified-technical-english.md` is the canonical copy of the Simplified Technical English (ASD-STE100) output style.

At session start, `.claude/hooks/writing_check.py` prints the style as context, activating it for the repo. This mirrors the personal `prose-style-activate.js` hook.

Before `gh issue create` or `gh pr create`, the hook checks the body. Blocking findings stop the command and identify the line and required fix.

The hook enforces STE rules that can be checked mechanically:

- Use infinitives, imperatives, or simple tenses.
- Avoid gerunds, present participles, passive constructions, and perfect tenses.
- Keep sentences to 20 words or fewer.
- Avoid filler, hype, and words with simpler approved alternatives.

Checks for missing articles and noun clusters either provide advice or are absent because they need part-of-speech data.

To override an incorrect finding, add this comment on the preceding line:

```html
<!-- ste-ok: RULE_ID reason -->
```

The reason is required and remains in the diff. Count overrides with `grep -c 'ste-ok'` to identify rules that cause repeated friction. Retire rules that authors routinely need to override.

A passing result does not prove good writing. The hook matches words and punctuation; it cannot judge tone, padding, self-justification, or the value of technical detail.

The hook reads `--body` and `--body-file`, but misses bodies supplied through heredocs because it does not evaluate shell commands. Submissions through GitHub's web form use only the templates and CI structure checks.

`.claude/settings.json` syncs with `merge-json`, preserving repo-specific hooks. The merge replaces only entries whose commands name `writing_check.py`. Repeated syncs produce no additional diff.

## Sync distribution

`sync/manifest.yml` defines which files go to each repo. `sync.yml` opens or updates one `ops-sync` pull request per affected repo.

| Content | Distribution |
|---|---|
| Community health files | Inherited from the [`.github` repo](https://github.com/portolan-sdi/.github) unless a repo has its own |
| Apache-2.0 `LICENSE` | Copied to every active repo; GitHub does not inherit licenses |
| Family CI callers | Copied once, then maintained by each repo |
| `AGENTS.md` pointer block | Inserted at the top; repo-specific content below remains untouched |
| `CLAUDE.md` | Copied to every active repo as one import line |
| Repo-checks caller and zizmor policy | Synced to every active repo |
| `_brand-vars.css` and three logo SVGs | Sent to portolan-cli |

Community health files include the organization profile, code of conduct, contributing guide, security policy, and issue and pull request templates.

`brand/emit_css.py` generates `_brand-vars.css` from `brand/brand.json`. The website and browser do not yet use it.

The repo-checks caller is an exception to the rule against syncing callers: it has no repo-specific inputs. It enforces pull request structure and agent-file layout. To require its checks, record them in `sync/protection.yml` and apply the GitHub settings after several passing runs.

### Sync pull requests

Sync refuses to push if the `ops-sync` branch contains a commit it did not create, because a force-push would discard that work. Merge or remove those commits, then rerun sync.

Merge a repo's first sync pull request manually. It includes `.github/workflows/repo-checks.yml`, which prevents auto-merge, and introduces the layout check alongside the agent files it requires. If repo linters reject synced files, adjust the repo's ignores before merging.

`sync-drift.yml` checks repos weekly. It fails and maintains a tracking issue when:

- Files differ from their sources.
- A repo cannot be cloned.
- The manifest sends no files to an active organization repo.

portolan-ops is excluded because it holds the source files and cannot be its own sync target.

### Release branches

Sync writes only to default branches. Long-lived release branches retain the files they started with.

For example, portolan-cli's `release/v1.0.0b0` had `.claude/settings.json` without `.claude/hooks/writing_check.py`, causing its layout check to fail.

Add branches that need drift monitoring to `extra_branches`:

```yaml
extra_branches:
  portolan-sdi/portolan-cli:
    - release/v2.0.0
```

Each branch gets a separate report row. This monitors drift but does not deliver files; the repo must cherry-pick missing updates.

Remove entries after the branch merges into the default branch. The audit continues checking branches while they exist, so an old branch can keep the weekly check failing. The list is currently empty after portolan-cli#705 merged `release/v1.0.0b0` into `main`.

## Auto-merging sync pull requests

To let required checks control sync merges, add the repo to `auto_merge` in `sync/manifest.yml`:

```yaml
auto_merge:
  - portolan-sdi/stac-partition-extension
```

Sync runs `gh pr merge --auto --squash`. GitHub merges after required checks pass; sync does not merge directly.

Before enabling this:

- Configure required status checks on the base branch. Without them, auto-merge merges immediately.
- Enable the repo's `allow_auto_merge` setting. The command fails without it.

Dry runs skip auto-merge because they do not push changes.

## Repository automation policy

GitHub can disable individual workflows while leaving Actions enabled for the repo. This happens to scheduled workflows in public forks.

Each hour, `automation-reconcile.yml` checks every active organization repo and enables Actions, auto-merge, and any disabled workflows.

The `portolan-ops-sync` app provides the repository token and requires `Actions: write` and `Administration: write`.

## Auto-merging Dependabot pull requests

Every repo with `.github/dependabot.yml` receives `ci/dependabot-automerge.yml`, which calls the shared workflow.

The workflow verifies the author without checking out pull request code. It uses `pull_request_target` because Dependabot's `pull_request` runs receive a read-only token.

Auto-merge is enabled for every Dependabot update type. The target branch's required checks control when it merges.

The website also receives `ci/registry-bot-automerge.yml` for coverage refreshes from `portolan-registry-bot[bot]`. The same required checks apply. Matching the exact login limits this policy to that bot.

## AGENTS.md and CLAUDE.md

`AGENTS.md` is canonical. It contains organization rules in a synced marker block and repo-specific rules below it.

Claude Code reads `CLAUDE.md`, so that file contains only an import of `AGENTS.md`, following the Claude Code documentation. A symlink would cause problems on Windows and cannot contain sync markers.

The `AGENTS.md` block includes the full rules because agents read file contents without fetching linked URLs.

`scripts/build_agents_block.py` generates `templates/repo/AGENTS.md` from this repo's `AGENTS.md`. `check.yml` fails if they differ.

## Security audit

The Python family workflow runs bandit and pip-audit. Findings fail pull request checks.

The optional `reusable-security-audit.yml` runs pip-audit nightly and maintains one tracking issue, opening it on findings and closing it when the audit passes. Scheduled findings remain visible in Actions and the issue while the badge stays green.

The nightly audit is separate because it requires `issues: write`. GitHub checks called-workflow permissions even for jobs that do not run. Adding the audit to the family workflow would require every caller to grant that permission and would need a major release.

To opt in, copy `ci/python-package/security-audit.yml` and choose a distinct cron minute. Enable it only if the repo will triage the issues.

## Mutation testing

mutmut changes the source one mutation at a time and reruns tests. A mutation that passes identifies a change the tests did not catch. The full run is slow, so it runs nightly rather than on pull requests.

To opt in:

1. Set `mutation: true` in the caller.
2. Add `[tool.mutmut]` to `pyproject.toml`, listing the paths to mutate.

`scripts/mutation_score.py` computes a consistent score across repos. Previously, rashid and portolan-cli used different calculations.

```text
killed_total = killed + timeout + suspicious
testable     = killed_total + survived
kill_rate    = killed_total / testable
```

Timeouts and suspicious results count as kills because the suite reacted. Mutants without a covering test are excluded; coverage measures that gap. A run with no testable mutants fails.

Each repo sets its minimum in `.mutation-baseline`. Raise it as tests improve. Explain any reduction in the pull request.

### Sharding mutation tests

If a full run exceeds the timeout, set `mutation-shards` above zero. Each night tests one shard, selected by day of year. All shards run over `mutation-shards` nights.

A hash of each file's path determines its shard. Adding a module therefore leaves existing assignments and recorded shard rates unchanged.

Shard scores depend on their modules. Measured portolan-cli scores ranged from 18% to 95%, making a single minimum either unreliable or ineffective. Record each shard's baseline in `.mutation-shards.json`. The scorer enforces those baselines alongside the repo-wide minimum.

## Tool versions

Workflows read shared prek and pyyaml versions from the organization Actions variables `PREK_VERSION` and `PYYAML_VERSION`:

```yaml
env:
  PREK_VERSION: ${{ vars.PREK_VERSION || '0.4.11' }}
```

The value after `||` is the fallback. In reusable workflows, `vars` refers to the caller's repo. Forks and callers outside the organization use the fallback when the variable is unavailable.

Changing an organization variable updates every repo immediately, without a pull request or review. Treat it as a deployment.

wily stays pinned inline because its `uvx wily@X.Y.Z` argument does not read an `env:` value.

### Automated updates

Dependabot does not detect versions in `env:` values or uvx arguments. Each week, `bump-tools.yml` checks PyPI for new prek, pyyaml, and wily releases, updates matching literals, and opens a pull request. CI tests the new versions before merge.

The job edits `.github/workflows`, which `GITHUB_TOKEN` cannot do at any permission level. It uses an app token with `workflows: write`.

`scripts/test_bump_tools.py` tests the rewrites. `check.yml` also runs `bump_tools.py --check`, which fails if an expected pattern no longer matches.

Organization variables override literals. If an override is set, merging the update alone has no effect; the pull request body includes the command to update the variable.

### lychee updates

lychee is updated separately. `scripts/lychee.sh` pins its version and a SHA-256 for each platform.

Update the version and all platform checksums together, using the release's `.sha256` assets. `scripts/test_lychee.py` verifies that the script rejects downloads with mismatched checksums.
