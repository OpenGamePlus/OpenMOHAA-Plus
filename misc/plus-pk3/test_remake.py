# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unit tests for the Remake menu tools in remake/ (the build tests need Pillow)."""
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

from remake import hotspots  # noqa: E402

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

    def test_load_mapping_off(self):
        # "off": lamps a room copied from another keeps dark in every render (a list of patterns)
        room = self.mapping([self.BOARD, self.SPOT])
        self.assertEqual(self.load(dict(room, off=["Map_Spot", "Pend_*"]))["off"], ["Map_Spot", "Pend_*"])
        with self.assertRaises(ValueError):
            self.load(dict(room, off="Map_Spot"))

    def test_load_mapping_rejects_bad_corner(self):
        data = self.mapping([self.BOARD, self.SPOT])
        data["corners"] = [{"title": "Quit", "side": "up", "command": "quit"}]
        with self.assertRaisesRegex(ValueError, "side"):
            self.load(data)


class Screens(unittest.TestCase):
    """Option screens: a close-up with working controls (spec 2026-11-21-remake-option-screens-design.md)."""
    SCREEN = {"menu": "video_options", "screen": True, "camera": "Cam_Video", "controls": [
        {"name": "resolution", "kind": "list", "knob": ["K"], "plate": ["P"], "cvar": "r_mode",
         "items": [["Desktop", "set r_mode -2"], ["1920x1080", "set r_mode -1; set r_customwidth 1920"],
                   ["1280x720", "set r_mode -1; set r_customwidth 1280"]]},
        {"name": "model detail", "kind": "list", "knob": ["K2"], "plate": ["P2"], "cvar": "r_lodscale",
         "items": [["Low", "set r_lodscale 0.35; set r_lodcap 0.35"], ["Highest", "set r_lodscale 1.1; set r_lodcap 1.0"]]},
        {"name": "brightness", "kind": "slider", "plate": ["B"], "cvar": "r_gamma", "range": [0.5, 3.0],
         "step": 0.1, "format": "%.1f"},
        {"name": "wall decals", "kind": "check", "lamp": ["L"], "plate": ["W"], "cvar": "cg_marks_add"}],
        "corners": [{"title": "Back", "side": "left", "command": "popmenu 0"},
                    {"title": "Apply", "side": "right", "command": "ui_checkrestart; popmenu 0"},
                    {"title": "Defaults", "side": "right", "slot": 1, "command": "ui_resetcvars"}]}
    EXPORT = {"menu": "video_options", "picture": [854, 480], "background": "background.png", "controls": {
        "resolution": {"knob": [100, 100, 20, 20], "plate": [125, 100, 60, 12]},
        "model detail": {"knob": [100, 130, 20, 20], "plate": [125, 130, 60, 12]},
        "brightness": {"plate": [300, 200, 80, 10]},
        "wall decals": {"lamp": [500, 150, 10, 10], "plate": [512, 150, 70, 10]}}}

    def load(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            write_json(tmp, "s.json", data)
            return hotspots.load_mapping(os.path.join(tmp, "s.json"))

    def test_load_screen(self):
        self.assertTrue(self.load(self.SCREEN)["screen"])
        for bad in ({"kind": "dial"}, {"cvar": ""}, {"items": []}, {"plate": []}):
            screen = json.loads(json.dumps(self.SCREEN))
            screen["controls"][0].update(bad)
            with self.assertRaises(ValueError, msg=bad):
                self.load(screen)

    def test_real_video_screen(self):
        screen = hotspots.load_mapping(os.path.join(HERE, "remake", "video_options.json"))
        self.assertEqual(screen["menu"], "video_options")
        cvars = {c["cvar"] for c in screen["controls"]}
        self.assertEqual(cvars, {"r_mode", "r_colorbits", "r_picmip", "r_texturebits", "r_texturemode", "r_gamma",
                                 "cg_marks_add", "cg_rain", "r_ext_compressed_textures",  # the original's
                                 "r_fullscreen", "com_maxfps", "r_ext_texture_filter_anisotropic", "r_swapInterval"})  # added in OPM

    def test_real_audio_screen(self):
        screen = hotspots.load_mapping(os.path.join(HERE, "remake", "audio_options.json"))
        self.assertEqual(screen["menu"], "audio_options")
        self.assertEqual({c["cvar"] for c in screen["controls"]}, {"s_volume", "s_musicvolume", "s_speaker_type", "s_khz",
                                                                      "s_ambientvolume"})  # ambience: added in OPM

    def test_real_advanced_screen(self):
        screen = hotspots.load_mapping(os.path.join(HERE, "remake", "advancedoptions.json"))
        self.assertEqual({c["cvar"] for c in screen["controls"]}, {  # the original's
            "cg_drawviewmodel", "cg_shadows", "ter_error", "r_lodscale", "cg_effectdetail", "r_subdivisions", "g_subtitle",
            "ui_console", "r_drawstaticdecals", "r_fastdlights", "r_fastentlight", "vss_draw", "ui_weaponsbar", "ui_crosshair",
            # added in OPM
            "cl_renderer", "cl_language", "cg_fov", "ui_hudscale", "cg_crosshair_size", "cg_crosshair_scale", "ui_menuaspect"})

    def test_binds_and_check_commands(self):
        # the controls screen: the game's key list on the card, and a check that runs a command each
        # way (invert mouse flips m_pitch, as the original's did)
        from remake import pak
        screen = json.loads(json.dumps(self.SCREEN))
        screen["controls"].append({"name": "keys", "kind": "binds", "plate": ["C"]})
        screen["controls"][-2].update(checked_command="set m_pitch -0.022", unchecked_command="set m_pitch 0.022")
        export = json.loads(json.dumps(self.EXPORT))
        export["controls"]["keys"] = {"plate": [50, 300, 200, 120]}
        text = pak.screen_urc(self.load(screen), export)
        binds = self.block(text, "keys")
        for line in ("rect 50 300 200 120", "filename ui/bind.scr", "fgcolor 0 0 0 1", "cover 854 480"):
            self.assertIn("\n" + line + "\n", binds + "\n", line)
        self.assertIn("FakkBindList", text)
        check = self.block(text, "wall decals")
        self.assertIn('\nchecked_command "set m_pitch -0.022"\n', check + "\n")
        self.assertIn('\nunchecked_command "set m_pitch 0.022"\n', check + "\n")

    def test_real_controls_screen(self):
        screen = hotspots.load_mapping(os.path.join(HERE, "remake", "controls.json"))
        self.assertEqual({c.get("cvar") for c in screen["controls"]}, {None, "sensitivity", "m_invert_pitch", "m_filter", "cl_run"})
        self.assertEqual(next(c for c in screen["corners"] if c["title"] == "Defaults")["command"],
                         "ui_resetcvars; exec default.cfg")  # the original's

    MEDALS = {"menu": "medals", "screen": True, "camera": "Cam_Medals", "sign_cvar": "ui_medalsign",
              "name_plate": ["N"], "desc_plate": ["D"], "controls": [
                  {"name": "silver star", "kind": "medal", "medal": ["Medal_silverstar"], "cvar": "g_eogmedal1",
                   "title": "Silver Star", "desc": "For gallantry in action."}],
              "corners": [{"title": "Back", "side": "left", "command": "popmenu 0"}]}
    MEDALS_EXPORT = {"menu": "medals", "picture": [854, 480], "background": "background.png",
                     "plates": {"name": [100, 400, 300, 20], "desc": [100, 20, 300, 30]},
                     "controls": {"silver star": {"medal": [500, 200, 60, 120], "image": "medal_silver_star.png"}}}

    def test_medal_case(self):
        # the medal case: a medal shows only when earned (its cvar), and pointing at it writes its name
        # on the name plate and its description on the card (the original's ui_medalsign)
        from remake import pak
        text = pak.screen_urc(self.load(self.MEDALS), self.MEDALS_EXPORT)
        pic, hot = self.block(text, "silver star"), self.block(text, "silver star button")
        for line in ("rect 500 200 60 120", 'shader "textures/menu_plus/remake/medals_silver_star"', 'enabledcvar "g_eogmedal1"'):
            self.assertIn("\n" + line + "\n", pic + "\n", line)
        for line in ("rect 500 200 60 120", 'enabledcvar "g_eogmedal1"', 'hovercommand "set ui_medalsign silver_star"'):
            self.assertIn("\n" + line + "\n", hot + "\n", line)
        name, desc = self.block(text, "medal name"), self.block(text, "medal description")
        self.assertIn('\nlinkstring "silver_star" "Silver Star"\n', name + "\n")
        self.assertIn('\nlinkstring "silver_star" "For gallantry in action."\n', desc + "\n")
        for block in (name, desc):
            self.assertIn('\nlinkcvar "ui_medalsign"\n', block + "\n")
        with self.assertRaises(ValueError):  # a medal needs its title and description
            bad = json.loads(json.dumps(self.MEDALS)); del bad["controls"][0]["desc"]
            self.load(bad)

    LOADSAVE = {"menu": "loadsave", "screen": True, "camera": "Cam_LoadSave", "controls": [
        {"name": "LoadSaveShot", "kind": "shot", "plate": ["P"]},
        {"name": "Load Game", "kind": "action", "plate": ["S"], "title": "Load",
         "command": "widgetcommand LoadSaveList loadgame"},
        {"name": "LoadSaveList", "kind": "saves", "plate": ["L"]}],
        "corners": [{"title": "Back", "side": "left", "command": "popmenu 0"}]}
    LOADSAVE_EXPORT = {"menu": "loadsave", "picture": [854, 480], "background": "background.png", "controls": {
        "LoadSaveShot": {"plate": [100, 60, 150, 110]}, "Load Game": {"plate": [300, 60, 100, 20]},
        "LoadSaveList": {"plate": [100, 200, 500, 150]}}}

    def test_loadsave(self):
        # the game finds the picture and the list by name (cl_uiloadsave.cpp): LoadSaveShot, LoadSaveList
        from remake import pak
        text = pak.screen_urc(self.load(self.LOADSAVE), self.LOADSAVE_EXPORT)
        shot, act, lst = self.block(text, "LoadSaveShot"), self.block(text, "Load Game"), self.block(text, "LoadSaveList")
        self.assertIn("\nrect 100 60 150 110\n", shot + "\n")
        self.assertIn("FakkLoadGameClass", text)
        self.assertIn("\nrect 100 200 500 150\n", lst + "\n")
        for line in ("rect 300 60 100 20", 'title "Load"', "font courier-20", 'stuffcommand "widgetcommand LoadSaveList loadgame"',
                     'hovershader "textures/menu_plus/remake/stamp_h"', 'shader "textures/menu_plus/clear"'):
            self.assertIn("\n" + line + "\n", act + "\n", line)
        stamp = json.loads(json.dumps(self.LOADSAVE)); del stamp["controls"][1]["title"]  # text in the picture
        stamped = self.block(pak.screen_urc(self.load(stamp), self.LOADSAVE_EXPORT), "Load Game")
        self.assertNotIn("title", stamped)
        self.assertIn("\nfgcolor 1 1 1 1\n", stamped)  # the button tints its hover picture with it
        stamp["controls"][1]["lit"] = ["SL"]  # its lit look rendered in Blender, cut by the pak
        lit = self.block(pak.screen_urc(self.load(stamp), self.LOADSAVE_EXPORT), "Load Game")
        self.assertIn('\nhovershader "textures/menu_plus/remake/loadsave_load_game"\n', lit)
        with self.assertRaises(ValueError):  # an action needs a command
            bad = json.loads(json.dumps(self.LOADSAVE)); del bad["controls"][1]["command"]
            self.load(bad)

    def test_model_credits_stay_above_back(self):
        # Back's plate is anchored 20 above the bottom, 30 tall: its top at y 430 of 480
        from remake import pak
        models = [{"title": f"Model {i}", "author": "a", "url": f"https://example.org/{i}", "license": "CC0 1.0"}
                  for i in range(11)]
        text = pak.credits_urc({"license_url": "https://example.org/by", "models": models[:10]})
        last = self.block(text, "source 9")
        y = int(re.search(r"anchor 30 (\d+) ", last).group(1))
        self.assertLessEqual(y + 16, 428)
        with self.assertRaises(ValueError):  # more than the board holds: a build error, not an overlap
            pak.credits_urc({"license_url": "https://example.org/by", "models": models})

    def test_real_model_credits_fit_the_game_charset(self):
        # the credits room is written in cp1252: a name outside it (Polish l-stroke) stops the build
        from remake import pak
        with open(os.path.join(HERE, "remake", "credits", "models.json"), encoding="utf-8") as f:
            pak.credits_urc(json.load(f))

    MPOPTIONS = {"menu": "mpoptions", "screen": True, "camera": "Cam_MPOptions", "controls": [
        {"name": "player name", "kind": "field", "plate": ["N"], "cvar": "ui_name"},
        {"name": "allies model name", "kind": "text", "plate": ["A"], "cvar": "ui_dm_playermodel"},
        {"name": "allies button", "kind": "action", "plate": ["B"], "title": "Allies Player Model",
         "command": "playermodel 0", "font": "verdana-14"},
        {"name": "allies model", "kind": "model", "plate": ["S"], "cvar": "ui_disp_playermodel",
         "anim": "americanselectionidle", "offset": "60 8 0", "angles": "10 180 0", "scale": 1.0}],
        "corners": [{"title": "Back", "side": "left", "command": "popmenu 0"}]}
    MPOPTIONS_EXPORT = {"menu": "mpoptions", "picture": [854, 480], "background": "background.png", "controls": {
        "player name": {"plate": [300, 20, 200, 24]}, "allies model name": {"plate": [100, 90, 200, 24]},
        "allies model": {"plate": [60, 150, 250, 300]}, "allies button": {"plate": [100, 60, 200, 20]}}}

    def test_player_options_controls(self):
        # the original's mpoptions: a name field, the model's name, the model itself drawn by the engine
        from remake import pak
        text = pak.screen_urc(self.load(self.MPOPTIONS), self.MPOPTIONS_EXPORT)
        field, name, model = (self.block(text, n) for n in ("player name", "allies model name", "allies model"))
        self.assertIn("Field", text.split('name "player name"')[0].rsplit("resource", 1)[1])
        for block, lines in ((field, ("rect 300 20 200 24", 'linkcvar "ui_name"')),
                             (name, ("rect 100 90 200 24", 'linkcvar "ui_dm_playermodel"')),
                             # the engine's model view is 30 by 30 degrees: a square rect, its height, same middle
                             (model, ("rect 35 150 300 300", 'linkcvar "ui_disp_playermodel"', "rendermodel 1",
                                      "modelanim americanselectionidle", 'modeloffset "60 8 0"',
                                      'modelangles "10 180 0"', "modelscale 1.0", "fgcolor 1 1 1 1"))):
            for line in lines:
                self.assertIn("\n" + line + "\n", block + "\n", line)
        self.assertIn("\nfont verdana-14\n", self.block(text, "allies button") + "\n")  # a smaller title fits
        felt = json.loads(json.dumps(self.MPOPTIONS)); felt["controls"][0]["ink"] = "light"  # on green felt
        self.assertIn("\nfgcolor 0.92 0.90 0.84 1\n", self.block(pak.screen_urc(self.load(felt), self.MPOPTIONS_EXPORT), "player name") + "\n")
        felt["controls"][0]["ink"] = "pink"
        with self.assertRaises(ValueError):
            self.load(felt)
        # a lit render with an engine title cannot work: the title's label would sit over the button and
        #  take the pointer (FindResponder picks the topmost widget), under it the hover hides the text
        lit = json.loads(json.dumps(self.MPOPTIONS)); lit["controls"][2]["lit"] = ["BL"]
        with self.assertRaises(ValueError):
            self.load(lit)
        with self.assertRaises(ValueError):  # a model needs its animation
            bad = json.loads(json.dumps(self.MPOPTIONS)); del bad["controls"][3]["anim"]
            self.load(bad)

    def test_select_model_art(self):
        # the frame's window shows the room's photo; around the frame stays clear
        from remake import pak
        frame = Image.new("RGBA", (200, 160), (0, 0, 0, 0))
        frame.paste((120, 60, 30, 255), (10, 10, 190, 130))       # the frame's body
        frame.paste((0, 0, 0, 0), (25, 25, 175, 115))            # its window
        room = Image.new("RGB", (854, 480), (200, 30, 30))
        art = pak.select_model_art(frame, room)
        self.assertEqual(art.size, (512, 512))
        self.assertEqual(art.getpixel((256, 180)), (200, 30, 30, 255))   # the window: the room
        self.assertEqual(art.getpixel((5, 5))[3], 0)                      # outside the frame: clear
        self.assertEqual(art.getpixel((256, 56))[:3], (120, 60, 30))      # the frame itself

    def test_select_model_urc(self):
        # the original's dialog (join a team in free-for-all), our backdrop, the engine's titles
        from remake import pak
        text = pak.select_model_urc()
        self.assertIn('menu "SelectFFAModel" 640 480 NONE 0', text)
        self.assertIn('shader "textures/menu_plus/remake/selectmodel"', text)
        for title, command in (("Allies", "join_team allies;popmenu 0"), ("Axis", "join_team axis;popmenu 0"),
                               ("Cancel", "popmenu 0")):
            block = text[text.index(f'title "{title}"') - 400:text.index(f'title "{title}"') + 400]
            self.assertIn(f'stuffcommand "{command}"', block, title)
        self.assertIn('title "Select Model"', text)
        self.assertEqual(text.count("rendermodel 1"), 2)

    def test_server_list_control(self):
        # the game's server lists, found by name: langamelist (LANGameClass), netgamelist (FAKKServerList)
        from remake import pak
        mapping = {"menu": "joinnetgame", "screen": True, "camera": "C", "controls": [
            {"name": "netgamelist", "kind": "servers", "class": "FAKKServerList", "plate": ["P"]}]}
        export = {"menu": "joinnetgame", "picture": [854, 480], "background": "background.png",
                  "controls": {"netgamelist": {"plate": [50, 40, 700, 300]}}}
        text = pak.screen_urc(self.load(mapping), export)
        self.assertIn("\nFAKKServerList\n{\nname \"netgamelist\"\nrect 50 40 700 300\n", text)
        with self.assertRaises(ValueError):  # only the game's two list classes
            bad = json.loads(json.dumps(mapping)); bad["controls"][0]["class"] = "Button"
            self.load(bad)

    BRIEFING = {"menu": "briefingroom", "screen": True, "camera": "Cam_Briefing", "sign_cvar": "ui_briefingsign",
                "sign_plate": ["Sign"], "signs": {"briefing": "Briefing"}, "controls": [
        {"name": "arzew", "kind": "mission", "plate": ["A"], "shown": ["A_Name"], "lit": ["A_Red"],
         "command": "pushmenu mission1difficulty", "text": "Lighting The Torch"},
        {"name": "trondheim", "kind": "mission", "plate": ["T"], "shown": ["T_Name"], "lit": ["T_Red"], "cvar": "g_m2l1",
         "command": "pushmenu mission2difficulty", "text": "Scuttling The U-529"}],
        "corners": [{"title": "Back", "side": "left", "command": "popmenu 0"}]}
    BRIEFING_EXPORT = {"menu": "briefingroom", "picture": [854, 480], "background": "background.png",
                       "plates": {"sign": [600, 20, 200, 50]}, "controls": {
        "arzew": {"plate": [300, 380, 60, 20], "image": "picture_arzew.png", "lit_image": "lit_arzew.png"},
        "trondheim": {"plate": [400, 80, 90, 20], "image": "picture_trondheim.png", "lit_image": "lit_trondheim.png"}}}

    def test_briefing_missions(self):
        # a mission shows on the map when unlocked (g_mXl1; the first always), red under the pointer,
        # and names itself on the sign
        from remake import pak
        text = pak.screen_urc(self.load(self.BRIEFING), self.BRIEFING_EXPORT)
        name, button = self.block(text, "trondheim"), self.block(text, "trondheim button")
        for line in ('shader "textures/menu_plus/remake/briefingroom_trondheim"', 'enabledcvar "g_m2l1"', "rect 400 80 90 20"):
            self.assertIn("\n" + line + "\n", name + "\n", line)
        for line in ('hovershader "textures/menu_plus/remake/briefingroom_trondheim_h"', 'enabledcvar "g_m2l1"',
                     'stuffcommand "pushmenu mission2difficulty"', 'hovercommand "set ui_briefingsign trondheim"',
                     'shader "textures/menu_plus/clear"'):
            self.assertIn("\n" + line + "\n", button + "\n", line)
        self.assertNotIn("enabledcvar", self.block(text, "arzew"))
        sign = self.block(text, "mission sign")
        for line in ("rect 600 20 200 50", 'linkcvar "ui_briefingsign"', 'linkstring "trondheim" "Scuttling The U-529"',
                     'linkstring "briefing" "Briefing"'):   # what the doors set before opening it
            self.assertIn("\n" + line + "\n", sign + "\n", line)
        with self.assertRaises(ValueError):  # a mission needs its lit look
            bad = json.loads(json.dumps(self.BRIEFING)); del bad["controls"][0]["lit"]
            self.load(bad)

    def test_screen_as_include(self):
        # the briefing slides share ui/missionbriefingback.inc: a screen can be just that background
        from remake import pak
        mapping = {"menu": "missionbriefingback", "screen": True, "include": True, "camera": "C", "controls": []}
        export = {"menu": "missionbriefingback", "picture": [854, 480], "background": "background.png", "controls": {}}
        text = pak.screen_urc(self.load(mapping), export)
        self.assertNotIn('menu "', text)
        self.assertNotIn("end.", text)
        self.assertIn('shader "textures/menu_plus/remake/missionbriefingback_l"', text)

    def test_briefing_slide(self):
        # the game stretches a 640x480 menu to the screen: the slide is placed in picture units instead,
        # in the 4:3 middle of the slides' background (the original's 96,74 456x344 there)
        from remake import pak
        text = pak.slide_urc("briefing1b", "sabotage", 854)
        slide = self.block(text, "slide")
        for line in ("rect 203 74 456 344", "cover 854 480", 'shader "sabotage"'):
            self.assertIn("\n" + line + "\n", slide + "\n", line)
        self.assertIn('\ninclude "ui/missionbriefingback.inc"\n', text)
        first = pak.slide_urc("mission1_briefing", "briefing1a", 854, "spmap m1l1")
        self.assertIn('stuffcommand "spmap m1l1"', first)
        self.assertIn('title "Skip Briefing"', first)

    def test_credits_on_the_chalkboard(self):
        # with the board's export: its picture behind, the credits in chalk on the slate, in picture units
        from remake import pak
        models = [{"title": f"Model {i}", "author": "a", "url": f"https://example.org/{i}", "license": "CC0 1.0"}
                  for i in range(10)]
        export = {"menu": "remake_credits", "picture": [854, 480], "background": "background.png", "controls": {},
                  "plates": {"slate": [140, 40, 574, 380]}}
        text = pak.credits_urc({"license_url": "https://example.org/by", "models": models}, export)
        self.assertIn('shader "textures/menu_plus/remake/remake_credits_l"', text)
        title, last = self.block(text, "title"), self.block(text, "source 9")
        for block in (title, last):
            self.assertIn("\ncover 854 480\n", block + "\n")
            self.assertIn("\nfont pluschalk-32\n", block + "\n")
        x, y, w, h = (int(v) for v in re.search(r"\nrect (\d+) (\d+) (\d+) (\d+)", last).groups())
        self.assertTrue(140 <= x and x + w <= 714 and 40 <= y and y + h <= 420, (x, y, w, h))   # on the slate
        self.assertIn('stuffcommand "popmenu 0"', text)

    def test_real_medal_case(self):
        case = hotspots.load_mapping(os.path.join(HERE, "remake", "medals.json"))
        self.assertEqual({c["cvar"] for c in case["controls"]},  # the original's
                         {f"g_medal{i}" for i in range(6)} | {f"g_eogmedal{i}" for i in range(3)})

    def test_slider_multiplier(self):
        # a volume shows as a percentage: showvalue's multiplier, as in the Plus audio tab
        from remake import pak
        screen = json.loads(json.dumps(self.SCREEN))
        next(c for c in screen["controls"] if c["kind"] == "slider").update(format="%.0f%%", multiplier=100)
        self.assertIn('\nshowvalue "%.0f%%" 100\n', pak.screen_urc(self.load(screen), self.EXPORT))

    def block(self, text, name):
        return text[text.index(f'name "{name}"'):].split("\n}", 1)[0]

    def test_screen_urc(self):
        from remake import pak
        text = pak.screen_urc(self.load(self.SCREEN), self.EXPORT)
        self.assertIn('menu "video_options"', text)
        self.assertIn("cover 854 480", text)
        knob, plate = self.block(text, "resolution knob"), self.block(text, "resolution")
        for block in (knob, plate):  # both open the same list
            self.assertIn("PulldownMenuContainer", text)
            self.assertIn('addpopup "MENU" "1920x1080" command "set r_mode -1; set r_customwidth 1920"', block)
        self.assertIn("rect 100 100 20 20", knob)
        self.assertNotIn("linkcvar", knob)
        self.assertIn("rect 125 100 60 12", plate)
        self.assertIn('linkcvar "r_mode"', plate)  # the plate shows the value: every set must match
        # each item gives its own value of the cvar: a label maps it, as the original did (the other
        # sets need not match), under a pulldown without a value
        label, pull = self.block(text, "model detail value"), self.block(text, "model detail")
        # its text as big and as far in as a pulldown's: 6 units in, a rect 28% taller (labels fit 50% of it)
        for line in ("rect 131 128 54 16", 'linkcvar "r_lodscale"', 'linkstring "0.35" "Low"', 'linkstring "1.1" "Highest"'):
            self.assertIn("\n" + line + "\n", label + "\n", line)
        self.assertNotIn("linkcvar", pull)
        self.assertLess(text.index('name "model detail value"'), text.index('name "model detail"\n'))  # under it
        slider = self.block(text, "brightness")
        for line in ("rect 302 202 76 6", 'linkcvar "r_gamma"', "setrange 0.5 3.0", "stepsize 0.1", 'showvalue "%.1f"'):
            self.assertIn("\n" + line + "\n", slider + "\n", line)
        check = self.block(text, "wall decals")
        for line in ("rect 500 150 82 10", "fgcolor 1 1 1 1", 'linkcvar "cg_marks_add"', 'checked_shader "textures/menu_plus/remake/lamp_on"',
                     'unchecked_shader "textures/menu_plus/clear"'):
            self.assertIn("\n" + line + "\n", check + "\n", line)
        self.assertIn("anchor -1 -1 152 20", self.block(text, "Defaults"))  # next to Apply
        self.assertIn("anchor -1 -1 12 20", self.block(text, "Apply"))

    def test_stamp_highlight_art(self):
        from remake import pak
        img = pak.stamp_h()
        self.assertEqual(img.mode, "RGBA")
        self.assertEqual(img.getpixel((0, 0))[3], 0)  # soft: clear at its edge
        r, g, b, a = img.getpixel((img.width // 2, img.height // 2))
        self.assertTrue(0 < a < 255 and r > 200 and g < 60 and b < 60)  # deepens the stamp's red ink

    def test_lamp_on_art(self):
        from remake import pak
        lamp = pak.lamp_on()
        self.assertEqual(lamp.size, (64, 64))
        self.assertEqual(lamp.mode, "RGBA")
        self.assertEqual(lamp.getpixel((0, 0))[3], 0)  # a glow on transparency
        r, g, b, a = lamp.getpixel((32, 32))
        self.assertTrue(a > 200 and r > g > b, (r, g, b, a))  # amber, lit


class Mappings(unittest.TestCase):
    """The hotspots agreed with the maintainer (spec 2026-11-17-remake-menu-design.md)."""
    AGREED = {
        "main": {"sign": (None, None, None),
                 "new game": ("set ui_briefingsign briefing;pushmenu briefingroom", "newgame_sign", "New Game"),
                 "briefing": ("set ui_briefingsign briefing;pushmenu briefingroom", "briefingroom_sign", "Briefing"),
                 "multiplayer": ("pushmenu multiplayer", "multiplayer_sign", "Multiplayer"),
                 "options": ("pushmenu options_main", "options_sign", "Options"),
                 "records": ("pushmenu war_records", "warrecords_sign", "War Records"),
                 "credits": ("spmap credits", "credits_sign", "Credits"),
                 "model credits": ("pushmenu remake_credits", "modelcredits_sign", "Model Credits")},
        "options_main": {"sign": (None, None, None),
                         "advanced": ("ui_marklatched; pushmenu advancedoptions", "advanced_sign", "Advanced"),
                         "audio": ("ui_marklatched; pushmenu audio_options", "audio_sign", "Audio"),
                         "controls": ("pushmenu controls", "controls_sign", "Controls"),
                         "video": ("ui_marklatched; pushmenu video_options", "video_sign", "Video"),
                         "plus": ("pushmenu plus_options", "plus_sign", "Plus Options")},
        "war_records": {"sign": (None, None, None),
                        "personal records": ("pushmenu medals", "personalrecords_sign", "Personal Records"),
                        "loadsave": ("pushmenu_sp loadsave;pushmenu_dm loadsave_mp", "loadsave_sign", "Load / Save")},
    }
    SIGN_CVARS = {"main": "ui_signshader", "options_main": "ui_optionshader", "war_records": "ui_recordsign"}

    def test_agreed_mapping(self):
        for menu, agreed in self.AGREED.items():
            mapping = hotspots.load_mapping(os.path.join(HERE, "remake", menu + ".json"))
            self.assertEqual(mapping["menu"], menu)
            self.assertEqual(mapping["sign_cvar"], self.SIGN_CVARS[menu])
            got = {h["name"]: (h.get("command"), h.get("sign"), h.get("text")) for h in mapping["hotspots"]}
            self.assertEqual(got, agreed, menu)
            self.assertEqual(list(got), list(agreed), menu)  # board first, then the agreed order


@unittest.skipUnless(Image, "needs Pillow")
class BuildRemake(unittest.TestCase):
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
        global build_pk3, build_remake
        import build_pk3
        from remake import pak as build_remake
        cls.tmp = tempfile.TemporaryDirectory()
        mappings = os.path.join(cls.tmp.name, "mappings")
        os.makedirs(mappings)
        write_json(mappings, "main.json", cls.MAPPING)
        write_json(mappings, "options_main.json", dict(cls.MAPPING, menu="options_main"))
        write_json(mappings, "video_options.json", Screens.SCREEN)
        write_json(mappings, "medals.json", Screens.MEDALS)
        write_json(mappings, "briefingroom.json", Screens.BRIEFING)
        write_json(mappings, "remake_credits.json", {"menu": "remake_credits", "screen": True, "credits": True,
                                                      "camera": "C", "slate_plate": ["S"], "controls": []})
        os.makedirs(os.path.join(mappings, "briefing"))
        write_json(os.path.join(mappings, "briefing"), "slides.json", {"slides": {"briefing1b": "sabotage"},
                                                                       "skip": {"mission1_briefing": ["briefing1a", "spmap m1l1"]}})
        write_json(mappings, "missionbriefingback.json", {"menu": "missionbriefingback", "screen": True, "include": True,
                                                           "camera": "C", "controls": []})
        stamped = json.loads(json.dumps(Screens.LOADSAVE)); stamped["controls"][1]["lit"] = ["SL"]; del stamped["controls"][1]["title"]
        write_json(mappings, "loadsave.json", stamped)
        os.makedirs(os.path.join(mappings, "credits"))
        write_json(os.path.join(mappings, "credits"), "models.json", {"license_url": "https://example.org/by", "models": [
            {"title": "Old Phone", "author": "gorzi", "url": "https://example.org/phone", "license": "CC BY 4.0"},
            {"title": "Fan", "author": "cody", "url": "https://example.org/fan", "license": "CC BY 4.0"}]})
        export = os.path.join(cls.tmp.name, "export")
        build_remake.fake_export(mappings, export, cls.RECTS)
        os.remove(os.path.join(export, "options_main", "options_main.json"))  # a screen not exported yet
        cls.remake = os.path.join(cls.tmp.name, "zzzz-plus-remake.pk3")
        cls.stderr = io.StringIO()
        with redirect_stderr(cls.stderr):
            assert build_pk3.main(["--out", os.path.join(cls.tmp.name, "zzz-plus.pk3"), "--skip-fonts",
                                   "--remake", export, "--remake-mappings", mappings]) == 0
        cls.zip = zipfile.ZipFile(cls.remake)

    @classmethod
    def tearDownClass(cls):
        cls.zip.close()
        cls.tmp.cleanup()

    def read(self, name):
        return self.zip.read(name).decode("cp1252")

    def block(self, name):
        text = self.read("ui/main.urc")
        return text[text.index(f'name "{name}"'):].split("\n}", 1)[0]

    def test_remake_pak_contents(self):
        # the sign font too: plussign-32 is not in the game, and a zzz-plus.pk3 without it (--skip-fonts,
        # an older release) would stop the menu with "Couldn't load font"
        self.assertEqual(set(self.zip.namelist()), {
            "ui/main.urc", "textures/menu_plus/remake/main_l.jpg", "textures/menu_plus/remake/main_r.jpg",
            "textures/menu_plus/remake/main_a_b_h.jpg", "textures/menu_plus/remake/main_c_h.jpg",
            "fonts/plussign-32.RitualFont", "gfx/fonts/plussign-32.tga", "ui/remake_credits.urc",
            # the credits board's chalk font (Cabin Sketch, OFL: its licence goes with it)
            "fonts/pluschalk-32.RitualFont", "gfx/fonts/pluschalk-32.tga", "fonts/pluschalk-32-OFL.txt",
            "textures/menu_plus/remake/remake_credits_l.jpg", "textures/menu_plus/remake/remake_credits_r.jpg",
            "textures/menu_plus/remake/button.jpg", "textures/menu_plus/remake/button_h.jpg",
            "ui/video_options.urc", "textures/menu_plus/remake/video_options_l.jpg",
            "textures/menu_plus/remake/video_options_r.jpg", "textures/menu_plus/remake/lamp_on.tga",
            "textures/menu_plus/remake/stamp_h.tga",
            "ui/medals.urc", "textures/menu_plus/remake/medals_l.jpg", "textures/menu_plus/remake/medals_r.jpg",
            "textures/menu_plus/remake/medals_silver_star.jpg",
            "ui/loadsave.urc", "textures/menu_plus/remake/loadsave_l.jpg", "textures/menu_plus/remake/loadsave_r.jpg",
            "textures/menu_plus/remake/loadsave_load_game.jpg",
            "ui/briefingroom.urc", "textures/menu_plus/remake/briefingroom_l.jpg", "textures/menu_plus/remake/briefingroom_r.jpg",
            "textures/menu_plus/remake/briefingroom_arzew.jpg", "textures/menu_plus/remake/briefingroom_arzew_h.jpg",
            "textures/menu_plus/remake/briefingroom_trondheim.jpg", "textures/menu_plus/remake/briefingroom_trondheim_h.jpg",
            "ui/missionbriefingback.inc", "textures/menu_plus/remake/missionbriefingback_l.jpg",
            "textures/menu_plus/remake/missionbriefingback_r.jpg", "ui/briefing1b.urc", "ui/mission1_briefing.urc"})

    def test_medal_picture_is_cut_from_a_full_render(self):
        # a medal is rendered over the whole frame (a border render lit the velvet differently) and the
        # pak cuts its rect: fake_export's medal renders are white with a black rect
        img = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/remake/medals_silver_star.jpg"))).convert("RGB")
        self.assertLess(sum(img.getpixel((img.width // 2, img.height // 2))), 60)

    def test_lit_stamp_is_cut_from_a_full_render(self):
        img = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/remake/loadsave_load_game.jpg"))).convert("RGB")
        self.assertLess(sum(img.getpixel((img.width // 2, img.height // 2))), 60)

    def test_green_button_plates(self):
        # the classic green plates, drawn here (not the game's art): the hover one lighter, no text on them
        plain, hover = (Image.open(io.BytesIO(self.zip.read(f"textures/menu_plus/remake/{n}.jpg"))).convert("RGB")
                        for n in ("button", "button_h"))
        self.assertEqual(plain.size, (256, 64))
        r, g, b = plain.getpixel((128, 32))
        self.assertTrue(g > r + 15 and g > b + 5, (r, g, b))  # green
        self.assertGreater(sum(hover.getpixel((128, 32))), sum(plain.getpixel((128, 32))) + 60)

    def test_crops_power_of_two(self):
        sides = {2 ** n for n in range(4, 12)}
        for name in ("main_a_b_h", "main_c_h"):
            img = Image.open(io.BytesIO(self.zip.read(f"textures/menu_plus/remake/{name}.jpg")))
            self.assertIn(img.width, sides, name)
            self.assertIn(img.height, sides, name)
        self.assertEqual(Image.open(io.BytesIO(self.zip.read("textures/menu_plus/remake/main_l.jpg"))).size, (2048, 2048))

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
        order = re.findall(r'^name "([^"]+)"', build_remake.urc(mapping, export), re.M)
        self.assertLess(order.index("big"), order.index("small"), order)

    def test_urc_hotspot(self):
        block = self.block("c")
        for line in ("rect 823 276 3 183", "scalecvar ui_plusscale", "cover 1152 480",
                     'shader "textures/menu_plus/clear"', 'hovershader "textures/menu_plus/remake/main_c_h"',
                     'stuffcommand "pushmenu c;set x 1"', 'hovercommand "set ui_signshader c_sign"'):
            self.assertIn("\n" + line + "\n", block + "\n", line)

    def test_corner_widget_name(self):
        # the game enables "disconnect" by name (UI_MultiplayerMenuWidgetsUpdate), case-sensitive
        from remake import pak
        lines = pak.corner_button("Disconnect", "right", "disconnect", widget="disconnect")
        self.assertIn('name "disconnect"', lines)
        self.assertIn('title "Disconnect"', lines)

    def test_urc_sign_and_corners(self):
        sign = self.block("sign")
        for line in ("rect 681 38 144 72", "cover 1152 480", 'linkcvar "ui_signshader"', "font plussign-32",
                     "textalign center", "fgcolor 0.95 0.92 0.84 1",
                     'linkstring "a_sign" "A B"\nlinkstring "c_sign" "Ç"'):
            self.assertIn("\n" + line + "\n", sign + "\n", line)
        self.assertNotIn("linkcvartoshader", sign)
        for name, anchor in (("Back to game", "anchor 12 -1 -1 20"), ("Quit", "anchor -1 -1 12 20")):
            block = self.block(name)
            for line in (anchor, "rect 0 0 128 30", 'shader "textures/menu_plus/remake/button"',
                         'hovershader "textures/menu_plus/remake/button_h"', "textalign center", "font facfont-20",
                         "fgcolor 1 1 1 1", f'title "{name}"'):
                self.assertIn("\n" + line + "\n", block + "\n", (name, line))
        self.assertIn('stuffcommand "quit"', self.block("Quit"))

    def test_model_credits_menu(self):
        # CC BY: each model's title, author, source and licence, and a way back
        text = self.read("ui/remake_credits.urc")
        self.assertIn('menu "remake_credits"', text)
        for line in ('title "Old Phone - gorzi"', 'title "CC BY 4.0  https://example.org/phone"',
                     'title "Fan - cody"', 'stuffcommand "popmenu 0"', 'shader "textures/menu_plus/remake/button"'):
            self.assertIn("\n" + line + "\n", text, line)
        self.assertIn("https://example.org/by", text)

    def test_missing_screen_skipped(self):
        self.assertNotIn("ui/options_main.urc", self.zip.namelist())
        self.assertIn("remake: no export for options_main", self.stderr.getvalue())

    def test_hover_lights_the_masked_object_only(self):
        # fake_export: background (40, 60, 80); the mask of "a b" is white in its left half
        crop = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/remake/main_a_b_h.jpg"))).convert("RGB")
        w, h = crop.size
        lit, plain = crop.getpixel((w // 4, h // 2)), crop.getpixel((w - 4, h // 2))
        for got, base in zip(plain, (40, 60, 80)):
            self.assertAlmostEqual(got, base, delta=4)
        self.assertGreater(sum(lit), sum((40, 60, 80)) * 1.15)
        self.assertGreater(lit[0] - lit[2], (40 - 80) + 4)  # warmer than the background (+7 expected)

    def test_hover_with_lights_is_the_lit_render(self):
        # fake_export: the lit render of "c" (a hotspot with lights) is (200, 180, 150)
        crop = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/remake/main_c_h.jpg"))).convert("RGB")
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
        out = build_remake.zone_lit(background, lamp, mask)
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
            list(build_remake.files(mappings, broken))

    def test_zone_lit_frame_stops_at_the_frame(self):
        # "glow": "frame" (a door): the frame and the opening it encloses lit, no light on the wall
        background, lamp = Image.new("RGB", (200, 100), (10, 10, 10)), Image.new("RGB", (200, 100), (210, 210, 210))
        mask = Image.new("L", (200, 100), 0)
        mask.paste(255, (60, 10, 140, 20))   # head
        mask.paste(255, (60, 10, 70, 100))   # left jamb
        mask.paste(255, (130, 10, 140, 100))  # right jamb
        out = build_remake.zone_lit(background, lamp, mask, frame=True)
        self.assertEqual(out.getpixel((100, 60)), (210, 210, 210))  # the opening: lit
        self.assertEqual(out.getpixel((65, 60)), (210, 210, 210))   # the jamb: lit
        # the wall: a short soft edge right at the frame, nothing further out
        self.assertTrue(15 < out.getpixel((58, 60))[0] < 200)
        self.assertLess(out.getpixel((56, 60))[0], 120)
        self.assertLess(out.getpixel((40, 60))[0], 15)
        self.assertLess(out.getpixel((100, 2))[0], 15)

    def test_background_split_on_a_unit(self):
        # an odd picture width: the left tile holds the urc's 427 left units (1281 px at 3 px a unit)
        self.assertEqual(build_remake.halves(2565, 1440, 855), ((0, 0, 1281, 1440), (1281, 0, 2565, 1440)))
        with self.assertRaisesRegex(ValueError, "2560x1440"):
            build_remake.halves(2560, 1440, 853)

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
            build_pk3.write_remake(out, broken, mappings)
        with open(out, "rb") as f:
            self.assertEqual(f.read(), b"old pak")
        self.assertEqual([n for n in os.listdir(self.tmp.name) if n.startswith("keep.pk3")], ["keep.pk3"])

    def test_modern_pak_unchanged(self):
        with zipfile.ZipFile(os.path.join(self.tmp.name, "zzz-plus.pk3")) as modern:
            self.assertFalse([n for n in modern.namelist() if "remake" in n])


if __name__ == "__main__":
    unittest.main()
