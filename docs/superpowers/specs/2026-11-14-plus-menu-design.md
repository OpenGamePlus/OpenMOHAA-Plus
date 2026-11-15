# OpenMOHAA Plus menu (design)

Date: 2026-11-14. Status: approach 2 chosen; builder check done; pk3 location decided (A); waiting for approval.
Branch: `feat/plus-menu`, from `main`. It first started from `feat/menu-hd`; that work was discarded on 2026-11-15 (see the HD menus design) and the branch was rebased onto `main` without it.

## Intent

The original main menu is a fixed 640x480 picture: it does not adapt to the screen, and every
fork feature added to it means editing the game's own menu. The maintainer wants a menu of the
fork's own, shipped in a pk3 next to the binary together with the new fonts, built the same way
as the game's menus (`.urc` files loaded by `code/uilib`), that adapts to any resolution and grows
without touching the original. First uses: a better server browser (favourites, recent servers)
and a place for the fork's options, such as choosing the Vulkan or GL renderer.

## Goals

- A new `main` menu that fills the whole screen at any aspect (4:3 to 32:9): full-screen
  background, a fixed navigation bar on the left (Campaign, Multiplayer, Options, Plus, Quit) and
  a content area on the right that stretches with the width (layout A in the brainstorm).
- Text and buttons keep a readable size: a UI scale of the fork's own, not "everything grows with
  the resolution".
- Multiplayer opens a new server browser in the content area with tabs Internet / Favourites /
  Recent / LAN and a favourite column (toggle). More columns fit on wider screens.
- Plus opens the fork's options: renderer (`cl_renderer`, latched), HUD scale (`ui_hudscale`),
  menu aspect, crosshair, language; the exact list is the builder's (see below).
- Campaign, load/save, controls, medals, the other option screens and server creation open the
  **original** screens as they are (scope A: progressive replacement in later branches).
- One pk3 of the fork's data, built from the repository, shipped next to the binary: the fonts
  that `misc/fonts/make_fonts.py` already builds (`zzz-plus-fonts.pk3` today) plus the new menu.

## Non-goals

- Replacing the original screens in this branch (campaign, load/save, controls, medals...).
- Spearhead and Breakthrough menus (`mainta`, `maintt`); Allied Assault only.
- In-game menus (HUD, scoreboard, team/weapon menus), loading screens, briefings.
- Live data in the main menu (cards with favourites online, last save): rejected layout C.
- A generator for `.urc` files (approach 3), a new UI toolkit (HTML/RmlUi): the maintainer asked
  to keep the game's way of building menus.

## Anti-goals

- Game data in the pk3 or the repository: no image of the game, nothing derived from one (no
  img2img, no outpaint over game art), no copied `.urc`. The fork's `.urc` are written from
  scratch.
- Real symbols or marks in the art: no swastikas or Nazi insignia (illegal in a game distributed
  in Germany), no Medal of Honor logo, no text in images.
- A broken game without the pk3: without it the original menu must work exactly as today.
- Original menus that change: every new `uilib` keyword is opt-in; `.urc` files that do not use
  it behave as before, with `ui_menuaspect 0` and `1`.

## Constraints (checked on 2026-11-14)

- The engine refers to the menu `main` by name in many places (`code/client/cl_ui.cpp`: escape,
  connection drops, the in-game menu when `cg_gametype > 0`, `UI_MenuEscape("main")` in
  `cl_main.cpp` and `cl_keys.cpp`). The new menu is therefore `ui/main.urc` in the pk3, which
  replaces the original by load order (a pk3 sorted after `Pak0.pk3`); without the pk3 the
  original loads. Its behaviour on those paths must be kept.
- `uilib` already has `align left|right|centerx|top|bottom|centery` and
  `stretch horizontal|vertical` relative to the real screen (`UIWidget::Realign`,
  `code/uilib/uiwidget.cpp`), and `noparentclip`. Not checked: how children of an aligned or
  stretched container are placed and sized.
- Image sizes are rounded to powers of two (`r_roundImagesDown`); menu images load without
  mipmaps (see the menu-hd design). The background must be cut into power-of-two tiles.
- The server browser `UIFAKKServerList` (`code/client/cl_uiserverlist.cpp`) already marks
  favourites and recent servers from `cl_serverbook.cpp` and can toggle a favourite; it has no
  filter to list only favourites or only recent servers.
- `cl_renderer` is `CVAR_LATCH`: a renderer change needs a restart of the renderer
  (`vid_restart`) or the game.
- The fonts pk3 is built in CI (`.github/workflows/shared-build-linux.yml`, step "Fonts pk3",
  Pillow + `fonts-dejavu-core`) and released as its own asset (`branches-build.yml`).
- The game data is in `fs_basepath` (the game folder); users copy the release into the game
  folder, so a pk3 under `main/` in each package lands in the game's `main/`.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| 1 | Data only: hand-written `.urc` with the existing `align`/`stretch`/`noparentclip`, plus the browser filter | Least engine change; if children of an anchored container do not stretch, the content area cannot adapt and we are back to a fixed canvas |
| **2 (chosen)** | Data plus small opt-in `uilib` keywords, added only when a screen needs one ("Added in OpenMOHAA Plus"): e.g. anchoring to the parent's edges, sizes in percent of the parent, the fork's UI scale | Some engine code, but only where needed and invisible to the original menus; starts with a short test (bar + stretching panel) to find what is really missing |
| 3 | `.urc` generated from a Python description | Consistent styles, but one more tool for a handful of screens; dropped for now |

Chosen by the maintainer on 2026-11-14.

## Design decided with the maintainer

- **Scope A:** new `main` and new screens are the fork's; the original screens are opened as they
  are and replaced one by one later.
- **Adaptive layout, layout A:** full-screen background cropped from the centre (never stretched
  out of proportion); left bar of fixed size with a dark gradient over the background so text
  reads on any image; content area to the right that grows with the width; on the main screen no
  panel is open and the background shows. In 21:9 the bar keeps its size and more landscape shows.
- **Look:** painted 1940s semi-realistic scene, muted olive/ochre/steel grey; content in a
  semi-transparent dark panel with a thin warm border (mockup `fondo-v1`, accepted).
- **Art:** made by the maintainer with ComfyUI from text only (workflow
  `OMOHPlus_Menu_Fondo_T2I.json`, Flux.2 Klein, 3840x1600, 2.4:1, quiet dark left third, subject
  centre-right, the centre 16:9 works on its own). The first background is the maintainer's
  `fondo_00001_` with the turret insignia removed by hand. Art is committed under CC BY-SA 4.0.
- **Approach 2** (above).
- **One pk3 next to the binary** with the fonts and the menu.

## My calls (correct them if wrong)

- **Name of the pk3:** `zzz-plus.pk3`, replacing `zzz-plus-fonts.pk3` (one data pk3, as asked),
  shipped in every release package (Windows, Linux, AppImage, macOS) and still released as its own
  asset. The old `zzz-plus-fonts.pk3` must not stay with stale fonts: the user guide says to
  delete it.
- **Where it is loaded: decided by the maintainer (2026-11-14), fork-only folder.** A pk3 in `main/` breaks the default
  menu on `sv_pure 1` servers without it (missing images until restart, as recorded for menu-hd)
  and is read by the original `MOHAA.exe`, upstream OpenMoHAA and older fork builds, whose
  `uilib` does not know the new keywords. Chosen: a fork-only folder (e.g. `plus/` next to the
  executable) that only the fork binary loads, exempt from the pure check for UI and font files
  only (`ui/`, `fonts/`, `gfx/fonts/`, `textures/menu_plus/`; other files in it ignored), a small
  filesystem change marked "in OPM". Rejected: `main/` plus documentation (no engine change, but
  the breakage above stays).
- **State-dependent bar entries:** the engine enables widgets on `main` by name (`backtogame` in
  `UI_MainMenuWidgetsUpdate`, `continue game` / `new game` in `UI_UpdateContinueGame`) and Escape
  in a single-player game pushes `main` over the game (`UI_MenuEscape`). The bar shows Back to
  game, Continue, Save/Load and Disconnect only when they apply, with the widget names the engine
  expects; in-game, `main` opens the same way as the original.
- **Art while the licence is unchecked:** the first background is
  the maintainer's `fondo_00001_.png` (edited by hand). If the Klein 9B licence
  does not allow publishing it, the menu uses a placeholder gradient made by the builder until the
  maintainer regenerates it with Klein 4B.
- **menu-hd:** discarded by the maintainer on 2026-11-15 (a remaster of the original menu, replaced by this menu); not merged.
- **Where the menu sources live:** `misc/plus-pk3/` with the tree as it goes in the pk3
  (`ui/*.urc`, `textures/menu_plus/...`), plus a short build script that adds it to the pk3 made
  by `make_fonts.py`. No CMake step: the fork already builds data pk3s with Python in CI.
- **Same repository, no content repo:** the `.urc` files and the opt-in `uilib` keywords they use
  change together, so one commit keeps menu and binary in step and CI checks out one repo. Art is
  committed as high-quality JPEG (the 3840x1600 master is a 9.5 MB PNG; a JPEG is about 1-2 MB);
  a separate repo or Git LFS only if committed art grows past a few tens of MB.
- **Art license file:** `misc/plus-pk3/ART-LICENSE.md` (CC BY-SA 4.0, author, tool and model, and
  that it was made from text only).
- **Model license:** Flux.2 Klein 9B is released under a non-commercial licence; before
  committing art, the builder checks what that licence allows for outputs, or the art is
  regenerated with Klein 4B (Apache 2.0, on disk). Not verified yet.
- **Fonts:** the fork's existing font set for now; a display font for titles is a later step.
- **Each new screen is its own `.urc` menu** that repeats background and bar and adds its panel
  (uilib menus are full-screen containers on a stack); if repeating gets heavy, the builder may
  find a uilib way to share them.
- **Allied Assault only;** Spearhead/Breakthrough keep their own menus.

## Left to the builder

- Which new `uilib` keywords are really needed, after the bar + panel test; their names and syntax.
- How the UI scale is defined (a cvar such as `ui_plusscale`, or derived from `ui_hudscale`) and
  its default.
- The browser filter for the Favourites / Recent tabs (engine side) and how tabs map to it.
- The exact list of options in Plus and how a renderer change is applied (prompt + `vid_restart`).
- How the background is cut into tiles and anchored (centre crop at any aspect).
- Tests (an automated check that the new `main` loads without errors and fills 16:9 and 21:9, with screenshots) and the user guide page (`docs/markdown/NN-plus-*.md`).
