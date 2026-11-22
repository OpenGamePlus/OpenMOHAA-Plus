# Legacy menu prototype: Blender rooms with hotspots (design)

Date: 2026-11-17. Status: draft for the maintainer's review.

Calls marked *(Claude's call)* were not asked of the maintainer; correct them if wrong.

## Intent

The maintainer models the original menu rooms of Allied Assault in Blender (own models, own
renders, compositions loosely based on the original screens) and wants a menu that works
**exactly the old way**: one picture per screen, click an object to go somewhere, the object
lights up under the pointer and a sign names it. Veterans know the original by heart; they get the
same navigation, sharp on today's screens. It is less discoverable than a list of entries, and
that is accepted.

This is a prototype to decide the project's default menu. If it convinces, the fork could ship two
menus: **Legacy** (this one) and **Modern** (the current Plus menu, the left bar with text
entries), chosen by the player. How the player chooses is decided after the prototype.

## Goals

- Three screens from the maintainer's renders, each 3840x1600 (2.4:1, the same as the Plus
  backgrounds):

  | Screen (menu name) | Render (maintainer's Blender folder, outside the repo) |
  |---|---|
  | `main` | `03_principal/principal_1940_v2_final.png` |
  | `options_main` | `02_opciones/opciones_1940_v2_final.png` |
  | `war_records` | `01_war_records/escritorio_1940_v2_final.png` (the screen drafted, uncommitted, in `misc/plus-pk3/data/ui/war_records.urc`) |

- The hotspots of the original menus, mapped to objects in the renders (agreed with the
  maintainer):

  | Screen | Blender object | Command | Sign shown (original texture) |
  |---|---|---|---|
  | main | `Map_Europe` | `pushmenu briefingroom` | `newgame_sign` |
  | main | `DoorB_root` (back door) | `pushmenu briefingroom` | `briefingroom_sign` |
  | main | `DoorR_root` (right door) | `pushmenu multiplayer` | `multiplayer_sign` |
  | main | `Options_Root` (radio table) | `pushmenu options_main` | `options_sign` |
  | main | `WarRecords_Root` (desk with phones) | `pushmenu war_records` | `warrecords_sign` |
  | main | `FilmBox` (box of film reels; was `Projector_Deco`, outside 4:3) | `spmap credits` | `credits_sign` |
  | main | `Board_Frame` | none: the sign is drawn here (`linkcvar ui_signshader`) | |
  | options_main | the panel labelled Advanced | `pushmenu advancedoptions` | `advanced_sign` |
  | options_main | the Audio unit | `pushmenu audio_options` | `audio_sign` |
  | options_main | the Controls unit | `pushmenu controls` | `controls_sign` |
  | options_main | the Video unit | `pushmenu video_options` | `video_sign` |
  | options_main | the sign board (top left) | none: `linkcvar ui_optionshader` | |
  | war_records | the medal box | `pushmenu medals` | `personalrecords_sign` |
  | war_records | the LOAD/SAVE trays | `pushmenu_sp loadsave;pushmenu_dm loadsave_mp` | `loadsave_sign` |
  | war_records | the sign board | none: `linkcvar ui_recordsign` | |

  The original `options_main` hotspots are those four plus Back; the commands, cvars and sign
  names come from the original `ui/main.urc` and `ui/options_main.urc` (read from `Pak0.pk3`, never
  copied). Which Blender objects are the four options units and the war records box, trays and board
  is read from `02_opciones/opciones_1940_v2.blend` and `01_war_records/escritorio_1940_v2.blend`;
  if their names are unclear, the builder asks. War records gets the lit-object hover like the
  others *(Claude's call)*.
- Every other menu (the options dialogs, multiplayer, briefing room, load/save, medals) is the
  original from the player's own game files, reached by name. Nothing from those files is shipped.
- Text entries for **Back to game** (`popmenu 0` four times, as the original), **Quit** (main)
  and **Back** (options, war records) in the bottom corners, in the Plus font, like the Back of
  `war_records.urc`.
- Under the pointer an object lights up: the hotspot's `hovershader` is the background under the
  hotspot with the object lit (brighter by 1.2, tinted warm, soft rim), from an object mask.
- Hotspots stay on their objects at any aspect ratio and any `ui_plusscale` (checked with
  `ui_printwidgets` in tests).

## Non-goals

- The Plus option tabs and any new settings panel (a later "box with the new options" is a
  possible addition, not part of this prototype).
- Choosing between Legacy and Modern in game; the prototype is a separate pak that, when installed,
  replaces the Modern main menu.
- Animated camera moves between rooms; the original cuts straight from screen to screen.
- Spearhead and Breakthrough menus.
- Engine changes: none are needed (see Constraints).

## Anti-goals

- A hotspot that drifts off its object on some screen shape or scale.
- New text baked into renders for navigation (it cannot be translated; the signs and engine-drawn
  labels carry the names). The English labels already in the war records (LOAD, SAVE) and options
  renders stay for the prototype as 1940 set dressing; the maintainer revisits them later.
- Any original game file (art, `.urc`) in the repo or in a published pak.
- Committing or publishing the renders before the maintainer settles their licence: they are
  recreations of the original compositions, and `misc/plus-pk3/ART-LICENSE.md` today describes
  text-to-image art. The prototype must build from renders kept outside the repo.
- Changing the Modern menu or the original menus' geometry. The trial renders and art changes in
  the working tree of `feat/plus-menu-art` (`misc/plus-pk3/art/*.jpg`, `background_warrecords.jpg`,
  the `war` tiles in `build_pk3.py` and its tests) are never committed; the committed Modern art
  stays the ComfyUI pictures. `war_records` moves to the Legacy pak (its background is a render),
  so the Modern menu opens the original war records *(Claude's call)*.

## Constraints (checked on 2026-11-17)

- `cover <w> <h>` (fork keyword, `UIWidget::ApplyCover` in `code/uilib/uiwidget.cpp`) places any
  widget as the `rect` part of a `w` x `h` picture scaled to cover the screen. Checked with the
  war records hotspots given `scalecvar ui_plusscale` and `cover 1152 480`: their screen rects
  match the picture to the pixel at 1280x720 (`ui_plusscale` 1 and 1.2), 1024x768 and 3840x1080.
  So hotspots in picture units (1152x480 for a 2.4:1 render) need no engine work. The
  `shortcut:` note in `war_records.urc` about frame placement is therefore obsolete.
- Cover crops: at 16:9 the visible picture is x 149..1003 (of 1152), at 4:3 x 256..896; wider
  than 2.4:1 it crops top and bottom (at 32:9 the main sign board is cut off at the top; accepted,
  such screens are rare and clicking still works *(Claude's call)*).
  Everything clickable must sit in the 4:3 zone, the sides are decoration. Today
  `Options_Root` (x 173..322) and `Projector_Deco` (x 926..1070) are outside it; see Scene
  adjustments.
- Textures are powers of two (`r_roundImagesDown`); paintings ship as JPEG (`build_pk3.py`
  splits each background into two 2048x2048 tiles).
- Paks in `plus/` load in `FS_PathCmp` order and a later pak wins; `zzz-plus.pk3` holds the
  Modern `ui/main.urc`, so the Legacy pak must sort after it (for example `zzzz-plus-legacy.pk3`;
  verify with `ui/main.urc` resolving to it).
- On pure servers only `ui/`, `fonts/`, `gfx/fonts/` and `textures/menu_plus/` of the `plus/` paks
  are read (`code/qcommon/files.cpp`), so the legacy textures live under `textures/menu_plus/legacy/`.
  The legacy pak relies on `zzz-plus.pk3` for the font and `textures/menu_plus/clear`.
- The headless client has no mouse: hover and clicks are checked by hand, layout through
  `ui_printwidgets`.
- The maintainer works in Blender 5.3 on Windows; Blender MCP is connected to this project
  (Claude can run Python in the open scene).

## Approaches

| | Approach | Trade-off |
|---|---|---|
| A | Hand-written `.urc` with rects measured on the render, the generic hover gradient | Fastest; hotspots re-measured by hand whenever the camera moves; hover is a bar over a photo, not a lit object |
| **B (chosen)** | Blender export (hotspot rects from the camera + highlighted crops) and `.urc` generated from it | Exact at any shape; the old lit-object hover; re-export after any scene change. More work up front, repaid by every room added |
| C | Animated camera moves between rooms | Not how the original works; many more renders and pak size |

The maintainer chose B. It was first sketched with an engine keyword for picture coordinates;
`cover` turned out to do that already, so B has no engine part.

## Design

### Blender export (`misc/plus-pk3/legacy/export_hotspots.py`, AGPL-3.0-or-later)

Runs inside Blender (through Blender MCP or Blender's text editor) on a screen's `.blend`, with
the screen's mapping file (below). It renders **everything** from one scene state, so the crops
always match the background (agreed with the maintainer): first the background at the scene's
render settings, then per hotspot object (with its children):

- **Rect**: project the evaluated mesh vertices through the scene camera
  (`world_to_camera_view`), keep those in front of the camera, take the bounding box, scale to the
  picture units (1152x480 for 3840x1600), round outwards, clamp to the picture. Occlusion is
  ignored (a chair in front of a desk is inside the desk's rect).
- **Mask**: render only that rect (render border, cropped) with Workbench, the hotspot's objects
  white and every other mesh black (so what stands in front stays dark); under a second. Object
  colours, engine and colour management are restored afterwards.
- Changed during the build (2026-11-17): the first design rendered each crop with the object's
  emission raised. On the main room it washed the map out to white and took about 8 minutes a crop
  (EEVEE, 512 samples). The maintainer picked the mask and a gain of 1.2 from mockups.
- Writes, in an output folder next to the `.blend` (outside the repo), the background, the crops
  and `<screen>.json`: picture size, background file, and per hotspot the rect and the crop file.
  The maintainer approves the scene before a run; the script never saves the `.blend`.

### Mapping files (`misc/plus-pk3/legacy/<screen>.json`, in the repo)

The agreed table above, as data: per hotspot a widget name, the Blender object, the command, the
sign shader, and the sign cvar of the screen (`ui_signshader` for main, `ui_optionshader` for
options). The sign board is an entry with no command. The export fills in rects; to change a
clickable area, change the objects listed (for example `DoorB_root` plus the frame `DoorL_*`).

### Pak build (`misc/plus-pk3/build_pk3.py --legacy <export folder>`)

- Reads the mapping files and the exported `<screen>.json` from the render folder.
- Background: same split as today into `textures/menu_plus/legacy/<screen>_l.jpg` / `_r.jpg`.
- Hovers: the background under each hotspot, lit where its mask is white (`pak.lit`: brightness
  times the mapping's `highlight.gain`, 1.2, blended 10% towards `highlight.color`, 255 214 150, and
  a soft rim of that colour), resized to the nearest power of two on each side (the widget
  stretches it back), `textures/menu_plus/legacy/<screen>_<widget>_h.jpg`.
- Generates `ui/<screen>.urc`: the two background labels as in `war_records.urc`; per hotspot a
  `Button` with the rect, `scalecvar ui_plusscale`, `cover 1152 480`, `shader
  textures/menu_plus/clear`, `hovershader` the crop, `clicksound sound/menu/apply.wav`,
  `stuffcommand` and `hovercommand "set <signcvar> <sign>"`; the sign label with `cover` and
  `linkcvar <signcvar>` `linkcvartoshader`; the corner text buttons with `anchor`. Generated files
  carry a header saying so and naming the mapping file.
- Writes `plus/zzzz-plus-legacy.pk3` (or the name that sorts after `zzz-plus.pk3`). Without
  `--legacy` the build is as today.
- `war_records` is generated like the others, into the Legacy pak only; the hand-written draft
  and its `war` tiles leave the Modern build.

### Tests

- `misc/plus-pk3/test_build_pk3.py`: with a small fake render folder (generated in the test:
  plain images and a `<screen>.json`), the legacy pak holds the tiles, power-of-two crops and a
  `.urc` per screen with one button per mapped hotspot.
- `tests/test_client.py` (`PlusMenu`): with the legacy pak built from that fake folder, each
  screen opens without UI errors, and each hotspot's screen rect equals its picture rect under
  cover at 1280x720, 1024x768 and 2560x1080, and with `ui_plusscale 1.2`. Every command target
  menu opens (`pushmenu` of each, no "Couldn't find menu").
- By hand on Windows with the real renders: hover lights each object, each click goes to the
  right screen, the sign changes.

### Scene adjustments (art, with the maintainer)

Measured on 2026-11-17: moving the options desk (~0.9 m) or the projector (~0.9 m) into the 4:3
zone collides with the cabinet and with the reels, and widening the camera would need a ~10 mm
lens. The maintainer chose, for the prototype: credits on `FilmBox` (inside 4:3), the options desk
left where it is (inside 16:9, cut on 4:3 and 5:4; a debt row).

### Docs

- `docs/dev/architecture/ui-menus.md`: the legacy pak, the export, `legacy/pak.py` and the generated `.urc`.
- User page `docs/markdown/03-configuration/14-plus-menu.md`: a short "Legacy menu (prototype)"
  section, and that `cover` also places widgets in a picture.
- `docs/ai/PROJECT_MEMORY.md` stage; `docs/dev/roadmap/debt.md` row for the unsettled art licence
  if the prototype is merged without the renders.

## Left to the builder

- How the fake render folder for tests is produced.
- Where in the task order the scene adjustments go (they only change exported rects); the export
  and build can be built and tested on the current scenes before the art is final.
