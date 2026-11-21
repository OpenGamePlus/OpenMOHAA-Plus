# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Blender side of the Legacy menu: renders a screen's background and one object mask per hotspot
from the open scene, and writes the hotspot rects in picture units. A hotspot with "lights" (lamps
and lit shades in the mapping) gets a render of its rect with only its own lamps on, and the
background is rendered with every such lamp off, so the room is dark until a hotspot is pointed at.
Without lights, the pak build lights the masked part of the background for the hover (legacy/pak.py).

Run inside Blender (Blender MCP or the text editor), with the screen's .blend open:

    path = r"<repo>/misc/plus-pk3/legacy/export_hotspots.py"
    exec(compile(open(path).read(), path, "exec"), g := {"__file__": path, "__name__": "legacy_export"})
    g["export_all"](r"<repo>/misc/plus-pk3/legacy/main.json", r"<export root>")

Export the background and the masks from one scene state. Writes <export root>/<menu>/background.png,
mask_<slug>.png and <menu>.json:
{"menu", "picture": [W, 480], "background": "background.png",
 "hotspots": {name: {"rect": [x, y, w, h], "mask": "mask_<slug>.png", "lit": "lit_<slug>.png"}}}
(the board has no mask, a hotspot without lights no lit render).
A mask is a Workbench render of the hotspot's rect: its objects white, every other object black, so
what stands in front of it stays dark (under a second). The background is a full render with the
scene's own engine (minutes), a lit render the same for its rect. The .blend is never saved; object
colours, lamps, materials, the engine and the render settings are restored after each render.
"""
import json
import os
import sys
import time
from contextlib import contextmanager

import bpy
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hotspots  # noqa: E402


def _paths(mapping_path, out_root):
    mapping = hotspots.load_mapping(mapping_path)
    folder = os.path.join(out_root, mapping["menu"])
    os.makedirs(folder, exist_ok=True)
    return mapping, folder, os.path.join(folder, mapping["menu"] + ".json")


def _picture():
    r = bpy.context.scene.render
    return hotspots.picture_size(r.resolution_x * r.resolution_percentage // 100,
                                 r.resolution_y * r.resolution_percentage // 100)


def _update_json(json_path, menu, update):
    data = {"menu": menu, "picture": list(_picture()), "background": "background.png", "hotspots": {}}
    if os.path.exists(json_path):
        with open(json_path) as f:
            data = json.load(f)
    update(data)
    with open(json_path, "w") as f:
        json.dump(data, f, indent=1)


def _render(path, border=None):
    """Renders the scene camera to a PNG; border (x, y, w, h) in picture units renders that part only."""
    scene = bpy.context.scene
    r = scene.render
    saved = (r.filepath, r.use_border, r.use_crop_to_border, r.border_min_x, r.border_max_x,
             r.border_min_y, r.border_max_y, r.image_settings.file_format)
    try:
        r.filepath = path
        r.image_settings.file_format = "PNG"
        if border:
            width, height = _picture()
            x, y, w, h = border
            r.use_border, r.use_crop_to_border = True, True
            r.border_min_x, r.border_max_x = x / width, (x + w) / width
            r.border_min_y, r.border_max_y = 1 - (y + h) / height, 1 - y / height
        else:
            r.use_border = False
        for attempt in range(3):
            try:
                bpy.ops.render.render(write_still=True)
                break
            except RuntimeError as error:
                # over the WSL share Windows now and then refuses the write ("cannot save")
                if "cannot save" not in str(error) or attempt == 2:
                    raise
                time.sleep(2)
    finally:
        (r.filepath, r.use_border, r.use_crop_to_border, r.border_min_x, r.border_max_x,
         r.border_min_y, r.border_max_y, r.image_settings.file_format) = saved


def _objects(spot):
    """The hotspot's render-visible mesh objects: the matched ones and their children."""
    scene = bpy.context.scene
    names = hotspots.match_objects([o.name for o in scene.objects], spot["objects"])
    found = {}
    for name in names:
        for ob in [scene.objects[name], *scene.objects[name].children_recursive]:
            if ob.type == "MESH" and not ob.hide_render:
                found[ob.name] = ob
    return list(found.values())


def _lamps(patterns):
    """Lamps and the meshes whose emission shows a lamp lit (bulbs, shades) matching the patterns,
    with their children."""
    scene = bpy.context.scene
    names = hotspots.match_objects([o.name for o in scene.objects], patterns) if patterns else []
    found = {}
    for name in names:
        for ob in [scene.objects[name], *scene.objects[name].children_recursive]:
            if ob.type in ("LIGHT", "MESH", "CURVE", "FONT"):
                found[ob.name] = ob
    return list(found.values())


def _zone_lights(mapping):
    """{hotspot name: objects} of every hotspot's "lights"; the mapping's "off" (lamps of a room this
    one was copied from) are off in every render, so they join every zone's list of lamps to turn off."""
    zones = {spot["name"]: _lamps(spot.get("lights", [])) for spot in mapping["hotspots"]}
    zones[None] = _lamps(mapping.get("off", []))
    return zones


def _emission_off(mat):
    """A copy of the material with no emission (shared lamp materials stay as they are)."""
    off = mat.copy()
    off.name = mat.name + ".legacy_off"
    for node in off.node_tree.nodes if off.use_nodes else []:
        if node.type == "EMISSION":
            node.inputs["Strength"].default_value = 0
        elif node.type == "BSDF_PRINCIPLED":
            node.inputs["Emission Strength"].default_value = 0
    return off


@contextmanager
def _hidden(objects):
    """Hides the objects from the render; their visibility is restored afterwards."""
    saved = [(ob, ob.hide_render) for ob in objects]
    try:
        for ob, _ in saved:
            ob.hide_render = True
        yield
    finally:
        for ob, value in saved:
            ob.hide_render = value


@contextmanager
def _lights_off(objects):
    """Turns the lamps off for the render: lights hidden, meshes' materials swapped for copies
    without emission; everything restored and the copies removed afterwards."""
    hidden = [(ob, ob.hide_render) for ob in objects if ob.type == "LIGHT"]
    slots, copies = [], {}
    try:
        for ob, _ in hidden:
            ob.hide_render = True
        for ob in objects:
            if ob.type == "LIGHT":
                continue
            for slot in ob.material_slots:
                if slot.material is None:
                    continue
                mat, link = slot.material, slot.link
                if mat.name not in copies:
                    copies[mat.name] = _emission_off(mat)
                slot.link = "OBJECT"  # the swap stays on this object, even for mesh-linked slots
                slots.append((slot, link, slot.material))  # the object's own material, often None
                slot.material = copies[mat.name]
        yield
    finally:
        for slot, link, mat in reversed(slots):
            slot.material = mat
            slot.link = link
        for ob, value in hidden:
            ob.hide_render = value
        for mat in copies.values():
            bpy.data.materials.remove(mat)


def _rect(spot, menu):
    scene, depsgraph = bpy.context.scene, bpy.context.evaluated_depsgraph_get()
    points = []
    for ob in _objects(spot):
        evaluated = ob.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points += [tuple(world_to_camera_view(scene, scene.camera, ob.matrix_world @ v.co)) for v in mesh.vertices]
        finally:
            evaluated.to_mesh_clear()
    rect = hotspots.rect_from_points(points, _picture())
    if rect is None:
        raise ValueError(f"{menu}: hotspot {spot['name']} is not in the camera's view")
    return rect


def _render_mask(path, rect, objects):
    """Renders the rect with Workbench: the objects white, every other object and the world black,
    with neutral colour management, so the mask is pure black and white."""
    scene = bpy.context.scene
    r, shading, view = scene.render, scene.display.shading, scene.view_settings
    targets = {ob.name for ob in objects}
    colors = {ob.name: tuple(ob.color) for ob in scene.objects}
    settings = [(r, "engine"), (r, "film_transparent"),
                (shading, "light"), (shading, "color_type"), (shading, "show_shadows"), (shading, "show_cavity"),
                (shading, "show_object_outline"), (shading, "show_xray"), (shading, "show_backface_culling"),
                (shading, "use_dof"), (view, "view_transform"), (view, "look"), (view, "exposure"), (view, "gamma"),
                (view, "use_curve_mapping")]
    if scene.world:
        settings.append((scene.world, "color"))
    saved = [(owner, name, getattr(owner, name)) for owner, name in settings]
    saved = [(o, n, tuple(v) if n == "color" else v) for o, n, v in saved]
    try:
        try:
            r.engine = "BLENDER_WORKBENCH"
        except TypeError as error:  # the message lists the engines this Blender has
            raise RuntimeError(f"no Workbench engine: {error}") from error
        r.film_transparent = False
        shading.light, shading.color_type = "FLAT", "OBJECT"
        shading.show_shadows = shading.show_cavity = shading.show_object_outline = False
        shading.show_xray = shading.show_backface_culling = shading.use_dof = False
        view.view_transform, view.look, view.exposure, view.gamma = "Standard", "None", 0.0, 1.0
        view.use_curve_mapping = False
        if scene.world:
            scene.world.color = (0, 0, 0)
        for ob in scene.objects:  # every type: curves and text default to white
            ob.color = (1, 1, 1, 1) if ob.name in targets else (0, 0, 0, 1)
        _render(path, border=rect)
    finally:
        try:
            for owner, name, value in saved:
                setattr(owner, name, value)
        finally:
            for name, color in colors.items():
                try:
                    scene.objects[name].color = color
                except (AttributeError, TypeError):  # linked, read-only
                    pass


def export_background(mapping_path, out_root):
    """Renders <out_root>/<menu>/background.png; returns its path."""
    mapping, folder, json_path = _paths(mapping_path, out_root)
    path = os.path.join(folder, "background.png")
    with _lights_off([ob for objects in _zone_lights(mapping).values() for ob in objects]):
        _render(path)
    _update_json(json_path, mapping["menu"], lambda d: d.update(picture=list(_picture())))
    return path


def export_hotspot(mapping_path, out_root, name):
    """Measures one hotspot and, unless it is the board, renders its mask; returns its entry."""
    mapping, folder, json_path = _paths(mapping_path, out_root)
    spot = next((s for s in mapping["hotspots"] if s["name"] == name), None)
    if spot is None:
        raise ValueError(f"{mapping['menu']}: no hotspot {name}")
    rect = _rect(spot, mapping["menu"])
    if not spot.get("board"):  # room for the hover's light to fade out (the sign's text keeps the board)
        rect = hotspots.pad_rect(rect, _picture())
    entry = {"rect": list(rect)}
    if not spot.get("board"):
        entry["mask"] = f"mask_{hotspots.slug(name)}.png"
        _render_mask(os.path.join(folder, entry["mask"]), entry["rect"], _objects(spot))
    if spot.get("lights"):  # the rect with only this hotspot's lamps on: its hover
        zones = _zone_lights(mapping)
        entry["lit"] = f"lit_{hotspots.slug(name)}.png"
        with _lights_off([ob for zone, objects in zones.items() if zone != name for ob in objects]):
            _render(os.path.join(folder, entry["lit"]), border=entry["rect"])
    _update_json(json_path, mapping["menu"], lambda d: d["hotspots"].__setitem__(name, entry))
    return entry


def export_screen(mapping_path, out_root):
    """An option screen (a mapping with "screen"): renders the background from the screen's camera and
    writes <menu>.json with the rect of every control's parts (knob, plate, lamp) in picture units:
    {"menu", "picture", "background", "controls": {name: {part: [x, y, w, h]}}}. Every rect is
    measured before anything is written; the scene's camera is restored afterwards."""
    mapping, folder, json_path = _paths(mapping_path, out_root)
    scene = bpy.context.scene
    camera = scene.objects.get(mapping["camera"])
    if camera is None or camera.type != "CAMERA":
        raise ValueError(f"{mapping['menu']}: no camera {mapping['camera']}")
    saved = scene.camera
    try:
        scene.camera = camera
        bpy.context.view_layer.update()
        controls = {}
        for control in mapping["controls"]:
            controls[control["name"]] = {
                part: list(_rect({"name": f"{control['name']} {part}", "objects": control[part]}, mapping["menu"]))
                for part in hotspots.CONTROL_PARTS[control["kind"]]}
        data = {"menu": mapping["menu"], "picture": list(_picture()), "background": "background.png",
                "controls": controls}
        medals = {c["name"]: _objects({"objects": c["medal"]}) for c in mapping["controls"] if c["kind"] == "medal"}
        if medals:  # a medal case: the plates the engine writes on, then the case empty, then each medal alone
            data["plates"] = {plate: list(_rect({"name": plate, "objects": mapping[plate + "_plate"]}, mapping["menu"]))
                              for plate in ("name", "desc")}
        path = os.path.join(folder, "background.png")
        with _hidden([ob for objects in medals.values() for ob in objects]):
            _render(path)
        for name, objects in medals.items():
            controls[name]["image"] = f"medal_{hotspots.slug(name)}.png"
            # the whole frame (a border render lights the velvet differently); the pak cuts the rect
            with _hidden([ob for other, obs in medals.items() if other != name for ob in obs]):
                _render(os.path.join(folder, controls[name]["image"]))
        with open(json_path, "w") as f:
            json.dump(data, f, indent=1)
    finally:
        scene.camera = saved
    return path


def export_all(mapping_path, out_root):
    """A fresh export of the screen: every hotspot is measured first, so a mapping error stops the
    run before anything is written; <menu>.json then starts over with no hotspots, so a run that
    fails half way leaves an export the pak build refuses (a hotspot is missing) instead of a mix of
    old and new rects. (It is overwritten, not deleted: over the WSL share Windows refuses to create
    a file again right after deleting it.) export_background and export_hotspot alone update an
    existing export."""
    mapping, folder, json_path = _paths(mapping_path, out_root)
    if mapping.get("screen"):
        return export_screen(mapping_path, out_root)
    for spot in mapping["hotspots"]:
        _rect(spot, mapping["menu"])
    with open(json_path, "w") as f:
        json.dump({"menu": mapping["menu"], "picture": list(_picture()), "background": "background.png",
                   "hotspots": {}}, f, indent=1)
    export_background(mapping_path, out_root)
    for spot in mapping["hotspots"]:
        export_hotspot(mapping_path, out_root, spot["name"])
