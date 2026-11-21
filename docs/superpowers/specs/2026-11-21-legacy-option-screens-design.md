# Legacy option screens (video first)

Status: agreed with the maintainer on 2026-11-21; video is the prototype, then audio, advanced and
controls the same way.

## Goal

The options room's units open the original option screens (`video_options`, `audio_options`,
`advancedoptions`, `controls`) as close-ups of the same Blender units, with working controls whose
state the engine writes (decision: engine text, not one render per control state).

## The original screens

Each is a 640x480 painting of a unit plus widgets: per list a `PulldownMenuContainer` over a knob
(64x64) and a `Label` beside it whose `linkcvar`/`linkstring` shows the value on a blank plate;
`CheckBox`es, `Slider`s, and Back (`popmenu 0`), Apply (`ui_checkrestart; popmenu 0`), Defaults
(`ui_resetcvars`). Video: resolution, colour depth, texture quality, texture colour depth, texture
filter (lists), wall decals, weather effects, texture compression (checkboxes), brightness (slider).

## Design

- Scene: `opciones_detalle_1940.blend`, a copy of the options room (nothing lost there), one camera
  per screen (`Cam_Video`, ...). The close-up may change the units: the plates of a list become blank
  (the engine writes the value), their titles move above them as small engraved text, and every
  checkbox gets an indicator lamp.
- Mapping `misc/plus-pk3/legacy/<menu>.json` with `"screen": true`: camera, and `controls`, each with
  the Blender objects that give its rect (picture units, like hotspots) and its widget: `list` (the
  original's items and cvar; a transparent pulldown over knob and plate, the plate's text is the
  pulldown's own value), `check` (cvar; lamp on/off art drawn by the pak build), `slider` (cvar,
  range, step); buttons Back, Apply, Defaults as green corner plates.
- Export: `export_screen` renders the background from the screen's camera and writes the control
  rects; no lamps per zone.
- Engine: a widget under `cover` places its children in it (a pulldown's value lives in its child
  menu, which was placed from the screen's origin and clipped away), and a covering checkbox's box
  fills its rect's height (the lamp). Text size needed no change: the widgets' scale already follows
  the picture.
- Lists use the Plus lists where the original's are obsolete (resolution: Desktop and the Plus
  resolutions, not r_mode 0..9).

## Checks

Pak tests for the screen mapping and its urc; a client test opens the screen, checks every control
lands on its plate, and sets a value with `ui_testmouse`.
