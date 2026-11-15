# UI and the Plus menu

The menus are `.urc` files read by `code/uilib` inside the client. The Plus menu is fork data in
`plus/zzz-plus.pk3`, plus engine changes that are opt-in (a keyword or flag), so the original
menus keep their geometry. Keywords, commands and cvars for menu authors:
[the user page](../../markdown/03-configuration/14-plus-menu.md). Decision on the data folder:
[ADR 0007](adr/0007-fork-data-folder.md).

## Where things are

| Part | Location |
|---|---|
| Widgets (labels, lists, pulldowns, bind list), layout, menu stack | `code/uilib` (`uiwidget.cpp`, `uimenu.cpp`, `uipulldownmenu*.cpp`, `uibindlist.cpp`) |
| Console commands (`replacemenu`, `ui_*latched`, `ui_printwidgets`), Esc hook (`UI_MenuEscape`), `ui_plusscale` | `code/client/cl_ui.cpp` |
| Server list widget (columns, favourites) | `code/client/cl_uiserverlist.cpp` |
| `plus/` paks, pure-server exemption (`ui/`, `fonts/`, `gfx/fonts/`, `textures/menu_plus/`) | `code/qcommon/files.cpp` (`fs_pluspath`) |
| Menu files | `misc/plus-pk3/data/ui/` (`main.urc`, `plus_browser.urc`, `plus_options*.urc`) |
| Pak build, generated textures (background tiles, bar and hover gradients, pulldown field, clear) | `misc/plus-pk3/build_pk3.py`; fonts from `misc/fonts/make_fonts.py`; art licence `misc/plus-pk3/ART-LICENSE.md` |
| Tests | `PlusMenu` in `tests/test_client.py`; `misc/plus-pk3/test_build_pk3.py` |

## Rules

- Fork behaviour is opt-in: `anchor` sets `WF_ANCHORED`, `cover` sets `WF_COVER`, `scalecvar`
  sets `m_scaleCvar`, `linkcvar` turns on the pulldown value. Branch on those, never on menu names; the one exception
  is the Esc hook on `plus_options*` menus.
- Units, the 2048-unit menu frame and why every placed widget needs `anchor`, `align` or `cover`:
  the user page, "Writing menus".
- Textures in the pak are powers of two. Widget art meant to follow the widget's colour is
  generated white, so `fgcolor` tints it (`field.tga`); the bar and hover gradients carry their
  own colour.
- New user-visible behaviour is documented on the user page in the same commit.

## Pitfalls (each cost a debugging round)

| Pitfall | Consequence |
|---|---|
| `MenuManager::PopMenu` locks the menus until a posted unlock event and posts `showmenu` to the menu below | `popmenu 0;pushmenu X` on one line silently fails; `replacemenu` (`MenuManager::ReplaceMenu`) swaps in one step |
| A container clips its children to its own `rect` | A child taller than the container (the pulldown, as tall as its arrow shader) must centre its text on the parent, not on itself |
| A `ui_plusscale` change reaches widgets through `AlignPosition`, not `Realign` | Widgets that lay out children (`FakkBindList`) relayout in `Draw` when the scale moved |
| The game's `ui/bind.scr` gives bind-list columns in fixed units; rows are 16 units (`commandheight`) | Columns are narrowed to fit scaled lists; a list height must be whole rows |
| Children of a `WF_NOPARENTADJUST` widget were placed from the screen origin | Fixed for anchored widgets only (the server list's scroll bar) |
| `CVAR_SOUND_LATCH` / `CVAR_TERRAIN_LATCH` never latch in `cvar.c` | `ui_marklatched` snapshots their values; Apply and Back compare against it |
| While its list is open a pulldown is the first responder and gets every mouse event | A list left open by a hidden menu closes on the next mouse event |

## Testing

- `ui_printwidgets` prints every widget's screen rect, text rect, pulldown values and list
  columns; `PlusMenu.widgets` parses it. Prefer it to pixels.
- Screenshots: `+set ui_consoleposition "<x> <y> 8 8"` moves the console out of the picture.
- The headless client has no mouse input: clicks, hover and drag are checked by hand.
- A navigation test asserts every step, not only where it ends (a failed tab switch also ends on
  the main menu).
