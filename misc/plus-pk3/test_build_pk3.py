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
        cls.art = Image.open(os.path.join(HERE, "art", "background.jpg")).convert("RGB")

    @classmethod
    def tearDownClass(cls):
        cls.zip.close()
        cls.tmp.cleanup()

    def tile(self, name):
        return Image.open(io.BytesIO(self.zip.read(f"textures/menu_plus/{name}.tga"))).convert("RGB")

    def test_pk3_holds_data_tree_tiles_and_license(self):
        names = set(self.zip.namelist())
        expected = {"textures/menu_plus/bg_l.tga", "textures/menu_plus/bg_r.tga", "ART-LICENSE.md"}
        data = os.path.join(HERE, "data")
        for root, _, files in os.walk(data):
            for f in files:
                if not f.startswith("."):
                    expected.add(os.path.relpath(os.path.join(root, f), data).replace(os.sep, "/"))
        self.assertTrue(expected <= names, expected - names)

    def test_tiles_are_power_of_two(self):
        for name in ("bg_l", "bg_r"):
            self.assertEqual(self.tile(name).size, (2048, 2048))

    def test_tiles_split_the_art_in_halves(self):
        w, h = self.art.size
        self.assertEqual((w, h), (3840, 1600))
        for y in (100, 800, 1500):
            ty = round(y * 2048 / h)
            for got, want in ((self.tile("bg_l").getpixel((0, ty)), self.art.getpixel((0, y))),
                              (self.tile("bg_r").getpixel((2047, ty)), self.art.getpixel((w - 1, y)))):
                self.assertTrue(all(abs(a - b) < 24 for a, b in zip(got, want)), (y, got, want))

    def test_bar_gradient_fades_out(self):
        bar = Image.open(io.BytesIO(self.zip.read("textures/menu_plus/bar.tga")))
        self.assertEqual((bar.mode, bar.size), ("RGBA", (256, 4)))
        alphas = [bar.getpixel((x, 0))[3] for x in range(256)]
        self.assertGreater(alphas[0], 200)
        self.assertEqual(alphas[-1], 0)
        self.assertEqual(alphas, sorted(alphas, reverse=True))


if __name__ == "__main__":
    unittest.main()
