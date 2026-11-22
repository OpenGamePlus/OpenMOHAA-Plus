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

    def test_pk3_holds_no_menu(self):
        # the Plus menu is gone: no ui/ files, no menu art (the Remake pak brings its own)
        self.assertEqual(self.zip.namelist(), [])     # --skip-fonts: nothing else goes in


if __name__ == "__main__":
    unittest.main()
