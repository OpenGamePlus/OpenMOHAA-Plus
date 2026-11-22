# Remake loading screens: design

Date: 2026-11-22. Status: approved (Blender).

## Intent

The original's 34 loading screens (`ui/loading_*.urc`) are 4:3 pictures with black bars on wide
screens and the old Continue art: the generic box art, 21 mission letters with the briefing typed
into the picture, 12 multiplayer map photos. The Remake replaces them with full-screen desks
rendered in Blender, the Remake's loading bar and corner Continue.

## Constraint

The letters' text and the map pictures are the game's art: the pak must not ship them, nor
derivatives (outpainting, img2img). The `.urc` shows them from the player's own files, as the
original does: a letter is cut out of its briefing textures by a shader of ours
(`clampMap textures/mohmenu/levelbriefing/<shader>_<1|2>.tga` + `tcMod transform`); a map photo is
the original shader by name. The language paks hold the letters, so each player sees theirs.

## Design

- One scene, `07_carga/carga_1940.blend`: a wooden desk, three top-down orthographic cameras:
  an open folder with the letter's sheet (`Load_Letter`), a print with corner mounts
  (`Load_Photo`), a closed folder (generic). Own props only (the credits board is full).
- Three include mappings (`loadingdesk_letter|photo|default.json`) list their screens: file, menu
  name (the map's, as the engine finds it), shader, and for letters the letter's rect in the
  640x481 picture (measured by hand from the originals; numbers, not art).
- The pak writes each `ui/loading_<file>.urc`: the desk, the letter or photo fitted to the plate,
  `loadingflasher`, `loadingbar_border`, `loadingbar` (new art drawn by the build) and a corner
  `continuebutton` running `finishloadingscreen`.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| **Chosen** | Blender desks + the player's letter/photo | Matches the Remake; letters keep the player's language |
| ComfyUI backgrounds | Only new art without the letters; would not match the 3D rooms |

## Update (same day): typed letters

After the `m1l1` test the maintainer chose typed letters for every mission: each mission has its own
desk in the spirit of the original (photographs, objects, maps, a letter paper and letterhead of
its own), and the letter is our own text typed by the engine (`wordwrap`, `addtext`), in English
with a Spanish translation in `lang/es/remake_loading.txt`. Maps are drawn from Natural Earth, never
generated. The cut-out letters from the player's briefing textures were dropped.
