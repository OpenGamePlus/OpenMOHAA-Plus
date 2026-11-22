# Plus checkbox, slider and build label (design)

Date: 2026-11-15. Status: approved by the maintainer (mockup choices: checkbox with a tick, slider
showing its value, build label in every menu).

## Intent
Finish the option controls in the style of the bordered pulldown field, and show which build is
running in every menu, so screenshots and reports always identify it.

## Decisions
- **Checkbox:** generated white textures (`textures/menu_plus/checkbox_on`, `checkbox_off`): gold
  border and dark fill like the field, a tick when on; tinted by the widget's `fgcolor`. Menu
  files only, no engine change.
- **Slider:** opt-in `.urc` keyword `showvalue "<format>" [<multiplier>]` on `Slider`. With it the
  slider draws a flat style in code (thin track with outline, filled part up to the thumb, square
  thumb, no arrows) and prints `value * multiplier` with the format at its right, in the widget's
  font and `fgcolor`; the track ends before the widest value (min or max formatted). The format is
  checked: one `%f`/`%g`/`%e` conversion (flags, width, precision allowed) and `%%`; anything else
  ignores the keyword. Without the keyword the slider is unchanged.
- **Build label:** "OpenMOHAA-Plus <version>[ · <short hash>]" (`PRODUCT_VERSION_1`, git hash when
  the build has one), bottom right, small, with a shadow, drawn by the client whenever a menu is
  shown (original menus and the in-game menu too), never during play. `ui_printwidgets` prints it.
- **Fresh hash:** `cmake/version.cmake` declares the git `HEAD` file and the branch ref as configure
  dependencies, so a commit triggers a reconfigure and the embedded hash follows HEAD. Builds from a
  `git archive` have no hash and show the version only.

## Approaches considered
- Slider by textures only (track, thumb, arrows through `shader`/`thumbshader`/`leftshader`): no
  value, and the arrows cannot be removed without code. Rejected.
- Build label as a `.urc` label in each Plus menu: misses the original and in-game menus, which the
  maintainer wants. Rejected.

## Left to the builder
Exact sizes, colours from the field texture, label font and margin.
