# Brand kit pattern

This file defines the target shape of the Portolan brand kit: one self-contained `brand/` folder holding SVG assets, a machine-readable JSON registry, and two small stdlib-only Python scripts. No build step, no external dependencies.

> **STATUS: the kit is a stub.** `brand.json` carries `_stub: true`, and `logos/`, `fonts/`, and `icons/` hold only `.gitkeep` files. The layout below describes what the folder becomes when branding lands, not what it holds today. See "Current state" for where the live brand values are.

## Current state

The brand as shipped lives in the consuming repos, not here yet:

- The **website** ([portolan-sdi.org](https://github.com/portolan-sdi/portolan-sdi.org)) defines its design tokens as `--p-*` custom properties in `src/app/globals.css`: a warm paper and ink palette with one blue accent (`#4163cc`), fonts Hanken Grotesk, Cairo, and JetBrains Mono, and logo SVGs in `public/`.
- The **browser** ([portolan-browser](https://github.com/portolan-sdi/portolan-browser)) sets `$primary: #4163cc` in `src/theme/variables.scss`.

Nothing consumes this folder today. No `_brand-vars.css` is generated, and `sync/manifest.yml` carries no brand entry. When branding lands here, part of that work is wiring the website and browser to the generated CSS and reconciling this kit's token names with the website's existing `--p-*` scheme.

## Required files (once populated)

```
brand/
├── README.md          brand rules that don't fit in JSON: color usage,
│                      logo clearance, font hierarchy, banned-word additions
├── brand.json         machine-readable registry (palette, roles, fonts,
│                      logos, icons)
├── index.html         visual preview rendering the values in brand.json
├── emit_css.py        generator: brand.json → _brand-vars.css
├── check.py           drift validator (run by CI in check.yml)
├── _brand-vars.css    generated; synced to consuming repos once the
│                      manifest carries a brand entry
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
| `palette` | yes | Brand identity colors. Each entry is `{ "hex": "#4163CC", "name": "..." }`. `primary` and `surface` are required keys. `accent`, `accent_light`, and `highlight` are the sanctioned extras. |
| `roles` | yes | Functional tokens. Each value is a literal hex or an `@palette.<key>` reference. Required roles: `background`, `text`, `accent`, `link`, `link_hover`, `success`, `warning`, `danger`. |
| `fonts` | yes | One slot per role (`heading`, `body`, `mono`): `family`, `dir`, and one entry per weight/style file, with `_woff2` variants for web. |
| `logos` | yes | Slot names to relative paths. Required slots: `full` (horizontal lockup) and `mark` (square). Color variants use hex-suffixed filenames (`portolan-logo-4163cc.svg`). Dark-surface variants take a `_dark` slot suffix, and a `currentcolor` variant serves inline SVG. |
| `icons` | no | Favicon and app-icon set: `svg` master, `favicon`, `apple_touch` (180), `pwa_192`, `pwa_512`, maskable variants. `check.py` validates every declared icon path. |
| `imagery`, `social_avatars` | no | Reference imagery and 1024×1024 avatars. |
| `footer_url` | no | Canonical site URL. |

Keys starting with `_` are documentation comments, and tools ignore them. `_stub: true` marks the kit as unpopulated. While it is set, `check.py` passes trivially and `emit_css.py` refuses to run.

## Rules

- **Roles reference the palette.** Most role values should be `@palette.<key>` references so a palette change cascades everywhere. Literal hex is for status colors and deliberate exceptions.
- **Two CSS namespaces.** `emit_css.py` emits `--palette-*` (identity) and `--color-*` (function). Consuming CSS reaches for `--color-*` almost everywhere, and for `--palette-*` only when the intent is "this literal brand color." Derived working tokens (alpha borders, muted neutrals) use `color-mix()` with `var(--palette-*)` in the consuming site, never new entries here. The website's `--p-*` tokens predate this kit. Mapping them onto these namespaces is part of the branding drop.
- **No pure-black or pure-white marks.** Monochrome reproduction uses the primary or surface variant on a contrasting surface.
- **Binaries stay minimal.** Finished, canonical, small, rarely changing assets only. Replace in place when a new canonical version supersedes. Working files and renders-in-progress live elsewhere.
- **Lowercase paths.** File and folder names never mix case.

## Changing a brand value

```bash
$EDITOR brand/brand.json
python3 brand/emit_css.py --write
python3 brand/check.py
```

Commit the JSON and the regenerated CSS together. Once the manifest carries the brand entry, the sync workflow fans `_brand-vars.css` out to consuming repos as `ops-sync` PRs.
