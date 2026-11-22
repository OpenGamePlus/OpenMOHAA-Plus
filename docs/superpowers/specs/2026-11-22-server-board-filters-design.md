# Server board: filters, separate favourite plates, bigger board: design

Date: 2026-11-22. Status: approved.

## Intent

The browser filters (`docs/markdown/03-configuration/06-plus-server-browser.md`) never had a UI in
any menu; they are console-only. The Remake's server board (`joinnetgame`) becomes the place to
find a game: a bigger board, the filters on it, and two favourite plates instead of one toggle
(one plate doing both confuses players).

## Goals

- Board bigger on screen (camera closer and/or bigger board), list about 3/4 of its width.
- A filter column on the board's frame, right of the list, in the option units' style:
  - lamp switches: `dm_filter_empty`, `dm_filter_full`, `dm_filter_pure`, the six game types
    (`dm_free_for_all`, `dm_team_match`, `dm_round_based_match`, `dm_objective_match`,
    `dm_tow_match`, `dm_liberation_match`; on = shown), `dm_run_fast`, `dm_run_normal`;
  - knob lists: `dm_max_ping` (no limit / 50 / 100 / 150 / 250 / 400), `dm_max_players` (no limit / 8 /
    16 / 24 / 32) and `dm_min_players` (any / 1 / 4 / 8);
  - a text field over the list for `dm_browser_search`.
- Changing a filter refreshes the list (`widgetcommand netgamelist refreshserverlist`).
- Bottom row: status plate, ADD FAVOURITE, REMOVE FAVOURITE.
- Engine: `addfavorite` / `removefavorite` events on `FAKKServerList` (fork additions, marked).

## Non-goals

- New filters; changes to how the engine filters.
- The stock menus.

## Anti-goals

- Controls that look pasted on (same as the Remake-only spec).
- Baked values: the engine draws them.

## Constraints

As in `2026-11-22-remake-only-menu-design.md`: generated `.urc` from the JSON mapping plus the
Blender export, renders outside the repo, CC BY-SA 4.0.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| **Chosen** | Filters on the board's frame, one room | Everything at hand; the board must grow |
| Separate filter room | Board keeps its size | One more screen to go through; rejected |

## Left to the builder

Exact geometry, which knob values, whether a filter change waits for the refresh in flight.
