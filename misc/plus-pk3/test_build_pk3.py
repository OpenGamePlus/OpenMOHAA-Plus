# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Unit tests for build_pk3.py (need Pillow; skipped otherwise)."""
import io
import os
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from PIL import Image
except ImportError:  # Pillow missing
    Image = None


@unittest.skipUnless(Image, "needs Pillow")
class BuildPk3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global build_pk3
        import build_pk3
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pk3 = os.path.join(cls.tmp.name, "zzz-plus.pk3")
        assert build_pk3.main(["--out", cls.pk3, "--skip-fonts"]) == 0
        cls.zip = zipfile.ZipFile(cls.pk3)

    @classmethod
    def tearDownClass(cls):
        cls.zip.close()
        cls.tmp.cleanup()

    def tile(self, name):
        return Image.open(io.BytesIO(self.zip.read(f"textures/menu_plus/{name}.jpg"))).convert("RGB")

    def test_pk3_holds_data_tree_tiles_and_license(self):
        names = set(self.zip.namelist())
        expected = {f"textures/menu_plus/{n}.jpg" for n in ("bg_l", "bg_r", "opt_l", "opt_r")} | {"ART-LICENSE.md"}
        data = os.path.join(HERE, "data")
        for root, _, files in os.walk(data):
            for f in files:
                if not f.startswith("."):
                    expected.add(os.path.relpath(os.path.join(root, f), data).replace(os.sep, "/"))
        self.assertTrue(expected <= names, expected - names)

    def test_pulldown_field(self):
        """The pulldown field: white border and arrow (tinted by the widget), dark see-through fill,
        power of two; the arrow cell and the clear click texture."""
        field = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/field.tga"))).convert("RGBA")
        self.assertEqual(field.size, (1024, 128))
        w, h = field.size
        self.assertEqual(field.getpixel((w // 2, 1))[:3], (255, 255, 255))      # top border
        self.assertGreater(field.getpixel((w // 2, 1))[3], 100)
        fill = field.getpixel((w // 3, h // 2))
        self.assertLess(max(fill[:3]), 10)
        self.assertTrue(30 < fill[3] < 160, fill)
        cx = w - round(12 * w / 160)                                             # the arrow cell is 24 units
        self.assertEqual(field.getpixel((cx, h // 2))[:3], (255, 255, 255))
        clear = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/clear.tga"))).convert("RGBA")
        self.assertEqual({px[3] for px in clear.getdata()}, {0})

    def test_checkbox(self):
        """Checkbox textures: white border, dark see-through fill, a white tick only when on."""
        on, off = (Image.open(io.BytesIO(self.zip.read(f"textures/menu_plus/checkbox_{n}.tga"))).convert("RGBA")
                   for n in ("on", "off"))
        for img in (on, off):
            self.assertEqual(img.size, (64, 64))
            self.assertEqual(img.getpixel((32, 1))[:3], (255, 255, 255))
            self.assertGreater(img.getpixel((32, 1))[3], 100)
        fill = off.getpixel((32, 32))
        self.assertLess(max(fill[:3]), 10)
        self.assertTrue(30 < fill[3] < 160, fill)
        ink = lambda img: sum(1 for x in range(8, 56) for y in range(8, 56) if img.getpixel((x, y))[3] > 200)
        self.assertEqual(ink(off), 0)
        self.assertGreater(ink(on), 100)

    def test_tiles_are_power_of_two(self):
        for name in ("bg_l", "bg_r", "opt_l", "opt_r"):
            self.assertEqual(self.tile(name).size, (2048, 2048))

    def test_tiles_split_the_art_in_halves(self):
        """Each background (main menu, options) is split in a left and right tile."""
        for prefix, art_file in (("bg", "background.jpg"), ("opt", "background_options.jpg")):
            art = Image.open(os.path.join(HERE, "art", art_file)).convert("RGB")
            w, h = art.size
            self.assertEqual((w, h), (3840, 1600))
            for y in (100, 800, 1500):
                ty = round(y * 2048 / h)
                for got, want in ((self.tile(prefix + "_l").getpixel((0, ty)), art.getpixel((0, y))),
                                  (self.tile(prefix + "_r").getpixel((2047, ty)), art.getpixel((w - 1, y)))):
                    self.assertTrue(all(abs(a - b) < 24 for a, b in zip(got, want)), (prefix, y, got, want))

    def test_bar_gradient_fades_out(self):
        bar = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/bar.tga")))
        self.assertEqual((bar.mode, bar.size), ("RGBA", (256, 4)))
        alphas = [bar.getpixel((x, 0))[3] for x in range(256)]
        self.assertGreater(alphas[0], 200)
        self.assertEqual(alphas[-1], 0)
        self.assertEqual(alphas, sorted(alphas, reverse=True))


if __name__ == "__main__":
    unittest.main()
