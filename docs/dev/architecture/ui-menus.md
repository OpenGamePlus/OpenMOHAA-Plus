# UI and the Remake menu

The menus are `.urc` files read by `code/uilib` inside the client. The fork's menu is the Remake
menu, fork data in `plus/zzzz-plus-remake.pk3` (the fonts are in `plus/zzz-plus.pk3`), plus engine
changes that are opt-in (a keyword or flag), so the original menus keep their geometry. The Plus
("Modern") menu was dropped on 2026-11-22; the engine parts only it used (anchored server list
columns, `replacemenu`, the `plus_options*` Esc hook, `plus_browser_refresh`) wait for a cleanup. Keywords, commands and cvars for menu authors:
[the user page](../../markdown/03-configuration/14-plus-menu.md). Decision on the data folder:
[ADR 0007](adr/0007-fork-data-folder.md).

## Where things are

| Part | Location |
|---|---|
| Widgets (labels, lists, pulldowns, bind list), layout, menu stack | `code/uilib` (`uiwidget.cpp`, `uimenu.cpp`, `uipulldownmenu*.cpp`, `uibindlist.cpp`) |
| Console commands (`replacemenu`, `ui_*latched`, `ui_printwidgets`; `ui_testmouse` in `cl_input.cpp`, `ui_testkey` in `cl_keys.cpp`), Esc hook (`UI_MenuEscape`), `ui_plusscale`, build label (`UI_DrawBuildLabel`) | `code/client/cl_ui.cpp` |
| Server list widget (columns, favourites) | `code/client/cl_uiserverlist.cpp` |
| `plus/` paks, pure-server exemption (`ui/`, `fonts/`, `gfx/fonts/`, `textures/menu_plus/`) | `code/qcommon/files.cpp` (`fs_pluspath`) |
| Pak build (fonts pak; the Remake pak with `clear.tga` and the art licence) | `misc/plus-pk3/build_pk3.py`; fonts from `misc/fonts/make_fonts.py`; art licence `misc/plus-pk3/ART-LICENSE.md` |
| Remake menu: mappings `<menu>.json`, Blender export `export_hotspots.py` (checked by hand with `check_export.py` in `blender -b`), pak build `pak.py` (generated `.urc`, tiles, hovers) | `misc/plus-pk3/remake/`; `build_pk3.py --remake <export>` writes `zzzz-plus-remake.pk3`; design `docs/superpowers/specs/2026-11-17-legacy-menu-design.md` |
| Tests | `MenuWidgets` (engine widget features on test menus) and `RemakeMenu` in `tests/test_client.py`; `misc/plus-pk3/test_build_pk3.py`, `misc/plus-pk3/test_remake.py` |

## Rules

- Fork behaviour is opt-in: `anchor` sets `WF_ANCHORED` (also sizes a checkbox's box), `cover`
  sets `WF_COVER`, `scalecvar` sets `m_scaleCvar`, `linkcvar` turns on the pulldown value and its styled list,
  `showvalue` the flat slider, `escapecommand` (a menu keyword) Esc's command. The build label is the one exception that shows in every menu. Branch on those, never on menu names; the one exception
  is the Esc hook on `plus_options*` menus.
- Units, the 2048-unit menu frame and why every placed widget needs `anchor`, `align` or `cover`:
  the user page, "Writing menus".
- Textures in the pak are powers of two. Paintings go in as JPEG (the renderer tries `.jpg` before `.tga`; a 2048x2048 TGA of a painting deflates to about 10 MB). Widget art meant to follow the widget's colour is
  generated white, so `fgcolor` tints it.
- New user-visible behaviour is documented on the user page in the same commit.
- Remake menu `.urc` files are generated: change the mapping (`misc/plus-pk3/remake/<menu>.json`) or
  the Blender scene and build again. Their widgets sit in picture units with `cover` (exact at any
  shape and `ui_plusscale`); the background is rendered with the hotspots' lamps (`lights` in the
  mapping) off, and a hotspot's hover is its rect rendered with its own lamps on, faded into the
  background (`zone_lit`: the light falls off from the object inside a rect padded 8% by the export,
  so it never meets the tile's edge; `"glow": "frame"` keeps a short falloff at a door or board); a hotspot without lamps gets the
  background lit through its object mask. A hotspot's button is named after it and a corner may
  give `widget`, its name apart from its title: the multiplayer room keeps the original's names
  (`startnew`, `changemap`, `joinlan`, `disconnect`), which the game enables by name, case-sensitive
  (`UI_MultiplayerMenuWidgetsUpdate`). `dm_ffamodelselect.urc` (the free-for-all model dialog) is the original's on a backdrop the pak
  composes from `selectmodel/frame.png` in the export and the multiplayer room's render.
  `remake_credits.urc` (model credits) is generated from
  `remake/credits/models.json` (ten fit the board; more is a build error), written in chalk (`pluschalk-32`,
  made from Cabin Sketch, OFL, in `misc/fonts/ofl/`) on the chalkboard's picture when its export exists (a screen with `"credits": true` and a `slate_plate`). Option screens (`"screen": true` mappings, `export_screen`, `screen_urc`) are
  close-ups whose controls sit on the units: a list is a transparent pulldown over the plate
  (the knob is only drawn, as it has no click picture; the plate shows the value; when every item sets the list's cvar to a value of its
  own, a label maps that value as the original did, so the item's other cvars need not match; every
  fork list, this one or one showing its value, opens in the pulldown's font with the original's
  yellow on green, `UIPulldownMenu::CreateSubmenu`), a check lights its lamp (`lamp_on`), a slider sits on its
  plate; `binds` puts the game's key list (`FakkBindList`) on a card; `medal` shows its own render
  (cut by the pak from a full-frame render: a border render lights differently) when its cvar is
  set, and pointing at it writes its name and description on the case's plates (`sign_cvar`);
  `field` (typed into), `text` (a cvar's text) and `model` (the engine draws a model standing in the
  picture; its rect is made square, as `CL_Draw3DModel`'s view is 30 by 30 degrees) make the player options; an action with a `lit` render has its text in the picture, as
  a title's label over the button would take the pointer (`FindResponder` picks the topmost widget);
  a control's `"ink": "light"` prints light on green felt; `mission` shows its own render when its cvar is set (always without one), its lit render under the pointer, and names itself on the `sign_plate` (with the mapping's extra `signs`); a screen with `"include": true` is written as `ui/<menu>.inc`, just its background (the briefing slides' `missionbriefingback.inc`; the telegram, `telegram.json` from `05_mensajes/telegrama_1940.blend`, whose `dialogs` the pak writes as the original's nine message menus with `dialog_urc`: lines 26 units tall typed in `courier-20` on its `message_plate`, the original's button names and commands); the slide menus themselves are generated from `remake/briefing/slides.json` with the slide in picture units, as the game stretches a 640x480 menu to the screen; `servers` is the game's server list by name (`langamelist`, a `LANGameClass`; `netgamelist`, a
  `FAKKServerList`); `shot`, `action` and `saves` make the load/save folder (an action's `lit` objects show only in its
  own full-frame render, cut by the pak as its hover picture, like a medal) (the game finds `LoadSaveShot` and
  `LoadSaveList` by name; its list's column titles are `facfont-20`, so the sheet must be wide). A room copied from another (war records is the main room's desk up close) lists the
  other room's lamps in `"off"`: dark in every render. Hotspot buttons go from the largest rect to the smallest, so where
  rects overlap the smaller one (on top) takes the pointer. Corner buttons are green plates drawn by the pak build (`green_plate`,
  not the game's art) with the engine's text over them. The sign is a label whose `linkstring`s map the sign cvar's values to the mapping's
  texts (font `plussign-32`); text under `cover` follows the picture (`UIWidget::getTextScale`).

## Pitfalls (each cost a debugging round)

| Pitfall | Consequence |
|---|---|
| `MenuManager::PopMenu` locks the menus until a posted unlock event and posts `showmenu` to the menu below | `popmenu 0;pushmenu X` on one line silently fails; `replacemenu` (`MenuManager::ReplaceMenu`) swaps in one step |
| A container clips its children to its own `rect` | A child taller than the container (the pulldown, as tall as its arrow shader) must centre its text on the parent, not on itself |
| A `ui_plusscale` change reaches widgets through `AlignPosition`, not `Realign` | Widgets that lay out children (`FakkBindList`) relayout in `Draw` when the scale moved |
| The game's `ui/bind.scr` gives bind-list columns in fixed units; rows are 16 units (`commandheight`) | Columns are narrowed to fit scaled lists; a list height must be whole rows |
| Children of a `WF_NOPARENTADJUST` widget were placed from the screen origin | Fixed for anchored widgets only (the server list's scroll bar) |
| `CVAR_SOUND_LATCH` / `CVAR_TERRAIN_LATCH` never latch in `cvar.c` | `ui_marklatched` snapshots their values; Apply and Back compare against it |
| Remake render width not whole in picture units (2560x1440 is 853.33) | Background tiles and hovers drift ~1.5 px apart; `picture_size` refuses it: use e.g. 2562x1440 (854 units) |
| `ui_plusscale` below 1 shrinks the menu frame | A widget placed on the screen (`anchor`, `cover`) can lie outside it; `FindResponder` now checks those children too, else they take no hover or click (remake corner buttons at 0.85) |
| `.gitignore` ignores `build*` | A new `build_*.py` is silently left out of commits (`remake/build_remake.py` was; now `remake/pak.py`) |
| A font with no `.shader` script got a lit world shader and crashed the GL renderers on its first text | `R_LoadFontShader` falls back to the 2D shader; fork fonts need no script (and `scripts/` is not read from fork paks on pure servers) |
| `UIWidget::InitFrame` sets the font again (default `verdana-12`) | A popup that sizes its rows with another font must pass it to `InitFrame` too |
| While its list is open a pulldown is the first responder and gets every mouse event | A list left open by a hidden menu closes on the next mouse event |

## Testing

- `ui_printwidgets` prints every widget's screen rect, text rect, pulldown values and list
  columns; `PlusMenu.widgets` parses it. Prefer it to pixels.
- Screenshots: `+set ui_consoleposition "<x> <y> 8 8"` moves the console out of the picture.
- The headless client has no mouse input: clicks, hover and drag are checked by hand.
- A navigation test asserts every step, not only where it ends (a failed tab switch also ends on
  the main menu).
