# Portolan brand kit

> **STATUS: stub.** Logos, colors, and fonts are close to final and land here when ready. Until then `brand.json` carries `_stub: true`, `check.py` passes trivially, and nothing downstream consumes these values.

The kit follows [PATTERN.md](PATTERN.md): a self-contained folder holding `brand.json` (the machine-readable registry), `logos/`, `fonts/`, `icons/`, a visual preview (`index.html`), and two stdlib-only scripts (`emit_css.py`, `check.py`).

Until the kit is populated, the live brand values are in the consuming repos. The website defines `--p-*` tokens in `src/app/globals.css` (paper and ink palette, blue accent `#4163cc`, fonts Hanken Grotesk, Cairo, and JetBrains Mono, logos in `public/`), and the browser sets `$primary: #4163cc` in `src/theme/variables.scss`. PATTERN.md's "Current state" section is the authoritative description of that arrangement.

When branding lands, this README gains the brand-specific rules: color names and usage, logo lockups and clearance, font hierarchy, and any additions to the org's banned-words list. Voice lives in [VOICE.md](../VOICE.md) and does not move here.
