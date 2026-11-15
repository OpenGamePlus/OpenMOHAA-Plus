# OpenMOHAA Plus: the Plus menu

OpenMOHAA Plus ships its own main menu, server browser and options screen for Allied Assault. They
adapt to the screen: the background covers any aspect ratio (4:3 up to 32:9) without stretching,
the buttons and lists follow the screen edges, and a "Version" column appears in the server list
when it is wide enough. Spearhead, Breakthrough and any mod that brings its own `ui/` files are
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
- Plus options: renderer (press Apply to restart the video), HUD scale, menu aspect, crosshair
  size and scale, language and menu scale. A language change needs a restart of the game, and the
  Spanish choice needs the `lang/es/` files of [the translations](07-plus-translations.md), which
  the fork does not ship.

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
selected server) and `selectitem <n>`. Its `printlist` command prints a `Columns: N` line first;
the "Version" column appears when the list is wider than 800 virtual units. An anchored list has
its header in the row font and its columns end at the scroll bar.

The console command `ui_printwidgets` prints, for the menu on top, every widget with its class,
whether it is shown, its rectangle on the screen in pixels and the rectangle of its text; for a
server list also the header and row heights and each column's position, width and title width.
The tests use it to check the layout.
