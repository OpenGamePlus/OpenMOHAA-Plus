# OpenMOHAA Plus options screens (design)

Date: 2026-11-15. Status: approach 1 chosen; builder check done (six tabs and Back behaviour
decided by the maintainer); waiting for approval.

## Intent

The Plus main menu (see the [Plus menu design](2026-11-14-plus-menu-design.md)) still opens the
original 640x480 option screens (`options_main` and its four screens). The maintainer wants a
functional Plus menu base: port the options to the Plus look **and modernise them**, since the
original video settings date from 1999 (4:3 modes up to 1600x1200, 16-bit colour, no window
mode, no vsync or FPS cap). This is the first of the remaining screens to port (then player
setup, create server, load/save, campaign).

## Goals

- One Plus options screen with six tabs in the left bar, like the Plus browser's tabs: **Video,
  Detail, Audio, Controls, Game, Plus** (six, not five: the original advanced options do not fit
  one tab; decided by the maintainer). Each tab is its own `.urc` menu (e.g.
  `plus_options_video`, `_detail`, `_audio`, `_controls`, `_game`; the existing `plus_options`
  becomes the Plus tab), sharing the bar, background and panel.
- The main menu's **Options** entry opens the Video tab instead of `options_main`; its **Plus**
  entry keeps opening the Plus tab.
- Every original option the port keeps, plus modern video settings; every pulldown shows its
  current value (`linkcvar`, see the Plus menu docs).
- **Video tab** (the modernised part):
  - Resolution: "Desktop" (`r_mode -2`, the engine default) and a fixed list with `r_mode -1`
    plus `r_customwidth`/`r_customheight`: 1280x720, 1600x900, 1920x1080, 2560x1440,
    3840x2160 (16:9); 2560x1080, 3440x1440 (21:9); 1024x768 (4:3), 1280x1024 (5:4).
  - Display mode: fullscreen, window, borderless window (`r_fullscreen`, `r_noborder`).
  - Vsync (`r_swapInterval`), maximum FPS (`com_maxfps`).
  - Brightness (`r_gamma`), texture quality (`r_picmip`), texture filter (`r_texturemode`),
    anisotropic filtering (`r_ext_texture_filter_anisotropic`, `r_ext_max_anisotropy`).
- **Audio tab:** the original volumes (master `s_volume`, music `s_musicvolume`) and the
  original quality and speaker settings **only if** they still do something in OpenMoHAA's sound
  code (see Left to the builder).
- **Controls tab:** the original key list (`FakkBindList`), mouse sensitivity (`sensitivity`),
  invert mouse (`m_invert_pitch`), mouse filter (`m_filter`), always run (`cl_run`), and the
  original "Defaults" action (`ui_resetcvars; exec default.cfg`).
- **Detail tab:** model, terrain, effect and curve detail; shadows; entity and dynamic lighting;
  volumetric smoke; static and wall decals (`cg_marks_add`); weather (`cg_rain`).
- **Game tab:** field of view (`cg_fov`), view model, subtitles, console, weapons bar, crosshair.
- **Apply** on every tab restarts what pending changes need, **whatever tab they were made on**,
  and nothing when nothing is pending. `ui_checkrestart` cannot do this: `Menu::CheckRestart`
  (`uimenu.cpp`) only compares the current menu's `linkcvar` widgets with their values when the
  menu was pushed, so a resolution change (only `r_customwidth`/`r_customheight` change) or a
  change made on another tab is missed. **Engine:** a new command (e.g. `ui_applylatched`) that
  runs `vid_restart` when any `CVAR_LATCH` cvar has a pending `latchedString` (else
  `snd_restart`/`ter_restart` for their latch flags, as `CheckRestart` does).
- **Back** returns to the main menu (not the previous tab) and **discards pending changes that
  need a restart** (decided by the maintainer): every cvar with a pending `latchedString` goes
  back to its current value, so an unapplied resolution never takes effect later by surprise.
  Changes that apply at once (volume, sensitivity, brightness) stay. **Engine:** a command (e.g.
  `ui_discardlatched`) next to the one above.
- **Engine:** a pulldown with `linkcvar` recognises an item when **every** `set`/`seta` in the
  item's command matches the cvar's current (or latched) value, not only the first command, so
  "1920x1080" (`set r_mode -1; set r_customwidth 1920; set r_customheight 1080`) and
  multi-cvar presets ("Model detail") show the right item. The `reset <cvar>` rule stays.

## Non-goals

- Antialiasing (MSAA): `r_ext_multisample` works only in `renderer_opengl1`; `renderer_vulkan`
  renders with one sample. Left out until Vulkan supports it.
- A resolution list read from the monitor (approach 2 below): can be added later.
- Restyling the other original screens (player setup, create server, load/save, campaign,
  `multiplayeroptions`); gamepad settings; Spearhead and Breakthrough.
- Removing the original option screens from the game data: they stay (the original `main`
  without the Plus pk3 still uses them).

## Anti-goals

- No change to any cvar's default value or meaning: the screens only set cvars the player
  chooses.
- No option that does nothing on one of the shipped renderers or in OpenMoHAA's sound code (an
  option that silently does nothing is worse than none).
- The original menus keep working unchanged, with or without the Plus pk3 (the engine change
  only affects pulldowns with `linkcvar`; the original files do not use it).
- Nothing copied from the original `.urc` files: the Plus files are written from scratch (the
  original menus are a reference for which cvars and values exist).

## Constraints

- Plus `.urc` rules already learned (Plus menu docs, `14-plus-menu.md`): every widget needs
  `anchor`; `ui_plusscale` on every widget; pulldown `rect` wide enough for its longest title and
  arrow; the narrowest case is 5:4 at `ui_plusscale` 1.1 (panel right edge at 525 units).
- Rows in the panel are 32 units apart from y=112; the panel ends 50 units above the bottom
  (y=430 at 480), so about 10 rows fit per tab; two columns do not fit at 5:4 and
  `ui_plusscale` 1.1 (panel 305 units wide, a label and a pulldown take about 284).
- `FakkBindList` was written for the original 640x480 screen; the server list needed engine fixes
  to work anchored (children placed from the screen origin, header font, scroll bar). The bind
  list may need the same.
- Many video cvars are latched (`r_mode`, `r_customwidth`, `r_fullscreen`, `r_noborder`,
  `r_swapInterval`, `r_picmip`, `r_ext_max_anisotropy`...): they apply on `vid_restart`, which
  Apply triggers through `ui_checkrestart`.
- `renderer_vulkan` honours `r_swapInterval` (present mode) and anisotropy; GL1 honours all
  listed video cvars.
- Tests run headless (no window, no sound); `ui_printwidgets` and `PlusMenu` in
  `tests/test_client.py` check layout.

## Approaches

| # | Approach | Trade-off |
|---|---|---|
| **1 (chosen)** | Fixed resolution list in the `.urc` ("Desktop" plus common 16:9, 21:9, 4:3, 5:4 sizes) | No new engine widget; may list sizes a monitor lacks (windowed still works, fullscreen picks the closest mode) |
| 2 | Engine fills the pulldown from the monitor's modes (SDL) | Exact list, but a new engine feature and more tests; can come later |

Port style chosen by the maintainer: **modernised** port (rejected: faithful port with the same
1999 options). Structure (one `.urc` per tab) is the only sensible one: one file with widgets
shown per tab would be unmanageable.

## Proposals (the builder's calls unless the maintainer corrects them)

- **Row count:** each tab has at most 10 rows (Video has 9, Detail 10); every row must stay
  inside the panel in the layout tests. If one does not fit, 28-unit rows on that tab.
- **Values:** max FPS 60, 85, 120, 144, 165, 240, 333; FOV slider 80 to 120 (the cvar's default
  80 included); anisotropy off, 2x, 4x, 8x, 16x; vsync on/off; texture quality low/medium/high
  (`r_picmip` 2/1/0); texture filter bilinear/trilinear. Dropped from the original video screen:
  colour depth (`r_colorbits`), texture depth (`r_texturebits`), texture compression
  (`r_ext_compressed_textures`).
- **Tab switching** replaces the current tab menu instead of stacking it, so Back always lands on
  the main menu.
- **Tests:** layout test per tab at the existing `LAYOUT_SCREENS`; pulldown values for a custom
  resolution, "Desktop" and a multi-cvar preset; the Options and Plus entries open the right tab;
  Apply restarts video after a resolution change made on the Video tab and applied from another
  tab, and does not restart when nothing is pending; Back discards a pending resolution and keeps
  a volume change; the anchored bind list's geometry (inside the panel, scroll bar at its right
  edge).

## Left to the builder

- Which audio cvars still have an effect in OpenMoHAA's sound code (OpenAL and the legacy
  mixer): keep `s_khz` and `s_speaker_type` only if they do something; add other effective
  volumes (dialogue, effects) if they exist.
- Whether `r_gamma` and `r_noborder` work under `renderer_vulkan` and without hardware gamma;
  drop or label them per the anti-goal if not.
- Whether `cg_fov` is honoured in multiplayer (server restrictions) and in single player; label it
  accordingly or drop it if it is not.
- Exact labels, file names, row order, and whether the bind list needs engine fixes to anchor.
- How tab switching is done in `.urc` commands.
