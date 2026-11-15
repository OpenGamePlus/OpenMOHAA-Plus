# Project context

## Identity
OpenMOHAA Plus: a fork of OpenMoHAA (`openmoh/openmohaa`), the open reimplementation of
Medal of Honor: Allied Assault, Spearhead and Breakthrough (client, dedicated server, game logic)
on an ioquake3-based engine, sibling of the maintainer's OpenCoD2-Plus.

## Visual identity
[docs/banner.svg](../banner.svg) (the maintainer's design) sets the look of the repo; use its palette
for new art and badges:

| Use | Colours |
|-----|---------|
| Background (olive, centre to edge) | `#2f3a22`, `#1b2214`, `#0c100a` |
| Ribbon olive (badges) | `#6e7f3c` |
| Gold (accents, rules, frame) | `#c9a85a`; highlights `#e3c069`, text gradient `#f3dd9a` to `#b89048` |
| Cream (main text) | `#f1e6c8`, `#efe3c2`; muted `#b9b08f` |
| Red accent | `#9b2a26` |

Fonts: Playfair Display 900 (name), Oswald 500 (upper-case headings), Rajdhani 500 (body), all OFL.
The banner's text is outlined, since GitHub shows an SVG as an image, which cannot load web fonts.

## Goal
Move OpenMoHAA forward with AI coding agents, which upstream does not accept: fix bugs reported
upstream (and others found along the way) and add new features beyond the original game (e.g.
server tick rates above `sv_fps 20`, as OpenCoD2-Plus does with its 40 Hz server), in a fork that
keeps merging upstream, with every change reproduced and verified on real binaries.

## Non-goals
- Submitting AI-assisted work upstream (forbidden by upstream policy; ADR 0001).
- Rewriting or modernizing subsystems; large refactors.
- Shipping game data (pk3 files are proprietary and never committed).
- Changing original-game behaviour without a clear bug (ADR 0002).

## Principles
- Root cause over symptoms; smallest complete change.
- Reproduce before and after with the same command; report what was not checked.
- Upstream files stay untouched where possible; fork material lives in new files.
- Tests and tools never open windows or play sound (see testing guide).

## Stack
C (engine) and C++ (game, UI, script VM, corepp); CMake + Ninja; SDL2; OpenAL Soft; GameSpy SDK;
flex/bison for the script grammar; GitHub Actions; Doxygen for user docs; Python (stdlib) for
the docs checker.

## Constraints
- Must stay compatible with original game data, saves and network protocol.
- Module ABI versions (`GAME_API_VERSION`, `CGAME_IMPORT_API_VERSION`, `REF_API_VERSION`).
- License: AGPL-3.0 for the program and the fork's own files; upstream files keep GPL-2.0-or-later
  (ADR 0006). No GPL-2.0-only code may be added.
- Test coverage so far: Linux with Allied Assault data only; no Spearhead/Breakthrough, macOS or
  GPU-specific testing.
- Docs, code comments and commits in English.
