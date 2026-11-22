# Legacy menu: sign text drawn by the engine

## Intent

The Legacy rooms (main, options_main, war_records) show the hovered target's name on a board in
the render. Today the sign Label draws the original 128x32 `*_sign` images with `linkcvartoshader`.
They carry their own felt, so they look blurred and pasted over the Blender board. The maintainer
wants the engine to write the text, with no image per sign. The work starts with options_main; the
generator is shared, so all three rooms change.

## Goals

- The sign shows white serif capitals on the board's felt, sharp at any resolution, with no
  `*_sign` image.
- The text keeps its place and size relative to the board at every aspect ratio and every
  `ui_plusscale`, like the rest of the picture.
- The text goes through the translation (cl_language), like other menu text.
- The buttons keep setting the same sign cvars with the same values (`ui_optionshader
  advanced_sign` ...), so nothing else changes.

Non-goals: new rooms, new hotspots, text in the renders, the Modern menu.

## Approaches

- **A. Reuse `facfont-20`.** No new asset, but it reads as a modern UI rather than a sign.
- **B. A new serif bitmap font from `misc/fonts/make_fonts.py` (chosen by the maintainer).** It
  is the closest to the original signs, and one atlas serves every sign.

## Design

1. **Font.** `make_fonts.py` gets a `plussign-32` font in its default set, built from
   `DejaVuSerif-Bold.ttf` in white with no reference width. It is drawn at 4x, its own scale
   (the others stay at 2x), so a 4K sign stays sharp. It ships in `zzz-plus.pk3` with the other
   fonts. The DejaVu licence notice already ships.
2. **Mapping.** Every non-board hotspot gets a `"text"` field (for example `"Advanced"`).
   `load_mapping` requires it and rejects `"` in it.
3. **Generated `.urc`.** The sign Label keeps `linkcvar <sign_cvar>` and drops
   `linkcvartoshader`. It gets `font plussign-32`, `textalign center` (vertically centred too, if
   the label supports it), a warm off-white `fgcolor` and one line per hotspot:
   `linkstring "<sign>" "<text>"`.
4. **Engine, text scale under `cover`.** A covered widget's frame follows the picture (k =
   max(vidW/W, vidH/480)), but the font follows the virtual scale (vidH/480 x `ui_plusscale`).
   For widgets with `WF_COVER`, `UILabel::Draw` prints the text at (k, k) instead, so the text
   matches the board everywhere. Other widgets are unchanged. It is marked "Added in OpenMOHAA
   Plus".
5. **Engine, translated linkstrings.** The text a `linkstring` picks goes through
   `Sys_LV_CL_ConvertString`. Strings missing from the dictionary come back unchanged, so the
   original menus only change where a translation file has the text. It is marked "Added in
   OpenMOHAA Plus".
6. **Unchanged.** The sign starts empty until the first hover (the cvars default to ""), as in
   the original.

## Tests

- Unit tests: the font builds with Latin-1 glyphs; the mapping needs `text`; the urc sign block
  has the `linkstring` lines, the font and no `linkcvartoshader`; the pak no longer needs
  `*_sign`.
- Client test, headless: after a hover command, the sign text is drawn inside the board rect, at
  the same relative height, at 1280x720 with scale 1 and 1.2, at 1024x768 and at 2560x1080.
- Client test: with a translation entry, the sign shows the translated text.

## Left to the builder

The exact colour, the font height if 32 looks too small or too large on the board, and whether
centring uses `textalign` or padding.
