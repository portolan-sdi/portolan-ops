---
name: setup-repo
description: >
  Scaffold a new portolan-sdi repo, or bring an existing one up to org
  norms. Use when asked to "set up a repo", "stand up a new repo", "add
  org boilerplate", or "bring this repo up to ops standards". Reads the
  canonical files from portolan-ops and applies the norms in norms/.
---

# Setup a portolan-sdi repo

Scaffold a repo to org standards. Ground truth is [portolan-ops](https://github.com/portolan-sdi/portolan-ops); never invent values this repo already defines.

## Step 1: Assess

Inventory what exists before writing anything: `LICENSE`, `README.md`, `AGENTS.md`, `.github/workflows/`, `.github/dependabot.yml`, `.pre-commit-config.yaml`, and (Python) `pyproject.toml`. Read before write; merge, never blindly overwrite.

Determine the repo's CI family from `norms/ci.md`: python-package, stac-extension, or web-app.

## Step 2: Confirm the checklist

Present what will be added or changed and get confirmation. Everything below is on by default except PyPI publishing, which is opt-in.

## Step 3: Apply

1. **LICENSE** — copy `LICENSE` from portolan-ops (Apache-2.0). Never another license without a human decision recorded in `norms/repos.md`.
2. **README.md** — from `templates/repo/README.md` if missing; otherwise leave it alone.
3. **AGENTS.md** — from `templates/repo/AGENTS.md`; if the file exists, splice only the `ops-sync:begin`/`ops-sync:end` block at the top.
4. **CI** — copy the family's caller from `ci/<family>/ci.yml` to `.github/workflows/ci.yml`. Delete superseded inline workflows only after the caller runs green.
5. **dependabot.yml** — from `templates/repo/dependabot.yml`; drop the `uv` ecosystem for non-Python repos.
6. **pre-commit** (Python) — from `templates/repo/.pre-commit-config.yaml`, merged with any existing hooks.
7. **pyproject.toml** (Python) — dependency groups `dev` (pytest, pre-commit, ruff) and `docs` (mkdocs-material, mkdocstrings); ruff config per the family reference (reis).
8. **Register the repo** — add it to `sync/manifest.yml` in portolan-ops (LICENSE and AGENTS.md entries at minimum) and to the org-profile repo table in `copy/org-profile/README.md`.

## Hard rules

- Pin every GitHub Action to a full commit SHA with a version comment. Verify the SHA against the action's repo; never write one from memory.
- `permissions: contents: read` at workflow top level; broaden per job only as needed.
- Python tooling is `uv`. Test matrix default is 3.10–3.13.
- Conventional commits; squash-merge.
- Community health files (CoC, CONTRIBUTING, SECURITY, templates) are NOT copied into the repo; the org `.github` repo provides them. Add one only to override the org default.

## Step 4: Validate

Run the repo's linters and tests (`uv run pre-commit run --all-files`, `uv run pytest`, or the family equivalent). In portolan-ops, run `python3 scripts/check_manifest.py`. Nothing is done until everything is green.
