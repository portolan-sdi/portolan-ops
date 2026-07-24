# Brand kit pattern

The Portolan brand kit is a single self-contained `brand/` folder holding hand-edited SVG, hand-edited JSON, and two small stdlib-only Python scripts. No build step, no external dependencies. Adapted from the Radiant Earth ops-re brand kit pattern.

## Required files

```
brand/
├── README.md          brand rules that don't fit in JSON: color usage,
│                      logo clearance, font hierarchy, banned-word additions
├── brand.json         machine-readable registry (palette, roles, fonts,
│                      logos, icons)
├── index.html         visual preview rendering the values in brand.json
├── emit_css.py        generator: brand.json → _brand-vars.css
├── check.py           drift validator (run by CI in check.yml)
├── _brand-vars.css    generated; synced to consuming repos via
│                      sync/manifest.yml
├── logos/             SVG, one file per lockup × color variant
├── fonts/             licensed brand fonts (ttf + woff2)
└── icons/             favicon + touch + PWA set derived from the mark
```

## brand.json schema

Top-level keys:

| Key | Required | Purpose |
|---|---|---|
| `key` | yes | Machine identifier (`portolan`). |
| `name` | yes | Human-readable name (`Portolan`). |
| `palette` | yes | Brand identity colors. Each entry is `{ "hex": "#26383A", "name": "Ponderosa Pine" }`. `primary` and `surface` are required keys. `accent`, `accent_light`, and `highlight` are the sanctioned extras. |
| `roles` | yes | Functional tokens. Each value is a literal hex or an `@palette.<key>` reference. Required roles: `background`, `text`, `accent`, `link`, `link_hover`, `success`, `warning`, `danger`. |
| `fonts` | yes | One slot per role (`heading`, `body`, `mono`): `family`, `dir`, and one entry per weight/style file, with `_woff2` variants for web. |
| `logos` | yes | Slot names to relative paths. Required slots: `full` (horizontal lockup) and `mark` (square). Color variants use hex-suffixed filenames (`portolan-logo-26383a.svg`). Dark-surface variants take a `_dark` slot suffix, and a `currentcolor` variant serves inline SVG. |
| `icons` | no | Favicon and app-icon set: `svg` master, `favicon`, `apple_touch` (180), `pwa_192`, `pwa_512`, maskable variants. Unlike ops-re, `check.py` validates every declared icon path. |
| `imagery`, `social_avatars` | no | Reference imagery and 1024×1024 avatars. |
| `footer_url` | no | Canonical site URL. |

Keys starting with `_` are documentation comments, and tools ignore them. `_stub: true` marks the kit as unpopulated. While it is set, `check.py` passes trivially and `emit_css.py` refuses to run.

## Rules

- **Roles reference the palette.** Most role values should be `@palette.<key>` references so a palette change cascades everywhere. Literal hex is for status colors and deliberate exceptions.
- **Two CSS namespaces.** `emit_css.py` emits `--palette-*` (identity) and `--color-*` (function). Consuming CSS reaches for `--color-*` almost everywhere, and for `--palette-*` only when the intent is "this literal brand color." Derived working tokens (alpha borders, muted neutrals) use `color-mix()` with `var(--palette-*)` in the consuming site, never new entries here.
- **No pure-black or pure-white marks.** Monochrome reproduction uses the primary or surface variant on a contrasting surface.
- **Binaries stay minimal.** Finished, canonical, small, rarely changing assets only. Replace in place when a new canonical version supersedes. Working files and renders-in-progress live elsewhere.
- **Lowercase paths from day one.** The ops-re kit carried a stale-casing bug from a folder rename. This kit never mixes case.

## Changing a brand value

```bash
$EDITOR brand/brand.json
python3 brand/emit_css.py --write
python3 brand/check.py
```

Commit the JSON and the regenerated CSS together. The sync workflow fans `_brand-vars.css` out to consuming repos as `ops-sync` PRs. Their handwritten CSS picks up the new values without edits.
