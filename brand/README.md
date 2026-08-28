# Portolan brand kit

The kit follows [PATTERN.md](PATTERN.md): a self-contained folder holding `brand.json` (the machine-readable registry), `logos/`, `fonts/`, `icons/`, a visual preview (`index.html`), and two stdlib-only scripts (`emit_css.py`, `check.py`). `slidev-addon-portolan/` holds the Slidev addon that builds decks from these values. See its [README](slidev-addon-portolan/README.md).

`brand.json` is the canonical home for every value below. Consuming repos read it here rather than restating it.

| Color | Hex | Where it goes |
|---|---|---|
| Portolan blue | `#4163cc` | The single accent: links, logo fill, figure strokes, controls |
| Cream paper | `#fcfcfa` | Page ground |
| Near-black ink | `#16170f` | Body text and structural rules |
| Soft rule | `#d6d5ca` | Interior separators inside an already-bordered block |

`fonts/` holds all three families as static TTF for desktop use and as WOFF2 for the web. Each weight is a separate file, cut from the variable font Google publishes. Install the TTF files to build a deck or a document.

Type is Hanken Grotesk for Latin prose and headlines, JetBrains Mono for the machine register (code, labels, kickers, data, paths, controls), and Cairo for all Arabic. The `rules` block in `brand.json` carries the rest: light mode only, square corners, flat surfaces ruled in ink, no gradients, a solid-fill logo, and no compass roses.

Each repo implements those values in its own token scheme, and its AGENTS.md documents how. The website's `--p-*` properties in `src/app/globals.css` and the browser's `$primary` in `src/theme/variables.scss` predate this kit. PATTERN.md's "Current state" section describes that arrangement and what reconciling it takes.

## Logos

`logos/` holds three lockups in three fills. The mark is the two pennants alone. The horizontal lockup sets the wordmark beside the mark. The vertical lockup stacks the wordmark under it.

| Fill | Use |
|---|---|
| `-4163cc` | The default. Use it on any light ground. |
| `-fcfcfa` | Dark grounds only. |
| `-currentcolor` | Inline SVG. The mark inherits the color around it. |

The wordmark is Hanken Grotesk SemiBold, converted to outlines. No file needs a font to render.

Three rules govern every use. Keep clearspace of one pennant height on all four sides. Do not set the mark below 16 px wide. Do not recolor, rotate, stretch, or add a gradient.

Voice lives in [VOICE.md](../VOICE.md) and does not move here.
