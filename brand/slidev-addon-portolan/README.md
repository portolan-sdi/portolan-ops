# slidev-addon-portolan

The Portolan brand for [Slidev](https://sli.dev), factored out of every deck.
One source for fonts, colors, logo components, and the footer mark.

It is a Slidev **addon** layered on `theme: default`, not a theme. The built-in
layouts (`center`, `two-cols`, `full`) keep working.

## What it provides

- **Colors** come from `brand.json` through `_brand-vars.css`. The stylesheet
  restates no hex value. Run `python3 brand/emit_css.py --write` after a
  palette edit and every deck picks the change up.
- **Fonts** live in `fonts/`, copied from `brand/fonts`. Vite refuses to
  serve a file outside the package root, and it resolves a symlink to the
  real path, so the addon needs its own copy. `check.py` compares the two
  sets byte for byte and fails on any difference. After changing a font,
  run `cp brand/fonts/*.woff2 brand/slidev-addon-portolan/fonts/`.
- **Logo components**: `<PortolanLogo>`, `<PortolanLogoHorizontal>`, and
  `<PortolanLogoVertical>`. Each takes its color from `currentColor`, so set it
  with a utility class such as `text-[#4163cc]`.
- **Footer mark** in `global-bottom.vue`. Hide it on one slide with
  `hideLogomark: true` in that slide's frontmatter.

## Using it in a deck

Add the addon in the deck headmatter. The path is relative to the deck folder:

```yaml
---
theme: default
addons:
  - ../../brand/slidev-addon-portolan
---
```

Slidev resolves the path one level up from the deck folder, so it takes one
fewer `../` than you count by hand. An `ENOENT ... package.json` error means
the path landed wrong. Add or remove one `../`.

The deck then needs no font block, no `components/`, and no `package.json`.

## Running a deck

Install the shared toolchain once:

```
cd brand/slidev-addon-portolan
npm install
```

Then run any deck from this folder:

```
npx slidev example/slides.md                    # dev server
npx slidev build example/slides.md              # static site
npx slidev export example/slides.md             # PDF
npx slidev export --format pptx example/slides.md   # PowerPoint
```

Slidev renders each slide to an image in the PPTX export. The text is not
editable in PowerPoint. Use the PPTX to present or to hand a deck to
someone who needs a `.pptx` file. Edit the content in `slides.md`.

To build a deck by hand in PowerPoint instead, install the TTF files from
`brand/fonts` and set the colors from `brand.json`.

## Example

`example/slides.md` is a three-slide deck that exercises the type registers,
the table rules, and the horizontal lockup. Use it to check a change.
