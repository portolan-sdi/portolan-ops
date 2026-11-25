# Maintaining CI

Procedures for portolan-ops maintainers. The rules for every CI change live in [norms/ci.md](../norms/ci.md).

## Releasing a CI change

A merge to `main` releases itself. When `Check` passes on the push, `release.yml` reads the conventional commits since the last `vX.Y.Z` tag. It tags the merge commit and moves `v1` to that tag. A `feat` commit bumps the minor version. Any other commit bumps the patch version.

Test a change before you merge it, because the merge releases it:

1. Confirm that `ci-selftest.yml` passes on the pull request.
2. Point one downstream caller at the pull request branch and confirm that its checks pass.
3. Return that caller to `@v1`.

A breaking commit (`type!:` or a `BREAKING CHANGE:` footer) stops the release, and `v1` stays where it is. Choose one path:

- Release it under `v2` by hand, and move callers to `@v2` when they are ready.
- If no caller uses what broke, release it as a `v1` minor version:

```bash
gh workflow run release.yml -f bump=minor
```

A dispatch with `bump=patch` or `bump=minor` skips the breaking check and releases the current `main`.

To roll back, move `v1` to the previous release tag:

```bash
git fetch --tags
git tag -f v1 v1.15.0
git push -f origin v1
```

`tag-guard.yml` runs after each release run and every week. It fails while `v1` lags `main` on enforcement files. That happens when a breaking commit stops the release.

After `v1` moves, close and reopen open downstream pull requests. A rerun keeps the workflow version it started with.

## Adding a repo to a family

1. Copy the family caller from `ci/` to `.github/workflows/ci.yml`.
2. Confirm that the portolan-renovate app can reach the repo, and delete any `.github/dependabot.yml`. Renovate needs no file in the repo.
3. Add the repo to `sync/manifest.yml` so it receives `zizmor.yml` and the agent files. Without the zizmor policy, linting rejects the caller's version tag.
4. Fix what the new checks find.
5. Delete the old workflows after the new caller passes.

Each repo maintains its own copy of the family caller, because repos set different inputs. Sync would overwrite them.

Merge a repo's first sync pull request by hand. It adds `repo-checks.yml`, which blocks auto-merge until it is merged.

To opt a Python repo into the nightly audit, copy `ci/python-package/security-audit.yml` and give it its own cron minute. Opt in only if someone will triage the issues it opens.

## Sync

Sync writes default branches only. To report drift on a long-lived release branch, list it under `extra_branches` in `sync/manifest.yml`. The repo cherry-picks the fixes itself. Remove the entry once the branch merges. Otherwise the weekly report fails on a branch nobody uses.

Sync refuses to push when the `ops-sync` branch holds a commit it did not make. Merge or drop that commit, then rerun sync.

To let a repo's required checks merge its sync pull request, add the repo to `auto_merge`. The repo needs required checks on its base branch and `allow_auto_merge` on. Without required checks, auto-merge merges at once.

## Branch protection

`sync/protection.yml` records the required checks and review count for each protected branch. Every branch requires `checks / layout` and `checks / pull-request`.

All branches set `reviews: 0`. A maintainer cannot approve their own work, and auto-merge ignores admin bypass. In portolan-cli#777, a review requirement blocked a sync pull request whose checks passed.

`protection-audit.yml` runs `scripts/check_protection.py` every Monday and keeps one issue open until GitHub matches the record. Update the record before you change GitHub.

Classic protection and rulesets are stored apart. Moving a branch between them drops its required checks without warning.

Update required checks with the endpoint that changes only checks:

```bash
gh api -X PATCH \
  repos/OWNER/REPO/branches/main/protection/required_status_checks \
  -f 'contexts[]=checks / layout' \
  -f 'contexts[]=checks / pull-request'
```

`PUT .../protection` replaces the whole object and deletes the review rules.

Require a check only after it has passed several times, and only if it runs on pull requests. A push-only check leaves pull requests waiting forever.

## Tool versions

Workflows read prek and pyyaml versions from the org variables `PREK_VERSION` and `PYYAML_VERSION`, with an inline fallback. GitHub applies a change to an org variable in every repo at once, with no review. Treat it as a deployment.

Renovate updates each literal that has a `# renovate:` comment on the line above it. When an org variable overrides the literal, also update the variable. The pull request body says so.

Renovate updates `LYCHEE_VERSION` in `scripts/lychee.sh` and then runs `scripts/lychee_sums.sh`, which rewrites every platform checksum. To update lychee by hand, change the version and run that script.
