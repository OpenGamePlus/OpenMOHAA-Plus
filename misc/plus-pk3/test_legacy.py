# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unit tests for the Legacy menu tools in legacy/ (the build tests need Pillow)."""
import io
import json
import os
import re
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from legacy import hotspots  # noqa: E402

try:
    from PIL import Image
except ImportError:  # Pillow missing
    Image = None


def write_json(folder, name, data):
    path = os.path.join(folder, name)
    with open(path, "w") as f:
        json.dump(data, f)
    return path


class Hotspots(unittest.TestCase):
    def test_picture_size(self):
        self.assertEqual(hotspots.picture_size(3840, 1600), (1152, 480))
        self.assertEqual(hotspots.picture_size(1920, 1080), (853, 480))

    def test_rect_rounds_outwards(self):
        pts = [(0.25, 0.5, 1), (0.5004, 0.25, 2)]
        self.assertEqual(hotspots.rect_from_points(pts, (1152, 480)), (288, 240, 289, 120))

    def test_rect_clamped(self):
        self.assertEqual(hotspots.rect_from_points([(-0.1, 1.2, 1), (0.1, 0.9, 1)], (1152, 480)), (0, 0, 116, 48))

    def test_rect_none_when_outside(self):
        self.assertIsNone(hotspots.rect_from_points([(1.1, 0.5, 1), (1.3, 0.6, 1)], (1152, 480)))
        self.assertIsNone(hotspots.rect_from_points([(0.5, 0.5, -1)], (1152, 480)))
        self.assertIsNone(hotspots.rect_from_points([], (1152, 480)))

    def test_match_objects(self):
        names = ["Tray0_L", "Tray1_R", "Board_Frame", "Board_Wire"]
        self.assertEqual(hotspots.match_objects(names, ["Tray*", "Board_Frame"]), ["Board_Frame", "Tray0_L", "Tray1_R"])

    def test_match_objects_missing_pattern_raises(self):
        with self.assertRaisesRegex(ValueError, r"Box_\*"):
            hotspots.match_objects(["Tray0_L"], ["Tray*", "Box_*"])

    def test_slug(self):
        self.assertEqual(hotspots.slug("Personal records!"), "personal_records")
        self.assertEqual(hotspots.slug("new game"), "new_game")

    def mapping(self, hotspot_list):
        return {"menu": "main", "sign_cvar": "ui_signshader", "hotspots": hotspot_list,
                "corners": [{"title": "Quit", "side": "right", "command": "quit"}]}

    def load(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            return hotspots.load_mapping(write_json(tmp, "m.json", data))

    BOARD = {"name": "sign", "board": True, "objects": ["Board"]}
    SPOT = {"name": "a", "objects": ["A"], "command": "pushmenu x", "sign": "x_sign"}

    def test_load_mapping(self):
        self.assertEqual(self.load(self.mapping([self.BOARD, self.SPOT]))["menu"], "main")

    def test_load_mapping_rejects_two_boards(self):
        with self.assertRaisesRegex(ValueError, "board"):
            self.load(self.mapping([self.BOARD, dict(self.BOARD, name="sign2"), self.SPOT]))

    def test_load_mapping_rejects_missing_command(self):
        with self.assertRaisesRegex(ValueError, "main.*a"):
            self.load(self.mapping([self.BOARD, {"name": "a", "objects": ["A"], "sign": "s"}]))

    def test_load_mapping_rejects_quotes_and_duplicates(self):
        with self.assertRaisesRegex(ValueError, "name"):
            self.load(self.mapping([self.BOARD, dict(self.SPOT, name='a"b')]))
        with self.assertRaisesRegex(ValueError, "a"):
            self.load(self.mapping([self.BOARD, self.SPOT, self.SPOT]))

    def test_load_mapping_rejects_bad_corner(self):
        data = self.mapping([self.BOARD, self.SPOT])
        data["corners"] = [{"title": "Quit", "side": "up", "command": "quit"}]
        with self.assertRaisesRegex(ValueError, "side"):
            self.load(data)


class Mappings(unittest.TestCase):
    """The hotspots agreed with the maintainer (spec 2026-11-17-legacy-menu-design.md)."""
    AGREED = {
        "main": {"sign": (None, None),
                 "new game": ("pushmenu briefingroom", "newgame_sign"),
                 "briefing": ("pushmenu briefingroom", "briefingroom_sign"),
                 "multiplayer": ("pushmenu multiplayer", "multiplayer_sign"),
                 "options": ("pushmenu options_main", "options_sign"),
                 "records": ("pushmenu war_records", "warrecords_sign"),
                 "credits": ("spmap credits", "credits_sign")},
        "options_main": {"sign": (None, None),
                         "advanced": ("pushmenu advancedoptions", "advanced_sign"),
                         "audio": ("pushmenu audio_options", "audio_sign"),
                         "controls": ("pushmenu controls", "controls_sign"),
                         "video": ("pushmenu video_options", "video_sign")},
        "war_records": {"sign": (None, None),
                        "personal records": ("pushmenu medals", "personalrecords_sign"),
                        "loadsave": ("pushmenu_sp loadsave;pushmenu_dm loadsave_mp", "loadsave_sign")},
    }
    SIGN_CVARS = {"main": "ui_signshader", "options_main": "ui_optionshader", "war_records": "ui_recordsign"}

    def test_agreed_mapping(self):
        for menu, agreed in self.AGREED.items():
            mapping = hotspots.load_mapping(os.path.join(HERE, "legacy", menu + ".json"))
            self.assertEqual(mapping["menu"], menu)
            self.assertEqual(mapping["sign_cvar"], self.SIGN_CVARS[menu])
            got = {h["name"]: (h.get("command"), h.get("sign")) for h in mapping["hotspots"]}
            self.assertEqual(got, agreed, menu)
            self.assertEqual(list(got), list(agreed), menu)  # board first, then the agreed order


@unittest.skipUnless(Image, "needs Pillow")
class BuildLegacy(unittest.TestCase):
    MAPPING = {"menu": "main", "sign_cvar": "ui_signshader", "hotspots": [
        {"name": "sign", "board": True, "objects": ["Board"]},
        {"name": "a b", "objects": ["A"], "command": "pushmenu a", "sign": "a_sign"},
        {"name": "c", "objects": ["C"], "command": "pushmenu c;set x 1", "sign": "c_sign"}],
        "corners": [{"title": "Back to game", "side": "left", "command": "popmenu 0"},
                    {"title": "Quit", "side": "right", "command": "quit"}]}
    RECTS = {"main": {"sign": [681, 38, 144, 72], "a b": [336, 304, 386, 145], "c": [823, 276, 3, 183]}}

    @classmethod
    def setUpClass(cls):
        global build_pk3, build_legacy
        import build_pk3
        from legacy import build_legacy
        cls.tmp = tempfile.TemporaryDirectory()
        mappings = os.path.join(cls.tmp.name, "mappings")
        os.makedirs(mappings)
        write_json(mappings, "main.json", cls.MAPPING)
        write_json(mappings, "options_main.json", dict(cls.MAPPING, menu="options_main"))
        export = os.path.join(cls.tmp.name, "export")
        build_legacy.fake_export(mappings, export, cls.RECTS)
        os.remove(os.path.join(export, "options_main", "options_main.json"))  # a screen not exported yet
        cls.legacy = os.path.join(cls.tmp.name, "zzzz-plus-legacy.pk3")
        cls.stderr = io.StringIO()
        with redirect_stderr(cls.stderr):
            assert build_pk3.main(["--out", os.path.join(cls.tmp.name, "zzz-plus.pk3"), "--skip-fonts",
                                   "--legacy", export, "--legacy-mappings", mappings]) == 0
        cls.zip = zipfile.ZipFile(cls.legacy)

    @classmethod
    def tearDownClass(cls):
        cls.zip.close()
        cls.tmp.cleanup()

    def read(self, name):
        return self.zip.read(name).decode()

    def block(self, name):
        text = self.read("ui/main.urc")
        return text[text.index(f'name "{name}"'):].split("\n}", 1)[0]

    def test_legacy_pak_contents(self):
        self.assertEqual(set(self.zip.namelist()), {
            "ui/main.urc", "textures/menu_plus/legacy/main_l.jpg", "textures/menu_plus/legacy/main_r.jpg",
            "textures/menu_plus/legacy/main_a_b_h.jpg", "textures/menu_plus/legacy/main_c_h.jpg"})

    def test_crops_power_of_two(self):
        sides = {2 ** n for n in range(4, 12)}
        for name in ("main_a_b_h", "main_c_h"):
            img = Image.open(io.BytesIO(self.zip.read(f"textures/menu_plus/legacy/{name}.jpg")))
            self.assertIn(img.width, sides, name)
            self.assertIn(img.height, sides, name)
        self.assertEqual(Image.open(io.BytesIO(self.zip.read("textures/menu_plus/legacy/main_l.jpg"))).size, (2048, 2048))

    def test_urc_widget_order(self):
        order = re.findall(r'^name "([^"]+)"', self.read("ui/main.urc"), re.M)
        self.assertEqual(order, ["background left", "background right", "sign", "a b", "c", "Back to game", "Quit"])

    def test_urc_hotspot(self):
        block = self.block("c")
        for line in ("rect 823 276 3 183", "scalecvar ui_plusscale", "cover 1152 480",
                     'shader "textures/menu_plus/clear"', 'hovershader "textures/menu_plus/legacy/main_c_h"',
                     'stuffcommand "pushmenu c;set x 1"', 'hovercommand "set ui_signshader c_sign"'):
            self.assertIn("\n" + line + "\n", block + "\n", line)

    def test_urc_sign_and_corners(self):
        sign = self.block("sign")
        for line in ("rect 681 38 144 72", "cover 1152 480", 'linkcvar "ui_signshader"', "linkcvartoshader"):
            self.assertIn(line, sign)
        self.assertIn("anchor 30 -1 -1 40", self.block("Back to game"))
        self.assertIn("anchor -1 -1 30 40", self.block("Quit"))
        self.assertIn('stuffcommand "quit"', self.block("Quit"))

    def test_missing_screen_skipped(self):
        self.assertNotIn("ui/options_main.urc", self.zip.namelist())
        self.assertIn("legacy: no export for options_main", self.stderr.getvalue())

    def test_missing_hotspot_raises(self):
        mappings, export = os.path.join(self.tmp.name, "mappings"), os.path.join(self.tmp.name, "export")
        with open(os.path.join(export, "main", "main.json")) as f:
            data = json.load(f)
        del data["hotspots"]["c"]
        broken = os.path.join(self.tmp.name, "broken")
        os.makedirs(os.path.join(broken, "main"))
        write_json(os.path.join(broken, "main"), "main.json", data)
        with self.assertRaisesRegex(ValueError, "main.*c"):
            list(build_legacy.files(mappings, broken))

    def test_modern_pak_unchanged(self):
        with zipfile.ZipFile(os.path.join(self.tmp.name, "zzz-plus.pk3")) as modern:
            self.assertFalse([n for n in modern.namelist() if "legacy" in n])


if __name__ == "__main__":
    unittest.main()
