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
        self.assertEqual(hotspots.picture_size(2562, 1440), (854, 480))
        # 1920x1080 is 853.33 units wide: rounded, the background and the hovers drifted apart
        with self.assertRaisesRegex(ValueError, "1920x1080"):
            hotspots.picture_size(1920, 1080)

    def test_padded_rect(self):
        # room for the hover's light to fade out: 8% of the longer side each way, clamped to the picture
        self.assertEqual(hotspots.pad_rect((100, 100, 50, 25), (854, 480)), (96, 96, 58, 33))
        self.assertEqual(hotspots.pad_rect((0, 470, 100, 10), (854, 480)), (0, 462, 108, 18))

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
    SPOT = {"name": "a", "objects": ["A"], "command": "pushmenu x", "sign": "x_sign", "text": "X"}

    def test_load_mapping(self):
        self.assertEqual(self.load(self.mapping([self.BOARD, self.SPOT]))["menu"], "main")

    def test_load_mapping_rejects_two_boards(self):
        with self.assertRaisesRegex(ValueError, "board"):
            self.load(self.mapping([self.BOARD, dict(self.BOARD, name="sign2"), self.SPOT]))

    def test_load_mapping_rejects_missing_command(self):
        with self.assertRaisesRegex(ValueError, "main.*a"):
            self.load(self.mapping([self.BOARD, {"name": "a", "objects": ["A"], "sign": "s", "text": "S"}]))

    def test_load_mapping_rejects_missing_text(self):
        spot = dict(self.SPOT)
        del spot["text"]
        with self.assertRaisesRegex(ValueError, "main.*a.*text"):
            self.load(self.mapping([self.BOARD, spot]))

    def test_load_mapping_rejects_quote_in_text(self):
        with self.assertRaisesRegex(ValueError, "text"):
            self.load(self.mapping([self.BOARD, dict(self.SPOT, text='say "x"')]))

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
        "main": {"sign": (None, None, None),
                 "new game": ("pushmenu briefingroom", "newgame_sign", "New Game"),
                 "briefing": ("pushmenu briefingroom", "briefingroom_sign", "Briefing"),
                 "multiplayer": ("pushmenu multiplayer", "multiplayer_sign", "Multiplayer"),
                 "options": ("pushmenu options_main", "options_sign", "Options"),
                 "records": ("pushmenu war_records", "warrecords_sign", "War Records"),
                 "credits": ("spmap credits", "credits_sign", "Credits"),
                 "model credits": ("pushmenu legacy_credits", "modelcredits_sign", "Model Credits")},
        "options_main": {"sign": (None, None, None),
                         "advanced": ("pushmenu advancedoptions", "advanced_sign", "Advanced"),
                         "audio": ("pushmenu audio_options", "audio_sign", "Audio"),
                         "controls": ("pushmenu controls", "controls_sign", "Controls"),
                         "video": ("pushmenu video_options", "video_sign", "Video")},
        "war_records": {"sign": (None, None, None),
                        "personal records": ("pushmenu medals", "personalrecords_sign", "Personal Records"),
                        "loadsave": ("pushmenu_sp loadsave;pushmenu_dm loadsave_mp", "loadsave_sign", "Load / Save")},
    }
    SIGN_CVARS = {"main": "ui_signshader", "options_main": "ui_optionshader", "war_records": "ui_recordsign"}

    def test_agreed_mapping(self):
        for menu, agreed in self.AGREED.items():
            mapping = hotspots.load_mapping(os.path.join(HERE, "legacy", menu + ".json"))
            self.assertEqual(mapping["menu"], menu)
            self.assertEqual(mapping["sign_cvar"], self.SIGN_CVARS[menu])
            got = {h["name"]: (h.get("command"), h.get("sign"), h.get("text")) for h in mapping["hotspots"]}
            self.assertEqual(got, agreed, menu)
            self.assertEqual(list(got), list(agreed), menu)  # board first, then the agreed order


@unittest.skipUnless(Image, "needs Pillow")
class BuildLegacy(unittest.TestCase):
    MAPPING = {"menu": "main", "sign_cvar": "ui_signshader", "hotspots": [
        {"name": "sign", "board": True, "objects": ["Board"]},
        {"name": "a b", "objects": ["A"], "command": "pushmenu a", "sign": "a_sign", "text": "A B"},
        {"name": "c", "objects": ["C"], "command": "pushmenu c;set x 1", "sign": "c_sign", "text": "Ç",
         "lights": ["C_Lamp"]}],
        "corners": [{"title": "Back to game", "side": "left", "command": "popmenu 0"},
                    {"title": "Quit", "side": "right", "command": "quit"}]}
    RECTS = {"main": {"sign": [681, 38, 144, 72], "a b": [336, 304, 386, 145], "c": [823, 276, 3, 183]}}

    @classmethod
    def setUpClass(cls):
        global build_pk3, build_legacy
        import build_pk3
        from legacy import pak as build_legacy
        cls.tmp = tempfile.TemporaryDirectory()
        mappings = os.path.join(cls.tmp.name, "mappings")
        os.makedirs(mappings)
        write_json(mappings, "main.json", cls.MAPPING)
        write_json(mappings, "options_main.json", dict(cls.MAPPING, menu="options_main"))
        os.makedirs(os.path.join(mappings, "credits"))
        write_json(os.path.join(mappings, "credits"), "models.json", {"license_url": "https://example.org/by", "models": [
            {"title": "Old Phone", "author": "gorzi", "url": "https://example.org/phone", "license": "CC BY 4.0"},
            {"title": "Fan", "author": "cody", "url": "https://example.org/fan", "license": "CC BY 4.0"}]})
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
        return self.zip.read(name).decode("cp1252")

    def block(self, name):
        text = self.read("ui/main.urc")
        return text[text.index(f'name "{name}"'):].split("\n}", 1)[0]

    def test_legacy_pak_contents(self):
        # the sign font too: plussign-32 is not in the game, and a zzz-plus.pk3 without it (--skip-fonts,
        # an older release) would stop the menu with "Couldn't load font"
        self.assertEqual(set(self.zip.namelist()), {
            "ui/main.urc", "textures/menu_plus/legacy/main_l.jpg", "textures/menu_plus/legacy/main_r.jpg",
            "textures/menu_plus/legacy/main_a_b_h.jpg", "textures/menu_plus/legacy/main_c_h.jpg",
            "fonts/plussign-32.RitualFont", "gfx/fonts/plussign-32.tga", "ui/legacy_credits.urc",
            "textures/menu_plus/legacy/button.jpg", "textures/menu_plus/legacy/button_h.jpg"})

    def test_green_button_plates(self):
        # the classic green plates, drawn here (not the game's art): the hover one lighter, no text on them
        plain, hover = (Image.open(io.BytesIO(self.zip.read(f"textures/menu_plus/legacy/{n}.jpg"))).convert("RGB")
                        for n in ("button", "button_h"))
        self.assertEqual(plain.size, (256, 64))
        r, g, b = plain.getpixel((128, 32))
        self.assertTrue(g > r + 15 and g > b + 5, (r, g, b))  # green
        self.assertGreater(sum(hover.getpixel((128, 32))), sum(plain.getpixel((128, 32))) + 60)

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

    def test_smaller_hotspots_on_top(self):
        # where two rects overlap the smaller one takes the pointer (a door in front of a big desk's
        # rect): buttons go from the largest to the smallest, later ones on top
        mapping = dict(self.MAPPING, hotspots=[self.MAPPING["hotspots"][0],
                                               dict(self.MAPPING["hotspots"][2], name="small"),
                                               dict(self.MAPPING["hotspots"][1], name="big")])
        export = {"picture": [1152, 480], "hotspots": {"sign": {"rect": [1, 1, 10, 10]},
                                                       "small": {"rect": [100, 100, 20, 20]},
                                                       "big": {"rect": [50, 50, 300, 300]}}}
        order = re.findall(r'^name "([^"]+)"', build_legacy.urc(mapping, export), re.M)
        self.assertLess(order.index("big"), order.index("small"), order)

    def test_urc_hotspot(self):
        block = self.block("c")
        for line in ("rect 823 276 3 183", "scalecvar ui_plusscale", "cover 1152 480",
                     'shader "textures/menu_plus/clear"', 'hovershader "textures/menu_plus/legacy/main_c_h"',
                     'stuffcommand "pushmenu c;set x 1"', 'hovercommand "set ui_signshader c_sign"'):
            self.assertIn("\n" + line + "\n", block + "\n", line)

    def test_urc_sign_and_corners(self):
        sign = self.block("sign")
        for line in ("rect 681 38 144 72", "cover 1152 480", 'linkcvar "ui_signshader"', "font plussign-32",
                     "textalign center", "fgcolor 0.95 0.92 0.84 1",
                     'linkstring "a_sign" "A B"\nlinkstring "c_sign" "Ç"'):
            self.assertIn("\n" + line + "\n", sign + "\n", line)
        self.assertNotIn("linkcvartoshader", sign)
        for name, anchor in (("Back to game", "anchor 12 -1 -1 20"), ("Quit", "anchor -1 -1 12 20")):
            block = self.block(name)
            for line in (anchor, "rect 0 0 128 30", 'shader "textures/menu_plus/legacy/button"',
                         'hovershader "textures/menu_plus/legacy/button_h"', "textalign center", "font facfont-20",
                         "fgcolor 1 1 1 1", f'title "{name}"'):
                self.assertIn("\n" + line + "\n", block + "\n", (name, line))
        self.assertIn('stuffcommand "quit"', self.block("Quit"))

    def test_model_credits_menu(self):
        # CC BY: each model's title, author, source and licence, and a way back
        text = self.read("ui/legacy_credits.urc")
        self.assertIn('menu "legacy_credits"', text)
        for line in ('title "Old Phone - gorzi"', 'title "CC BY 4.0  https://example.org/phone"',
                     'title "Fan - cody"', 'stuffcommand "popmenu 0"', 'shader "textures/menu_plus/legacy/button"'):
            self.assertIn("\n" + line + "\n", text, line)
        self.assertIn("https://example.org/by", text)

    def test_missing_screen_skipped(self):
        self.assertNotIn("ui/options_main.urc", self.zip.namelist())
        self.assertIn("legacy: no export for options_main", self.stderr.getvalue())

    def test_hover_lights_the_masked_object_only(self):
        # fake_export: background (40, 60, 80); the mask of "a b" is white in its left half
        crop = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/legacy/main_a_b_h.jpg"))).convert("RGB")
        w, h = crop.size
        lit, plain = crop.getpixel((w // 4, h // 2)), crop.getpixel((w - 4, h // 2))
        for got, base in zip(plain, (40, 60, 80)):
            self.assertAlmostEqual(got, base, delta=4)
        self.assertGreater(sum(lit), sum((40, 60, 80)) * 1.15)
        self.assertGreater(lit[0] - lit[2], (40 - 80) + 4)  # warmer than the background (+7 expected)

    def test_hover_with_lights_is_the_lit_render(self):
        # fake_export: the lit render of "c" (a hotspot with lights) is (200, 180, 150)
        crop = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/legacy/main_c_h.jpg"))).convert("RGB")
        # mostly the lit render (the tile is 10 px wide: its edge fade reaches the middle)
        got = crop.getpixel((crop.width // 4, crop.height // 2))
        for g, lit, dark in zip(got, (200, 180, 150), (40, 60, 80)):
            self.assertGreater(abs(g - dark), 2 * abs(g - lit), got)

    def test_zone_lit_fades_to_the_background_at_the_edges(self):
        # the light falls off with the distance to the object and is gone before the tile's edge:
        # no straight cut along the rect, no rectangular plateau inside it
        background, lamp = Image.new("RGB", (200, 100), (10, 10, 10)), Image.new("RGB", (200, 100), (210, 210, 210))
        mask = Image.new("L", (200, 100), 0)
        mask.paste(255, (80, 30, 120, 70))
        out = build_legacy.zone_lit(background, lamp, mask)
        row = [out.getpixel((x, 50))[0] for x in range(0, 81, 4)]
        self.assertEqual(out.getpixel((100, 50)), (210, 210, 210))  # the object: fully lit
        self.assertTrue(all(a <= b for a, b in zip(row, row[1:])), row)  # brighter towards the object
        self.assertLess(row[0], 15)  # the tile's edge: the background
        self.assertTrue(15 < out.getpixel((72, 50))[0] < 200)  # just beside the object: a soft glow
        for corner in ((0, 0), (199, 0), (0, 99), (199, 99), (100, 0), (100, 99)):
            self.assertLess(out.getpixel(corner)[0], 15, corner)

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

    def test_zone_lit_frame_stops_at_the_frame(self):
        # "glow": "frame" (a door): the frame and the opening it encloses lit, no light on the wall
        background, lamp = Image.new("RGB", (200, 100), (10, 10, 10)), Image.new("RGB", (200, 100), (210, 210, 210))
        mask = Image.new("L", (200, 100), 0)
        mask.paste(255, (60, 10, 140, 20))   # head
        mask.paste(255, (60, 10, 70, 100))   # left jamb
        mask.paste(255, (130, 10, 140, 100))  # right jamb
        out = build_legacy.zone_lit(background, lamp, mask, frame=True)
        self.assertEqual(out.getpixel((100, 60)), (210, 210, 210))  # the opening: lit
        self.assertEqual(out.getpixel((65, 60)), (210, 210, 210))   # the jamb: lit
        # the wall: a short soft edge right at the frame, nothing further out
        self.assertTrue(15 < out.getpixel((58, 60))[0] < 200)
        self.assertLess(out.getpixel((56, 60))[0], 120)
        self.assertLess(out.getpixel((40, 60))[0], 15)
        self.assertLess(out.getpixel((100, 2))[0], 15)

    def test_background_split_on_a_unit(self):
        # an odd picture width: the left tile holds the urc's 427 left units (1281 px at 3 px a unit)
        self.assertEqual(build_legacy.halves(2565, 1440, 855), ((0, 0, 1281, 1440), (1281, 0, 2565, 1440)))
        with self.assertRaisesRegex(ValueError, "2560x1440"):
            build_legacy.halves(2560, 1440, 853)

    def test_failed_build_keeps_the_old_pak(self):
        # a broken export used to leave an empty 22-byte zip over the working pak
        mappings, export = os.path.join(self.tmp.name, "mappings"), os.path.join(self.tmp.name, "export")
        with open(os.path.join(export, "main", "main.json")) as f:
            data = json.load(f)
        del data["hotspots"]["c"]
        broken = os.path.join(self.tmp.name, "broken_keep")
        os.makedirs(os.path.join(broken, "main"))
        write_json(os.path.join(broken, "main"), "main.json", data)
        out = os.path.join(self.tmp.name, "keep.pk3")
        with open(out, "wb") as f:
            f.write(b"old pak")
        with self.assertRaises(ValueError):
            build_pk3.write_legacy(out, broken, mappings)
        with open(out, "rb") as f:
            self.assertEqual(f.read(), b"old pak")
        self.assertEqual([n for n in os.listdir(self.tmp.name) if n.startswith("keep.pk3")], ["keep.pk3"])

    def test_modern_pak_unchanged(self):
        with zipfile.ZipFile(os.path.join(self.tmp.name, "zzz-plus.pk3")) as modern:
            self.assertFalse([n for n in modern.namelist() if "legacy" in n])


if __name__ == "__main__":
    unittest.main()
