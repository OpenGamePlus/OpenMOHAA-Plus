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

Every menu, the original ones and the in-game menu too, shows the build in its bottom right corner,
for example `OpenMOHAA-Plus 0.83.0-plus.1-unstable (867cfc7e)`: version and git commit. A build made
without git (from a source archive) shows the version only. It is not shown during play.

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

The script packs the fonts, the menu files in `misc/plus-pk3/data/` and the backgrounds
(`misc/plus-pk3/art/`: `background.jpg` for the main menu and server browser,
`background_options.jpg` for the options, each 3840x1600, packed as the JPEG textures
`textures/menu_plus/bg_l`/`bg_r` and `opt_l`/`opt_r`) into `zzz-plus.pk3`. The art is AI-generated and under CC BY-SA 4.0
(`misc/plus-pk3/ART-LICENSE.md`).

## Legacy menu (prototype)

A second, optional pak, `plus/zzzz-plus-legacy.pk3`, replaces the main menu with rooms rendered in
Blender that work like the original game's menus: click an object, the object lights up under the
pointer and a sign names it. The main room, the options room and war records come from the pak;
every other screen is the original menu from the game files. It needs `zzz-plus.pk3` next to it.
Remove the file to get the Plus menu back.

The renders are not in the repository yet, so the pak is built locally from a Blender export:

```
python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3 --legacy <export folder>
```

`misc/plus-pk3/legacy/export_hotspots.py` (run inside Blender) writes the export: the background,
one mask per clickable object and the objects' rectangles. `misc/plus-pk3/legacy/<menu>.json` says
which objects are clickable, what they do and the name the sign shows. The game writes the sign
with the Plus serif font `plussign-32`, sized to its board, and translates it with `cl_language`
like other menu text.

## Writing menus (`.urc`)

Two opt-in keywords for fork menus; the original files do not use them:

| Keyword | Effect |
|---|---|
| `anchor <left> <top> <right> <bottom>` | Margins from the screen edges, in virtual units (1/480 of the screen height, times `ui_plusscale`). `-1` keeps the value of the `rect`. |
| `cover <w> <h>` | The widget is the `rect` part of a `w` x `h` picture that covers the whole screen without distortion, centred, cropping the excess. With `rect 0 0 w h` it is the background; with a smaller `rect` (in picture units) it stays on that part of the picture at any screen shape and `ui_plusscale`. A label's text scales with the picture too, shrunk if needed to 90% of the `rect`'s width and 50% of its height. |

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
matching item the pulldown shows the linked cvar's value itself. A pulldown with a single entry
(every `PulldownMenuContainer` in practice) opens on a click anywhere in its `rect`; its arrow
keeps its own size. A click leaves the list open until the next click: on an item it picks it,
anywhere else it closes the list (press, drag and release on an item also picks it, as in the
original game). The list of a pulldown with `linkcvar` matches the field: the container's `font`
and scale, the field's width, padded rows on a dark box with a 1-unit `fgcolor` border, the
highlighted row tinted with `fgcolor` (the original list keeps `verdana-12` on green). The Plus options draw the field with `shader "textures/menu_plus/field"` (border,
fill, divider and down arrow, made for a 160x24 `rect`, tinted by `fgcolor`) and set the transparent
`textures/menu_plus/clear` as `menushader` and `selmenushader`. Make the `rect` wide enough for the
longest title and the arrow cell (24 units at the right of the field).

A `Slider` with `showvalue "<format>" [<multiplier>]` has a flat look (track, filled part and thumb
in its `fgcolor`, no arrows) and prints its value times the multiplier with the format right of the
track, in its `font`; the track ends before the widest value. The format takes one `%f`, `%g` or
`%e` (flags, width and precision allowed) and `%%` for a percent sign, e.g. `showvalue "%.0f%%" 100`
for a 0 to 1 volume shown as `80%`; any other format is refused with a console warning and the
slider keeps the original look. A `CheckBox` with an `anchor` draws its box as tall as its `rect`
less 2 units at the top and bottom, at its left edge (the original checkboxes draw a 14-unit box).
The Plus options use `textures/menu_plus/checkbox_on` and `checkbox_off` (white, tinted by
`fgcolor`).

`replacemenu <name>` puts a menu in place of the one on top in one step (the option tabs use it;
`popmenu 0;pushmenu <name>` does not work, because popping locks the menus until the next frame).

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
slider with `showvalue` the value shown and where its track and value text run (`slider value`); the
build label and its rectangle (`build label`); for a server list also the header and row heights, the scale its rows are drawn at (`items scale`) and
each column's position, width and title width.
The tests use it to check the layout.
