# Project memory

Append-only operational memory. Newest first, at most 3 bullets per stage, never rewrite history.
Template: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md#memory-entry-template).

## 2026-11-21 — Legacy player options and join screens
- Copies of the multiplayer room with boards hung from the ceiling (`mpboard.py`): the player options (name, models, connection; the engine draws both soldiers in the room), and the join screens: LAN or internet, the server lists (`servers` control: `langamelist`, `netgamelist`), an address, the Plus browser where GameSpy was. The free-for-all model dialog frames the room's view.
- `CL_Draw3DModel` uses a 30x30 degree view whatever the rect: narrow model rects squeezed the soldiers, so the pak makes them square. A title's label over a button takes the pointer (`FindResponder` picks the topmost widget), so lit buttons carry their text in the picture.
- Not checked: joining a server, typing an address, the dialog in a real free-for-all game.

## 2026-11-21 — Legacy multiplayer room
- The main room's multiplayer door opens a corridor built from a copy of the main room (`mp_build.py` rebuilds it from that file each run), framed on the original by overlaying it: map-room doorway, locker (player options, three Sketchfab jackets), red door (join), board and chest (start or change map). Hotspot and corner names stay the original's (`startnew`, `changemap`, `joinlan`, `disconnect`): the game enables them by name.
- Zone hovers are now rendered over the whole frame and cut by the pak: a border render lit the room darker, so a hover could darken its zone. Hotspots sharing a lamp (start and change map) keep it on for both.
- Credits: a Polish name broke cp1252 (now transliterated, tested on the real file) and ten models overflowed the board under Back (spacing fits it, eleven is a build error).

## 2026-11-21 — Legacy war records, medal case, load/save folder
- War records is the main room's desk up close (`off` lists the room's zone lamps); its box opens the medal case and its trays a load/save folder, both close-ups built from copies of that scene.
- Medal case: the original's nine medals, modelled, ComfyUI reliefs; each shows when earned and names itself on the case's strips. Folder: built in 3D (ComfyUI paper textures, DejaVu stamps), seen straight down so the game's save list (`LoadSaveList`, fixed `facfont-20` column titles) is not distorted.
- A control's own render (medal, a stamp's `lit` look) is the whole frame, cut by the pak: a border render lit the velvet differently. A button tints its hover picture with `fgcolor`; textless buttons use white (the glow came out brown). A first folder from a 4:3 picture cut every paper at the frame and was rebuilt in 3D. Not checked: load, save and delete with real saves.

## 2026-11-21 — Legacy option screens (video, audio, advanced, controls)
- The options room's units open close-ups (`opciones_detalle_1940.blend`, one camera each) with the original screens' controls on them: `"screen"` mappings, `export_screen`, `screen_urc`; a list is a transparent pulldown over knob and plate, a check lights a lamp (`lamp_on`), a slider sits on a plate, `binds` puts the key list on a card. Plates went blank with their titles painted under them.
- Engine: a widget under `cover` now places its children in it (a pulldown's value is a child: it sat at the screen's origin, clipped away) and a covering checkbox's box fills its rect. A list whose items each give the cvar its own value shows it with a label, as the original did (multi-cvar items rarely all match).
- Apply is `popmenu 0; wait; wait; ui_applylatched`: with ui_checkrestart the renderer restart brought the screen back on the maintainer's Windows (not reproducible headless). Open: Windows check of Apply; cgame cvars (wall decals, view model) are blank until a game loaded, as in the original.

## 2026-11-21 — Legacy menu: model credits, green buttons, exact picture units
- A 16:9 render (2560x1440) is 853.33 picture units: rounded, the background tiles and hovers sat ~1.5 px apart. `picture_size` now refuses a width that is not whole (the room renders 2562x1440, 854 units) and the pak splits the background on the urc's unit. A broken export used to leave an empty pak over the working one: `write_legacy` now writes a temp file.
- The chalkboard opens `legacy_credits` (from `legacy/credits/models.json`: 7 Sketchfab models, all CC BY 4.0, title, author, source, licence); credits moved to the projector like the original; `"glow": "frame"` keeps a door's or a board's hover inside its outline.
- Green corner plates (`green_plate`) took no hover or click at `ui_plusscale` 0.85: the scaled menu frame ended above them and `FindResponder` skipped children outside it; screen-placed children (anchor, cover) are now checked, proven with a new `ui_testmouse` (headless clients have no mouse; the floating console takes the pointer unless `ui_console 0`). Hovers fade from the object inside an 8% padded rect (no straight cuts); build label at 0.65 size. Scene v4: sign one beam closer, larger, parallel to the image; fan on the room side.

## 2026-11-20 — Legacy menu: dark room, lamps per hotspot, 4:3 framing
- The main room is dim and cool like the original (teal fill, maintainer's pick against a screenshot): a hotspot's `lights` (lamps, lit shades) are off in the background, and its hover is its rect rendered with only its own lamps on, faded in (`zone_lit`); lamp meshes lose their emission through per-object material copies. A stale export without lit renders is refused.
- Hovers drew up to 1.5 px up and left of the background: `Set2DWindow` takes whole pixels and cut fractional `cover` frames. `ApplyCover` now puts the edges on whole pixels; `ui_printwidgets` prints two decimals so a test sees it.
- Framing: camera 1.4 m back, 2.5° turned (`principal_1940_v3.blend`), every hotspot in x 284..867 of 1152 (4:3 and 5:4); `Hover_<zone>` spots light the doors and film box. Open: the room reads far away, options and war records rooms still lit the old way.

## 2026-11-18 — Legacy menu: engine-drawn signs
- The signs were the original 128x32 `*_sign` images stretched over the rendered boards. Now the sign label maps each sign value to the mapping's text with `linkstring`, in a new `plussign-32` serif font (DejaVu Serif Bold, 3x: 4x would be a 16 MB atlas). Linked texts now go through the localization, and text under `cover` scales with the picture, shrunk to 90% x 50% of its widget (the real main board cut "Multiplayer").
- The new font crashed the GL renderers: game fonts have a `.shader` script, and without one `R_FindShader` built a lit world shader. A script would not fix pure servers (`scripts/` is not exempt), so scriptless fonts get the 2D shader.
- Leftover headless clients from timed-out throwaway scripts ran for hours at ~380% CPU each and slowed the suite. Throwaway scripts must kill the client in `finally`. Open: Windows hand check of the signs.

## 2026-11-17 — Legacy menu prototype (Blender rooms)
- The maintainer's Blender rooms (main, options, war records) as a separate `zzzz-plus-legacy.pk3` that works like the original menus; every other screen is the game's own. No engine change: `cover <w> <h>` already places any widget in picture units, exact at every shape and `ui_plusscale` (the war records draft's frame placement was a needless shortcut).
- Hover: rendering each crop with raised emission washed the map out and took ~8 min a crop; a Workbench object mask (<1 s, occlusion kept) plus a 2D light in the pak build (gain 1.2, maintainer's pick) matches the background exactly. Background exports run in `blender -b` from the saved `.blend`, about 40 s a room, so the maintainer's open session is never touched.
- `.gitignore`'s `build*` silently kept `legacy/build_legacy.py` out of a commit (now `legacy/pak.py`). Open: renders not committed (licence), options desk outside 4:3, Windows hover/click check by the maintainer.

## 2026-11-15 — Menu backgrounds per screen
- Maintainer's ComfyUI art (3840x1600, 2.4:1 like the old one): an operations room for the main menu and browser, a radio desk for the options (`opt_l`/`opt_r`).
- The tiles moved from TGA to JPEG: as TGA the two paintings made the pak 40 MB; as JPEG it is about 5 MB, smaller than before. The client tests swap in plain TGAs, so they drop the built JPEGs (the renderer would load those first).
- Open: more screens (campaign, load/save, war records, player setup) are not ported yet; each new background costs about 1.5 MB.

## 2026-11-15 — Plus pulldown lists match the field
- The open list still used the original popup: `verdana-12` scaled up (blurry) on a fixed green box. A `linkcvar` pulldown's list now takes the container's font and scale, the field's width, a dark box, a gold border and padded rows.
- The lit row is a translucent accent with a bar, not dark text on gold: the Plus `facfont-20` has a baked dark outline that smears on a light fill.
- Not covered by tests: the headless client cannot open a list; checked with a temporary hook and screenshots.

## 2026-11-15 — Plus checkbox, slider and build label
- Maintainer picked from mockups: tick checkbox (generated textures, no code but a box sized to the rect for anchored ones; the original draws 14 units whatever the rect), sliders with their value (`showvalue`, flat style drawn in code; textures alone could not drop the arrows) and a build label in every menu, original and in-game ones too.
- The embedded git hash only changed on a manual reconfigure (the build said `4db67c7a` three days and many commits later); `cmake/version.cmake` now lists HEAD, the branch ref and packed-refs as configure dependencies. A `git archive` build has no hash and the label shows the version only.
- The `showvalue` format comes from a menu file, so it is checked (one float conversion) before it reaches `snprintf`.

## 2026-11-15 — Docs audit
- Structure, ADRs and memory were sound; the drift was in what recent work never wrote down. New `docs/dev/architecture/ui-menus.md` gathers the UI code map, the opt-in rule and the pitfalls that were only in memory stages.
- Also added: doc-sync rows (menus, pk3 art, banner), where specs and plans live, and the MSVC strictness note in `compiling.md`. A fresh review caught three overstatements (`cover` flag, white textures, ART-LICENSE scope), fixed before merge.
- The checker now covers the fork's `docs/markdown/**/NN-plus-*.md` pages (fork files, never checked) and the committed specs, the latter for personal data only: a discarded spec names files that were never written, which is history, not a broken path. The workflow also triggers on those folders and the READMEs.

## 2026-11-15 — New banner and visual identity
- The maintainer supplied a new banner (medal with laurel, Playfair Display / Oswald / Rajdhani); it is the repo's identity, palette in PROJECT_CONTEXT.md. Its fonts were only named: GitHub shows the SVG as an image, which cannot load fonts, and with the fallback the subtitle ran past the right edge. The text was outlined (harfbuzz shaping, fontTools outlines, OFL fonts from google/fonts), checked against a render with the fonts installed: identical.
- Editing the banner's text means outlining again; the outlined file has no `<text>` left (title and description stay as `<title>`/`<desc>`). The "MOHAA" badge took the ribbon olive `6e7f3c`.

## 2026-11-15 — Plus pulldowns drawn as a bordered field
- The maintainer disliked the original arrow (a cut dome, placed right after the value, so each row's arrow sat elsewhere) and picked mockup "A" of three (bordered field, divider, down arrow). The container's own `shader` draws `textures/menu_plus/field.tga`, generated by `build_pk3.py` in white so `fgcolor` tints it; the old arrow became the transparent `clear.tga`. No drawing code beyond keeping the arrow at its own size.
- A lone pulldown is now clickable over its whole widget: before, only the value and the arrow were, and with no value (Detail pulldowns before the first map) just the 8-unit transparent arrow. `assert_options_tab` checks the clickable width covers the field.
- Asked by the maintainer: the list only stayed open while the button was held (original press-drag-release). A click now leaves it open: the pulldown stays first responder, so it gets every move and click and passes moves to the popup. If its menu is hidden with the list open (Esc), the next mouse event closes it. Not testable headless (no mouse input): checked by hand on Windows only.

## 2026-11-15 — Plus option tabs could not be switched
- Seen by the maintainer on Windows: only the Video tab opened. `popmenu 0;pushmenu X` never works in one command line: `MenuManager::PopMenu` locks the menus until its unlock event runs (next frame) and schedules a `showmenu` for the menu below, so the push was ignored. New `replacemenu` (`MenuManager::ReplaceMenu`) swaps the top menu in one step.
- `test_tabs_do_not_stack` passed anyway: it only checked that Back ended on `main`, which is also where a failed switch leaves you. It now asserts each tab opens; a test of a navigation must check every step, not only the end.

## 2026-11-15 — Plus options tabs (modernised port of the option screens)
- Six tabs replace `options_main` and its screens (Video, Detail, Audio, Controls, Game, Plus), tabs replace each other (`popmenu 0;pushmenu`). `ui_checkrestart` only compares the current menu's `linkcvar` widgets, so a resolution change (only `r_customwidth/height` move) or one made on another tab was missed: Apply is `ui_applylatched`, Back (and Esc) `ui_discardlatched`, against a snapshot taken by `ui_marklatched` when the options open: without it every server latch (`g_gametype` for the next map) made each Apply restart video and Back dropped it; `CVAR_SOUND_LATCH`/`CVAR_TERRAIN_LATCH` never latch in cvar.c (`s_khz` changes at once), so their values are compared instead (found by the final review). Pulldown items match when every `set` matches (quotes, numbers), so resolutions and detail presets show their title.
- `FakkBindList` in a scaled menu: `ui_plusscale` changes reach it through `AlignPosition`, not `Realign`, so rows kept the old size; columns come from `ui/bind.scr` in fixed units (about 330, more than the 5:4 x1.1 panel). Now relaid out on scale change and narrowed to fit, scalecvar lists only (original screen geometry identical). A list height must be whole 16-unit rows or the last row is cut.
- Checked before keeping options: borderless and brightness work on Vulkan (SDL window flags and gamma ramp), `cg_fov` is client side (65-120, not zoom/cameras), all five audio cvars are read by the OpenAL code; antialiasing left out (Vulkan has one sample).

## 2026-11-15 — Plus browser columns reworked
- Screenshots with real servers (the headless Linux client reaches the masters unless `NO_MASTERS`): at 1080p the list is ~590 virtual units, so the Version column (> 800) never showed while every name carried OPM's "(1.11) " prefix. The anchored list now drops the prefix, always has a version column ("Ver." when narrow) and shows IP only above 800 units; the original list is unchanged.
- Title widths decide the narrow split (5:4 at ui_plusscale 1.1): "Gametype" needs ~19%, "Players" ~15%, "Version" would need 15%, hence "Ver.". `printlist` lines end with the version. `+set ui_consoleposition "<x> <y> 8 8"` moves the console out of headless screenshots.

## 2026-11-15 — Plus options pulldowns show their value
- `PulldownMenuContainer` with `linkcvar` (opt-in, unused by the original menus) shows the title of the item whose first command is `set|seta <cvar> <value>`, or `reset <cvar>` at the default; the pending value of a latched cvar (`cl_renderer`, `cl_language`), else the raw value. The two value labels are gone.
- The pulldown widget is as tall as its arrow shader (68 units) but the container clips it to its own `rect`, so the value is centred on the container: centred on its own frame it was drawn below the visible part. `ui_printwidgets` prints `pulldown value` and the drawn width, which must fit the `rect` ("Game default" needed 160 units, not 148).
- `test_plus_options_opens` failed twice (pulldowns missing from the output) in the first runs after a pause, then passed 8 times; likely `start()`'s fixed 8 s wait for the main menu.

## 2026-11-15 — Plus browser rows readable
- Seen on the maintainer's 1920x1080 screenshot: rows were tall but their text tiny, because `FAKKServerListItem::DrawListItem` prints at `getHighResScale()` (`uid.scaleRes`, 1 unless `ui_hudscale` is set) while the header and row height use the list's virtual scale. The anchored list now draws rows at its virtual scale; the original list is unchanged.
- Cells are cut at their column's edge (long server names ran over Map at the new size). `ui_printwidgets` prints `items scale`; `test_browser_layout` checks it. The cut is not tested: the headless client gets no rows (no masters, no LAN server).

## 2026-11-15 — Plus menu layout fixed, geometry tests
- Seen on the maintainer's 5:4 Windows screenshots: `align left` puts a widget at x=0 whatever its `rect`, and a widget with neither `align` nor `anchor` lands in the 2048-unit frame, off the screen (options labels piled in the bar, controls invisible). Every Plus widget now uses `anchor`; bar texts left-aligned, in-game entries grouped above Quit, "New game" kept only as an empty zero-size widget (the engine sends it events that would leak otherwise).
- Browser: a widget with `WF_NOPARENTADJUST` gave its children the screen origin, so the list's scroll bar sat at `width - 16` from the screen's left edge; fixed for anchored widgets only. The anchored list takes its header in the row font and leaves room for the scroll bar; the original browser keeps its columns.
- New `ui_printwidgets` console command (widget, text and list geometry in pixels); `PlusMenu.test_{main,options,browser}_layout` assert on it at 1280x1024 (ui_plusscale 0.85 and 1.1), 1920x1080 and 2560x1080.

## 2026-11-14 — Plus menu (adaptive main menu, browser, options)
- Engine: `fs_pluspath` data folder loads `plus/*.pk3` above base and below `fs_game` (Allied Assault only), pure-exempt only for UI/fonts/menu art and never reported to servers (ADR 0007); `.urc` gained opt-in `anchor` and `cover`, the server list `togglefavorite`/`selectitem`. `misc/plus-pk3/build_pk3.py` builds `zzz-plus.pk3`; CI ships it in zips, AppImages and as an asset.
- Mod paks must beat the fork folder on pure servers (fixed after the first cut); the background uses `cover` so 32:9 needs no dark sides; pulldowns cannot show their value, so labels do. Art is AI-generated (CC BY-SA 4.0). The HD remaster of the original menus (`feat/menu-hd`) was discarded for this menu and never merged.
- Open (debt.md): `.msi` lacks the pk3, macOS path, LAN tab test, entry hover/click untested, Spanish needs translation files.

## 2026-11-12 — 4:3 menus: knobs and popups
- Seen by the maintainer on Windows (Vulkan) but renderer-independent: four `uilib` widgets computed width/640 and height/480 themselves instead of `SetVirtualScale`, so the #583 uniform scale missed them (advanced options knobs stretched and cut). Grep for `vidWidth / 640` before adding a scaled widget.

## 2026-11-12 — Vulkan renderer ships in the Linux and Windows builds
- No release had it: every CI configured `USE_RENDERER_DLOPEN=OFF` (renderer linked into the client), and `renderer_vulkan` only exists as a loadable module; the Linux job installed `libvulkan-dev` for nothing. Linux and Windows now load renderers at run time; the Windows MSI lists `renderer_opengl1.dll`/`renderer_vulkan.dll` (without them the installed game has no renderer).
- Windows checked on the maintainer's machine from WSL: a copy of the tree on a Windows drive (MSVC cannot build from the WSL share), VS 2019 Build Tools x64 generator, CMake 4.4, win_flex_bison 2.5.25, Linux's Vulkan headers; run with SDL's `dummy` video driver (the bundled `SDL2.dll` has no `offscreen`): the renderer falls back to offscreen on the RTX 5080, `dm/mohdm2` drawn right. GL1 cannot be compared that way (no GL context).
- Headless parity rechecked on six maps (mohdm1, 4, 6, 7, obj_team1, 2): only swaying foliage differs; maps load 450-540 images, far from the 4096-allocation cap some drivers have.

## 2026-11-12 — fifth batch: #219 and #526 fixed, #538 and #243 not reproduced
- #219: the issue's message on stock heads was not reproduced (AA `head1.skd` is valid), but its check had `||` for `&&`: a crafted morph offset crashed the server in `strlen`. The box message on `allied_pilot.skd`/`hedge_bomb.skd` is right: the shipped files end where 18 hit boxes should start.
- #526: upstream already installs to `<prefix>/lib/openmohaa`; left were the `.desktop` entries that ran launchers not on PATH, and the vendored recastnavigation installing headers and static libs (`EXCLUDE_FROM_ALL` stops that without touching vendored code).
- Effects for screenshots: `global/model.scr` with `models/emitters/gren_exp.tik` shows the fire; the script command is `angles_toforward`. `training` prints 16 missing-label errors from the stock data (BSP triggers name labels absent from Pak5's `training.scr`).

## 2026-11-12 — fourth batch: #793 fixed, #688, #927, #675/#894 not reproduced
- 68 open upstream issues were still untriaged; this batch took the ones testable here. #793 reproduced only artificially (140 long sound names cached mid-game): stock maps with 8 bots stay near 20 KB of the 41952-byte gamestate, so the reporter's server likely ran mods. The server now refuses the configstring that would not fit instead of dropping every client.
- Campaign screenshots need `finishloadingscreen` (the briefing's continue button); `spawn` stays refused even with `cheats 1` in `devmap`, `sv_scripts` with `global/model.scr` spawns effects instead.
- `.cmake` still pointed at the old checkout path; reconfigured in place with the same options. The Plus protocol idea of OpenCoD2-Plus is recorded as deferred in ideas.md.

## 2026-11-11 — fork licensed AGPL-3.0 (ADR 0006)
- Possible because every GPL header in `code/` is GPL-2.0-or-later; fork-only files (40 sources) now carry AGPL-3.0-or-later, upstream files keep their GPL header, `LICENSE` added next to `COPYING.txt`.
- `vk_core.c` checked against Quake3e's `vk.c` (GPL-2.0, no header): only API boilerplate matches.
- Open: GameSpy SDK has no licence notice (inherited); release zips and the AppImage ship no licence text (pre-existing).

## 2026-11-11 — bug batch: resident cgame, rehashbans line ends, init time
- cgame on emulated musl crashed twice: `CL_ShutdownCGame` runs several times, so "nothing loaded" must not mean "unloaded" (a later call freed the resident module's memory); emitters kept the previous level's tiki pointers and crashed the autosave. `rehashbans` now reads CRLF and a last line without newline; the init time prints positive.
- Not reproduced: client hang on shutdown (kick + quit, SIGTERM). Kept as is: `SetDMMaxAmount`, `G_SetTime` comparison (original-game code, no symptom). The HRTF-off test failed only because the game config picks headphones.
- GitHub Pages enabled (Actions source); the docs workflow deploys. A second Claude session worked in the same checkout meanwhile (stale `index.lock`): use a worktree for parallel sessions.

## 2026-11-11 — README follows the sibling projects; repo moved to OpenGamePlus
- README (en, es) takes the OpenCoD2-Plus / OpenBF1942-Plus layout: banner, "What works today", callouts, Game versions, Roadmap, collapsible Building / Testing / "What is where"; maintainer is OpenGamePlus, as in OpenBF1942-Plus.
- The repo move had broken the update checker (old API URL answers 301, curl does not follow) and silently disabled the upstream-sync workflow (`github.repository` guard).
- Not done: four more README languages (siblings have six), own screenshots (still OpenMoHAA's v0.60.0 ones); the update checker still finds nothing until a stable (non-pre-release) release exists.

## 2026-11-11 — docs audit: drift fixed
- Checker passed but facts had drifted (fork owner now `OpenGamePlus`, lag compensation missing from the summary, incomplete fork-file list, "next" already done, `test_lz77` claimed unwired while CTest runs it in CI): checks against git and code catch what path/link checks cannot.
- Phase progress moved from `ideas.md` to `SYSTEM_SUMMARY.md` (live state in one place); `ideas.md` stays the backlog.
- `AGENTS.md` now allows fork user pages `docs/markdown/**/NN-plus-*.md` (practice already did); doc-sync row added for new cvars, commands and events.

## 2026-11-09 — Vulkan renderer in a window; opengl2 checked
- First windowed run of `renderer_vulkan` on real hardware (NVIDIA RTX 5080, proprietary driver, X11): `training` played, `vid_restart` at first start, clean exit; the picture looked right to the maintainer.
- Headless FPS (`com_speeds`, no vsync): GL1 and Vulkan both hit the engine's 1000 fps cap (integer ms frames) up to 4K; at 8K Vulkan ~580, GL1 still capped. Headless GL may not wait for the GPU, so the gap is likely overstated.
- `renderer_opengl2` built and run for comparison: not usable for MOHAA (terrain, alpha-tested sprites, HUD colors); recorded in `debt.md`.

## 2026-11-09 — bots throw grenades (#833)
- Bots never threw grenades and with grenades only took out an empty pistol (`UseWeaponWithAmmo` skipped throwables). Now: switch, aim above the enemy, charge 0.7-2 s (overcook is at 4 s), throw, switch back.
- Three traps found by tracing: `WEAPON_CLASS_THROWABLE` includes the binoculars (use `WEAPON_CLASS_GRENADE`); `useWeapon()` is undone because `CheckValidWeapon` sees the bot without a weapon mid-switch and re-arms it (skipped during a throw); the switch then works through the player's own `useweaponclass grenade`.

## 2026-11-09 — Vulkan renderer, first stage
- Not a port: the GL1 renderer calls OpenGL through 76 `qgl*` pointers, mostly GL 1.x fixed function, so `renderer_vulkan` is GL1 plus an emulation of those calls (ADR 0005); no renderer copy, pictures comparable pixel by pixel with GL1.
- First bug: front faces must stay counter-clockwise when the shader flips y (clockwise culled the whole BSP while models showed). Spawn points are random, so screenshots use an `sv_scripts` camera.
- Not tested: a real window/swapchain, Windows/macOS builds; Zink cannot run on lavapipe (rejects CPU devices), so Zink was not an option to test here.

## 2026-11-09 — lag compensation (g_antilag)
- Bullets rewind the other players to the shooter's `usercmd.serverTime` (the time the client renders), restoring position, angles and the animation state the bone hit locations are computed from (the per-frame pose cache is reset); history of 64 frames, capped by `g_antilag_maxms`.
- Counting hits was too noisy to test (client pitch jumps with recoil, SMG spread); the test checks the logged sideways aim distance instead: about 2 units from the rewound bot, 14 from where it is now, with 150 ms of client delay.
- Not done: hit validation, projectiles; the kill-while-rewound restore keeps the new animation (seen once, death animation not inspected).

## 2026-11-09 — bot skill levels and weapons (#684)
- Bots already had aim cvars (`g_bot_attack_*`, `g_bot_turn_speed`) and reported a fixed "Average" skill; `g_bot_skill` 1-5 multiplies them (3 = unchanged) and `g_bot_weapons` replaces the automatic weapon choice. The level's real effect on fights is not measured.

## 2026-11-09 — HUD round timer already existed
- `hud_timelimit` shows "Time Left" from `CS_MATCHEND` (round time in round-based modes); it was invisible in tests only because they run without a time limit. Screenshots show it standing still during a match pause.

## 2026-11-09 — hit markers
- Server command `hitmarker` sent only to clients whose userinfo has `cg_hitmarker 1` (a USERINFO cvar of the Plus cgame), so original clients never see an unknown command; drawn as small boxes (no rotated 2D pictures in the cgame API).
- Tested on a plain background (`r_clear 1`, no world or entities) with the player hitting a bot every 0.1 s, so a marker is always visible.

## 2026-11-09 — 4:3 menus on wide screens (#583)
- Smaller than expected: menu containers center themselves (`UIWidgetContainer::AlignPosition`) and children are relative to them, so one scale for both axes in `SetVirtualScale` gives centered 4:3 menus and loading screens; the container's background fill draws the bars. `ui_menuaspect 0` keeps the stretched original.

## 2026-11-09 — browser game type filters
- The original filter cvars (`dm_free_for_all` ... `dm_liberation_match`, `dm_filter_pure`, `dm_run_fast`/`dm_run_normal`) were declared and never applied; now applied client-side from `gametype_i`, `pure` and `sprinton` (masters may not understand filters), favorites exempt.

## 2026-11-09 — fonts with accents (zzz-plus-fonts.pk3)
- Glyph positions are divided by a nominal 256 and screen sizes come from those nominal pixels, so a 2x texture is sharper without changing layout; fonts load without mipmaps, so 4x looks grainy. The TGA must be bottom-up (the top-down flag is ignored).
- DejaVu only (URW fonts are AGPL); glyphs are stretched to the original widths (facfont was 1.3x wider and got clipped in the HUD) and facfont keeps its grey fill with a dark outline.
- A pixel-count test of `n` vs `ñ` was too noisy in a 3D scene (random spawn, brush entities even with `r_drawworld 0`); visual checks were done by screenshots, the test checks loading.

## 2026-11-09 — plus-match competition mod
- Reference mod in scripts only: score per round, halftime `team_swap`, win at rounds/2+1 via `fraglimit`, draw, team timeouts with auto-resume (`registercmd` commands reach scripts from players' consoles with `self` = the player).
- Pitfalls: round-based modes restart the map every round, so `main` reruns (state in cvars; `fraglimit` set in `match_start`, not `main`); `level_intermission` also fires between rounds.
- Not covered by a test: `timeout` typed by a real player (the test uses the server console form).

## 2026-11-09 — 40 Hz keeps the 20 Hz fire rate
- Measured with a temporary trace (now `g_showweaponfire`): BAR 150 ms at 20 Hz, 125 ms at 40 Hz; the maintainer chose the original feel. Above 20 Hz `ReadyToFire` waits for the delay a 20 Hz frame would give; 20 Hz keeps the original expression.
- Semi-automatics are limited by clicks and animations: with 20 ms click spam the shortest interval at 40 Hz (rifle 225 ms, shotgun 825 ms) is not below 20 Hz (200, 800 ms).

## 2026-11-09 — match pause and hit sounds
- Pause reuses `PMF_FROZEN` (as `freezeplayer`) plus no damage; clocks stand still by moving `m_fRoundTime` forward every paused frame and by subtracting the paused time from the time limit (HUD end time included), so resuming needs no catch-up.
- Hit sounds go through `stufftext "play <file>"` (whitelisted in the cgame filter), so original clients hear them; the default file is the stock `sound/items/hit_notify.wav`.
- Script gotcha: a return command without arguments is read as a string in expressions; state is exposed as a level getter (`level.match_paused`). The round-mode clock shift has no test of its own.

## 2026-11-09 — Linux AppImage
- AppImage rather than Flatpak first: no store review, runs on any distro and the Steam Deck; the binaries have no rpath, so `AppRun` sets `LD_LIBRARY_PATH` to the bundled SDL2/OpenAL/cURL.
- Tested here: the unpacked AppDir (server, client, Spearhead launcher) with the game folder taken from the AppImage's location. Not tested here: `appimagetool` itself (downloading and running it locally was refused); CI builds and publishes it.

## 2026-11-09 — translations (cl_language)
- Four upstream gaps stopped translations: the first entry of a text wins (an added `localization_es.txt` was ignored), `UILabel` never localized its text (HUD "Health"), the file-sort comparator compared pointer bytes, and a width loop read the first character every time.
- The game's fonts hold printable ASCII only: accents were drawn as `?`; now as base letters. Language files may be UTF-8 (converted to Latin-1, keys included: two original keys contain Latin-1 bytes).
- No game text is committed: `misc/i18n/loc_tool.py` builds the template from the player's own paks; a full Spanish translation would be a community/user file.

## 2026-11-09 — server browser favorites, history, filters
- Half of it existed: favorites sorted first and drawn as header rows (`m_bFavorite`), master-side filters; nothing stored or set favorites, and `dm_max_ping` and the gametype filter cvars were declared but never applied (gametype filters still are not).
- Favorites and history are queried with `ServerListAuxUpdate`; with no master answering they were never queried (no UDP update sockets, list went idle), and `updatelist` had the same descriptor-0 problem as the master sockets.
- Servers publish `net_gamespy_port` in serverinfo so the history knows the query port; key F is not covered by a test (no key injection headless).

## 2026-11-09 — server browser DNS freeze (#376)
- Reproduced with an `LD_PRELOAD` shim that makes host-name lookups take 5 s (numeric addresses must pass through, or socket setup slows down too): refreshing the list froze the game ~8 s on upstream.
- Three faults in `gserverlist.c`: blocking `gethostbyname`, no move to the next master on DNS failure, master sockets zero-initialized so a never-created one closed descriptor 0 (stdin) on timeout.
- Debugging lesson: a leftover headless client from a failed probe kept running; list `pgrep -x openmohaa` before blaming the code.

## 2026-11-09 — game install detection
- Upstream's Windows store lookups were ioquake3's Quake 3 ones (Steam 2200, GOG 1441704920, Microsoft Store "Quake 3"): GOG now uses MOHAA War Chest 1207659126, the others are off. Windows paths not tested here (no Windows); CI compiles them.
- New `fs_eapath` (EA installer folder, also in the Wine prefix) when the base path has no `main/Pak0.pk3`; the bare "Couldn't load default.cfg" now lists the searched folders and the `fs_basepath` fix.

## 2026-11-09 — HUD scale and crosshair size (#585, #911)
- Up to 1920x1080 the HUD was never scaled (drawn at 640x480 pixel size); `ui_hudscale` multiplies the automatic scale, `getScreenWidth` uses the real scale instead of a fixed 1920.
- Headless screenshot tests: `sv_maxclients 2` avoids the loading screen's continue button, `screenshot silent` avoids the "Wrote" centerprint, `popmenu 0` closes team/weapon menus.
- Not done: menus stretch on wide screens (per-axis virtual scale), sharp text (MOHAA bitmap fonts, FreeType only wired to Quake 3 fonts). FOV is already Hor+.

## 2026-11-09 — server administration (#905)
- In the server module (`sv_admin.cpp`), not the game: `ad_*` wrap existing console commands with their output redirected to the admin, accounts survive map changes. Without libsodium/yaml-cpp: PBKDF2-SHA256 in-tree (checked against Python's `hashlib`), plain-text config (maintainer choice).
- A password check costs ~50 ms of server frame: checked only for existing enabled accounts, at most one per second, per-address throttle; `ad_login` hidden from the `developer 2` command log.
- Pitfalls found: `rconPassword` is only `CVAR_TEMP` (so `ad_set` refuses password cvars without `admin.rcon`), a `"` in a `print` server command cuts the text, level changes must go through `Cbuf`.

## 2026-11-09 — gametype API level 2
- `team_swap` swaps the player lists and scores of both teams in one step (moving players one by one through `JoinTeam` fails on "team is full" with uneven teams) and respawns living players.
- Upstream bug: `team_getscore` was declared `EV_NORMAL`, so scripts could never read its value; now `EV_RETURN`. Most of level 2 already existed (`teamwin`, `team_setscore`, `join_team`, `respawn`).
- Gotcha: in round-based modes the map restarts every round, so `main` runs again; tests guard round-1-only code with the score.

## 2026-11-09 — phases 0-3 and part of 4 merged
- 23 branches merged into `main`: test suite, watchdog, HRTF, disconnect reasons, sanitizer fixes, fuzzing, `sv_perf`, upstream sync, gametype events, libmoh, script toolkit, `sv_fps 40`, `sv_scripts`, plus-stats mod, HTTP downloads, Spanish README.
- Upstream bugs found on the way: libcurl never loaded since the CMake rewrite, `compilescript` aborted the server, HTTP download redirection was dead code; a `RB_Color4f` fix was rejected because the HUD relies on it.
- Open: fire rate rises at 40 Hz (BAR 400 -> 480 rpm; maintainer decision), GitHub Pages and the upstream-sync schedule need enabling, base paks `Pak5`/`pak6` not treated as base paks (debt.md).

## 2026-11-09 — phase 0 started
- `feat/fork-identity`: version `0.83.0-plus.1`, update checker reads the fork's releases and parses `-plus.N` tags; an unparsable tag no longer stores uninitialized values.
- Corrected an earlier note: the `dev` pre-release's Windows `-pdb` zips include the executables; the docs workflow fails only because GitHub Pages is not enabled on the fork.

## 2026-11-09 — idea backlog prioritized
- `docs/dev/roadmap/ideas.md` now holds 36 ideas plus a plan: 11 clusters (overlaps and dependencies) and 6 phases, foundations first, then the script platform the community favors.
- Found while brainstorming: the update checker queries upstream's releases (`code/sys/sys_update_checker.cpp`), so fork players would be sent to upstream; first task of phase 0.

## 2026-11-09 — feature ideas recorded
- Design discussion recorded in `docs/dev/roadmap/ideas.md`: zPAM-like competition mode (C++ match layer + script rules, since MOHAA game modes are C++), libmoh (script functions added natively, NightFall-compatible HTTP first), Vulkan renderer as a new renderer module.
- Checked along the way: `openmohaa +set dedicated 1` already runs as a dedicated server; the fs_homepath fixes made in OpenCoD2-Plus are not needed here (ioquake3 filesystem already handles them).

## 2026-11-09 — README and project direction
- README rewritten after OpenCoD2-Plus: the fork exists to advance with AI agents (forbidden upstream) and will add new features, not only fixes; a faster server tick (40 Hz and up) is the first idea, still unstarted.
- A fresh-context review of the docs found real errors (nonexistent `ttycon` cvar, unbuilt `test_lz77`, wrong function names, missing `corepp` coupling); fixed, and the checker now checks paths against what git would commit.
- The `dev` pre-release ships only `-pdb` archives for Windows and the "Generate Documentation" workflow fails on the fork; both open.

## 2026-11-09 — technical documentation system
- Added `AGENTS.md`, `docs/dev` (architecture, ADRs, development, debt, glossary) and `docs/ai`; `LAYOUT.md` (stale: named the old game and docker directories) now points to the overview.
- Upstream user docs (`docs/markdown`, Doxygen main page `docs/README.md`) left untouched to keep upstream merges clean; docs written in English.
- Added `misc/docs-check` (links, paths, personal data, memory format) with unit tests and its own CI workflow.

## 2026-11-09 — batch merged into main
- Merged 13 fix branches with `--no-ff`; merged `main` passed headless server (map changes, bots) and client (maps, `vid_restart`) smoke tests; branches deleted.
- A false alarm (client ignoring stdin commands) was the intro video with `developer 0`; tests now pass `+set cl_playintro 0`.

## 2026-11-09 — third batch: #287, #918, #850, #422
- #287: same-map restart left the Director timer at the previous map's time, firing all script waits at once; synced in `G_SetTime`. #918: engine freed `TAG_GAME` while a resident module (musl) still used it; reproduced via `LD_PRELOAD` no-op `dlclose`.
- #850 (entity numbers shift with `sv_maxbots`) and #422 (`map` vs `spmap`) documented as working as intended.
- Open: `cgame` has the same unconditional free as #918.

## 2026-11-08 — second batch: #534, #702, #589, #659
- #534 not reproducible; a cursor double-free found nearby was fixed. A first attempt that kept the renderer's free function crashed on `vid_restart` and was reworked.
- #702 `waitForState` now waits (behaviour change vs original, no stock script uses it); #589 `.wav` default extension; #659 stale pak references on pure servers (issue's hang not reproduced).
- User asked that tests never open windows or play sound: offscreen SDL + null OpenAL became the rule.

## 2026-11-08 — first batch: #885, #923, #530, #916, #926, #672, #920
- Each fix reproduced before/after on real binaries (audio measured with the OpenAL wave backend; HUD via screenshots; server via stdin console).
- #885 raises the gain clamp, so the default mix gets louder; noted as a risk rather than reverted.
- Skipped #928/#917 (upstream PRs exist) and #937 (keyboard not testable headless).

## 2026-11-08 — fork created
- Forked `openmoh/openmohaa` as `JotaJazz/OpenMOHAA-Plus`; remotes `origin` (fork) and `upstream`.
- Upstream forbids AI-generated contributions, so all assistant work stays in the fork (ADR 0001).
