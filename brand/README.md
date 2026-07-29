# Portolan brand kit

> **STATUS: partial.** The palette, the three type families, and the standing visual rules are recorded in `brand.json`. Logo and icon files have not landed, so `brand.json` still carries `_stub: true`, `check.py` passes trivially, and nothing downstream consumes these values.

The kit follows [PATTERN.md](PATTERN.md): a self-contained folder holding `brand.json` (the machine-readable registry), `logos/`, `fonts/`, `icons/`, a visual preview (`index.html`), and two stdlib-only scripts (`emit_css.py`, `check.py`).

`brand.json` is the canonical home for every value below. Consuming repos read it here rather than restating it.

| Color | Hex | Where it goes |
|---|---|---|
| Portolan blue | `#4163cc` | The single accent: links, logo fill, figure strokes, controls |
| Cream paper | `#fcfcfa` | Page ground |
| Near-black ink | `#16170f` | Body text and structural rules |
| Soft rule | `#d6d5ca` | Interior separators inside an already-bordered block |

Type is Hanken Grotesk for Latin prose and headlines, JetBrains Mono for the machine register (code, labels, kickers, data, paths, controls), and Cairo for all Arabic. The `rules` block in `brand.json` carries the rest: light mode only, square corners, flat surfaces ruled in ink, no gradients, a solid-fill logo, and no compass roses.

Each repo implements those values in its own token scheme, and its AGENTS.md documents how. The website's `--p-*` properties in `src/app/globals.css` and the browser's `$primary` in `src/theme/variables.scss` predate this kit. PATTERN.md's "Current state" section describes that arrangement and what reconciling it takes.

Logo lockups and clearance land here when the SVGs do. Voice lives in [VOICE.md](../VOICE.md) and does not move here.
