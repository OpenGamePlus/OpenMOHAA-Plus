- Loading screens are a desk filling the screen, seen from above. Each mission has its own: a
  letter typed by the game among the mission's photographs, maps and objects (our own text, in
  English or, with `cl_language es`, in Spanish from `lang/es/remake_loading.txt` in the Remake
  pak); a multiplayer map's picture lies as a print; other maps show a closed folder. A green bar
  shows the progress and Continue (bottom right) starts the mission once it is loaded.
# OpenMOHAA Plus: the Remake menu

OpenMOHAA Plus replaces the main menu of Allied Assault with the Remake menu: the original game's
rooms rebuilt in Blender, which work as the original menus did (click an object, the object lights
up under the pointer and a sign names it). The fork's own settings sit on the option units next to
the original ones. Without the Remake pak the game shows its own menus. Spearhead, Breakthrough and
any mod that brings its own `ui/` files are not affected.

## Install

Two paks go in a `plus/` folder next to the executable:

- `plus/zzz-plus.pk3`: the fonts with accented letters ([fonts](09-plus-fonts.md)). The development
  builds, the release `.zip` files and the AppImage already have it; it is also a separate asset of
  each release.
- `plus/zzzz-plus-remake.pk3`: the Remake menu. It is a separate asset of each release (its pictures
  are not in the repository): download it and put it next to `zzz-plus.pk3`.

The Windows `.msi` carries neither yet: copy both into a `plus/` folder next to `openmohaa.exe`.

| Cvar | Default | Meaning |
|---|---|---|
| `fs_pluspath` | the folder of the executable | Folder that holds `plus/`. Only set at start (`+set fs_pluspath <dir>`). Empty turns the Plus data off. On Linux the folder is found next to the real binary, not a symlink to it (`cmake --install`, launchers): set it there. |
| `ui_plusscale` | `1` | Size of the Remake menu's corner buttons, from `0.85` to `1.1`. |
| `dm_browser_show` | `0` | Which servers the internet list shows: `0` all, `1` favourites, `3` recently played (see [the server browser](06-plus-server-browser.md)). The Browse, Favourites and Recent plates set it. It is saved, so the original browser keeps it if the Remake pak is removed. |

The paks in `plus/` load above the base game and below `fs_game`, so a mod's own menu files still
win.

Every menu, the original ones and the in-game menu too, shows the build in its bottom right corner,
for example `OpenMOHAA-Plus 0.83.0-plus.1-unstable (867cfc7e)`: version and git commit. A build made
without git (from a source archive) shows the version only. It is not shown during play.

## Go back to the original menu

Remove `plus/zzzz-plus-remake.pk3`. Start the game with `+set fs_pluspath ""` to drop the Plus
fonts too.

## The rooms

The main room, the options room and war records are rendered rooms; screens the Remake does not
rebuild are the original menus from the game files.

- Options room: the units open close-ups with working controls, as the original option screens did.
  - Video: resolution (Desktop, or 1280x720 up to 3840x2160, 21:9 2560x1080 and 3440x1440, 4:3
    1024x768, 5:4 1280x1024), colour depth, texture detail and colour depth, texture filter,
    brightness, wall decals, weather, texture compression, and the fork's display mode (fullscreen,
    window or borderless window), maximum FPS, anisotropic filtering and vsync.
  - Audio: master, music and ambience volume, speaker setup and sound quality.
  - Advanced: the original detail settings, subtitles, console, weapons bar and crosshair, and the
    fork's renderer, language, field of view, HUD scale, crosshair size and scale, and menus that
    keep 4:3. A language change needs a restart of the game, and the Spanish choice needs the
    `lang/es/` files of [the translations](07-plus-translations.md), which the fork does not ship.
  - Controls: the game's key list on the unit's card, mouse sensitivity, invert mouse, mouse filter,
    always run, and Defaults.

  Settings that need a restart (resolution, display mode, textures, renderer, sound quality,
  terrain detail) take effect with Apply; Back (or Esc) drops them if Apply was not pressed. Other
  settings (volumes, brightness, sensitivity...) apply at once. A change waiting for a restart from
  before the options opened (a server setting for the next map, for example) is left alone.
  Antialiasing is not offered: the Vulkan renderer does not support it.
- War records: the box opens the medal case (each medal earned shows in it, and pointing at one
  names it); the trays open a folder with the saved games.
- New Game and Briefing open a briefing room: a wall map from Norway to Algeria where each mission
  shows once unlocked and names itself on the sign, the Basic Training clipboard, a difficulty
  board, and the briefing slides over the darkened room.
- Multiplayer: a corridor like the original's. The dark doorway goes back; the locker opens the
  player options (a board hung in the corridor, the two soldiers standing in it; joining a
  free-for-all game shows them in a framed photo of the room); the red door joins a game (a board
  for LAN or internet, the server lists on a big board, an address to connect to); the board starts
  one (the game type, then the map, limits, rotation, server name). On the internet board Browse
  lists every server, Favourites and Recent only those. The server board fills the screen: the
  list, the browser's filters on its right (a search field, where Enter refreshes; max ping, min
  and max players; lamps for the game types, hiding empty or full servers, sprint and pure
  servers), and plates to add the selected server to the favourites or remove it. Changing a
  filter refreshes the list.
- The game's messages (connecting, server full, disconnected, timed out, bad address, wrong
  version, error, no saving in multiplayer) are typed on a Signal Corps telegram lying on the radio
  desk, with the Remake's Continue and Back plates.
- Loading screens are a desk filling the screen: a mission's letter lies in an open folder, a
  multiplayer map's picture is a print, other maps show a closed folder; the letter and the
  picture come from your own game files. A green bar shows the progress and Continue (bottom
  right) starts the mission once it is loaded. The first mission's screen is a test of a typed
  letter: our own text, typed by the game on an OSS letterhead among the mission's objects, in
  English or, with `cl_language es`, in Spanish (`lang/es/remake_loading.txt` in the Remake pak).
- The chalkboard in the main room opens the credits of the 3D models in the scenes, written in chalk
  on that board up close (`misc/plus-pk3/remake/credits/models.json`, CC BY 4.0 or CC0).

The game writes the signs with the Plus serif font `plussign-32`, sized to its board, and translates
them with `cl_language` like other menu text.

## Pure servers

On a `sv_pure 1` server the game may still read the Plus paks, but only for `ui/`, `fonts/`,
`gfx/fonts/` and `textures/menu_plus/`. The paks are never reported to the server, so they cannot
make a connection fail or count as a different set of files.

## Build the paks

```
python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3
python3 -m unittest discover -s misc/plus-pk3 -v
```

writes the fonts pak. The Remake pak is built from a Blender export kept outside the repository:

```
python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3 --remake <export folder>
```

`misc/plus-pk3/remake/export_hotspots.py` (run inside Blender) writes the export: the background,
one mask per clickable object, the objects' rectangles and, for objects with lamps, a render with
those lamps on. `misc/plus-pk3/remake/<menu>.json` says which objects are clickable, what they do,
the name the sign shows and which lamps light up when the pointer is on them (the room is dark
otherwise). The renders are under CC BY-SA 4.0 (`misc/plus-pk3/ART-LICENSE.md`, also in the pak).

## Writing menus (`.urc`)

Opt-in keywords for fork menus; the original files do not use them:

| Keyword | Effect |
|---|---|
| `anchor <left> <top> <right> <bottom>` | Margins from the screen edges, in virtual units (1/480 of the screen height, times `ui_plusscale`). `-1` keeps the value of the `rect`. |
| `escapecommand "<command>"` | A menu keyword (before its widgets): Esc runs the command instead of closing the menu and restoring its widgets' cvars. The Remake's option screens give it their Back command, `ui_discardlatched; popmenu 0`. |
| `cover <w> <h>` | The widget is the `rect` part of a `w` x `h` picture that covers the whole screen without distortion, centred, cropping the excess. With `rect 0 0 w h` it is the background; with a smaller `rect` (in picture units) it stays on that part of the picture at any screen shape and `ui_plusscale`. A label's text scales with the picture too, shrunk if needed to 90% of the `rect`'s width and 50% of its height. |

A widget with neither `align`, `anchor` nor `cover` is placed in the menu's own frame, which on a
`virtualres 1` menu 2048 units wide starts off the screen: give every widget an `anchor` or `cover`. `align left`
puts the widget at the screen edge whatever the `rect` says.

The server list widget also takes the events `togglefavorite` (favourite on or off for the
selected server), `addfavorite` and `removefavorite` (the selected server only becomes, or stops
being, a favourite), `restartrefresh` (stops the refresh in progress and refreshes once the list is
idle; a plain refresh asked while the list is querying does nothing) and `selectitem <n>`. A changed `dm_filter_empty`, `dm_filter_full`,
`dm_min_players` or `dm_max_players` empties the list on the next refresh, like the other filters.
A `Label` with `wordwrap <height>` breaks its text into lines of that height (picture units under
`cover`) that fit its width, `\n` starting a new line, so a longer translation takes more lines at
the same type size; `addtext "<piece>"` adds a piece of its text, translated on its own and joined
to the previous one by a space (the localization reader keeps 255 characters a text, a `.urc`
token 511). A `Field` with `stuffcommand` runs it on Enter with the typed text appended (the Remake's search
ends its command with `//` so the text is a comment). Its `printlist` command prints a `Columns: N` line first,
then one line per server ending with its version. A placed list (`anchor` or `cover`) has a version column ("Ver."
when narrow), names without the version (as the server sends them), and an IP column when wider than 800 virtual units. A placed list has
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
original game). The list of a pulldown with `linkcvar`, or of one placed with `cover`, is in the container's `font`
and scale, as wide as the field, with padded rows in the original's colours (yellow on green, a
1-unit yellow border, the highlighted row light); other lists keep the original `verdana-12`. The
Remake sets the transparent `textures/menu_plus/clear` as the pulldowns' `shader`, `menushader` and
`selmenushader`, so the list only takes the clicks over the unit's plate (the knob is only drawn).

A `Slider` with `showvalue "<format>" [<multiplier>]` has a flat look (track, filled part and thumb
in its `fgcolor`, no arrows) and prints its value times the multiplier with the format right of the
track, in its `font`; the track ends before the widest value. The format takes one `%f`, `%g` or
`%e` (flags, width and precision allowed) and `%%` for a percent sign, e.g. `showvalue "%.0f%%" 100`
for a 0 to 1 volume shown as `80%`; any other format is refused with a console warning and the
slider keeps the original look. A `CheckBox` with an `anchor` draws its box as tall as its `rect`
less 2 units at the top and bottom, at its left edge (the original checkboxes draw a 14-unit box).

`replacemenu <name>` puts a menu in place of the one on top in one step (`popmenu 0;pushmenu <name>`
does not work, because popping locks the menus until the next frame).

Three console commands for option screens. `ui_marklatched` (run when an option screen opens)
records which cvars already wait for a restart and the values of the sound and terrain cvars
(their `CVAR_SOUND_LATCH`/`CVAR_TERRAIN_LATCH` flags never latch: those cvars change at once and
only take effect after `snd_restart`/`ter_restart`). `ui_applylatched` then restarts what the
changes since the mark need, whichever menu made them: `vid_restart` for a cvar newly waiting for
a restart, else `snd_restart` for a changed sound cvar and `ter_restart` (in a game) for a changed
terrain cvar, and nothing when nothing changed (`ui_checkrestart` only looks at the current menu's
widgets). `ui_discardlatched` drops the changes since the mark that need a restart and puts the
sound and terrain cvars back. Esc on a menu whose name starts with `plus_options` does what
`ui_discardlatched;popmenu 0` does (a leftover of the dropped Plus options; new menus use
`escapecommand`).

The console command `ui_printwidgets` prints, for the menu on top, every widget with its class,
whether it is shown, its rectangle on the screen in pixels and the rectangle of its text; for a
pulldown with `linkcvar` the value it shows and the width of what it draws (`pulldown value`); for a
slider with `showvalue` the value shown and where its track and value text run (`slider value`); the
build label and its rectangle (`build label`); for a server list also the header and row heights, the scale its rows are drawn at (`items scale`) and
each column's position, width and title width.
The tests use it to check the layout. `ui_testmouse <x> <y> <buttons>` and `ui_testkey <key>` (a key
name as `bind` takes it, e.g. `escape`) stand in for the mouse and the keyboard of a headless client.
