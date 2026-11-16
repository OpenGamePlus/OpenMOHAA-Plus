# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Headless client regression tests (need game data: OMOH_GAME_DIR).

The client runs with SDL's offscreen video driver and OpenAL's null backend: no window, no sound.
Run: OMOH_GAME_DIR=<GAME_DIR> python3 -m unittest discover -s tests -v
"""

import glob
import tempfile
import re
import statistics
import sys
import subprocess
import shutil
import functools
import http.server
import threading
import os
import struct
import time
import unittest
import zipfile

import omoh
from omoh import GameTestCase, require_game, game_dir


def read_tga(path):
    """Uncompressed 24/32-bit TGA -> (width, height, rows of (r, g, b) tuples, top row first)."""
    with open(path, "rb") as f:
        data = f.read()
    id_len, cmap_type, img_type = data[0], data[1], data[2]
    if img_type != 2 or cmap_type != 0:
        raise ValueError(f"unsupported TGA type {img_type}")
    width, height = struct.unpack("<HH", data[12:16])
    bpp, desc = data[16], data[17]
    step = bpp // 8
    pixels = data[18 + id_len:]
    rows = []
    for y in range(height):
        row = pixels[y * width * step:(y + 1) * width * step]
        rows.append([(row[x + 2], row[x + 1], row[x]) for x in range(0, width * step, step)])
    if not desc & 0x20:  # origin at the bottom
        rows.reverse()
    return width, height, rows


def bright_pixels(path, x0, x1, y0, y1, threshold=200):
    """Count near-white pixels in a region given as fractions of the screen size."""
    width, height, rows = read_tga(path)
    count = 0
    for row in rows[int(y0 * height):int(y1 * height)]:
        for r, g, b in row[int(x0 * width):int(x1 * width)]:
            if r > threshold and g > threshold and b > threshold:
                count += 1
    return count


@require_game
class ClientSmoke(GameTestCase):
    def test_map_loads_and_vid_restart(self):
        c = self.client("+devmap", "training")
        c.wait_for(r"^Server: training")
        time.sleep(10)
        c.send("vid_restart")
        c.wait_for(r"finished CL_Vid_Restart_f", timeout=60)
        c.send("devmap dm/mohdm1")
        c.wait_for(r"^Server: dm/mohdm1", timeout=120)
        self.assertEqual(c.quit(), 0)
        self.assertRegex(c.log(), r"Client Initialization Complete ----- \d+ ms")  # was negative

    @unittest.skipUnless(shutil.which("cc") and os.name == "posix", "needs a C compiler on POSIX")
    def test_map_change_with_resident_cgame_module(self):
        # #918 on the client side: emulate musl, where dlclose() never unloads the library
        shim_dir = tempfile.mkdtemp(prefix="omoh-shim-")
        self.addCleanup(shutil.rmtree, shim_dir, True)
        src = os.path.join(shim_dir, "nodlclose.c")
        lib = os.path.join(shim_dir, "nodlclose.so")
        with open(src, "w") as f:
            f.write("int dlclose(void *handle) { (void)handle; return 0; }\n")
        subprocess.run(["cc", "-shared", "-fPIC", "-o", lib, src], check=True)
        c = self.client("+devmap", "dm/mohdm1", env={"LD_PRELOAD": lib})
        loaded = r"Sys_GetCGameAPI\(cgame\.so\): succeeded"
        c.wait_for(loaded, timeout=120)
        for n, level in enumerate(("dm/mohdm2", "dm/mohdm1"), start=2):
            time.sleep(3)
            c.send("devmap " + level)
            c.wait_for(loaded, count=n, timeout=120)
        time.sleep(3)
        self.assertEqual(c.quit(), 0)


@require_game
class SaveLoad(GameTestCase):
    def test_stopwatch_survives_loading_a_save(self):
        # upstream #916: the HUD stopwatch (left edge, mid height) must be drawn after a load
        self.home.write("maps/training.scr", """main:
	level waittill spawn
	$player nodamage
	println "T916 spawned"
	wait 8
	$player stopwatch 120
	println "T916 started"
end
""")
        region = (0.0, 0.12, 0.38, 0.62)
        c = self.client("+set", "developer", "1", "+devmap", "training")
        c.wait_for(r"T916 spawned", timeout=120)
        time.sleep(3)
        c.send("screenshot t916_none")
        c.wait_for(r"T916 started", timeout=30)
        time.sleep(3)
        c.send("screenshot t916_before")
        time.sleep(2)
        c.send("savegame t916")
        c.wait_for(r"Saving to t916", timeout=30)
        time.sleep(3)
        mark = len(c.log())
        c.send("loadgame t916")
        c.wait_for(r"Loading game\.\.\.t916", timeout=60, start=mark)
        time.sleep(15)
        c.send("screenshot t916_after")
        time.sleep(3)
        self.assertEqual(c.quit(), 0)
        shots = {n: self.home.file(f"screenshots/t916_{n}.tga") for n in ("none", "before", "after")}
        counts = {n: bright_pixels(p, *region) for n, p in shots.items()}
        self.assertGreater(counts["before"], counts["none"] + 300, counts)
        self.assertGreater(counts["after"], counts["none"] + 300, f"stopwatch missing after load: {counts}")


@require_game
class Sounds(GameTestCase):
    def test_alias_without_wav_extension_loads(self):
        # upstream #589: impact_playerleavewater1 points to a file name without ".wav"
        self.home.write("maps/training.scr", """main:
	level waittill spawn
	$player nodamage
	wait 2
	println "T589 playing"
	$player playsound impact_playerleavewater1
end
""")
        c = self.client("+set", "developer", "1", "+devmap", "training")
        c.wait_for(r"T589 playing", timeout=120)
        c.wait_for(r"S_LoadSound: sound/characters/body_mvmtwater_01", timeout=20)
        time.sleep(3)
        self.assertEqual(c.quit(), 0)
        self.assertNotIn("Couldn't load sound: sound/characters/body_mvmtwater_01", c.log())


@require_game
class NoSound(GameTestCase):
    def test_intro_movie_without_sound(self):
        # the intro movie set up its audio through OpenAL even when sound never started: crash at startup
        if not glob.glob(os.path.join(game_dir(), "main", "video", "[Ee][Aa]logo.[Rr]o[Qq]")):
            self.skipTest("the game data has no intro movie (main/video/EAlogo.RoQ)")
        c = self.client("+set", "s_initsound", "0", "+set", "cl_playintro", "1")   # the helper turns the intro off
        c.wait_for(r"Loading inventory", timeout=60)
        time.sleep(10)                     # the intro plays; the console takes no input meanwhile
        self.assertIsNone(c.proc.poll(), c.log()[-2000:])
        c.kill()


@require_game
class Hrtf(GameTestCase):
    def test_s_hrtf_forces_hrtf(self):
        c = self.client("+set", "s_hrtf", "1")
        c.wait_for(r"OpenAL: HRTF (enabled|disabled)", timeout=60)
        self.assertEqual(c.quit(), 0)
        self.assertRegex(c.log(), r"OpenAL: HRTF enabled \(")

    def test_hrtf_off_by_default(self):
        # speakers: game configs may pick headphones (s_speaker_type 1), which lets OpenAL use HRTF
        c = self.client("+set", "s_speaker_type", "0")
        c.wait_for(r"OpenAL: HRTF (enabled|disabled)", timeout=60)
        self.assertEqual(c.quit(), 0)
        self.assertIn("OpenAL: HRTF disabled", c.log())


@require_game
class FrameRate(GameTestCase):
    def test_maxfps_caps_at_the_requested_rate(self):
        # upstream #530: 1000 / com_maxfps used to truncate (85 -> ~90 fps)
        c = self.client("+set", "com_maxfps", "85", "+set", "com_maxfpsUnfocused", "0",
                        "+set", "com_maxfpsMinimized", "0", "+set", "r_swapInterval", "0",
                        "+set", "com_speeds", "1")
        c.wait_for(r"^frame:", count=200, timeout=120)
        time.sleep(3)
        n0, t0 = c.log().count("\nframe:"), time.time()
        time.sleep(10)
        n1, t1 = c.log().count("\nframe:"), time.time()
        c.quit()
        fps = (n1 - n0) / (t1 - t0)
        if fps < 70:
            self.skipTest(f"machine too slow to reach 85 fps ({fps:.1f})")
        self.assertAlmostEqual(fps, 85, delta=3)


@require_game
class Disconnect(GameTestCase):
    def test_client_shows_the_disconnect_reason(self):
        s = self.server("+set", "g_gametype", "1", "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = omoh.client(client_home, "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        s.wait_for(r"entered the battle", timeout=120)
        s.send("kicknum 0")
        # kicks arrive as a "droperror" packet; mid-connection drops (unpure client) as a reliable
        # "disconnect" command: both must leave the reason in com_errorMessage
        c.wait_for(r"Server disconnected: \S|Server dropped connection\. Reason: \S", timeout=30)
        c.send("com_errorMessage")
        c.wait_for(r'"com_errorMessage" is:"[^"]+"', timeout=10)
        c.quit()
        self.assertEqual(s.quit(), 0)


@require_game
class FastServer(GameTestCase):
    def test_client_plays_on_a_40hz_server(self):
        s = self.server("+set", "sv_fps", "40", "+set", "g_gametype", "1", "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = omoh.client(client_home, "+set", "snaps", "40", "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        s.wait_for(r"entered the battle", timeout=120)
        time.sleep(15)
        mark = len(s.log())
        s.send("status")
        status = s.wait_for(r"^map: dm/mohdm1", timeout=20, start=mark)[mark:]
        c.quit()
        self.assertEqual(s.quit(), 0)
        self.assertRegex(status, r"\n\s*0\s+\d+\s+\d+\s")      # client 0 still connected
        for bad in ("ERROR:", "Server disconnected", "Server dropped connection"):
            self.assertNotIn(bad, c.log())

    # upstream #793: configstrings registered mid-game (here 140 long sound names) used to exceed
    # the client's gamestate buffer and drop it with "MAX_GAMESTATE_CHARS exceeded"
    FILL_SCRIPT = """main:
    level waittill spawn
    local.go = getcvar "plus_gs_fill"
    while (local.go != "1") {
        wait 0.5
        local.go = getcvar "plus_gs_fill"
    }
    for (local.i = 0; local.i < 140; local.i++) {
        cache ("sound/plus_test/""" + "gamestate_fill_" * 12 + """" + local.i + ".wav")
    }
    println "PLUS_GS_FILLED"
end
"""

    def test_client_stays_when_configstrings_outgrow_the_gamestate(self):
        self.home.write("maps/dm/mohdm1.scr", self.FILL_SCRIPT)
        s = self.server("+set", "developer", "1", "+set", "g_gametype", "1", "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = omoh.client(client_home, "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        s.wait_for(r"entered the battle", timeout=120)
        s.send("set plus_gs_fill 1")
        s.wait_for(r"PLUS_GS_FILLED", timeout=30)
        time.sleep(5)
        mark = len(s.log())
        s.send("status")
        status = s.wait_for(r"^map: dm/mohdm1", timeout=20, start=mark)[mark:]
        c.quit()
        self.assertEqual(s.quit(), 0)
        self.assertNotIn("MAX_GAMESTATE_CHARS exceeded", c.log())
        self.assertRegex(status, r"\n\s*0\s+\d+\s+\d+\s")      # client 0 still connected
        self.assertTrue("would exceed MAX_GAMESTATE_CHARS" in s.log(), "server did not refuse a configstring")

    def _fire_intervals(self, sv_fps, weapon):
        home = omoh.Home()
        self.addCleanup(home.cleanup)
        c = omoh.client(home, "+set", "developer", "1", "+set", "sv_fps", str(sv_fps), "+set", "g_showweaponfire", "1",
                        "+set", "g_gametype", "2", "+set", "sv_maxclients", "2", "+devmap", "dm/mohdm1")
        self.games.append(c)
        c.wait_for(r"==== InitGame ====", timeout=120)
        time.sleep(10)
        c.send(f"primarydmweapon {weapon}")
        c.send("join_team allies")
        time.sleep(6)
        c.send("popmenu 0")
        c.send("popmenu 0")
        time.sleep(2)
        c.send("+attack")
        time.sleep(2)
        c.send("-attack")
        time.sleep(1)
        self.assertEqual(c.quit(), 0)
        times = [int(t) for t in re.findall(r"weapon fire: .* at (\d+) ms", c.log())]
        self.assertGreater(len(times), 5)
        return sorted({b - a for a, b in zip(times, times[1:])})

    def test_40hz_keeps_the_20hz_fire_rate(self):
        # the fire delay is checked once per frame: a 20 Hz server rounds it up to 50 ms steps
        self.assertEqual(self._fire_intervals(40, "mg"), [150])    # BAR: 400 rpm, not 480
        self.assertEqual(self._fire_intervals(40, "smg"), [100])   # Thompson: 600 rpm


@require_game
class PureServer(GameTestCase):
    MENU_FILES = ("ui/connecting.urc", "ui/errormessage.urc", "textures/mohmenu/internet.tga")

    def _extra_pak(self, path):
        """A client-only pk3 with byte-identical copies of files the main menu reads."""
        wanted = {name.lower(): None for name in self.MENU_FILES}
        for pk3 in sorted(glob.glob(os.path.join(game_dir(), "main", "*.pk3")), key=str.lower):
            with zipfile.ZipFile(pk3) as z:
                for info in z.infolist():
                    if info.filename.lower() in wanted:
                        wanted[info.filename.lower()] = (info.filename, z.read(info))
        found = [v for v in wanted.values() if v]
        if not found:
            self.skipTest("menu files not found in the game pk3s")
        with zipfile.ZipFile(path, "w") as out:
            for name, data in found:
                out.writestr(name, data)

    def test_client_with_extra_menu_pak_joins_pure_server(self):
        # upstream #659: paks read in the menu before connecting were reported to the pure server
        s = self.server("+set", "developer", "1", "+set", "sv_pure", "1", "+set", "g_gametype", "1",
                        "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        os.makedirs(os.path.join(client_home.path, "main"))
        self._extra_pak(os.path.join(client_home.path, "main", "zzz_t659.pk3"))
        c = omoh.client(client_home, "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        log = s.wait_for(r"entered the battle|Unpure", timeout=120)
        c.quit()
        self.assertEqual(s.quit(), 0)
        self.assertNotIn("Unpure", log)


@require_game
class PlusDataFolder(GameTestCase):
    """The fork-only <fs_pluspath>/plus/*.pk3 folder."""

    def plus_client(self, home, plus_dir, *args):
        """A client whose fork data folder is <plus_dir>/plus ("" disables it)."""
        c = omoh.client(home, "+set", "fs_pluspath", plus_dir, *args)
        self.games.append(c)
        return c

    def _plus_pak(self, files):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "plus"))
        with zipfile.ZipFile(os.path.join(tmp, "plus", "zzz-plus.pk3"), "w") as z:
            for name in files:
                z.writestr(name, "plus")
        return tmp

    def _which(self, c, name):
        start = len(c.log())
        c.send(f"which {name}")
        return c.wait_for(rf'File "{re.escape(name)}" found|File not found: "{re.escape(name)}"',
                          start=start)[start:]

    def test_plus_pak_overrides_base_menu(self):
        c = self.plus_client(self.home, self._plus_pak(["ui/main.urc"]))
        self.assertIn("plus/zzz-plus.pk3", self._which(c, "ui/main.urc"))
        c.quit()

    def test_plus_fonts_beat_old_fonts_pak(self):
        name = "fonts/plus_test.RitualFont"  # not a real font: the game must not load it
        old = os.path.join(self.home.path, "main", "zzz-plus-fonts.pk3")
        os.makedirs(os.path.dirname(old), exist_ok=True)
        with zipfile.ZipFile(old, "w") as z:
            z.writestr(name, "old")
        c = self.plus_client(self.home, self._plus_pak([name]))
        self.assertIn("plus/zzz-plus.pk3", self._which(c, name))
        c.quit()

    def test_no_plus_folder_keeps_original_menu(self):
        c = self.plus_client(self.home, "")
        out = self._which(c, "ui/main.urc")
        self.assertRegex(out, r"main[/\\]Pak\d+\.pk3")
        c.quit()

    def test_fs_game_mod_beats_plus_pak(self):
        os.makedirs(os.path.join(self.home.path, "plusmod"))
        with zipfile.ZipFile(os.path.join(self.home.path, "plusmod", "zzz-mod.pk3"), "w") as z:
            z.writestr("ui/main.urc", "mod")
        c = self.plus_client(self.home, self._plus_pak(["ui/main.urc"]), "+set", "fs_game", "plusmod")
        self.assertIn("zzz-mod.pk3", self._which(c, "ui/main.urc"))
        c.quit()

    def test_fs_game_mod_beats_plus_pak_on_pure_server(self):
        def mod_pak(home):
            os.makedirs(os.path.join(home.path, "plusmod"))
            with zipfile.ZipFile(os.path.join(home.path, "plusmod", "zzz-mod.pk3"), "w") as z:
                z.writestr("ui/main.urc", "mod")
        mod_pak(self.home)
        s = self.server("+set", "developer", "1", "+set", "sv_pure", "1", "+set", "g_gametype", "1",
                        "+set", "fs_game", "plusmod", "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        mod_pak(client_home)
        c = self.plus_client(client_home, self._plus_pak(["ui/main.urc"]),
                             "+set", "fs_game", "plusmod", "+connect", f"127.0.0.1:{s.port}")
        s.wait_for(r"entered the battle|Unpure", timeout=120)
        self.assertIn("zzz-mod.pk3", self._which(c, "ui/main.urc"))
        c.quit()
        s.quit()

    def test_plus_pak_on_pure_server(self):
        s = self.server("+set", "developer", "1", "+set", "sv_pure", "1", "+set", "g_gametype", "1",
                        "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = self.plus_client(client_home, self._plus_pak(["ui/main.urc", "maps/plus_test.txt"]),
                             "+connect", f"127.0.0.1:{s.port}")
        log = s.wait_for(r"entered the battle|Unpure", timeout=120)
        self.assertIn("plus/zzz-plus.pk3", self._which(c, "ui/main.urc"))
        self.assertIn("File not found", self._which(c, "maps/plus_test.txt"))
        c.send("disconnect")
        c.wait_for(r"Disconnect|disconnect")
        time.sleep(2)
        self.assertIn("plus/zzz-plus.pk3", self._which(c, "ui/main.urc"))
        c.quit()
        self.assertEqual(s.quit(), 0)
        self.assertNotIn("Unpure", log)


def _quiet_handler(directory):
    class Handler(http.server.SimpleHTTPRequestHandler):
        requests = []

        def log_message(self, fmt, *args):
            Handler.requests.append(fmt % args)
    return functools.partial(Handler, directory=directory), Handler


@require_game
class Downloads(GameTestCase):
    def _mod_server(self, dl_url=None):
        import zipfile as zf
        server_home = omoh.Home()
        self.addCleanup(server_home.cleanup)
        os.makedirs(os.path.join(server_home.path, "main"))
        with zf.ZipFile(os.path.join(server_home.path, "main", "zzz_dltest.pk3"), "w") as z:
            z.writestr("maps/dm/mohdm1.scr", "main:\n\tlevel waittill spawn\n\tprintln \"DLTEST\"\nend\n")
        args = ["+set", "sv_allowDownload", "1", "+set", "g_gametype", "1"]
        if dl_url:
            args += ["+set", "sv_dlURL", f'"{dl_url}"']   # quoted: // starts a comment
        s = omoh.server(server_home, *args, "+map", "dm/mohdm1")
        self.games.append(s)
        s.wait_for(r"==== InitGame ====")
        return server_home, s

    def _join(self, s):
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = omoh.client(client_home, "+set", "cl_allowDownload", "1", "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        s.wait_for(r"entered the battle", timeout=120)
        c.quit()
        return os.path.join(client_home.path, "main", "zzz_dltest.pk3")

    def test_udp_download(self):
        _, s = self._mod_server()
        pak = self._join(s)
        self.assertEqual(s.quit(), 0)
        self.assertTrue(os.path.exists(pak))
        self.assertIn("clientDownload", s.log())

    def test_http_redirect_download(self):
        handler, record = _quiet_handler(".")
        web = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=web.serve_forever, daemon=True).start()
        self.addCleanup(web.server_close)
        self.addCleanup(web.shutdown)
        home, s = self._mod_server(f"http://127.0.0.1:{web.server_address[1]}")
        web.RequestHandlerClass.keywords["directory"] = home.path   # serve the server's home folder
        pak = self._join(s)
        self.assertEqual(s.quit(), 0)
        self.assertTrue(os.path.exists(pak))
        self.assertTrue(any("zzz_dltest.pk3" in r and " 200 " in r for r in record.requests), record.requests)
        self.assertNotIn("clientDownload", s.log())


def green_pixels(path, x0, x1, y0, y1):
    """Count saturated green pixels (the HUD health bar) in a region given as screen fractions."""
    width, height, rows = read_tga(path)
    return sum(1 for row in rows[int(y0 * height):int(y1 * height)]
               for r, g, b in row[int(x0 * width):int(x1 * width)] if g > 120 and r < 80 and b < 80)


@require_game
class HudScale(GameTestCase):
    def shot(self, scale):
        home = omoh.Home()
        self.addCleanup(home.cleanup)
        # sv_maxclients 2: a one-player local game waits on the loading screen's continue button
        c = omoh.client(home, "+set", "developer", "1", "+set", "r_mode", "-1", "+set", "r_customwidth", "1920",
                        "+set", "r_customheight", "1080", "+set", "ui_hudscale", str(scale), "+set", "g_gametype",
                        "2", "+set", "sv_maxclients", "2", "+devmap", "dm/mohdm1")
        self.games.append(c)
        c.wait_for(r"==== InitGame ====", timeout=120)
        time.sleep(10)
        c.send("join_team allies")
        time.sleep(1)
        c.send("primarydmweapon rifle")
        time.sleep(8)
        c.send("screenshot hud")
        time.sleep(3)
        self.assertEqual(c.quit(), 0)
        return green_pixels(os.path.join(home.path, "main", "screenshots", "hud.tga"), 0.0, 0.1, 0.75, 1.0)

    def test_crosshair_scale_and_size(self):
        # upstream #911: crosshair size independent of the texture (cg_crosshair_size) and a multiplier
        # a plain background: no world or entities (swaying trees changed thousands of pixels)
        c = self.client("+set", "developer", "1", "+set", "r_mode", "-1", "+set", "r_clear", "1",
                        "+set", "r_drawworld", "0", "+set", "r_drawentities", "0",
                        "+set", "r_customwidth", "1280", "+set", "r_customheight", "720", "+set", "g_gametype", "2",
                        "+set", "sv_maxclients", "2", "+devmap", "dm/mohdm1")
        c.wait_for(r"==== InitGame ====", timeout=120)
        time.sleep(10)
        c.send("primarydmweapon smg")
        c.send("join_team allies")
        time.sleep(6)
        c.send("popmenu 0")    # team and weapon menus cover the crosshair
        c.send("popmenu 0")
        time.sleep(2)
        c.send("freezeplayer")  # a still camera (random spawn point, the player may still fall), no message
        time.sleep(3)
        names = ("normal", "scale3", "size64")
        for cvars in ("cg_crosshair_scale 1", "cg_crosshair_scale 3", "cg_crosshair_scale 1; cg_crosshair_size 64"):
            for cvar in cvars.split("; "):
                c.send(cvar)
            time.sleep(1)
            c.send("screenshot silent")    # a named screenshot centerprints "Wrote ..." over the crosshair
            time.sleep(1)
        self.assertEqual(c.quit(), 0)
        shots = dict(zip(names, sorted(glob.glob(self.home.file("screenshots/shot*.tga")))))
        self.assertEqual(len(shots), 3)

        def crosshair_pixels(name):    # pixels that differ from the plain background in the center
            w, h, rows = read_tga(shots[name])
            y0, y1, x0, x1 = int(h * 0.39), int(h * 0.61), int(w * 0.4375), int(w * 0.5625)
            background = rows[y0][x0]
            return sum(1 for y in range(y0, y1) for x in range(x0, x1)
                       if sum(abs(a - b) for a, b in zip(rows[y][x], background)) > 60)

        count = {n: crosshair_pixels(n) for n in names}
        self.assertGreater(count["normal"], 5, count)
        self.assertGreater(count["scale3"], count["normal"] * 3, count)
        self.assertGreater(count["size64"], count["normal"] * 2, count)

    def test_menus_keep_4_3_on_wide_screens(self):
        # upstream #583: at 1280x720 a 4:3 menu is 960 pixels wide, so the left 160 pixels are side bar
        def left_bar_pixels(aspect):
            home = omoh.Home()
            self.addCleanup(home.cleanup)
            c = omoh.client(home, "+set", "ui_menuaspect", str(aspect), "+set", "r_mode", "-1",
                            "+set", "r_customwidth", "1280", "+set", "r_customheight", "720")
            self.games.append(c)
            c.wait_for(r"Opening IP socket", timeout=60)
            time.sleep(8)                      # the main menu is up
            c.send("screenshot silent")
            time.sleep(2)
            self.assertEqual(c.quit(), 0)
            w, h, rows = read_tga(glob.glob(os.path.join(home.path, "main", "screenshots", "shot*.tga"))[0])
            return sum(1 for y in range(int(h * 0.6), int(h * 0.95)) for x in range(0, int(w * 0.11))
                       if sum(rows[y][x]) > 30)

        self.assertEqual(left_bar_pixels(1), 0)          # black side bar
        self.assertGreater(left_bar_pixels(0), 1000)     # stretched menu background

    def test_menu_knobs_keep_4_3_on_wide_screens(self):
        # The advanced options knobs (pulldown menus) used width/640 while their menu used the 4:3
        # scale: at 1280x720 they were drawn 2.0x wide in a 1.5x frame, cut on the right. The model
        # detail knob is the 64x64 virtual rect at (4, 316): pixels 166-262 by 474-570 here, and
        # its white arrow must sit in the middle (x 214), not at the middle of a 128-pixel picture
        home = omoh.Home()
        self.addCleanup(home.cleanup)
        c = omoh.client(home, "+set", "r_mode", "-1", "+set", "r_customwidth", "1280", "+set", "r_customheight", "720")
        self.games.append(c)
        c.wait_for(r"Opening IP socket", timeout=60)
        time.sleep(8)
        c.send("pushmenu advancedoptions")
        time.sleep(3)
        c.send("screenshot silent")
        time.sleep(2)
        self.assertEqual(c.quit(), 0)
        _, _, rows = read_tga(glob.glob(os.path.join(home.path, "main", "screenshots", "shot*.tga"))[0])
        arrow = [x for y in range(474, 570) for x in range(166, 262) if min(rows[y][x]) > 200]
        self.assertGreater(len(arrow), 20)
        self.assertAlmostEqual(sum(arrow) / len(arrow), 214, delta=8)

    def test_ui_hudscale_scales_the_hud(self):
        # upstream #585: at 1920x1080 the HUD is drawn at its 640x480 pixel size; ui_hudscale enlarges it
        normal, double = self.shot(1), self.shot(2)
        self.assertGreater(normal, 300)
        self.assertGreater(double / normal, 3.0, (normal, double))   # twice the size on both axes


@require_game
@unittest.skipUnless(sys.platform.startswith("linux") and shutil.which("gcc"), "needs Linux and gcc (LD_PRELOAD)")
class ServerBrowser(GameTestCase):
    def test_slow_dns_does_not_freeze_the_game(self):
        # upstream #376: refreshing the internet server list froze the game while master DNS lookups hung
        shim = os.path.join(self.home.path, "slowdns.so")
        subprocess.run(["gcc", "-shared", "-fPIC", "-o", shim,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "slowdns.c"), "-ldl"], check=True)
        c = self.client("+set", "developer", "1", env={"LD_PRELOAD": shim})
        c.wait_for(r"Opening IP socket", timeout=60)
        time.sleep(10)
        c.send("pushmenu joinnetgame")
        time.sleep(2)
        c.send("widgetcommand netgamelist refreshserverlist")
        time.sleep(0.5)
        mark = len(c.log())
        start = time.time()
        c.send("echo BROWSER_ALIVE")
        c.wait_for(r"^BROWSER_ALIVE", start=mark, timeout=30)
        self.assertLess(time.time() - start, 2.0)          # was 5 s per master lookup
        time.sleep(6)                                       # past the master socket timeout
        mark = len(c.log())
        c.send("echo STDIN_ALIVE")                          # a never-created master socket closed fd 0
        c.wait_for(r"^STDIN_ALIVE", start=mark, timeout=10)
        self.assertIn("SLOWDNS getaddrinfo(master.", c.log())
        self.assertEqual(c.quit(), 0)


    NO_MASTERS = [arg for i in range(5) for arg in ("+set", f"com_master{i}_host", "")]

    def _list(self, c, expect):
        mark = len(c.log())
        c.send("widgetcommand netgamelist refreshserverlist")
        time.sleep(6)
        c.send("widgetcommand netgamelist printlist")
        return c.wait_for(expect, start=mark, timeout=20)[mark:]

    def test_game_type_filter(self):
        servers = []
        for name, gametype in (("Alpha", "1"), ("Bravo", "2")):
            home = omoh.Home()
            self.addCleanup(home.cleanup)
            s = omoh.server(home, "+set", "sv_hostname", name, "+set", "g_gametype", gametype, "+map", "dm/mohdm1")
            self.games.append(s)
            s.wait_for(r"==== InitGame ====")
            s.send("net_gamespy_port")
            qport = int(re.findall(r'"net_gamespy_port" is:"(\d+)', s.wait_for(r'"net_gamespy_port" is:"\d+'))[-1])
            servers.append(f"127.0.0.1:{s.port} {qport}")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        client_home.write("serverhistory.txt", "\n".join(servers) + "\n")
        c = omoh.client(client_home, "+set", "developer", "1", *self.NO_MASTERS)
        self.games.append(c)
        c.wait_for(r"Opening IP socket", timeout=60)
        time.sleep(8)
        c.send("pushmenu joinnetgame")
        time.sleep(2)
        listed = self._list(c, r"Server list \(\d+\):(\n  .*)*\n.*Bravo")      # both recent servers
        self.assertIn("Alpha", listed)
        c.send("dm_team_match 0")                                                  # hide team deathmatch
        listed = self._list(c, r"Server list \((\d+)\):")
        self.assertIn("Alpha", listed)
        self.assertNotIn("Bravo", listed)
        self.assertEqual(c.quit(), 0)

    def test_recent_only_filter(self):
        servers = []
        for name in ("Alpha", "Bravo"):
            home = omoh.Home()
            self.addCleanup(home.cleanup)
            s = omoh.server(home, "+set", "sv_hostname", name, "+map", "dm/mohdm1")
            self.games.append(s)
            s.wait_for(r"==== InitGame ====")
            s.send("net_gamespy_port")
            qport = int(re.findall(r'"net_gamespy_port" is:"(\d+)', s.wait_for(r'"net_gamespy_port" is:"\d+'))[-1])
            servers.append(f"127.0.0.1:{s.port} {qport}")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        client_home.write("serverfavorites.txt", servers[0] + "\n")     # Alpha is a favourite only
        client_home.write("serverhistory.txt", servers[1] + "\n")       # Bravo is recent only
        c = omoh.client(client_home, "+set", "developer", "1", *self.NO_MASTERS)
        self.games.append(c)
        c.wait_for(r"Opening IP socket", timeout=60)
        time.sleep(8)
        c.send("pushmenu joinnetgame")
        time.sleep(2)
        c.send("dm_browser_show 3")
        listed = self._list(c, r"Server list \(\d+\):(\n  .*)*\n.*Bravo")
        self.assertIn("Bravo", listed)
        self.assertNotIn("Alpha", listed)
        self.assertEqual(c.quit(), 0)

    def test_favourite_button_toggles(self):
        s = self.server("+set", "sv_hostname", "Alpha", "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        s.send("net_gamespy_port")
        qport = int(re.findall(r'"net_gamespy_port" is:"(\d+)', s.wait_for(r'"net_gamespy_port" is:"\d+'))[-1])
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        client_home.write("serverhistory.txt", f"127.0.0.1:{s.port} {qport}\n")
        c = omoh.client(client_home, "+set", "developer", "1", *self.NO_MASTERS)
        self.games.append(c)
        c.wait_for(r"Opening IP socket", timeout=60)
        time.sleep(8)
        c.send("pushmenu joinnetgame")
        time.sleep(2)
        c.send("dm_browser_show 2")
        self._list(c, r"Server list \(1\):\n.*Alpha")
        c.send("widgetcommand netgamelist selectitem 1")            # the Plus screen has the player click it
        for marked in (True, False):
            c.send("widgetcommand netgamelist togglefavorite")      # what the Plus Favourite button runs
            time.sleep(1)
            mark = len(c.log())
            c.send("widgetcommand netgamelist printlist")
            listed = c.wait_for(r"Server list \(\d+\):\n.*Alpha", start=mark, timeout=20)[mark:]
            self.assertEqual("  * " in listed, marked, listed)
        self.assertEqual(c.quit(), 0)
        self.assertNotIn("127.0.0.1", open(client_home.file("serverfavorites.txt")).read())

    def test_favorites_history_and_search(self):
        alpha = self.server("+set", "sv_hostname", "Alpha", "+map", "dm/mohdm1")
        home_b = omoh.Home()
        self.addCleanup(home_b.cleanup)
        bravo = omoh.server(home_b, "+set", "sv_hostname", "Bravo", "+map", "dm/mohdm1")
        self.games.append(bravo)
        for s in (alpha, bravo):
            s.wait_for(r"==== InitGame ====")
            s.send("net_gamespy_port")
        qa, qb = (int(re.findall(r'"net_gamespy_port" is:"(\d+)', s.wait_for(r'"net_gamespy_port" is:"\d+'))[-1])
                  for s in (alpha, bravo))
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        client_home.write("serverfavorites.txt", f"127.0.0.1:{alpha.port} {qa}\n")
        c = omoh.client(client_home, "+set", "developer", "1", *self.NO_MASTERS, "+connect", f"127.0.0.1:{bravo.port}")
        self.games.append(c)
        bravo.wait_for(r"entered the battle", timeout=120)
        c.send(f"fav_add 127.0.0.1:{bravo.port} {qb}")
        c.wait_for(r"Added favorite 127.0.0.1")
        c.send(f"fav_del 127.0.0.1:{bravo.port}")
        c.wait_for(r"Removed favorite 127.0.0.1")
        c.send("disconnect")
        time.sleep(3)
        c.send("history_list")
        c.wait_for(rf"127\.0\.0\.1:{bravo.port}")
        c.send("pushmenu joinnetgame")
        time.sleep(2)

        c.send("dm_browser_show 2")
        listed = self._list(c, r"Server list \(\d+\):(\n  .*)*\n.*Bravo")
        self.assertRegex(listed, r"\* .*Alpha \| 127\.0\.0\.1:%d" % alpha.port)
        self.assertRegex(listed, r"Bravo \(recent\) \| 127\.0\.0\.1:%d" % bravo.port)

        c.send("dm_browser_show 0")
        c.send("dm_browser_search Alp")
        listed = self._list(c, r"Server list \((\d+)\):")
        self.assertIn("Alpha", listed)
        self.assertNotIn("Bravo", listed)
        self.assertEqual(c.quit(), 0)

        history = open(client_home.file("serverhistory.txt")).read()
        self.assertIn(f"127.0.0.1:{bravo.port} {qb}", history)     # query port published by the server


@require_game
class Translations(GameTestCase):
    def test_cl_language_overrides_the_game_texts(self):
        # saved as UTF-8, like a modern editor does; the game shows Latin-1
        self.home.write("lang/es/localization.txt",
                        '{ "Health" "Salud" }\r\n{ "&&& has joined the Allies" "&&& se unió a los Aliados" }\r\n')
        for language, health in (("es", "Salud"), ("", "Health")):
            c = self.client("+set", "developer", "1", "+set", "cl_language", language)
            c.wait_for(r"Opening IP socket", timeout=60)
            c.send("localize Health")
            c.send("localize &&& has joined the Allies")
            c.wait_for(r'"&&& has joined the Allies" -> ')
            self.assertEqual(c.quit(), 0)
            with open(c.log_path, "rb") as f:
                log = f.read()
            self.assertIn(f'"Health" -> "{health}"'.encode(), log)
            if language:
                self.assertIn("2 entries translated by lang/es/localization.txt".encode(), log)
                self.assertIn('-> "&&& se unió a los Aliados"'.encode("latin-1"), log)


@require_game
class HitSounds(GameTestCase):
    SCRIPT = """main:
	level waittill spawn
	while (1) {
		local.human = NIL
		local.enemy = NIL
		for (local.i = 1; local.i <= $player.size; local.i++) {
			local.p = $player[local.i]
			if (!(isBot local.p) && local.p.dmteam != "spectator") {
				local.human = local.p
			}
		}
		if (local.human) {
			for (local.i = 1; local.i <= $player.size; local.i++) {
				local.p = $player[local.i]
				if ((isBot local.p) && local.p.dmteam != local.human.dmteam && local.p.health > 0) {
					local.enemy = local.p
				}
			}
		}
		if (local.enemy) {
			local.enemy damage local.human 5 local.human (0 0 0) (0 0 0) (0 0 0) 0 0 0 -1
			println "THIT hit"
		}
		wait 1
	}
end
"""

    def _play(self, enabled):
        server_home = omoh.Home()
        self.addCleanup(server_home.cleanup)
        server_home.write("maps/dm/mohdm1.scr", self.SCRIPT)
        s = omoh.server(server_home, "+set", "developer", "1", "+set", "g_gametype", "2", "+set", "sv_maxbots", "2",
                        "+set", "sv_minPlayers", "2", "+set", "g_hitsounds", str(enabled),
                        "+set", "g_hitsound", "sound/plus_hit_test.wav", "+map", "dm/mohdm1")
        self.games.append(s)
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = omoh.client(client_home, "+set", "developer", "1", "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        s.wait_for(r"UnnamedSoldier.* has entered the battle", timeout=120)
        time.sleep(3)
        c.send("primarydmweapon smg")
        c.send("join_team allies")
        s.wait_for(r"THIT hit", count=3, timeout=60)
        c.quit()
        self.assertEqual(s.quit(), 0)
        return c.log()

    def test_server_enabled_hit_sound_reaches_the_attacker(self):
        self.assertIn("sound/plus_hit_test.wav", self._play(1))

    def test_hit_sounds_are_off_by_default(self):
        self.assertNotIn("sound/plus_hit_test.wav", self._play(0))


def _build_fonts(pk3):
    """Run misc/fonts/make_fonts.py (needs Pillow and DejaVu, outside this isolated interpreter)."""
    tool = os.path.join(omoh.REPO, "misc", "fonts", "make_fonts.py")
    python = shutil.which("python3")
    if not python:
        return False
    result = subprocess.run([python, tool, "--out", pk3], cwd=tempfile.gettempdir(), capture_output=True, text=True)
    return result.returncode == 0


@require_game
class Fonts(GameTestCase):
    def test_generated_fonts_load_and_draw(self):
        pk3 = os.path.join(self.home.path, "main", "zzz-plus-fonts.pk3")
        os.makedirs(os.path.dirname(pk3), exist_ok=True)
        if not _build_fonts(pk3):
            self.skipTest("misc/fonts/make_fonts.py needs Pillow and the DejaVu fonts")
        self.home.write("lang/es/localization.txt", '{ "Health" "Salud ñáé ¿¡" }\r\n')
        c = self.client("+set", "developer", "1", "+set", "cl_language", "es", "+set", "ui_hudscale", "2",
                        "+set", "g_gametype", "2", "+set", "sv_maxclients", "2", "+devmap", "dm/mohdm1")
        c.wait_for(r"==== InitGame ====", timeout=120)
        time.sleep(10)
        c.send("primarydmweapon smg")
        c.send("join_team allies")
        time.sleep(5)
        c.send("screenshot silent")
        time.sleep(2)
        self.assertEqual(c.quit(), 0)
        log = c.log()
        self.assertIn("zzz-plus-fonts.pk3", log)
        for bad in ("Error parsing font", "Couldn't load font", "top-down", "character in font"):
            self.assertNotIn(bad, log)
        self.assertTrue(glob.glob(self.home.file("screenshots/shot*.tga")))


@require_game
class HitMarkers(GameTestCase):
    # the player hits an enemy bot every 0.1 s, so a marker is always fading out
    SCRIPT = HitSounds.SCRIPT.replace("5 local.human", "1 local.human").replace("println \"THIT hit\"\n", "") \
                             .replace("wait 1\n", "wait 0.1\n")

    def _center_pixels(self, *settings):
        home = omoh.Home()
        self.addCleanup(home.cleanup)
        home.write("maps/dm/mohdm1.scr", self.SCRIPT)
        # plain background: no world or entities, only the HUD
        c = omoh.client(home, "+set", "developer", "1", *settings, "+set", "r_clear", "1", "+set", "r_drawworld", "0",
                        "+set", "r_drawentities", "0", "+set", "r_mode", "-1", "+set", "r_customwidth", "1280",
                        "+set", "r_customheight", "720", "+set", "g_gametype", "2", "+set", "sv_maxclients", "4",
                        "+set", "sv_maxbots", "2", "+set", "sv_minPlayers", "2", "+devmap", "dm/mohdm1")
        self.games.append(c)
        c.wait_for(r"==== InitGame ====", timeout=120)
        time.sleep(10)
        c.send("primarydmweapon smg")
        c.send("join_team allies")
        time.sleep(5)
        c.send("popmenu 0")
        c.send("popmenu 0")
        time.sleep(3)
        c.send("screenshot silent")
        time.sleep(2)
        self.assertEqual(c.quit(), 0)
        w, h, rows = read_tga(glob.glob(os.path.join(home.path, "main", "screenshots", "shot*.tga"))[0])
        background = rows[h // 2 - 40][w // 2 - 40]
        return sum(1 for y in range(h // 2 - 40, h // 2 + 40) for x in range(w // 2 - 40, w // 2 + 40)
                   if sum(abs(a - b) for a, b in zip(rows[y][x], background)) > 60)

    def test_hit_marker_around_the_crosshair(self):
        on = self._center_pixels("+set", "g_hitmarkers", "1")
        off = self._center_pixels("+set", "g_hitmarkers", "0")
        opted_out = self._center_pixels("+set", "g_hitmarkers", "1", "+set", "cg_hitmarker", "0")
        self.assertGreater(on, off + 50, (on, off, opted_out))      # crosshair plus the X
        self.assertLess(abs(opted_out - off), 10, (on, off, opted_out))   # the server sends nothing


def vulkan_renderer():
    """The renderer_vulkan module next to the binaries, or None."""
    found = glob.glob(os.path.join(omoh.bin_dir() or "", "renderer_vulkan*"))
    return found[0] if found else None


# the tool needs Pillow, often a user install that "python3 -I" (how these tests run) does not see
HAVE_PILLOW = subprocess.run([sys.executable, "-c", "import PIL"], capture_output=True).returncode == 0


PLUS_PK3 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "misc", "plus-pk3",
                        "build_pk3.py")


def _tga(width, rows):
    """An uncompressed 24-bit TGA; rows of one colour each, bottom row first."""
    header = struct.pack("<3B2HB4H2B", 0, 0, 2, 0, 0, 0, 0, 0, width, len(rows), 24, 0)
    return header + b"".join(bytes(rgb[::-1]) * width for rgb in rows)


@require_game
@unittest.skipUnless(HAVE_PILLOW, "needs Pillow for misc/plus-pk3")
class PlusMenu(GameTestCase):
    """The fork's main menu (misc/plus-pk3/data/ui/main.urc), with plain background tiles: the left
    half red with its bottom quarter green, the right half blue."""

    # virtual units are 1/480 of the screen height (ui_plusscale 1)
    BAR_FADE_END = 300                     # the bar gradient is transparent from here
    # the main menu entries shown in a game only
    IN_GAME_ENTRIES = ("backtogame", "savegame", "disconnect")
    # screens of the maintainer's report (5:4) and two wide ones; the 5:4 one also at both scale ends
    LAYOUT_SCREENS = ((1280, 1024, ("0.85", "1.1")), (1920, 1080, ("1",)), (2560, 1080, ("1",)))

    # a test menu with a green panel anchored like the Plus content panel
    # two pulldowns whose items set several cvars (Plus options' resolution and effect presets)
    PULLDOWN_URC = """menu "plus_pulldown_test" 640 480 NONE 0
virtualres 1
scalecvar ui_plusscale
bgfill 0 0 0 1
fullscreen 1
resource
PulldownMenuContainer
{
name "res list"
rect 0 0 200 24
scalecvar ui_plusscale
anchor 100 100 -1 -1
linkcvar "r_mode"
menushader "MENU" "textures/menu/pulldownarrow"
addpopup "MENU" "Desktop" command "set r_mode -2"
addpopup "MENU" "1920x1080" command "set r_mode -1; set r_customwidth 1920; set r_customheight 1080"
addpopup "MENU" "2560x1440" command "set r_mode -1;set r_customwidth 2560;set r_customheight 1440"
addpopup "MENU" "Quoted" command "set r_mode -1; set r_customwidth \\"1000\\"; set r_customheight 1000.0"
addpopup "MENU" "Bare" command "r_mode 5"
}
resource
PulldownMenuContainer
{
name "fx list"
rect 0 0 200 24
scalecvar ui_plusscale
anchor 100 140 -1 -1
linkcvar "cg_effectdetail"
menushader "MENU" "textures/menu/pulldownarrow"
addpopup "MENU" "Low" command "set cg_effectdetail \\"0.5\\";set vss_maxcount 22"
addpopup "MENU" "Max" command "set cg_effectdetail \\"1.0\\";set vss_maxcount 10"
}
end.
"""

    # sliders with "showvalue": a percentage, a plain float, a format that is refused, and none
    SLIDER_URC = """menu "plus_slider_test" 640 480 NONE 0
virtualres 1
scalecvar ui_plusscale
bgfill 0 0 0 1
fullscreen 1
""" + "".join(f"""resource
Slider
{{
name "{name}"
rect 0 0 200 16
fgcolor 0.94 0.75 0.38 1
scalecvar ui_plusscale
anchor 100 {y} -1 -1
font facfont-20
linkcvar "{cvar}"
slidertype float
setrange {lo} {hi}
{extra}
}}
""" for name, y, cvar, lo, hi, extra in (
        ("pct", 100, "s_volume", 0, 1, 'showvalue "%.0f%%" 100'),
        ("gamma", 140, "r_gamma", 0.5, 3, 'showvalue "%.1f"'),
        ("bad", 180, "r_gamma", 0.5, 3, 'showvalue "%s"'),
        ("plain", 220, "r_gamma", 0.5, 3, ""))) + "end.\n"

    ANCHOR_URC = """menu "plus_anchor_test" 640 480 NONE 0
virtualres 1
scalecvar ui_plusscale
bgfill 0 0 0 1
fullscreen 1
resource
Label
{
name "panel"
rect 0 0 64 64
scalecvar ui_plusscale
bgcolor 0 1 0 1
borderstyle "NONE"
anchor 220 100 20 40
}
end.
"""

    @classmethod
    def setUpClass(cls):
        cls.plus_dir = tempfile.mkdtemp()
        built = os.path.join(cls.plus_dir, "built.pk3")
        subprocess.run([sys.executable, PLUS_PK3, "--out", built, "--skip-fonts"], check=True, capture_output=True)
        os.makedirs(os.path.join(cls.plus_dir, "plus"))
        left = _tga(4, [(0, 255, 0)] * 64 + [(255, 0, 0)] * 192)
        right = _tga(4, [(0, 0, 255)] * 256)
        with zipfile.ZipFile(built) as src, \
                zipfile.ZipFile(os.path.join(cls.plus_dir, "plus", "zzz-plus.pk3"), "w", zipfile.ZIP_DEFLATED) as z:
            for name in src.namelist():
                if name not in ("textures/menu_plus/bg_l.tga", "textures/menu_plus/bg_r.tga"):
                    z.writestr(name, src.read(name))
            z.writestr("textures/menu_plus/bg_l.tga", left)
            z.writestr("textures/menu_plus/bg_r.tga", right)
            z.writestr("ui/plus_anchor_test.urc", cls.ANCHOR_URC)
            z.writestr("ui/plus_pulldown_test.urc", cls.PULLDOWN_URC)
            z.writestr("ui/plus_slider_test.urc", cls.SLIDER_URC)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.plus_dir, True)

    def start(self, width, height, *args, home=None):
        if home is None:
            home = omoh.Home()
            self.addCleanup(home.cleanup)
        c = PlusDataFolder.plus_client(self, home, self.plus_dir, "+set", "r_mode", "-1",
                                       "+set", "r_customwidth", str(width), "+set", "r_customheight", str(height),
                                       *args)
        c.wait_for(r"Opening IP socket", timeout=60)
        time.sleep(8)                      # the main menu is up
        return home, c

    def screenshot(self, home, c):
        for old in glob.glob(os.path.join(home.path, "main", "screenshots", "shot*.tga")):
            os.remove(old)
        c.send("screenshot silent")
        time.sleep(2)
        return read_tga(glob.glob(os.path.join(home.path, "main", "screenshots", "shot*.tga"))[0])

    def shot(self, width, height, *commands):
        home, c = self.start(width, height)
        for command in commands:
            c.send(command)
            time.sleep(2)
        picture = self.screenshot(home, c)
        self.assertEqual(c.quit(), 0)
        return picture

    WIDGET_RE = re.compile(r'widget (\d+) "([^"]*)" (\S+) shown (\d) rect (\S+) (\S+) (\S+) (\S+)'
                           r'(?: text (\S+) (\S+) (\S+) (\S+) "(.*)")?$')

    def widgets(self, c, *commands):
        """Runs the commands, then ui_printwidgets: {"menu", "screen", "widgets": {name: {...}}, "list",
        "columns"}; rects are (x0, y0, x1, y1) in pixels, "text" the rect the text is drawn in."""
        for command in commands:
            c.send(command)
            time.sleep(2)
        mark = len(c.log())
        c.send("ui_printwidgets")
        out = c.wait_for(r"end of widgets", start=mark, timeout=20)[mark:]
        result = {"widgets": {}, "columns": [], "pulldowns": [], "sliders": {}}
        for line in out.splitlines():
            m = self.WIDGET_RE.match(line)
            if line.startswith("menu "):
                parts = line.split()
                result["menu"], result["screen"] = parts[1].strip('"'), (int(parts[3]), int(parts[4]))
            elif m:
                x, y, w, h = (float(v) for v in m.group(5, 6, 7, 8))
                item = {"class": m.group(3), "shown": m.group(4) == "1", "rect": (x, y, x + w, y + h),
                        "depth": int(m.group(1))}
                if m.group(9):
                    x, y, w, h = (float(v) for v in m.group(9, 10, 11, 12))
                    item["text"], item["title"] = (x, y, x + w, y + h), m.group(13)
                name = m.group(2)
                while name in result["widgets"]:     # unnamed children (scroll bars) share names
                    name += "'"
                result["widgets"][name] = item
            elif line.startswith("list "):
                parts = line.split()
                result["list"] = {"header": int(parts[3]), "row": int(parts[5])}
            elif line.startswith("pulldown value "):
                m2 = re.match(r'pulldown value "([^"]*)" width (\S+)', line)
                result["pulldowns"].append({"value": m2.group(1), "width": float(m2.group(2)), "rect": item["rect"]})
            elif line.startswith("build label "):
                m2 = re.match(r'build label "([^"]*)" rect (\S+) (\S+) (\S+) (\S+)', line)
                result["label"] = {"text": m2.group(1), "rect": tuple(float(v) for v in m2.group(2, 3, 4, 5))}
            elif line.startswith("slider value "):
                m2 = re.match(r'slider value "([^"]*)" track (\S+) (\S+) text (\S+) (\S+)', line)
                result["sliders"][name] = {"value": m2.group(1), "track": (float(m2.group(2)), float(m2.group(3))),
                                           "text": (float(m2.group(4)), float(m2.group(5))), "rect": item["rect"]}
            elif line.startswith("items scale "):
                result["items"] = float(line.split()[3])
            elif line.startswith("column "):
                m2 = re.match(r'column "([^"]*)" x (\S+) width (\S+) text (\S+)', line)
                result["columns"].append({"title": m2.group(1), "x": float(m2.group(2)),
                                          "width": float(m2.group(3)), "text": float(m2.group(4))})
        return result

    @staticmethod
    def overlap(a, b):
        return a[0] < b[2] - 1 and b[0] < a[2] - 1 and a[1] < b[3] - 1 and b[1] < a[3] - 1

    @staticmethod
    def inside(a, b, slack=1):
        return a[0] >= b[0] - slack and a[1] >= b[1] - slack and a[2] <= b[2] + slack and a[3] <= b[3] + slack

    @staticmethod
    def is_blue(p):
        return p[2] > 200 and p[0] < 60 and p[1] < 60

    @staticmethod
    def is_green(p):
        return p[1] > 200 and p[0] < 60 and p[2] < 60

    @staticmethod
    def mean_brightness(rows, x0, x1, y0, y1):
        return statistics.mean(sum(rows[y][x]) / 3 for y in range(y0, y1) for x in range(x0, x1))

    def test_main_fills_any_aspect(self):
        # the 2.4:1 picture covers the screen, centred and undistorted: cropped at the sides when the
        # screen is narrower, at the top and bottom when wider. Sampled below the console, which
        # covers the top half at start-up.
        for w, h in ((1280, 720), (2560, 1080), (1024, 768), (3840, 1080)):
            _, _, rows = self.shot(w, h)
            y = int(h * 0.6)
            self.assertTrue(self.is_blue(rows[y][w - 5]), (w, h, rows[y][w - 5]))   # reaches the right edge
            # the halves meet at the centre of the screen
            middle = next(x for x in range(w // 2 - 50, w) if self.is_blue(rows[y][x]))
            self.assertAlmostEqual(middle, w / 2, delta=3, msg=(w, h))
            # the green bottom quarter of the left half starts 3/4 down a picture 1/2.4 as high as wide
            height = max(h, w / 2.4)
            x = w // 2 - 8
            green = next(y for y in range(int(h * 0.55), h) if self.is_green(rows[y][x]))
            self.assertAlmostEqual(green, (h - height) / 2 + height * 0.75, delta=height / 256 + 3, msg=(w, h))
            ys = (int(h * 0.55), int(h * 0.65))
            bar = self.mean_brightness(rows, 0, int(h * 0.1), *ys)
            self.assertLess(bar, self.mean_brightness(rows, w - 20, w - 5, *ys) / 2, (w, h))

    def test_bar_size_follows_height(self):
        def fade_end(w, h):
            _, _, rows = self.shot(w, h)
            y = int(h * 0.6)
            return next(x for x in range(w) if rows[y][x][0] >= 250) / h

        a, b = fade_end(1280, 720), fade_end(2560, 1080)
        self.assertAlmostEqual(a, b, delta=0.02 * a)
        self.assertAlmostEqual(a, self.BAR_FADE_END / 480, delta=0.02 * a)

    def bar_entries(self, screen):
        """The visible buttons and the title of a screen's bar, top to bottom."""
        entries = [(n, w) for n, w in screen["widgets"].items() if w["depth"] == 1 and w["shown"]
                   and "text" in w and (w["class"] == "UIButton" or n == "title")]
        return sorted(entries, key=lambda e: e[1]["rect"][1])

    def assert_bar(self, screen, msg):
        # left-aligned under the title, inside the bar, no two entries overlapping
        entries = self.bar_entries(screen)
        h = screen["screen"][1]
        title = screen["widgets"]["title"]["text"]
        for i, (name, w) in enumerate(entries):
            self.assertAlmostEqual(w["text"][0], title[0], delta=2, msg=(msg, name))
            self.assertLess(w["text"][2], 200 * h / 480 * 1.1 + 2, (msg, name))
            for other, w2 in entries[i + 1:]:
                self.assertFalse(self.overlap(w["rect"], w2["rect"]), (msg, name, other))
        return entries

    def test_main_layout(self):
        # no game: no gap where the hidden entries are, no "New game" next to Campaign; in a game, the
        # in-game entries show next to Quit without overlapping the others; after "disconnect" they go
        for w, h, scales in self.LAYOUT_SCREENS:
            home, c = self.start(w, h)
            for scale in scales:
                screen = self.widgets(c, "set ui_plusscale " + scale, "popmenu 0", "pushmenu main")
                msg = (w, h, scale)
                self.assertEqual(screen["menu"], "main", msg)
                entries = [e for e in self.assert_bar(screen, msg) if e[0] not in ("title", "quit")]
                titles = [e[1]["title"] for e in entries]
                self.assertNotIn("New game", titles, msg)
                for name in self.IN_GAME_ENTRIES:
                    self.assertFalse(screen["widgets"][name]["shown"], (msg, name))
                row = entries[0][1]["rect"][3] - entries[0][1]["rect"][1]
                for (n1, e1), (n2, e2) in zip(entries, entries[1:]):
                    self.assertLessEqual(e2["rect"][1] - e1["rect"][1], 1.5 * row, (msg, n1, n2))
            self.assertEqual(c.quit(), 0)

        w, h = 1280, 1024
        home, c = self.start(w, h, "+set", "ui_plusscale", "1.1", "+devmap", "training")
        c.wait_for(r"==== InitGame ====", timeout=120)
        time.sleep(15)
        in_game = self.widgets(c, "pushmenu main")
        c.send("disconnect")
        time.sleep(5)
        no_game = self.widgets(c)
        self.assertEqual(c.quit(), 0)
        self.assertEqual(in_game["menu"], "main")
        entries = self.assert_bar(in_game, "in game")
        names = [n for n, _ in entries]
        for name in self.IN_GAME_ENTRIES:
            self.assertIn(name, names)
            self.assertFalse(no_game["widgets"][name]["shown"], name)
        # the in-game group sits right above Quit
        self.assertEqual(names[-4:], ["backtogame", "savegame", "disconnect", "quit"])

    OPTIONS_BAR = ["title", "tab_video", "tab_detail", "tab_audio", "tab_controls", "tab_game", "tab_plus",
                   "apply", "back"]
    # option tabs and their number of rows (one label per row)
    OPTION_TABS = [("plus_options_video", 8), ("plus_options_detail", 10), ("plus_options_audio", 5),
                   ("plus_options_game", 7), ("plus_options", 7)]

    def urc_command(self, urc, name):
        """The stuffcommand of the widget <name> in ui/<urc>.urc of the test pk3."""
        with zipfile.ZipFile(os.path.join(self.plus_dir, "plus", "zzz-plus.pk3")) as z:
            text = z.read("ui/%s.urc" % urc).decode()
        return re.search(r'name "%s".*?stuffcommand "([^"]*)"' % name, text, re.S).group(1)

    def assert_options_tab(self, screen, menu, rows, msg, bar=None):
        """An option tab: the tab bar, every row inside the panel, label on the left and control to
        its right, no text over another widget, rows evenly spaced, pulldowns clickable over the whole field."""
        self.assertEqual(screen["menu"], menu, msg)
        widgets = {n: v for n, v in screen["widgets"].items() if v["depth"] == 1 and v["shown"]}
        panel = widgets["panel"]["rect"]
        expected_bar = bar
        bar = [n for n, _ in self.assert_bar(screen, msg)]
        self.assertEqual(bar, expected_bar or self.OPTIONS_BAR, msg)
        in_panel = [n for n in widgets if n.endswith((" label", " slider", " checkbox", " list"))
                    or n.startswith("language note")]
        labels = sorted((widgets[n]["rect"][1], n) for n in in_panel if n.endswith(" label"))
        self.assertEqual(len(labels), rows, (msg, labels))
        for p in screen["pulldowns"]:
            # clickable over the whole field (value and arrow), not past it
            field = p["rect"][2] - p["rect"][0]
            self.assertLessEqual(p["width"], field + 1, (msg, p))
            self.assertGreaterEqual(p["width"], field * 0.95, (msg, p))
        for name, sl in screen["sliders"].items():
            # the value sits right of the track, inside the slider
            self.assertLessEqual(sl["track"][1], sl["text"][0], (msg, name, sl))
            self.assertGreaterEqual(sl["track"][0], sl["rect"][0] - 1, (msg, name, sl))
            self.assertLessEqual(sl["text"][1], sl["rect"][2] + 1, (msg, name, sl))
        texts = []
        for name in in_panel:
            v = widgets[name]
            self.assertTrue(self.inside(v["rect"], panel), (msg, name, v["rect"], panel))
            if "text" in v:
                self.assertTrue(self.inside(v["text"], panel), (msg, name, v["text"], panel))
                self.assertTrue(self.inside(v["text"], v["rect"]), (msg, name))
                texts.append(name)
        # no text over another widget's text or control
        for name in texts:
            for other in in_panel:
                if other != name:
                    self.assertFalse(self.overlap(widgets[name]["text"], widgets[other]["rect"]),
                                     (msg, name, other))
        # rows evenly spaced, controls to the right of their label
        steps = {round(b[0] - a[0]) for a, b in zip(labels, labels[1:])}
        self.assertLessEqual(max(steps) - min(steps), 2, (msg, steps))
        for top, name in labels:
            for v in widgets.values():
                if v is not widgets[name] and abs(v["rect"][1] - top) < 10 and \
                        self.inside(v["rect"], panel) and v["class"] != "UIFakkLabel":
                    self.assertGreater(v["rect"][0], widgets[name]["text"][2], (msg, name))
        return screen

    def test_options_layout(self):
        for w, h, scales in self.LAYOUT_SCREENS:
            _, c = self.start(w, h, "+set", "cl_language", "es")
            for scale in scales:
                for menu, rows in self.OPTION_TABS:
                    # cl_renderer is latched: the pulldown shows the choice waiting for Apply
                    screen = self.widgets(c, "set ui_plusscale " + scale, "set cl_renderer vulkan",
                                          "pushmenu " + menu)
                    c.send("popmenu 0")
                    self.assert_options_tab(screen, menu, rows, (w, h, scale, menu))
                    if menu == "plus_options":
                        self.assertEqual([p["value"] for p in screen["pulldowns"]], ["Vulkan", "Spanish"])
            self.assertEqual(c.quit(), 0)

    def pulldown_values(self, c, menu, *commands):
        screen = self.widgets(c, *commands, "pushmenu " + menu)
        c.send("popmenu 0")
        return [p["value"] for p in sorted(screen["pulldowns"], key=lambda p: p["rect"][1])]

    def test_video_pulldowns_show_values(self):
        # resolution, display mode, max FPS, texture quality, texture filter, anisotropy
        _, c = self.start(1280, 720)
        v = self.pulldown_values(c, "plus_options_video", "set r_mode -1;set r_customwidth 2560;set r_customheight 1080",
                                 "set r_fullscreen 0;set r_noborder 1", "set com_maxfps 144",
                                 "set r_ext_texture_filter_anisotropic 1;set r_ext_max_anisotropy 8")
        self.assertEqual((v[0], v[1], v[2], v[5]), ("2560x1080", "Borderless", "144", "8x"))
        v = self.pulldown_values(c, "plus_options_video", "set r_mode -2", "set r_fullscreen 1;set r_noborder 0",
                                 "set r_ext_texture_filter_anisotropic 0")
        self.assertEqual((v[0], v[1], v[5]), ("Desktop", "Fullscreen", "Off"))
        self.assertEqual(c.quit(), 0)

    def test_detail_presets_show_values(self):
        # model detail, terrain, effects, curves, shadows: presets that set several cvars
        _, c = self.start(1280, 720)
        v = self.pulldown_values(c, "plus_options_detail", "set r_lodscale 0.55;set r_lodcap 0.5;set r_lodviewmodelcap 0.55",
                                 "set cg_effectdetail 0.7;set vss_maxcount 20")
        self.assertEqual((v[0], v[2]), ("High", "Medium"))
        self.assertEqual(c.quit(), 0)

    def test_controls_layout(self):
        # the key list in the panel above four rows, its rows and scroll bar inside it; a Defaults
        # entry in the bar runs the original defaults
        self.assertEqual(self.urc_command("plus_options_controls", "defaults"), "ui_resetcvars;exec default.cfg")
        for w, h, scales in self.LAYOUT_SCREENS:
            _, c = self.start(w, h)
            for scale in scales:
                msg = (w, h, scale)
                screen = self.widgets(c, "set ui_plusscale " + scale, "pushmenu plus_options_controls")
                c.send("popmenu 0")
                self.assert_options_tab(screen, "plus_options_controls", 4, msg,
                                        bar=self.OPTIONS_BAR[:-1] + ["defaults", "back"])
                names = list(screen["widgets"])
                i = names.index("bindlist")
                lst = screen["widgets"]["bindlist"]
                self.assertTrue(self.inside(lst["rect"], screen["widgets"]["panel"]["rect"]), msg)
                children = []
                for name in names[i + 1:]:
                    v = screen["widgets"][name]
                    if v["depth"] <= lst["depth"]:
                        break
                    children.append((name, v))
                self.assertTrue(children, msg)
                for name, v in children:
                    if v["shown"] and v["depth"] == lst["depth"] + 1:
                        self.assertTrue(self.inside(v["rect"], lst["rect"], slack=2), (msg, name, v["rect"], lst["rect"]))
                scroll = [v["rect"] for _, v in children if v["class"] == "UIVertScroll"]
                self.assertEqual(len(scroll), 1, msg)
                self.assertAlmostEqual(scroll[0][2], lst["rect"][2], delta=3, msg=(msg, scroll, lst["rect"]))
                # the rows are below the list
                labels = [v for n, v in screen["widgets"].items() if n.endswith(" label") and v["depth"] == 1]
                self.assertTrue(all(v["rect"][1] >= lst["rect"][3] for v in labels), msg)
            self.assertEqual(c.quit(), 0)

    def top_menu(self, c):
        return self.widgets(c)["menu"]

    def test_options_entry_opens_video(self):
        _, c = self.start(1280, 720)
        c.send(self.urc_command("main", "options"))
        time.sleep(2)
        self.assertEqual(self.top_menu(c), "plus_options_video")
        self.assertEqual(c.quit(), 0)

    def test_tabs_do_not_stack(self):
        # every tab entry opens its tab (as the .urc runs it), and after visiting them all Back
        # returns to the main menu in one step
        tabs = [("tab_video", "plus_options_video"), ("tab_detail", "plus_options_detail"),
                ("tab_audio", "plus_options_audio"), ("tab_controls", "plus_options_controls"),
                ("tab_game", "plus_options_game"), ("tab_plus", "plus_options")]
        _, c = self.start(1280, 720)
        c.send(self.urc_command("main", "options"))
        time.sleep(2)
        current = "plus_options_video"
        for tab, menu in tabs[1:] + tabs[:1]:
            c.send(self.urc_command(current, tab))
            time.sleep(1.5)
            self.assertEqual(self.top_menu(c), menu, (current, tab))
            current = menu
        c.send(self.urc_command(current, "back"))
        time.sleep(2)
        self.assertEqual(self.top_menu(c), "main")
        self.assertEqual(c.quit(), 0)

    def test_browser_layout(self):
        # the scroll bar at the list's right edge, a header about as high as a row, every column
        # title fits its column, the columns end at the scroll bar
        for w, h, scales in self.LAYOUT_SCREENS:
            _, c = self.start(w, h, *ServerBrowser.NO_MASTERS)
            for scale in scales:
                screen = self.widgets(c, "set ui_plusscale " + scale, "pushmenu plus_browser")
                c.send("popmenu 0")
                msg = (w, h, scale)
                self.assert_bar(screen, msg)
                lst = screen["widgets"]["netgamelist"]["rect"]
                scroll = next(v for v in screen["widgets"].values() if v["class"] == "UIVertScroll")["rect"]
                self.assertAlmostEqual(scroll[2], lst[2], delta=3, msg=(msg, scroll, lst))
                self.assertTrue(self.inside(scroll, lst), (msg, scroll, lst))
                self.assertLessEqual(screen["list"]["header"], 1.6 * screen["list"]["row"], msg)
                # rows are drawn at the list's scale, not at the HUD's (text was tiny at 1080p)
                self.assertAlmostEqual(screen["items"], h / 480 * float(scale), delta=0.01, msg=msg)
                columns = screen["columns"]
                self.assertGreaterEqual(len(columns), 6, msg)
                for col in columns:
                    self.assertLessEqual(col["text"], col["width"], (msg, col))
                end = columns[-1]["x"] + columns[-1]["width"]
                self.assertLessEqual(lst[0] + end, scroll[0] + 1, msg)
                self.assertGreater(lst[0] + end, scroll[0] - 0.02 * (lst[2] - lst[0]), msg)
            self.assertEqual(c.quit(), 0)

    def test_anchor_follows_screen_edges(self):
        for w, h in ((1280, 720), (2560, 1080)):
            _, _, rows = self.shot(w, h, "pushmenu plus_anchor_test")
            s = h / 480
            y = int(h * 0.6)
            green = [x for x in range(w) if rows[y][x][1] > 200 and rows[y][x][0] < 60]
            self.assertAlmostEqual(green[0], 220 * s, delta=2)
            self.assertAlmostEqual(green[-1] + 1, w - 20 * s, delta=2)
            x = w * 3 // 4
            column = [y for y in range(h) if rows[y][x][1] > 200 and rows[y][x][0] < 60]
            self.assertAlmostEqual(column[-1] + 1, h - 40 * s, delta=2)

    def test_browser_screen_opens(self):
        for w, h in ((1280, 720), (2560, 1080)):
            home, c = self.start(w, h)
            c.send("pushmenu plus_browser")
            time.sleep(2)
            _, _, rows = self.screenshot(home, c)
            log = c.log()
            self.assertEqual(c.quit(), 0)
            for error in ("UI EXCEPTION", "Failed to find resource type", "Couldn't find menu"):
                self.assertNotIn(error, log)
            # the content panel (a dark fill, unlike the red/blue tiles) ends 20 units from the right edge
            y = int(h * 0.6)
            panel = [x for x in range(w // 2, w) if rows[y][x][2] < 150]
            self.assertAlmostEqual(panel[-1] + 1, w - 20 * h / 480, delta=3, msg=(w, h))

    def test_original_screens_reachable(self):
        # the buttons that open the original screens, run as the .urc holds them
        cmds = []
        with zipfile.ZipFile(os.path.join(self.plus_dir, "plus", "zzz-plus.pk3")) as z:
            for urc, name in (("plus_browser", "createserver"), ("plus_browser", "playersetup"),
                              ("main", "warrecords")):
                text = z.read("ui/%s.urc" % urc).decode()
                cmds.append(re.search(r'name "%s".*?stuffcommand "([^"]*)"' % name, text, re.S).group(1))
        _, c = self.start(1280, 720)
        for cmd in cmds:
            c.send(cmd)
            time.sleep(1.5)
        log = c.log()
        self.assertEqual(c.quit(), 0)
        for error in ("UI EXCEPTION", "Failed to find resource type", "Couldn't find menu"):
            self.assertNotIn(error, log)

    def test_browser_names_without_version(self):
        # the Plus list has a Version column, so names are shown as the server sends them; the
        # original list keeps "(1.11) " before the name
        home = omoh.Home()
        self.addCleanup(home.cleanup)
        s = omoh.server(home, "+set", "sv_hostname", "Alpha", "+map", "dm/mohdm1")
        self.games.append(s)
        s.wait_for(r"==== InitGame ====")
        s.send("net_gamespy_port")
        qport = int(re.findall(r'"net_gamespy_port" is:"(\d+)', s.wait_for(r'"net_gamespy_port" is:"\d+'))[-1])
        home_c = omoh.Home()
        self.addCleanup(home_c.cleanup)
        home_c.write("serverhistory.txt", f"127.0.0.1:{s.port} {qport}\n")
        _, c = self.start(1920, 1080, *ServerBrowser.NO_MASTERS, "+set", "dm_browser_show", "3", home=home_c)
        lines = {}
        for menu in ("plus_browser", "joinnetgame"):
            c.send("pushmenu " + menu)
            time.sleep(2)
            mark = len(c.log())
            c.send("widgetcommand netgamelist refreshserverlist")
            time.sleep(6)
            c.send("widgetcommand netgamelist printlist")
            lines[menu] = c.wait_for(r"Server list \(\d+\):\n.*Alpha.*\n", start=mark, timeout=20)[mark:]
            c.send("popmenu 0")
            time.sleep(1)
        self.assertEqual(c.quit(), 0)
        self.assertRegex(lines["plus_browser"], r"\n  Alpha( \(recent\))? \|.*\| \d\.\d+")
        self.assertRegex(lines["joinnetgame"], r"\n   \(\d\.\d+[^)]*\) Alpha")

    def test_browser_columns_follow_width(self):
        # a list wider than 800 virtual units also shows the IP
        for w, h, columns in ((1280, 720, 6), (2560, 1080, 7)):
            home, c = self.start(w, h, *ServerBrowser.NO_MASTERS)
            c.send("pushmenu plus_browser")
            time.sleep(2)
            mark = len(c.log())
            c.send("widgetcommand netgamelist printlist")
            found = c.wait_for(r"Columns: \d+", start=mark, timeout=20)[mark:]
            self.assertEqual(c.quit(), 0)
            self.assertIn(f"Columns: {columns}", found, (w, h))

    def test_build_label_in_every_menu(self):
        # "OpenMOHAA-Plus <version> (<hash>)" bottom right in any menu, the original ones too, over
        # no widget's text
        _, c = self.start(1600, 900)
        for commands, menu in (((), "main"), (("pushmenu plus_options_video",), "plus_options_video"),
                               (("popmenu 0", "pushmenu options_main"), "options_main")):
            screen = self.widgets(c, *commands)
            command = commands
            self.assertEqual(screen.get("menu"), menu)
            label = screen.get("label")
            self.assertIsNotNone(label, menu)
            self.assertRegex(label["text"], r"^OpenMOHAA-Plus \d+\.\d+\.\d+-plus\.\d+\S*( \([0-9a-f]{7,}\))?$")
            x0, y0, x1, y1 = label["rect"]
            self.assertTrue(1600 * 0.6 < x0 < x1 <= 1600 and 900 * 0.9 < y0 < y1 <= 900, label)
            for name, w in screen["widgets"].items():
                if w["shown"] and "text" in w and w["title"].strip():
                    self.assertFalse(self.overlap(w["text"], label["rect"]), (command, name, w, label))
        self.assertEqual(c.quit(), 0)

    def test_slider_shows_its_value(self):
        # "showvalue" prints value * multiplier with its format right of the track; a format with
        # anything but one float conversion is refused and the slider stays as before
        _, c = self.start(1280, 720)
        screen = self.widgets(c, "set s_volume 0.8", "set r_gamma 1.5", "pushmenu plus_slider_test")
        self.assertEqual(screen["menu"], "plus_slider_test")
        sliders = screen["sliders"]
        self.assertEqual(sorted(sliders), ["gamma", "pct"], sliders)
        self.assertEqual(sliders["pct"]["value"], "80%")
        self.assertEqual(sliders["gamma"]["value"], "1.5")
        for name, sl in sliders.items():
            self.assertLessEqual(sl["track"][1], sl["text"][0], (name, sl))
            self.assertLessEqual(sl["text"][1], sl["rect"][2] + 1, (name, sl))
            self.assertGreater(sl["track"][1] - sl["track"][0], (sl["rect"][2] - sl["rect"][0]) / 2, (name, sl))
        self.assertEqual(c.quit(), 0)

    def test_pulldown_matches_every_set(self):
        # an item matches when every set in it matches (quotes and number formats aside); an item
        # without any set never matches, so the bare value shows
        cases = [("set r_mode -2", "Desktop", None),
                 ("set r_mode -1;set r_customwidth 1920;set r_customheight 1080", "1920x1080", None),
                 ("set r_mode -1;set r_customwidth 2560;set r_customheight 1440", "2560x1440", None),
                 ("set r_mode -1;set r_customwidth 1000;set r_customheight 1000", "Quoted", None),
                 ("set r_mode 5", "5", None),
                 ("set cg_effectdetail 1;set vss_maxcount 10", None, "Max"),
                 ("set cg_effectdetail 0.5;set vss_maxcount 23", None, "0.5")]
        _, c = self.start(1280, 720)
        for cvars, res, fx in cases:
            screen = self.widgets(c, cvars, "pushmenu plus_pulldown_test")
            c.send("popmenu 0")
            values = [p["value"] for p in screen["pulldowns"]]
            self.assertEqual(len(values), 2, (cvars, screen.get("menu")))
            if res:
                self.assertEqual(values[0], res, cvars)
            if fx:
                self.assertEqual(values[1], fx, cvars)
        self.assertEqual(c.quit(), 0)

    def test_plus_options_opens(self):
        # the pulldowns show their item from linkcvar: "reset" matches the default, an unknown value
        # is shown as is
        with zipfile.ZipFile(os.path.join(self.plus_dir, "plus", "zzz-plus.pk3")) as z:
            urc = z.read("ui/plus_options.urc").decode()
        for cvar in ("cl_renderer", "cl_language"):
            self.assertRegex(urc, r'name "%s list"[^}]*linkcvar "%s"' % (cvar, cvar))
        _, c = self.start(1280, 720)
        for language, expected in (("", "Game default"), ("xx", "xx")):
            screen = self.widgets(c, "reset cl_language" if not language else "set cl_language " + language,
                                  "pushmenu plus_options")
            c.send("popmenu 0")
            self.assertEqual(len(screen["pulldowns"]), 2, (screen.get("menu"), screen["pulldowns"]))
            pulldown = screen["pulldowns"][1]
            self.assertEqual(pulldown["value"], expected)
            self.assertLessEqual(pulldown["width"], pulldown["rect"][2] - pulldown["rect"][0] + 1, pulldown)
        log = c.log()
        self.assertEqual(c.quit(), 0)
        for error in ("UI EXCEPTION", "Failed to find resource type", "Couldn't find menu"):
            self.assertNotIn(error, log)

    def test_renderer_apply_restarts(self):
        # run the Apply button's command string as the .urc holds it
        with zipfile.ZipFile(os.path.join(self.plus_dir, "plus", "zzz-plus.pk3")) as z:
            urc = z.read("ui/plus_options.urc").decode()
        apply_cmd = re.search(r'name "apply".*?stuffcommand "([^"]*)"', urc, re.S).group(1)
        _, c = self.start(1280, 720)
        c.send("set r_customwidth 1000")                # latched: Apply restarts only for pending changes
        mark = len(c.log())
        c.send(apply_cmd)
        c.wait_for(r"Initializing Renderer", start=mark, timeout=60)
        self.assertEqual(c.quit(), 0)

    def assert_no_restart(self, c, command, seconds=5):
        mark = len(c.log())
        c.send(command)
        time.sleep(seconds)
        self.assertNotIn("Initializing Renderer", c.log()[mark:], command)

    def test_apply_latched_restarts_only_when_pending(self):
        _, c = self.start(1280, 720)
        self.assert_no_restart(c, "ui_applylatched")
        c.send("set r_customwidth 1000")                       # latched
        mark = len(c.log())
        c.send("ui_applylatched")
        c.wait_for(r"Initializing Renderer", start=mark, timeout=60)
        self.assertEqual(c.quit(), 0)

    def test_discard_latched_keeps_immediate_settings(self):
        _, c = self.start(1280, 720)
        c.send("set r_customwidth 1000")
        c.send("set s_volume 0.3")
        c.send("ui_discardlatched")
        mark = len(c.log())
        c.send("r_customwidth")
        c.send("s_volume")
        out = c.wait_for(r'"s_volume" is:"[^"]*"', start=mark, timeout=20)[mark:]
        self.assertNotIn("latched", out)
        self.assertIn('"s_volume" is:"0.3', out)
        self.assert_no_restart(c, "ui_applylatched")
        self.assertEqual(c.quit(), 0)

    def test_sound_quality_applies_and_back_restores(self):
        # s_khz is CVAR_SOUND_LATCH (never latched by the cvar code): Apply restarts sound when it
        # changed since the options opened, Back puts the old value back
        _, c = self.start(1280, 720)
        c.send(self.urc_command("main", "options"))
        time.sleep(2)
        c.send("set s_khz 22")
        mark = len(c.log())
        c.send("ui_applylatched")
        c.wait_for(r"Sound Shutdown", start=mark, timeout=30)
        c.send(self.urc_command("main", "options"))
        time.sleep(2)
        c.send("set s_khz 11")
        c.send("ui_discardlatched")
        mark = len(c.log())
        c.send("s_khz")
        self.assertIn('"s_khz" is:"22', c.wait_for(r'"s_khz" is:"[^"]*"', start=mark, timeout=20)[mark:])
        self.assertEqual(c.quit(), 0)

    def test_latches_from_before_the_options_are_left_alone(self):
        # a server cvar latched before the options opened (g_gametype for the next map) neither makes
        # Apply restart video nor is dropped by Back
        _, c = self.start(1280, 720)
        c.send("set g_gametype 2")
        c.send(self.urc_command("main", "options"))
        time.sleep(2)
        self.assert_no_restart(c, "ui_applylatched")
        c.send("ui_discardlatched")
        mark = len(c.log())
        c.send("g_gametype")
        self.assertIn('latched: "2"', c.wait_for(r'"g_gametype" is:[^\n]*\n(latched[^\n]*\n)?', start=mark,
                                                 timeout=20)[mark:] + c.log()[mark:])
        self.assertEqual(c.quit(), 0)

    def test_plus_scale_is_clamped(self):
        _, c = self.start(1280, 720)
        for value, expected in (("3", "1.1"), ("0.1", "0.85")):
            c.send("set ui_plusscale " + value)
            mark = len(c.log())
            c.send("ui_plusscale")
            found = c.wait_for(r'"ui_plusscale" is:"[^"]*"', start=mark, timeout=20)[mark:]
            self.assertIn('is:"%s' % expected, found)
        self.assertEqual(c.quit(), 0)

    def test_no_ui_errors(self):
        _, c = self.start(1280, 720)
        log = c.log()
        self.assertEqual(c.quit(), 0)
        for error in ("UI EXCEPTION", "Failed to find resource type", "Couldn't find menu"):
            self.assertNotIn(error, log)


# Mesa's software Vulkan driver, when installed: same pictures on every machine, no GPU needed
LAVAPIPE = "/usr/share/vulkan/icd.d/lvp_icd.json"


@require_game
@unittest.skipUnless(vulkan_renderer(), "renderer_vulkan was not built (needs the Vulkan headers)")
class VulkanRenderer(GameTestCase):
    # The Vulkan renderer is the GL1 renderer on an emulation of its GL calls: pictures must match.
    # Headless (SDL offscreen driver), it draws into its offscreen image only, which screenshots read.

    # fixed camera through sv_scripts (the spawn point is random)
    CAMERA = """main:
	level waittill spawn
	while (1) {
		if ($player.size > 0) {
			local.p = $player[1]
			if (local.p.dmteam == "spectator") {
				local.p join_team "allies"
				wait 2
				continue
			}
			local.p.origin = ( (float (getcvar "cam_x")) (float (getcvar "cam_y")) (float (getcvar "cam_z")) )
			local.p.viewangles = ( (float (getcvar "cam_pitch")) (float (getcvar "cam_yaw")) 0 )
			local.p physics_off
		}
		waitframe
	}
end
"""

    def shot(self, renderer, *args, map_name=None):
        home = omoh.Home()
        self.addCleanup(home.cleanup)
        env = {"VK_ICD_FILENAMES": LAVAPIPE} if os.path.exists(LAVAPIPE) else {}
        if map_name:
            home.write("global/cam.scr", self.CAMERA)
            args = args + ("+set", "sv_maxclients", "2", "+set", "g_gametype", "1", "+set", "sv_scripts",
                           "global/cam.scr", "+devmap", map_name)
        c = omoh.client(home, "+set", "cl_renderer", renderer, "+set", "r_mode", "3", *args, env=env)
        self.games.append(c)
        if map_name:
            c.wait_for(r"==== InitGame ====", timeout=120)
            time.sleep(30)
            c.send("popmenu 0")
            c.send("freezeplayer")
            time.sleep(3)
        else:
            c.wait_for(r"Opening IP socket", timeout=60)
            time.sleep(8)                      # the main menu is up
        c.send("screenshot silent")
        time.sleep(3)
        self.assertEqual(c.quit(), 0)
        if renderer == "vulkan":
            self.assertIn("Vulkan device:", c.log())
        shots = glob.glob(os.path.join(home.path, "main", "screenshots", "shot*.tga"))
        self.assertEqual(len(shots), 1)
        return read_tga(shots[0])

    def assertSamePicture(self, a, b, tolerance):
        wa, ha, ra = a
        wb, hb, rb = b
        self.assertEqual((wa, ha), (wb, hb))
        differing = sum(1 for y in range(ha) for x in range(wa) if sum(abs(p - q) for p, q in zip(ra[y][x], rb[y][x])) > 48)
        self.assertLess(differing / (wa * ha), tolerance, f"{differing} of {wa * ha} pixels differ")

    def test_falls_back_to_opengl_without_vulkan(self):
        home = omoh.Home()
        self.addCleanup(home.cleanup)
        c = omoh.client(home, "+set", "cl_renderer", "vulkan", env={"VK_ICD_FILENAMES": "/nonexistent.json"})
        self.games.append(c)
        c.wait_for(r"Vulkan could not start, using OpenGL", timeout=60)
        c.wait_for(r"Opening IP socket", timeout=60)
        self.assertEqual(c.quit(), 0)

    def test_main_menu_matches_opengl1(self):
        # measured: identical
        self.assertSamePicture(self.shot("opengl1"), self.shot("vulkan"), 0.001)

    @unittest.skipUnless(os.environ.get("OMOH_SLOW"), "slow (about 2 minutes); set OMOH_SLOW=1")
    def test_world_matches_opengl1(self):
        # Algiers from above: world, lightmaps, models, trees, sky and distance fog. Measured: 0.03%
        # of the pixels differ (swaying leaves)
        camera = ("+set", "cam_x", "-2112", "+set", "cam_y", "-1776", "+set", "cam_z", "1217",
                  "+set", "cam_pitch", "25", "+set", "cam_yaw", "45")
        self.assertSamePicture(self.shot("opengl1", *camera, map_name="dm/mohdm2"),
                               self.shot("vulkan", *camera, map_name="dm/mohdm2"), 0.01)


@require_game
@unittest.skipUnless(os.environ.get("OMOH_SLOW"), "slow (about 1 minute); set OMOH_SLOW=1")
class LagCompensation(GameTestCase):
    # The server script keeps a bot (huge health) swinging left and right in front of the player and points
    # the player's view at it every frame; the client, with 150 ms of outgoing delay, holds the trigger
    # of a submachine gun. Its view (the bullets follow the client's eyes) lags behind like a real
    # player's. g_antilag_debug logs, per shot, how far sideways the aim passes from the rewound bot
    # and from where it is now (pitch, recoil and spread left out, so the check is deterministic).
    SCRIPT = """main:
	level waittill spawn
	while (1) {
		local.human = NIL
		local.bot = NIL
		for (local.i = 1; local.i <= $player.size; local.i++) {
			local.p = $player[local.i]
			if (!(isBot local.p) && (local.p.dmteam == "allies" || local.p.dmteam == "axis")) local.human = local.p
		}
		for (local.i = 1; local.i <= $player.size; local.i++) {
			local.p = $player[local.i]
			if (local.human && (isBot local.p)) {
				if (local.p.dmteam == local.human.dmteam) {
					if (local.human.dmteam == "axis") local.p join_team "allies"
					else local.p join_team "axis"
				} else if (local.p.health > 0) local.bot = local.p
			}
		}
		if (local.human && local.bot) break
		wait 1
	}
	setcvar "g_bot_manualmove" "1"
	local.human nodamage
	local.bot.max_health = 1000000
	local.bot.health = 1000000
	wait 2
	local.base = local.human.origin
	local.eye = local.base + (0 0 82)
	local.found = 0
	for (local.yaw = 0; local.yaw < 360 && !local.found; local.yaw += 45) {
		local.fwd = angles_toforward (0 local.yaw 0)
		local.left = angles_toleft (0 local.yaw 0)
		local.c = local.base + local.fwd * 300 + (0 0 50)
		if ((sighttrace local.eye local.c 1) && (sighttrace local.eye (local.c + local.left * 160) 1) && (sighttrace local.eye (local.c - local.left * 160) 1)) {
			local.found = 1
		}
	}
	println ("TLAG open direction found=" + local.found)
	wait 3
	local.t0 = level.time
	while (level.time - local.t0 < 20) {
		local.t = level.time - local.t0
		local.bot.origin = local.base + local.fwd * 300 + local.left * (150 * sin (local.t * 45))
		local.human.origin = local.base
		local.dir = (local.bot.origin + (0 0 50)) - local.eye
		local.human.viewangles = vector_toangles local.dir
		waitframe
	}
	println "TLAG done"
end
"""

    def test_moving_target_with_150ms_lag(self):
        server_home = omoh.Home()
        self.addCleanup(server_home.cleanup)
        server_home.write("maps/dm/mohdm5.scr", self.SCRIPT)
        s = omoh.server(server_home, "+set", "developer", "1", "+set", "g_gametype", "2", "+set", "sv_maxclients", "4",
                        "+set", "sv_maxbots", "1", "+set", "sv_minPlayers", "2", "+set", "g_antilag", "1",
                        "+set", "g_antilag_debug", "1", "+map", "dm/mohdm5")
        self.games.append(s)
        s.wait_for(r"==== InitGame ====")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = omoh.client(client_home, "+set", "cl_packetdelay", "150", "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        s.wait_for(r"UnnamedSoldier.* has entered the battle", timeout=120)
        time.sleep(3)
        c.send("primarydmweapon smg")
        c.send("join_team axis")
        s.wait_for(r"TLAG open direction found=1", timeout=60)
        c.send("+attack")
        log = s.wait_for(r"TLAG done", timeout=60)
        c.send("-attack")
        c.quit()
        self.assertEqual(s.quit(), 0)
        shots = [tuple(map(float, m)) for m in
                 re.findall(r"antilag: .* rewound bot\d+ (\d+) ms; aim passes ([\d.]+) units from it, ([\d.]+)", log)]
        self.assertGreater(len(shots), 50)
        rewind = statistics.median(r for r, _, _ in shots)
        rewound = statistics.median(m for _, m, _ in shots)
        now = statistics.median(m for _, _, m in shots)
        # measured: rewinds 230 ms, aim 2 units from the rewound bot and 14 from where it is now
        self.assertTrue(150 < rewind < 300, rewind)
        self.assertLess(rewound, 6, (rewound, now))
        self.assertGreater(now, rewound * 3, (rewound, now))


@require_game
class Admin(GameTestCase):
    CONFIG = """// test policy
role mod allow admin.status admin.kick* admin.ban* cvar.*
role mod deny admin.ban
account jota roles mod
account jota allow admin.say
account jota deny cvar.fraglimit
"""

    def test_admin_accounts_roles_and_sessions(self):
        self.home.write("admin_config.txt", self.CONFIG)
        s = self.server("+set", "g_gametype", "1", "+map", "dm/mohdm1")
        s.wait_for(r"==== InitGame ====")
        s.send("admin_add jota pass-1234")
        s.send("admin_add nobody pass-5678")
        s.wait_for(r"Account nobody created")
        client_home = omoh.Home()
        self.addCleanup(client_home.cleanup)
        c = omoh.client(client_home, "+connect", f"127.0.0.1:{s.port}")
        self.games.append(c)
        s.wait_for(r"entered the battle", timeout=120)

        def run(line, expect):
            mark = len(c.log())
            c.send(line)
            return c.wait_for(expect, start=mark, timeout=20)[mark:]

        run("ad_status", r"Not logged in")
        run("ad_login jota wrong", r"Login failed")
        run("ad_login jota pass-1234", r"Too many failed logins")       # throttled right after a failure
        time.sleep(2.5)
        run("ad_login jota pass-1234", r"Logged in as jota")
        run("ad_help", r"Admin commands for jota: ad_logout ad_status ad_kick ad_say ad_set")   # admin.kick* does not cover admin.clientkick
        run("ad_status", r"map: dm/mohdm1")                               # console output reaches the admin
        run("ad_ban 0", r"Permission denied: admin.ban")                  # deny wins over admin.ban*
        run("ad_rcon status", r"Permission denied: admin.rcon")
        run("ad_set timelimit 15", r"timelimit is '15'")
        run("ad_set fraglimit 1", r"Permission denied: cvar.fraglimit")
        run("ad_set rconPassword x", r"Permission denied: cvar.rconPassword")  # cvar.* does not grant rcon
        run('ad_kick "x;quit"', r"Usage: ad_kick")                         # no second command
        s.send("admin_passwd jota pass-9999")
        c.wait_for(r"Admin session ended: password changed", timeout=20)
        run("ad_status", r"Not logged in")
        c.quit()
        s.send("timelimit")
        s.wait_for(r'"timelimit" is:"15"')
        self.assertEqual(s.quit(), 0)

        audit = open(self.home.file("admin.log")).read()
        for entry in (r"account=jota failed: ad_login", r"account=jota throttled: ad_login",
                      r"account=jota ok: ad_login", r"account=jota denied: ad_ban 0",
                      r"account=jota ok: status", r"account=jota ok: ad_set timelimit 15",
                      r"console \"\" account=jota ok: admin_passwd"):
            self.assertRegex(audit, entry)
        accounts = open(self.home.file("admin_accounts.txt")).read()
        for secret in ("pass-1234", "pass-5678", "pass-9999"):
            self.assertNotIn(secret, audit + accounts)
        self.assertRegex(accounts, r"account nobody 1 pbkdf2-sha256\$100000\$[0-9a-f]{32}\$[0-9a-f]{64}")


if __name__ == "__main__":
    unittest.main()
