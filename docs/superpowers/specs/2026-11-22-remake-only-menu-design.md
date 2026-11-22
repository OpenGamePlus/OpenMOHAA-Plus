# Remake as the only fork menu: design

Date: 2026-11-22. Status: approved (approach A).

## Intent

The Plus ("Modern") menu (`main.urc`, `plus_browser.urc`, `plus_options*.urc` in
`misc/plus-pk3/data/ui/`) was born because the fork's own settings had no place in the original
menus. The Remake menu rebuilt the original rooms in Blender, so the fork now has full control over
the scenes and can add those settings as controls that look like they always belonged to the
units, keeping the original's atmosphere. The Plus menu is dropped. Two menus remain:

- **Remake**: the fork's menu, every fork setting reachable from it.
- **Stock**: the game's own menus, for players who do not install the Remake pak.

## Goals

- Every setting the Plus options offer and the Remake lacks today gets a control in a Remake
  options unit (table below).
- The Plus server browser's extras (Recent and Favourites lists, favourite toggle, refresh) move to
  the Remake's internet server board; the "Plus server browser" plate goes.
- The Plus menu files, its backgrounds (`art/background*.jpg`, `bg_*`/`opt_*` tiles) and the Plus
  widget textures that nothing else uses are deleted; the field telephone stops being a hotspot.
- Two fork paks, as today: `plus/zzz-plus.pk3` (fonts only, built by CI, in every package) and
  `plus/zzzz-plus-remake.pk3` (the Remake, built by the maintainer, attached to the release by hand).
- Releases ship the Remake renders as a release asset.

## Non-goals

- Removing engine features the Plus menu introduced (`anchor`, tab handling, the `plus_options*`
  Esc hook, `plus_browser_refresh`): a separate cleanup after this lands. The Remake itself uses
  `anchor`, `cover`, `scalecvar ui_plusscale`, `linkcvar`, `showvalue`, which stay.
- Changing the stock menus.
- New settings that neither menu has today.

## Anti-goals

- Controls that read as pasted on: new knobs, plates and lamps must match the unit's existing
  hardware (same models, materials, engraved-plate style), placed where the unit has room or where
  the unit is extended plausibly.
- A step that leaves a fork setting unreachable (why approach B was rejected).
- Baked text that would need translating: plate texts follow the existing plates (engraved in the
  scene, as today); values are drawn by the engine.

## Constraints

- Renders stay outside the repository. Licence (maintainer's decision): CC BY-SA 4.0 like the
  current menu art, with the AI-generation disclosure, in `ART-LICENSE.md`; the third-party models
  keep their own licences (`remake/credits/models.json`). The pak that
  carries them is built locally from the Blender export by the maintainer and attached to the
  release; CI cannot build it.
- Keep original-game behaviour; fork additions are marked with the `... in OPM` markers.
- Restart-needing settings (display mode, vsync, renderer, anisotropy, language) go on units that
  have Apply (`ui_applylatched`), which all options units already do.
- Generated `.urc` only: changes go in `misc/plus-pk3/remake/<menu>.json` and the Blender scene.
- Remake pitfalls in `docs/dev/architecture/ui-menus.md` apply (render width whole in picture
  units, overlapping rects, etc.).

## Settings to place

Values, ranges and list items are copied from the Plus `.urc` being removed (`plus_options*.urc`;
read them before deleting).

| Unit (mapping) | New control | Cvar(s) | Kind |
|---|---|---|---|
| Video (`video_options.json`) | Display mode: fullscreen / window / borderless | `r_fullscreen` (+ the borderless cvars the Plus list sets) | list |
| Video | Vsync | `r_swapInterval` | check |
| Video | Max FPS | `com_maxfps` | list |
| Video | Anisotropic filtering | `r_ext_max_anisotropy` | list |
| Video | Renderer | `cl_renderer` | list |
| Audio (`audio_options.json`) | Ambience volume | `s_ambientvolume`, 0–1 step 0.05 | slider |
| Advanced (`advancedoptions.json`) | Field of view | `cg_fov`, 80–120 step 1 | slider |
| Advanced | Crosshair size | `cg_crosshair_size`, 0–4 step 0.1 | slider |
| Advanced | Crosshair scale | `cg_crosshair_scale`, 0.1–4 step 0.1 | slider |
| Advanced | HUD scale | `ui_hudscale`, 0.5–4 step 0.1 | slider |
| Advanced | Menus keep 4:3 | `ui_menuaspect` | check |
| Advanced | Language | `cl_language` (restart needed; Spanish needs the `lang/es/` files) | list |

Dropped from the UI: `ui_plusscale` (cvar kept; it still scales the Remake's corner buttons).
Controls (`controls.json`) needs nothing. The resolution list of the Video unit already has the
Plus list's modes.

## Server browser

On `joininternetgame` the "Browse" plate opens `joinnetgame` (the big board with `netgamelist`).
Add to that board's room, as controls in the same style: All / Favourites / Recent (each sets
`dm_browser_show` 0 / 1 / 3 and refreshes, as `plus_browser.urc` does; Refresh already exists), and Favourite
(`widgetcommand netgamelist togglefavorite`). Remove the `MPI_P_Plus` plate and its control.
`plus_browser_refresh` may stay as the refresh indirection (engine-defined) or the commands may
refresh directly; builder's call.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| **A (chosen)** | Add first: new controls and browser controls in the Remake (step 1), then remove the Plus menu, merge the paks, update tests and docs (step 2) | Every step leaves a working menu with every setting reachable |
| B | Remove first, then add | Fork settings unreachable in between; rejected |

Packaging (the maintainer's decision): renders as a release asset. Within that, two paks rather
than one (my call, after the builder check): CI keeps building and uploading a fonts-only
`zzz-plus.pk3`, so the stock menus keep the accented fonts and `07-plus-translations.md` /
`09-plus-fonts.md` stay true; the hand-attached `zzzz-plus-remake.pk3` has its own name and never
clashes with it.

## Step 1: add (each unit can be its own commit)

1. Blender (the builder models, saves the `.blend` and exports through the Blender MCP; the
   maintainer reviews the result, no approval wait per unit): per unit, model the new controls from the unit's existing parts; name them in the
   scene's convention (`Unit_Mouse_lbl_<TEXT>` plates, `*_dial*` knobs, `VidLamp_*_Bezel` lamps).
2. Mapping: add the controls to the unit's JSON; export; build; check with `check_export.py`.
3. Tests: extend `RemakeMenu` in `tests/test_client.py` (each new control exists, sets its cvar,
   pulldown shows the value via `ui_printwidgets`).
4. Browser controls as above, with a test that each sets `dm_browser_show`.

## Step 2: remove

1. Delete `misc/plus-pk3/data/ui/{main,plus_browser,plus_options*}.urc`, `art/background*.jpg`, the
   tile/gradient/field/checkbox generators in `build_pk3.py` that only they use (check `pak.py`
   first: it uses `textures/menu_plus/clear`), and the telephone hotspot in `options_main.json`.
2. `build_pk3.py`: without `--remake` it writes the fonts-only `zzz-plus.pk3`; `--remake` also
   writes `zzzz-plus-remake.pk3`, as today.
3. CI: no change to what it builds or uploads beyond the pak losing the menus; the release workflow
   (`tags-publish-release.yml`) notes that `zzzz-plus-remake.pk3` is attached by hand.
4. Tests: drop `PlusMenu`; keep what `PlusDataFolder` checks (fork pak beats base menu, mods beat
   it, pure servers) against the Remake pak or a test pak.
5. Docs: rewrite `docs/markdown/03-configuration/14-plus-menu.md` as the Remake page (install from
   the release asset, settings per unit, going back to stock), `docs/dev/architecture/ui-menus.md`,
   `ART-LICENSE.md`, `docs/ai/SYSTEM_SUMMARY.md`, `PROJECT_MEMORY.md` stage; run the docs check.

## Left to the builder

Exact placement of each control in its unit; list items for display mode, max FPS, anisotropy,
renderer and language (copy from the Plus `.urc`); whether the server board keeps the version/IP
columns (they come from `anchor` on the list today; the board uses `cover`).
