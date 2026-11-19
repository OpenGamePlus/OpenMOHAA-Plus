# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Helpers shared by the Blender export and the pak build (no bpy here).

Picture units: the render seen as 480 units high, as wide as its aspect ratio (1152 for 3840x1600),
the units `cover <width> 480` places menu widgets in.
"""
import json
import math
import re

PICTURE_HEIGHT = 480


def picture_size(res_x, res_y):
    """Size of a res_x x res_y render in picture units."""
    return round(PICTURE_HEIGHT * res_x / res_y), PICTURE_HEIGHT


def rect_from_points(points, picture):
    """(x, y, w, h) in picture units around camera-view points (x, y from 0 to 1, bottom-left
    origin, z the depth), rounded outwards and clamped to the picture; None when no point is in
    front of the camera or the box lies wholly outside the frame."""
    front = [(x, y) for x, y, z in points if z > 0]
    if not front:
        return None
    x0, x1 = min(p[0] for p in front), max(p[0] for p in front)
    y0, y1 = min(p[1] for p in front), max(p[1] for p in front)
    if x1 <= 0 or x0 >= 1 or y1 <= 0 or y0 >= 1:
        return None

    def clamp(v):
        return min(max(v, 0.0), 1.0)

    width, height = picture
    left, right = math.floor(clamp(x0) * width), math.ceil(clamp(x1) * width)
    top, bottom = math.floor((1 - clamp(y1)) * height), math.ceil((1 - clamp(y0)) * height)
    return left, top, right - left, bottom - top


def match_objects(names, patterns):
    """Sorted names matching the patterns: an exact name, or a prefix ending in "*". Raises
    ValueError naming every pattern that matched nothing."""
    found, missing = set(), []
    for pattern in patterns:
        if pattern.endswith("*"):
            hits = {n for n in names if n.startswith(pattern[:-1])}
        else:
            hits = {pattern} if pattern in names else set()
        if not hits:
            missing.append(pattern)
        found |= hits
    if missing:
        raise ValueError("no object matches " + ", ".join(missing))
    return sorted(found)


def slug(name):
    """A file-name-safe form of a hotspot name: "personal records" -> "personal_records"."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def load_mapping(path):
    """Reads and checks a mapping file (misc/plus-pk3/legacy/<menu>.json)."""
    with open(path) as f:
        mapping = json.load(f)
    for key in ("menu", "sign_cvar", "hotspots"):
        if key not in mapping:
            raise ValueError(f"{path}: missing {key}")
    menu = mapping["menu"]
    names, boards = set(), 0
    for spot in mapping["hotspots"]:
        name = spot.get("name", "")
        if not name or '"' in name:
            raise ValueError(f"{menu}: bad hotspot name {name!r}")
        if name in names:
            raise ValueError(f"{menu}: hotspot {name} twice")
        names.add(name)
        if not spot.get("objects"):
            raise ValueError(f"{menu}: hotspot {name} has no objects")
        if spot.get("board"):
            boards += 1
            if "command" in spot:
                raise ValueError(f"{menu}: the board {name} cannot have a command")
        elif not spot.get("command") or not spot.get("sign"):
            raise ValueError(f"{menu}: hotspot {name} needs a command and a sign")
        else:
            text = spot.get("text", "")
            try:
                text.encode("cp1252")  # the game's charset
            except UnicodeEncodeError:
                text = '"'
            if not text or '"' in text:
                raise ValueError(f"{menu}: hotspot {name} needs a text for the sign, in Windows-1252, without quotes")
    if boards != 1:
        raise ValueError(f"{menu}: needs exactly one board hotspot, has {boards}")
    for corner in mapping.get("corners", []):
        if not corner.get("title") or not corner.get("command") or corner.get("side") not in ("left", "right"):
            raise ValueError(f"{menu}: corner {corner!r} needs a title, a command and side left or right")
    return mapping
