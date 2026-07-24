#!/usr/bin/env python3
"""Brand kit CSS generator.

Reads brand/brand.json and emits a CSS file declaring custom properties for
every palette color and role. Roles whose value is "@palette.<key>" are
emitted as `var(--palette-<key>)` so a palette edit cascades through every
role automatically.

Usage:

    python3 brand/emit_css.py                  # print to stdout
    python3 brand/emit_css.py --write          # write brand/_brand-vars.css
    python3 brand/emit_css.py --check          # verify the committed file
                                               # matches (CI-friendly)

The committed brand/_brand-vars.css syncs to consuming repos (website,
browser) via sync/manifest.yml. Downstream CSS reaches for --color-* (role
tokens) almost everywhere and --palette-* only when the intent is "this
literal brand color."

Stdlib only. Adapted from the Radiant Earth ops-re brand kit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BRAND_DIR = Path(__file__).resolve().parent
OUTPUT = BRAND_DIR / "_brand-vars.css"
PALETTE_REF = re.compile(r"^@palette\.([a-z0-9_]+)$")
BANNER = (
    "/* Generated from brand/brand.json by brand/emit_css.py."
    " Do not edit. */\n"
    "/* Run `python3 brand/emit_css.py --write` after editing"
    " brand.json. */\n"
)


def kebab(key: str) -> str:
    return key.replace("_", "-")


def load_brand() -> dict:
    brand = json.loads((BRAND_DIR / "brand.json").read_text(encoding="utf-8"))
    if brand.get("_stub"):
        raise SystemExit(
            "brand.json is a stub (_stub: true); nothing to emit yet"
        )
    return brand


def resolve_palette(brand: dict) -> dict[str, str]:
    palette = brand.get("palette") or {}
    out: dict[str, str] = {}
    for key, entry in palette.items():
        hex_val = (entry or {}).get("hex")
        if not isinstance(hex_val, str) or not hex_val.startswith("#"):
            raise SystemExit(f"brand.json: palette.{key}.hex is not hex")
        out[key] = hex_val
    return out


def role_css_value(value: str, palette: dict[str, str]) -> str:
    m = PALETTE_REF.match(value)
    if m:
        key = m.group(1)
        if key not in palette:
            raise SystemExit(f"@palette.{key} has no palette entry")
        return f"var(--palette-{kebab(key)})"
    if value.startswith("#"):
        return value
    raise SystemExit(
        f"role value must be hex or @palette.<key> reference: {value!r}"
    )


def emit(brand: dict) -> str:
    palette = resolve_palette(brand)
    roles = brand.get("roles") or {}
    names = {k: (brand["palette"][k] or {}).get("name", "") for k in palette}

    lines = [BANNER, ":root {"]
    lines.append("  /* Palette — brand identity colors. */")
    for key, hex_val in palette.items():
        comment = f" /* {names[key]} */" if names[key] else ""
        lines.append(f"  --palette-{kebab(key)}: {hex_val};{comment}")
    lines.append("")
    lines.append("  /* Roles — functional tokens. Reach for these first. */")
    for key, value in roles.items():
        lines.append(f"  --color-{kebab(key)}: {role_css_value(value, palette)};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    css = emit(load_brand())
    if args.check:
        committed = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if committed != css:
            print(
                "brand/_brand-vars.css is stale; run"
                " `python3 brand/emit_css.py --write`",
                file=sys.stderr,
            )
            return 1
        print("brand/_brand-vars.css is current")
        return 0
    if args.write:
        OUTPUT.write_text(css, encoding="utf-8")
        print(f"wrote {OUTPUT}")
        return 0
    sys.stdout.write(css)
    return 0


if __name__ == "__main__":
    sys.exit(main())
