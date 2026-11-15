# 0007. A fork-only data folder next to the executable

- Status: Accepted
- Date: 2026-11-14

## Context
The fork menu and its fonts ship as a pk3. Putting it in the game's `main` folder has two
problems: a pure server rejects any pk3 it does not list, so the menu would vanish while
connected, and other executables (the original game, other engines) share that folder and would
load fork-only UI files.

## Decision
The engine loads `<fs_pluspath>/plus/*.pk3` (cvar `fs_pluspath`, default the executable's
folder, empty disables it; packs only, no loose files), right after the base game folders and
before `fs_basegame` and `fs_game`, so a mod still overrides it. It is skipped unless
`com_target_game` is 0. On a pure server these packs stay readable for files under `ui/`,
`fonts/`, `gfx/fonts/` and `textures/menu_plus/` only; everything else in them is ignored.
They stay ahead of the server's paks in the search path, and are never reported to a server
(loaded, referenced and pure checksum lists) so the server never sees them.

## Consequences
- Only this binary reads the folder; other executables in the game folder are unaffected.
- Pure servers keep working without the client pak, and the menu survives a connection.
- A pack in the folder cannot change maps, scripts or models on a pure server; without a pure
  server it can (it is trusted, like `main`).
- Forces the exemption list to stay in sync with what the menu needs (`FS_PlusDataAllowed`).
