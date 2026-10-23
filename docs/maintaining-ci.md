# Maintaining CI

Procedures for portolan-ops maintainers. The rules for every CI change live in [norms/ci.md](../norms/ci.md).

## Releasing a CI change

Merging to `main` changes nothing downstream. Callers pick up a change when the `v1` tag moves.

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

To roll back, move `v1` to the previous release tag. Release breaking changes under `v2`.

`tag-guard.yml` fails when a merge changes enforcement files and `v1` still points at older code.

After you move `v1`, close and reopen open downstream pull requests. A rerun keeps the workflow version it started with.

## Adding a repo to a family

1. Copy the family caller from `ci/` to `.github/workflows/ci.yml`.
2. Confirm that the portolan-renovate app can reach the repo, and delete any `.github/dependabot.yml`. Renovate needs no file in the repo.
3. Add the repo to `sync/manifest.yml` so it receives `zizmor.yml` and the agent files. Without the zizmor policy, linting rejects the caller's version tag.
4. Fix what the new checks find.
5. Delete the old workflows after the new caller passes.

Each repo maintains its own copy of the family caller, because repos set different inputs. Sync would overwrite them.

Merge a repo's first sync pull request by hand. It adds `repo-checks.yml`, which blocks auto-merge until it is merged.

To opt a Python repo into the nightly audit, copy `ci/python-package/security-audit.yml` and give it its own cron minute. Opt in only if someone will triage the issues it opens.

To opt into mutation testing, set `mutation: true` in the caller and list paths under `[tool.mutmut]`. If a full run times out, set `mutation-shards` and record each shard's baseline in `.mutation-shards.json`.

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
