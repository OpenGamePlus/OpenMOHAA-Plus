# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Blender side of the Legacy menu: renders a screen's background and one object mask per hotspot
from the open scene, and writes the hotspot rects in picture units. The pak build lights the masked
part of the background for the hover (legacy/pak.py), so hovers match the background exactly.

Run inside Blender (Blender MCP or the text editor), with the screen's .blend open:

    path = r"<repo>/misc/plus-pk3/legacy/export_hotspots.py"
    exec(compile(open(path).read(), path, "exec"), g := {"__file__": path, "__name__": "legacy_export"})
    g["export_all"](r"<repo>/misc/plus-pk3/legacy/main.json", r"<export root>")

Export the background and the masks from one scene state. Writes <export root>/<menu>/background.png,
mask_<slug>.png and <menu>.json:
{"menu", "picture": [W, 480], "background": "background.png",
 "hotspots": {name: {"rect": [x, y, w, h], "mask": "mask_<slug>.png"}}} (the board has no mask).
A mask is a Workbench render of the hotspot's rect: its objects white, every other object black, so
what stands in front of it stays dark (under a second). The background is a full render with the
scene's own engine (minutes). The .blend is never saved; object colours, the engine and the render
settings are restored after each render.
"""
import json
import os
import sys

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
        bpy.ops.render.render(write_still=True)
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
    """Renders the rect with Workbench: the objects white, the other meshes black."""
    scene = bpy.context.scene
    r, shading, view = scene.render, scene.display.shading, scene.view_settings
    targets = {ob.name for ob in objects}
    colors = {ob.name: tuple(ob.color) for ob in scene.objects if ob.type == "MESH"}
    saved = (r.engine, shading.light, shading.color_type, shading.show_shadows, shading.show_cavity,
             shading.show_object_outline, r.film_transparent, view.view_transform, view.look)
    try:
        try:
            r.engine = "BLENDER_WORKBENCH"
        except TypeError as error:  # the message lists the engines this Blender has
            raise RuntimeError(f"no Workbench engine: {error}") from error
        shading.light, shading.color_type = "FLAT", "OBJECT"
        shading.show_shadows = shading.show_cavity = shading.show_object_outline = False
        r.film_transparent = False
        view.view_transform, view.look = "Standard", "None"
        for name in colors:
            scene.objects[name].color = (1, 1, 1, 1) if name in targets else (0, 0, 0, 1)
        _render(path, border=rect)
    finally:
        for name, color in colors.items():
            scene.objects[name].color = color
        (r.engine, shading.light, shading.color_type, shading.show_shadows, shading.show_cavity,
         shading.show_object_outline, r.film_transparent, view.view_transform, view.look) = saved


def export_background(mapping_path, out_root):
    """Renders <out_root>/<menu>/background.png; returns its path."""
    mapping, folder, json_path = _paths(mapping_path, out_root)
    path = os.path.join(folder, "background.png")
    _render(path)
    _update_json(json_path, mapping["menu"], lambda d: d.update(picture=list(_picture())))
    return path


def export_hotspot(mapping_path, out_root, name):
    """Measures one hotspot and, unless it is the board, renders its mask; returns its entry."""
    mapping, folder, json_path = _paths(mapping_path, out_root)
    spot = next((s for s in mapping["hotspots"] if s["name"] == name), None)
    if spot is None:
        raise ValueError(f"{mapping['menu']}: no hotspot {name}")
    entry = {"rect": list(_rect(spot, mapping["menu"]))}
    if not spot.get("board"):
        entry["mask"] = f"mask_{hotspots.slug(name)}.png"
        _render_mask(os.path.join(folder, entry["mask"]), entry["rect"], _objects(spot))
    _update_json(json_path, mapping["menu"], lambda d: d["hotspots"].__setitem__(name, entry))
    return entry


def export_all(mapping_path, out_root):
    """The background, then every hotspot."""
    export_background(mapping_path, out_root)
    for spot in hotspots.load_mapping(mapping_path)["hotspots"]:
        export_hotspot(mapping_path, out_root, spot["name"])
