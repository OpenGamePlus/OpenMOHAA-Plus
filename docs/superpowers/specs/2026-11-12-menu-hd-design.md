# HD menus with widescreen side art (design)

Date: 2026-11-12. Status: **discarded** (2026-11-15). The maintainer dropped the remaster of the
original menu in favour of a new fork menu (`docs/superpowers/specs/2026-11-14-plus-menu-design.md`);
the `feat/menu-hd` branch was never merged and was deleted. Kept as a record of what was tried.

## Intent

The maintainer wants the main menu, and the menus reached from it, to look sharp at modern
resolutions and to fill wide screens: the traditional menu stays in the centre, in HD, and on
wide screens the black side bars show more of the same scene. This comes before any redesign of
the menu: it is the HD and widescreen base the later redesign will use.

## Goals

- The menus reachable from `main` (18 menus) in HD. Checked in the data: 8 of them have a
  full-screen background (`main`, `options_main`, `war_records`, `advancedoptions`, `controls`,
  `loadsave`, `loadsave_mp`, `medals`); these get side art. The others are panels or dialogs
  over black (`multiplayerstart` and its 4 game types, `joingame`, `joininternetgame`) or have
  no image background (`multiplayer`, `joinlangame`, `joinnetgame`): their panel images get HD
  only, no sides (builder's call, see Design).
- On screens wider than 4:3 the side bars show side art that continues each scene; on 4:3 the
  menu looks as today (only sharper).
- Art is made by hand by the maintainer in ComfyUI (upscale + outpaint), one image per
  background; the repository ships the tool that prepares and packages it.

## Non-goals

- Spearhead and Breakthrough menus (`mainta`, `maintt`); Allied Assault only.
- Buttons, small labels, cursor and HUD images: they keep their files. A larger file with the
  same name and power-of-two size already loads at full size (checked: a 2048x2048 `main_a`),
  so they can be upscaled by hand without the tool.
- In-game menus (HUD, scoreboard, weapon/team menus), loading screens and briefings.
- Generating art automatically (no ComfyUI API).
- Engine changes. Everything is data: a pk3 with replacement `.urc` files and images.

## Anti-goals

- Moved or broken hotspots: buttons and their rects stay exactly as in the original `.urc`.
- Original art committed or published: HD versions and side art derived from the game's images
  are derived game data; the pk3 stays on the maintainer's machine (AGENTS.md: no game data).
- A menu that breaks without the pk3 or with `ui_menuaspect 0`.

## Constraints (checked on 2026-11-12)

- The engine rounds image sizes to powers of two, down by default (`r_roundImagesDown 1`,
  `code/renderergl1/tr_image.c`): every tile must be a power of two on both sides.
- Menu images are registered without mipmaps (`Rend_RegisterMaterial` is
  `RegisterShaderNoMip`); a 2048x2048 tile loads at 2048x2048 in GL1 and Vulkan.
- With `ui_menuaspect 1` (default) menus keep 4:3 and are centred; a Label with a rect outside
  0-640 and the existing `noparentclip` keyword is drawn in the side bars (tested at 1920x1080
  with two labels at x -213 and 640 in `ui/main.urc`). Rects are in the 640x480 virtual space.
- A `.urc` in a pk3 that loads after `Pak0.pk3` replaces the original (same path).
- `misc/fonts/make_fonts.py` already uses Pillow for a build-time tool: same dependency here.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| **A (chosen)** | Data mod: HD tiles + replacement `.urc` files whose side labels use `noparentclip`; a tool exports the canvases and builds the pk3 | No engine change, already proven; side art could later hold hotspots. Conflicts with other mods that replace the same `.urc` files |
| B | Engine draws `<menu>_left/_right` images in the bars by naming convention | No `.urc` edits, but new engine code and static images only |
| C | One full 16:9 background per menu drawn behind everything | Engine code; the centre is drawn twice |

The maintainer chose A. For the art, by hand in ComfyUI was chosen over driving ComfyUI's API:
8 wide images plus the panel images, and each side is creative work worth reviewing.

## Design

### Canvas

Each background becomes one wide canvas in virtual units: x from -240 to 880 (1120 wide), y from
0 to 480. 240 on each side covers up to 21:9 (480 x 21/9 = 1120); on 16:9 the screen cuts the
rest. The HD scale is 4 pixels per virtual unit: 4480x1920 pixels (at 1080p the menu scale is
2.25, at 2160p 4.5).

### Tool: `misc/menu-hd/menu_hd.py` (AGPL-3.0-or-later, Python 3 + Pillow)

`export --game-dir <GAME_DIR> --work <WORK_DIR>`

- Reads the paks in load order (later paks override), follows `pushmenu`/`showmenu` from
  `ui/main.urc` and finds the 18 menus.
- Background of a full-screen menu: its Labels drawn before the first non-Label resource whose
  `shader` resolves to an image (directly or through `scripts/*.shader`), without
  `enabledcvar`/`linkcvar`, whose shader has no `animMap`, and whose rect is at least 256x128
  virtual. Checked in the data: these shaders are single-stage and static (`rgbGen` and
  `blendFunc` only), so the first image is the picture. Small or animated Labels (the
  `fan_anim1` fan, the `controls` metal border pieces) stay live Labels, drawn over the tiles in
  their original order. Labels with `enabledcvar` (the `ui_voodoo` alternates) are left out of the
  canvas and stay in the `.urc` untouched (they only draw with `ui_voodoo 1`).
- A menu is full-screen when its background covers the whole 640x480 (`medals` counts: a black
  640x480 label plus the case); for it the canvas also covers the sides.
- Panel menus (builder's call): their background images are exported one by one as
  `<image>_panel.png`; an `<image>_hd.png` four times as large (same shape) is packed under the
  original image path as a power-of-two TGA, so the original `.urc` keeps working unchanged.
- Menus with the same background list share one canvas; panel images used by several menus are
  exported once.
- Writes per background: `<name>_wide.png` (1120x480: the original composite in the middle at
  x 240-880, transparent sides), `<name>_mask.png` (white where art must be invented, black where
  the original is), `<name>_preview.png` (composite with the menu's buttons and labels drawn, for
  orientation only), and `manifest.json` (menus, background labels, canvas geometry).
- Menus without a background (`multiplayer`, `joingame`, `joininternetgame`) are reported and
  skipped.

`build --game-dir <GAME_DIR> --work <WORK_DIR> --out <PK3>`

- For each background with `<name>_hd.png` in the work dir: any size with the 7:3 shape (±1%) is
  resized to 4480x1920 (Lanczos); other shapes are an error naming the file.
- Cuts it into 1024x1024 tiles (256x256 virtual), 5 columns from x -240 and 2 rows from y 0;
  edge tiles are padded with transparent pixels; fully transparent tiles are skipped. Saved as
  32-bit TGA at `textures/mohmenu/hd/<name>/r<row>c<col>.tga`.
- Writes each menu's `.urc`: the original text with the background Labels removed and the tile
  Labels inserted where the first one was (same draw order), every tile with `noparentclip`.
  Everything else is byte for byte the original; widget names must not change (the engine finds
  `backtogame` and others in `main` by name, `UI_MainMenuWidgetsUpdate`).
- Scale option `--scale 4|2` (default 4; at 2 each 1024-pixel tile covers 512 virtual units,
  a quarter of the memory) in case the measured texture memory is too high for a machine.
- Zips `.urc` files and tiles into the pk3 (default name `zzz-menu-hd.pk3`).
- Backgrounds without an HD image keep their original `.urc` (not written to the pk3).

### User workflow (fork user doc: `docs/markdown/03-configuration/13-plus-menu-hd.md`)

1. `export` to a work folder.
2. In ComfyUI, per background: upscale `<name>_wide.png` x4 and outpaint the masked sides; save
   `<name>_hd.png` in the work folder (the centre should stay faithful to the original).
3. `build`, copy the pk3 into `main/`. Remove it to go back.

## Testing

- Tool unit tests (`misc/menu-hd/test_menu_hd.py`, skip without Pillow): `.urc` parsing and
  background detection on a synthetic menu, tile geometry and padding, `.urc` rewriting keeps
  every non-background line, shape check on the HD image.
- Game test (`tests/test_client.py`, needs game data): export, a synthetic `main_hd.png` with
  solid colours in the side regions, build, load the pk3 at 1920x1080: side bars show the side
  colours, the centre matches the original within tolerance, and a hotspot still opens its menu
  (click or `uiclick`-free equivalent to be found by the builder); at 640x480 the picture is the
  original's.
- Texture memory measured with `imagelist` after opening all 18 menus with the pk3 (8 wide
  backgrounds x up to 10 tiles x 4 MiB, about 320 MiB at scale 4, if they stay loaded); the
  result goes into the user doc with the `--scale 2` advice. No pass/fail limit (builder's call).
- Pure server (builder's call): connect to a local `sv_pure 1` server without the pk3 on it and
  open `main` from the in-game menu; if the menus break, the user doc says to remove the pk3 for
  pure servers or to add it to the server.

## Left to the builder

- How to open each menu headless for screenshots (`pushmenu <name>` from the console works for
  `advancedoptions`).
- The exact keyword list for "resolves to an image" beyond `shader` (`menushader` etc. are not
  backgrounds).
- Whether `<name>_preview.png` draws text (fonts) or only images: images only is enough.
