#!/usr/bin/env python3
# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build plus/zzz-plus.pk3, the fork's data pack (menus, fonts, menu art).

  python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3 [--skip-fonts]

The pk3 holds misc/plus-pk3/data/**, the fonts from misc/fonts/make_fonts.py (unless --skip-fonts),
ART-LICENSE.md and the menu background as two 2048x2048 textures, textures/menu_plus/bg_l.tga and
bg_r.tga: the halves of art/background.jpg (3840x1600), each stretched anamorphically. Requires
Pillow (python3 -m pip install pillow).
"""
import argparse
import io
import os
import subprocess
import sys
import tempfile
import zipfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
TILE = 2048


def tiles():
    """(name, TGA bytes) of the left and right half of the art, each stretched to TILE x TILE."""
    art = Image.open(os.path.join(HERE, "art", "background.jpg")).convert("RGB")
    half = art.width // 2
    for name, box in (("bg_l", (0, 0, half, art.height)), ("bg_r", (half, 0, art.width, art.height))):
        out = io.BytesIO()
        art.crop(box).resize((TILE, TILE), LANCZOS).save(out, "TGA")
        yield f"textures/menu_plus/{name}.tga", out.getvalue()


def add_tree(z, root):
    for folder, _, files in os.walk(root):
        for f in sorted(files):
            if not f.startswith("."):  # .gitkeep
                path = os.path.join(folder, f)
                z.write(path, os.path.relpath(path, root).replace(os.sep, "/"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="the .pk3 file to write")
    ap.add_argument("--skip-fonts", action="store_true", help="do not run misc/fonts/make_fonts.py")
    args = ap.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
        add_tree(z, os.path.join(HERE, "data"))
        if not args.skip_fonts:
            fonts = os.path.join(tmp, "fonts") + os.sep
            subprocess.run([sys.executable, os.path.join(HERE, "..", "fonts", "make_fonts.py"), "--out", fonts],
                           check=True)
            add_tree(z, fonts)
        for name, data in tiles():
            z.writestr(name, data)
        z.write(os.path.join(HERE, "ART-LICENSE.md"), "ART-LICENSE.md")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
