#!/usr/bin/env python3
"""Brand kit drift validator.

    python3 brand/check.py

Exits 0 when consistent, 1 with a list of drifts. While brand.json carries
`_stub: true` the check passes trivially so CI stays green before branding
lands.

Verifies, in order:

1. Schema: required top-level keys; palette entries are {hex, name}
   objects with `primary` and `surface` present; every role value is a
   literal hex or an @palette.<key> reference to an existing key; the
   eight required roles exist.
2. Named colors: every palette hex appears in brand/README.md and
   brand/index.html, so designers and writers can grep the canonical hex.
3. Logos resolve: every declared logo path exists on disk.
4. Fonts exist: every declared font file exists on disk.
5. Icons resolve: every entry in the icons block exists on disk (the
   ops-re kit documented icons but never validated them; this kit does).
6. Optional asset blocks (imagery, social_avatars) resolve.
7. Generated CSS is current: brand/_brand-vars.css matches what
   emit_css.py would produce.

Stdlib only. Adapted from the Radiant Earth ops-re brand kit.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_css  # noqa: E402

BRAND_DIR = Path(__file__).resolve().parent
HEX_RE = re.compile(r"#[0-9A-Fa-f]{3,8}$")
REF_RE = re.compile(r"^@palette\.([a-z0-9_]+)$")
REQUIRED_TOP = ("key", "name", "palette", "roles", "fonts", "logos")
REQUIRED_PALETTE = ("primary", "surface")
REQUIRED_ROLES = (
    "background", "text", "accent", "link",
    "link_hover", "success", "warning", "danger",
)
ASSET_BLOCKS = ("icons", "imagery", "social_avatars")
FONT_META_KEYS = {"family", "dir"}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def check_schema(brand: dict, errors: list[str]) -> None:
    for key in REQUIRED_TOP:
        if key not in brand:
            errors.append(f"brand.json: missing required key '{key}'")

    palette = brand.get("palette") or {}
    if not isinstance(palette, dict) or not palette:
        errors.append("brand.json: 'palette' must be a non-empty object")
        palette = {}
    for key in REQUIRED_PALETTE:
        if key not in palette:
            errors.append(f"brand.json: palette missing '{key}'")
    for key, entry in palette.items():
        if not isinstance(entry, dict):
            errors.append(f"brand.json: palette.{key} must be an object")
            continue
        if not HEX_RE.fullmatch(str(entry.get("hex", ""))):
            errors.append(f"brand.json: palette.{key}.hex is not valid hex")
        if not entry.get("name"):
            errors.append(f"brand.json: palette.{key}.name is missing")

    roles = brand.get("roles") or {}
    if not isinstance(roles, dict) or not roles:
        errors.append("brand.json: 'roles' must be a non-empty object")
        roles = {}
    for key in REQUIRED_ROLES:
        if key not in roles:
            errors.append(f"brand.json: roles missing '{key}'")
    for key, value in roles.items():
        if not isinstance(value, str):
            errors.append(f"brand.json: roles.{key} is not a string")
            continue
        m = REF_RE.match(value)
        if m:
            if m.group(1) not in palette:
                errors.append(
                    f"brand.json: roles.{key} references missing palette"
                    f" key '{m.group(1)}'"
                )
        elif not HEX_RE.fullmatch(value):
            errors.append(
                f"brand.json: roles.{key} must be hex or @palette.<key>"
            )


def check_named_colors(brand: dict, errors: list[str]) -> None:
    files = {
        "README.md": _read(BRAND_DIR / "README.md"),
        "index.html": _read(BRAND_DIR / "index.html"),
    }
    for fname, contents in files.items():
        if not contents:
            errors.append(f"missing or empty file: brand/{fname}")
            continue
        for key, entry in (brand.get("palette") or {}).items():
            hex_v = (entry or {}).get("hex", "")
            if hex_v and hex_v.lower() not in contents.lower():
                errors.append(
                    f"named color drift: {key} ({hex_v}) not in brand/{fname}"
                )


def check_paths_block(
    brand: dict, block_name: str, errors: list[str], required: bool
) -> None:
    block = brand.get(block_name)
    if block is None:
        if required:
            errors.append(f"brand.json: '{block_name}' missing")
        return
    if not isinstance(block, dict) or (required and not block):
        errors.append(f"brand.json: '{block_name}' must be a non-empty object")
        return
    for key, rel in block.items():
        if key.startswith("_"):
            continue
        if not isinstance(rel, str) or not rel:
            errors.append(f"brand.json: {block_name}.{key} is not a path")
            continue
        if not (BRAND_DIR / rel).resolve().is_file():
            errors.append(
                f"missing {block_name} file: brand/{rel}"
                f" (declared {block_name}.{key})"
            )


def check_fonts(brand: dict, errors: list[str]) -> None:
    fonts = brand.get("fonts") or {}
    if not isinstance(fonts, dict) or not fonts:
        errors.append("brand.json: 'fonts' missing or empty")
        return
    for slot_name, slot in fonts.items():
        if not isinstance(slot, dict):
            errors.append(f"brand.json: fonts.{slot_name} must be an object")
            continue
        font_dir = slot.get("dir", "")
        for key, fname in slot.items():
            if key in FONT_META_KEYS or key.startswith("_"):
                continue
            path = BRAND_DIR / font_dir / str(fname)
            if not path.resolve().is_file():
                errors.append(
                    f"missing font file: brand/{font_dir}/{fname}"
                    f" (declared fonts.{slot_name}.{key})"
                )


def check_generated_css(brand: dict, errors: list[str]) -> None:
    committed = _read(BRAND_DIR / "_brand-vars.css")
    try:
        expected = emit_css.emit(brand)
    except SystemExit as e:
        errors.append(f"emit_css failed: {e}")
        return
    if committed != expected:
        errors.append(
            "brand/_brand-vars.css is stale; run"
            " `python3 brand/emit_css.py --write`"
        )


def main() -> int:
    errors: list[str] = []
    try:
        brand = json.loads(_read(BRAND_DIR / "brand.json"))
    except json.JSONDecodeError as e:
        print(f"brand.json: invalid JSON — {e}", file=sys.stderr)
        return 1
    if not isinstance(brand, dict):
        print("brand.json: top-level value is not an object", file=sys.stderr)
        return 1

    if brand.get("_stub"):
        print("brand.json is a stub (_stub: true); checks skipped")
        return 0

    check_schema(brand, errors)
    check_named_colors(brand, errors)
    check_paths_block(brand, "logos", errors, required=True)
    check_fonts(brand, errors)
    check_paths_block(brand, "icons", errors, required=False)
    check_paths_block(brand, "imagery", errors, required=False)
    check_paths_block(brand, "social_avatars", errors, required=False)
    check_generated_css(brand, errors)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("brand kit consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
