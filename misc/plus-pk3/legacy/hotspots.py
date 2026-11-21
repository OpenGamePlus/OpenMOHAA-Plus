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
    """Size of a res_x x res_y render in picture units. The width must come out whole (3840x1600,
    2562x1440): a rounded one puts the widgets and the background tiles a fraction of a unit apart."""
    if PICTURE_HEIGHT * res_x % res_y:
        raise ValueError(f"render {res_x}x{res_y} is {PICTURE_HEIGHT * res_x / res_y:.2f} picture units wide; "
                         f"pick a width that makes it whole (e.g. {res_y * round(PICTURE_HEIGHT * res_x / res_y) // PICTURE_HEIGHT}"
                         f"x{res_y} if that is whole)")
    return PICTURE_HEIGHT * res_x // res_y, PICTURE_HEIGHT


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


def pad_rect(rect, picture, frac=0.08):
    """The rect grown by frac of its longer side each way (at least one unit), clamped to the
    picture: room for a hover's light to fade out before the tile's edge."""
    x, y, w, h = rect
    pad = max(1, math.ceil(max(w, h) * frac))
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(picture[0], x + w + pad), min(picture[1], y + h + pad)
    return x0, y0, x1 - x0, y1 - y0


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
    if mapping.get("screen"):
        return _check_screen(path, mapping)
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
        if spot.get("glow", "frame") != "frame":
            raise ValueError(f"{menu}: hotspot {name}: glow can only be \"frame\"")
    if boards != 1:
        raise ValueError(f"{menu}: needs exactly one board hotspot, has {boards}")
    off = mapping.get("off", [])
    if not isinstance(off, list) or not all(isinstance(p, str) and p for p in off):
        raise ValueError(f"{menu}: off is a list of object names or prefixes")
    _check_corners(menu, mapping)
    return mapping


def _check_corners(menu, mapping):
    for corner in mapping.get("corners", []):
        if not corner.get("title") or not corner.get("command") or corner.get("side") not in ("left", "right"):
            raise ValueError(f"{menu}: corner {corner!r} needs a title, a command and side left or right")
        if not isinstance(corner.get("slot", 0), int) or corner.get("slot", 0) < 0:
            raise ValueError(f"{menu}: corner {corner['title']}: slot is a count from the corner (0, 1, ...)")


CONTROL_PARTS = {"list": ("knob", "plate"), "check": ("lamp", "plate"), "slider": ("plate",), "binds": ("plate",),
                 "medal": ("medal",), "shot": ("plate",), "action": ("plate",), "saves": ("plate",)}
NO_CVAR = ("binds", "shot", "action", "saves")  # controls the game drives by name or by command


def _check_screen(path, mapping):
    """An option screen: a close-up whose controls (list, check, slider) sit on Blender objects."""
    for key in ("menu", "camera", "controls"):
        if not mapping.get(key):
            raise ValueError(f"{path}: missing {key}")
    menu, names = mapping["menu"], set()
    for control in mapping["controls"]:
        name, kind = control.get("name", ""), control.get("kind")
        if not name or '"' in name or name in names:
            raise ValueError(f"{menu}: bad or repeated control name {name!r}")
        names.add(name)
        if kind not in CONTROL_PARTS:
            raise ValueError(f"{menu}: control {name}: kind is one of {', '.join(CONTROL_PARTS)}")
        if kind not in NO_CVAR and not control.get("cvar"):
            raise ValueError(f"{menu}: control {name} needs a cvar")
        if any('"' in control.get(k, "") for k in ("checked_command", "unchecked_command")):
            raise ValueError(f"{menu}: check {name}: no quotes in its commands")
        for part in CONTROL_PARTS[kind]:
            if not control.get(part):
                raise ValueError(f"{menu}: control {name} needs the objects of its {part}")
        if kind == "list":
            items = control.get("items") or []
            if not items or any(len(i) != 2 or '"' in "".join(i) for i in items):
                raise ValueError(f"{menu}: list {name} needs items [title, command] without quotes")
        if kind == "action" and (not control.get("command")
                                 or '"' in control.get("title", "") + control.get("command", "")):
            raise ValueError(f"{menu}: action {name} needs a command, and no quotes in it or its title")
        if kind == "medal":
            for key in ("title", "desc"):
                text = control.get(key, "")
                if not text or '"' in text:
                    raise ValueError(f"{menu}: medal {name} needs a {key} without quotes")
            if not mapping.get("sign_cvar") or not mapping.get("name_plate") or not mapping.get("desc_plate"):
                raise ValueError(f"{menu}: a medal case needs sign_cvar, name_plate and desc_plate")
        if kind == "slider":
            low, high = control.get("range", [0, 0])
            if not low < high or not control.get("step", 0) > 0:
                raise ValueError(f"{menu}: slider {name} needs a range [low, high] and a step")
    _check_corners(menu, mapping)
    return mapping
