# Remake message screens: the telegram: design

Date: 2026-11-22. Status: approved.

## Intent

Nine original menus are the same dialog on the same sepia box art (`sepiaload_a`/`_b`): a message
and a Continue or Back button. In the Remake they still show the original between 3D rooms. One
new scene replaces them all: a telegram on the radio operator's desk, the engine typing the
message on the slip.

| Menu | Message | Buttons |
|---|---|---|
| `badserveraddy` | Bad Server Address | Continue `popmenu 0` |
| `connecting` | Connecting to Server... | Back `popmenu 0;disconnect;wait 50;gotoreturnmenu` |
| `disconnected` | Server Disconnected | Continue `popmenu 0` |
| `errormessage` | `com_errormessage` | Continue `popmenu 0;wait 50;gotoreturnmenu` |
| `loadsave_mp` | Saving and loading is not allowed during a multiplayer game. | Continue `popmenu 0` |
| `serverdisconnected` | Server Disconnected | Continue `popmenu 0;wait 50;gotoreturnmenu` |
| `serverfull` | Server is full | Continue `popmenu 0` |
| `servertimeout` | Server Connection Timed Out | Continue `popmenu 0;wait 50;gotoreturnmenu` |
| `wrongversion` | Server is using a newer version / `com_errormessage` / Click Continue to go get the latest patch! | Back `Popmenu 0;wait 50;gotoreturnmenu`, Continue `gogetpatch` |

## Goals

- One Blender scene (`telegram`), exported once as an include background (like
  `missionbriefingback`), with a `message` plate on the slip.
- The pak writes the nine menus from the mapping's `dialogs`: the include, the message lines on
  the plate in a typewriter font (`courier-20`, dark ink), the buttons as the Remake's green corner
  plates. Names, commands and the `continuebutton` widget name are the original's.

## Non-goals

- Copying the box art; the loading screens; changing what the engine pushes.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| **Chosen** | One include background, menus generated from a list | One render; texts stay engine-drawn |
| One render per menu, text baked | Nine renders, baked text cannot be translated or show `com_errormessage` |

## Left to the builder

The scene's objects and camera; whether the slip has a printed header.
