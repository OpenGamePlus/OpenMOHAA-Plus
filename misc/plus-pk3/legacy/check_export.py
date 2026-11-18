# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checks of export_hotspots.py that need Blender (run by hand, prints CHECK1/CHECK2 PASS or FAIL):

    blender -b escritorio_1940_v2.blend --python check_export.py -- <export_hotspots.py> <scratch dir>

Uses the war records scene (Board_Frame, Board_Felt, Box_* objects); never saves the .blend.
1. A mapping error stops export_all before anything is written (an old export stays as it was).
2. A mask is pure black and white even with exposure -1 and a grey world.
"""
import sys, os, json, bpy
script, root = sys.argv[sys.argv.index("--") + 1:]
g = {"__file__": script, "__name__": "legacy_export"}
exec(compile(open(script).read(), script, "exec"), g)
def mapping(name, spots):
    p = os.path.join(root, name + ".json")
    json.dump({"menu": name, "sign_cvar": "ui_recordsign", "hotspots": spots}, open(p, "w"))
    return p
board = {"name": "sign", "board": True, "objects": ["Board_Frame", "Board_Felt"]}
box = {"name": "box", "objects": ["Box_*"], "command": "pushmenu medals", "sign": "s"}
# 1: a mapping error must stop the run before anything is written
out1 = os.path.join(root, "out1"); os.makedirs(os.path.join(out1, "stale"), exist_ok=True)
old = {"menu": "stale", "picture": [1, 480], "background": "background.png", "hotspots": {"gone": {"rect": [1, 2, 3, 4], "mask": "x"}}}
json.dump(old, open(os.path.join(out1, "stale", "stale.json"), "w"))
try:
    g["export_all"](mapping("stale", [board, box, {"name": "bad", "objects": ["NoSuchObject"], "command": "c", "sign": "s"}]), out1)
    print("CHECK1 no error raised")
except ValueError as e:
    files = sorted(os.listdir(os.path.join(out1, "stale")))
    same = json.load(open(os.path.join(out1, "stale", "stale.json"))) == old
    print("CHECK1", "PASS" if files == ["stale.json"] and same else "FAIL", files, "json unchanged:", same, "|", e)
# 2: the mask is pure black/white whatever the colour management and world colour
sc = bpy.context.scene
sc.view_settings.exposure = -1.0
if sc.world: sc.world.color = (0.5, 0.5, 0.5)
out2 = os.path.join(root, "out2")
e = g["export_hotspot"](mapping("mask", [board, box]), out2, "box")
img = bpy.data.images.load(os.path.join(out2, "mask", e["mask"]))
px = list(img.pixels)[0::4]
mid = sum(1 for v in px if 0.02 < v < 0.98) / len(px)
print("CHECK2", "PASS" if max(px) > 0.98 and mid < 0.02 else "FAIL", "max %.3f, share of grey pixels %.3f" % (max(px), mid))
print("exposure after", sc.view_settings.exposure)
