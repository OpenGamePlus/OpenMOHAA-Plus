# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unit tests for the Legacy menu tools in legacy/ (the build tests need Pillow)."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from legacy import hotspots  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
