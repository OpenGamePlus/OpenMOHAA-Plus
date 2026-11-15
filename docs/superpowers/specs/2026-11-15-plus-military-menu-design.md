# OpenMOHAA Plus military menu style (design)

Date: 2026-11-15. Status: **parked** by the maintainer on 2026-11-15 (the painted Plus menu and the
port of the remaining screens come first). Approach A chosen; builder check done; open questions
below. Not approved; nothing built.

## Intent

The Plus menu (painted 1940s background, see the [Plus menu design](2026-11-14-plus-menu-design.md))
stays. The maintainer wants a **second style** for the main menu, more war-like and military,
that modernises the interface now that the fork is a "Plus" version of the game: short
background clips of **Allied** soldiers (e.g. walking), taken from public-domain US federal
government film, and lettering in the spirit of the game's printed manual and strategy guide
(stamped labels, heavy slab/stencil titles, typewriter "dossier" text). Both styles live side by
side; the player chooses one in the options. First step: the main menu only.

Allied soldiers only, so that no Axis symbols appear (German law, StGB §86a, and the existing
anti-goal of the Plus menu).

## Goals

- A cvar `ui_plusstyle` (archived; `painted` default, `military`) chosen from a "Menu style"
  pulldown on the Plus options screen (`plus_options.urc`, with `linkcvar` so it shows the
  chosen item). The change takes effect at once, without restarting the game.
- A military main menu (`ui/main_military.urc`) with the same entries and widget names as the
  painted `main.urc` (the engine shows/hides and relabels entries by name, e.g. in-game Save
  and Return to game), in the military look.
- Full-screen background clips behind it: several short clips (a few seconds each) played one
  after the other in a loop, silent (the menu music keeps playing), cropped to cover any aspect
  from 4:3 to 32:9 without distortion, like the painted background's `cover`.
- A new `.urc` widget that plays RoQ clips, usable by any fork menu; works the same on
  `renderer_opengl1` and `renderer_vulkan`.
- Fonts in the military look generated from free (SIL OFL) fonts with
  `misc/fonts/make_fonts.py`, shipped in the same pk3 with their licence notices.

## Non-goals

- Other screens in the military style: the Plus browser and options, and every original screen
  opened from the main menu, keep their current look for now (the military main opens the same
  screens as the painted one).
- Spearhead and Breakthrough menus; in-game menus; loading screens.
- Movement or effects for the painted style (a later, separate project).
- Renderer work: an OpenGL 4 renderer, making Vulkan the default (separate project). `videoMap`
  in shaders is not needed: the widget draws frames itself.
- Clips with sound.

## Anti-goals

- **No Axis symbols in any frame** of any clip (swastikas, SS runes, Nazi flags or insignia,
  even small, in the background or on captured material). Every clip is reviewed frame by frame
  before it is committed; a clip with any doubtful frame is dropped or cut.
- **No copyrighted footage:** only works of the US federal government (17 U.S.C. § 105:
  Army Signal Corps, Navy, Marine Corps, Coast Guard, Office of War Information productions).
  Not commercial newsreels (Movietone, Pathé, Paramount, Hearst/News of the Day) even when an
  archive hosts them, and not "restored", colourised or upscaled versions that claim new rights:
  start from the archive's own scan. Universal Newsreel is excluded too, to keep the rule simple.
- No game data, nothing derived from the manuals or the guide (no scanned art, no traced
  lettering, none of their commercial fonts such as LoveLetterTypewriter or Franklin Gothic):
  the manuals are a mood reference only.
- The military main must not break what the painted one does: every entry reachable, in-game
  entries shown only in game, `ui_plusscale` respected, any aspect from 4:3 to 32:9.
- Without the Plus pk3, or with `ui_plusstyle` set to a style that has no menu, the game behaves
  as today (the painted `main`, or the original `main` without the pk3).

## Constraints

- Renderers shipped: `renderer_opengl1` (default) and `renderer_vulkan` (GL1 on a Vulkan
  emulation, ADR 0005). Neither supports `videoMap`; both implement `UploadCinematic` and
  `DrawStretchRaw`, which the intro movies already use through `code/client/cl_cin.cpp`
  (`CIN_PlayCinematic` with `CIN_loop | CIN_silent`, `CIN_SetExtents`, `CIN_RunCinematic`,
  `CIN_DrawCinematic`, `CIN_StopCinematic`; at most 16 handles).
- `code/uilib` reaches the client only through `uiimport_t` (`code/uilib/ui_public.h`): the
  cinematic calls must be added there.
- The menu name `main` is hard-coded in about eight places of `code/client/cl_ui.cpp`
  (`UI_MainMenuWidgetsUpdate`, `UI_PushMenu`, `FindMenu("main")`...). All `ui/*.urc` files are
  loaded at start (`FS_ListFiles("ui/", "urc")`); a file declares its menu name.
- Clips are RoQ (the only format the engine plays), encoded with `ffmpeg`'s `roqvideo` encoder
  (installed here): dimensions multiples of 16, integer frame rate. RoQ is blocky and large
  (roughly 1 MB per second at 640x480); grainy black-and-white film hides the blockiness.
- The Plus pk3 is about 15 MB today and ships in every release zip and AppImage.
- New fork files are AGPL-3.0-or-later; art and clips carry their own licence/provenance file
  (`misc/plus-pk3/ART-LICENSE.md`).
- Original-game behaviour stays when the fork's data is absent; changes to upstream files carry
  the `Added/Changed in OpenMOHAA Plus` markers.

## Approaches

| # | Approach | Trade-off |
|---|---|---|
| **A (chosen)** | Engine renames menus: `main_military.urc` declares `menu "main_military"`; `ui_plusstyle` makes the engine treat `main_<style>` as `main` | Instant switch, each style in its own file; one engine hook; both menus stay loaded (the clips play only while shown) |
| B | One pk3 per style; the option chooses which pak loads | Full separation, but changing style needs a game restart, and touches the file system and pure-server rules |
| C | One `main.urc` with both styles, widgets shown/hidden by the cvar | No engine hook, but one mixed file hard to maintain, and both styles must share every widget name |

Chosen by the maintainer on 2026-11-15.

## Design decided with the maintainer

- Two styles side by side, the player chooses in the options; the painted style stays the
  default.
- Approach A (engine treats `main_<style>` as `main`).
- Military look: inspired by the manual and the strategy guide (stamped labels, slab/stencil
  titles, typewriter dossier text), modernised.
- Clips: short, Allied soldiers (e.g. walking), public-domain US federal government film.
- Main menu only for this step.

## Decided after the builder check

- **Clips go in a separate, optional pk3**, not in `zzz-plus.pk3` (decided by the maintainer).
- **Clip size 512x256:** `RE_StretchRaw` in `renderer_opengl1` stops with `ERR_DROP` unless the
  frame is a power of two (`tr_backend.c`), and the cinematic buffer holds at most 512x512
  (`linbuf` in `cl_cin.cpp`); `CIN_DrawCinematic` only resamples on old hardware. This replaces
  the 640x352/640x480 proposal below; a sharper path would need an engine change, not planned.
  Cropping is done by drawing larger than the widget and clipping (`DrawStretchRaw` always draws
  the whole frame).
- **No video in game:** when the main menu opens during a match, the military style shows a dark
  background instead of clips (the decoder state is global and `RE_StretchRaw` calls `qglFinish`).

## Open when the work resumes

- Who sources the films and signs off the frame-by-frame review (proposed: the maintainer picks
  archive items and approves each clip; the builder prepares the pipeline and a first review).
- Size budget of the optional video pk3, and how releases ship it.
- Whether the mockup may use a stand-in public-domain frame before real clips exist.

## Proposals (the builder's calls unless the maintainer corrects them)

- **Style switch:** after `uWinMan.CreateMenus()` and whenever `ui_plusstyle` changes, if a menu
  `main_<style>` exists, the engine swaps names so that it answers to `main` (and the previous
  `main` gets its own style name back). If the main menu is open at that moment it is replaced
  in place, so leaving the options returns to the new style. Unknown style or missing menu:
  nothing changes.
- **Video widget:** a `.urc` resource (e.g. `Video`) with one or more `clip` lines (paths
  under `video/`), `cover <w> <h>` for the crop (same meaning as on labels), and the usual
  `anchor`. It opens its cinematic when shown and stops it when hidden, so a menu that is not
  on screen costs nothing. A missing or broken clip leaves the widget empty (the menu's
  `bgfill` shows), with one console warning.
- **Readability:** a dark overlay/vignette over the clip on the left, where the entries are, the
  same role as the painted style's bar gradient.
- **Fonts:** a stencil or heavy slab for the title (Black Ops One or Stardos Stencil), a strong
  condensed sans for the entries (Oswald or Barlow Condensed), a typewriter for small text
  (Special Elite or Courier Prime); all SIL OFL. The final pick is made on a mockup.
- **Look first:** before the art is final, a mockup screenshot (headless, real clip frame) is
  shown to the maintainer for approval.
- **Clip budget:** 3 to 5 clips of 5 to 10 seconds, 512x256 (see above), 24 or 30 fps.
- **Clip pipeline:** a script in `misc/plus-pk3/` that trims, crops, grades (contrast, grain) and
  encodes each source with `ffmpeg` into `video/plus_mil_*.roq`; the RoQ files are committed
  (like `art/background.jpg`); sources are not. Each clip's provenance (archive, item ID or URL,
  film title, producing agency, time range used, public-domain reason, frame review date) goes in
  `ART-LICENSE.md`.
- **Tests:** style switch (`ui_printwidgets` reports `main_military` content when `ui_plusstyle`
  is `military`, back to painted, and no change without the menu); the video widget plays (two
  headless screenshots or a printed frame counter differ over time) on GL1 and Vulkan; a missing
  clip does not crash and warns; the military main's layout at the same screens as the painted
  one (entries inside the screen, in-game entries hidden out of game).

## Left to the builder

- Exact names: widget class and keywords, cvar values, file names.
- How the clip playlist advances (one cinematic at a time, opened in turn) and how cropping is
  done (extents larger than the widget and clipped, or texture coordinates).
- Overlay art (gradient tile like the painted bar, or a shader).
- The order of work, as long as the mockup is approved before final art and clips.
