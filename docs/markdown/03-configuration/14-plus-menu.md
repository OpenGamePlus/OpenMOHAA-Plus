# OpenMOHAA Plus: the Plus menu

OpenMOHAA Plus ships its own main menu, server browser and options screen for Allied Assault. They
adapt to the screen: the background covers any aspect ratio (4:3 up to 32:9) without stretching,
the buttons and lists follow the screen edges, and the server list shows each server's game
version in its own column (names appear as the server sends them, without the "(1.11)" the
original list adds) and the IP when it is wide enough. Spearhead, Breakthrough and any mod that brings its own `ui/` files are
not affected.

## Install

The menu ships in `plus/zzz-plus.pk3`, in a `plus/` folder next to the executable. The development
builds, the release `.zip` files and the AppImage already have it, and it is also a separate asset
of each release. The Windows `.msi` does not carry it yet: copy `zzz-plus.pk3` into a `plus/` folder
next to `openmohaa.exe`.

| Cvar | Default | Meaning |
|---|---|---|
| `fs_pluspath` | the folder of the executable | Folder that holds `plus/`. Only set at start (`+set fs_pluspath <dir>`). Empty turns the Plus data off. On Linux the folder is found next to the real binary, not a symlink to it (`cmake --install`, launchers): set it there. |
| `ui_plusscale` | `1` | Size of the Plus menu text and buttons, from `0.85` to `1.1`. Also on the Plus options screen. |
| `dm_browser_show` | `0` | `3` lists only the servers you played recently (see [the server browser](06-plus-server-browser.md)); the Recent tab sets it for you. It is saved: leaving the Plus browser on Recent or Favourites carries over to the original browser if the pak is removed. |

The paks in `plus/` load above the base game and below `fs_game`, so a mod's own menu files still
win. `plus_browser_refresh` is used by the browser tabs; do not set it yourself.

## Go back to the original menu

Start the game with `+set fs_pluspath ""` (or remove `plus/zzz-plus.pk3`). The Plus fonts go with it.

## The screens

- Main menu: Continue shows when the last save exists, and Back to game, Save game and
  Disconnect (grouped above Quit) only in a game; Load game is always there. Campaign starts a
  new game.
- Server browser: Internet, LAN, Favourites and Recent tabs, a refresh button and a favourite
  button.
- Options (the main menu's Options and Plus entries), six tabs in the left bar:
  - Video: resolution (Desktop, or 1280x720 up to 3840x2160, 21:9 2560x1080 and 3440x1440, 4:3
    1024x768, 5:4 1280x1024), fullscreen, window or borderless window, vsync, maximum FPS,
    brightness, texture quality, texture filter and anisotropic filtering.
  - Detail: the original model, terrain, effect and curve presets, shadows, lighting, smoke and
    decals.
  - Audio: volume, music, ambience, quality and speakers.
  - Controls: the game's key list, mouse sensitivity, invert mouse, mouse filter, always run, and
    Defaults (the original defaults).
  - Game: field of view, weapon model, weather, subtitles, console, weapons bar, crosshair.
  - Plus: renderer, HUD scale, menu aspect, crosshair size and scale, language and menu scale. A
    language change needs a restart of the game, and the Spanish choice needs the `lang/es/` files
    of [the translations](07-plus-translations.md), which the fork does not ship.

  Settings that need a restart (resolution, display mode, textures, renderer, sound quality,
  terrain detail) take effect with Apply, from any tab; Back (or Esc) returns to the main menu and
  drops them if Apply was not pressed. Other settings (volumes, brightness, sensitivity...) apply at
  once. A change waiting for a restart from before the options opened (a server setting for the
  next map, for example) is left alone. Antialiasing is not offered:
  the Vulkan renderer does not support it.

## Pure servers

On a `sv_pure 1` server the game may still read the Plus pak, but only for `ui/`, `fonts/`,
`gfx/fonts/` and `textures/menu_plus/`. The pak is never reported to the server, so it cannot
make a connection fail or count as a different set of files.

## Build the pk3

```
python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3
python3 -m unittest discover -s misc/plus-pk3 -v
```

The script packs the fonts, the menu files in `misc/plus-pk3/data/` and the background
(`misc/plus-pk3/art/`) into `zzz-plus.pk3`. The art is AI-generated and under CC BY-SA 4.0
(`misc/plus-pk3/ART-LICENSE.md`).

## Writing menus (`.urc`)

Two opt-in keywords for fork menus; the original files do not use them:

| Keyword | Effect |
|---|---|
| `anchor <left> <top> <right> <bottom>` | Margins from the screen edges, in virtual units (1/480 of the screen height, times `ui_plusscale`). `-1` keeps the value of the `rect`. |
| `cover <w> <h>` | The widget covers the whole screen without distortion, centred, cropping the excess. `w` and `h` give the picture's shape. |

A widget with neither `align` nor `anchor` is placed in the menu's own frame, which on the Plus
screens is 2048 units wide and starts off the screen: give every widget an `anchor`. `align left`
puts the widget at the screen edge whatever the `rect` says.

The server list widget also takes the events `togglefavorite` (favourite on or off for the
selected server) and `selectitem <n>`. Its `printlist` command prints a `Columns: N` line first,
then one line per server ending with its version. An anchored list has a version column ("Ver."
when narrow), names without the version, and an IP column when wider than 800 virtual units. An anchored list has
its header in the row font, draws its rows at the menu's scale (the original list keeps the HUD
scale) and its columns end at the scroll bar. Text longer than its column is cut 4 units before
the column's edge.

A `PulldownMenuContainer` with `linkcvar <cvar>` shows, before its arrow and in its own `font`
and `fgcolor`, the title of the first item whose command has at least one `set <cvar> <value>`
(or `seta`) and in which every such `set` matches that cvar's value (so an item may set several
cvars, e.g. `set r_mode -1; set r_customwidth 1920; set r_customheight 1080`). Quotes around a
value are ignored and numbers compare as numbers (`"1.0"` matches `1`). A `reset <cvar>` in the
command matches while that cvar is at its default; other commands are ignored, so an item with no
`set` never matches. A latched cvar counts with the value waiting for the restart. With no
matching item the pulldown shows the linked cvar's value itself. Make
the `rect` wide enough for the longest title and the arrow, or clicks on the right part are lost.

Three console commands for option screens. `ui_marklatched` (run when the Plus options open)
records which cvars already wait for a restart and the values of the sound and terrain cvars
(their `CVAR_SOUND_LATCH`/`CVAR_TERRAIN_LATCH` flags never latch: those cvars change at once and
only take effect after `snd_restart`/`ter_restart`). `ui_applylatched` then restarts what the
changes since the mark need, whichever menu made them: `vid_restart` for a cvar newly waiting for
a restart, else `snd_restart` for a changed sound cvar and `ter_restart` (in a game) for a changed
terrain cvar, and nothing when nothing changed (`ui_checkrestart` only looks at the current menu's
widgets). `ui_discardlatched` drops the changes since the mark that need a restart and puts the
sound and terrain cvars back. Esc on a `plus_options*` menu does what `ui_discardlatched;popmenu 0`
does.

The console command `ui_printwidgets` prints, for the menu on top, every widget with its class,
whether it is shown, its rectangle on the screen in pixels and the rectangle of its text; for a
pulldown with `linkcvar` the value it shows and the width of what it draws (`pulldown value`); for a
server list also the header and row heights, the scale its rows are drawn at (`items scale`) and
each column's position, width and title width.
The tests use it to check the layout.
