# OpenMOHAA Plus: server browser favorites, history and filters

## Favorites

- In the internet server list, select a server and press **F** to add it to or remove it from your
  favorites. Favorites stay at the top of the list.
- From the console: `fav_add` (the server you are playing on), `fav_add <ip:port> [query port]`,
  `fav_del [ip:port]`, `fav_list`.

## History

The last 20 servers you joined are remembered; they show in the list as `(recent)`. Console:
`history_list`, `history_clear`.

Favorite and recent servers are queried directly every time the list is refreshed, so they show up
even when the master servers are down or do not list them.

## Filters

| Cvar | Effect |
|---|---|
| `dm_browser_show` | `0` all servers, `1` favorites only, `2` favorites and recent servers, `3` recent servers only (`1`, `2` and `3` do not ask the master servers) |
| `dm_browser_search` | show only servers whose name or map contains this text |
| `dm_max_ping` | hide servers with a higher ping (`0` = no limit) |
| `dm_filter_empty`, `dm_filter_full` | hide empty / full servers (existing) |
| `dm_min_players`, `dm_max_players` | player count range (existing) |
| `dm_free_for_all`, `dm_team_match`, `dm_round_based_match`, `dm_objective_match`, `dm_tow_match`, `dm_liberation_match` | `0` hides that game type (existing cvars, now applied) |
| `dm_filter_pure` | `1` shows only pure servers |
| `dm_run_fast`, `dm_run_normal` | `0` hides servers with / without sprint (`sv_sprinton`) |

The original 1.11 servers do not send their game type's number, whether sprint is on or whether
they are pure: their type is read from its name (Free-For-All, Team, Round, Objective, Tug,
Liberation; a mod's "Freeze-Tag-Objective" counts as objective, a name with none of these words is
never hidden by type), the sprint filters leave them alone and "pure only" hides them. Empty, full
and the player counts are checked on each server's answer, as the master servers ignore them.

Favorites are hidden by the Favourites and Recent filters (`dm_browser_show` 1 and 3): Favourites lists only them, Recent hides those you did not play lately. Only All (0) shows every server. Change a filter, then press Refresh. The Remake menu has every
filter on its server board, and refreshes when one changes ([the Remake menu](14-plus-menu.md)).

## Files

`serverfavorites.txt` and `serverhistory.txt` in the configuration folder, one server per line:
`<ip>:<port> <query port>`. The query port is the server's GameSpy port (`net_gamespy_port`,
12300 by default for game port 12203). OpenMOHAA Plus servers publish it; for other servers it is
taken from the browser, or guessed as the game port + 97.
