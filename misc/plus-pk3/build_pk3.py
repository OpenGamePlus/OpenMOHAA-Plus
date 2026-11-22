#!/usr/bin/env python3
# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build plus/zzz-plus.pk3, the fork's fonts, and the Remake menu pak.

  python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3 [--skip-fonts]

The pk3 holds the fonts from misc/fonts/make_fonts.py (unless --skip-fonts). Requires Pillow
(python3 -m pip install pillow).

  python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3 --remake <export root> [--remake-out PATH]

also writes the Remake menu pak (default zzzz-plus-remake.pk3 next to --out, so it loads after
zzz-plus.pk3) from misc/plus-pk3/remake/*.json and a Blender export (remake/export_hotspots.py),
with ART-LICENSE.md and textures/menu_plus/clear.tga, the transparent shader of its pulldowns and
buttons; see remake/pak.py.
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


def write_remake(out, export_root, mapping_dir):
    """Writes the Remake menu pak (see remake/pak.py)."""
    from remake import pak as build_remake
    sys.path.insert(0, os.path.join(HERE, "..", "fonts"))
    import make_fonts
    tmp = out + ".tmp"  # a failed build (broken export) must not leave a truncated pak over the old one
    try:
        _write_remake_zip(tmp, build_remake, make_fonts, export_root, mapping_dir)
        os.replace(tmp, out)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f"wrote {out}")


def _write_remake_zip(out, build_remake, make_fonts, export_root, mapping_dir):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("textures/menu_plus/clear.tga", clear())
        z.write(os.path.join(HERE, "ART-LICENSE.md"), "ART-LICENSE.md")
        for name, data in build_remake.files(mapping_dir, export_root):
            z.writestr(name, data)
        # the sign font ships here too: it is not in the game, and without it next to an older or
        # --skip-fonts zzz-plus.pk3 the menu stops with "Couldn't load font"
        chalk = os.path.join(HERE, "..", "fonts", "ofl", "cabinsketch")
        for font, ttf in (("plussign-32", os.path.join(make_fonts.DEJAVU, make_fonts.DEFAULT_SET["plussign-32"])),
                          ("pluschalk-32", os.path.join(chalk, "CabinSketch-Bold.ttf"))):   # the credits board's chalk
            text, tga, _ = make_fonts.build(font, 32, ttf, 3)
            z.writestr(f"fonts/{font}.RitualFont", text.encode("ascii"))
            z.writestr(f"gfx/fonts/{font}.tga", tga)
        with open(os.path.join(chalk, "OFL.txt"), "rb") as f:   # the OFL goes with the font made from it
            z.writestr("fonts/pluschalk-32-OFL.txt", f.read())


def clear():
    """TGA bytes of an 8x8 fully transparent picture."""
    out = io.BytesIO()
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(out, "TGA")
    return out.getvalue()


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
    ap.add_argument("--remake", metavar="EXPORT_ROOT", help="also write the Remake menu pak from this Blender export")
    ap.add_argument("--remake-out", help="the Remake pak (default: zzzz-plus-remake.pk3 next to --out)")
    ap.add_argument("--remake-mappings", default=os.path.join(HERE, "remake"), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
        if not args.skip_fonts:
            fonts = os.path.join(tmp, "fonts") + os.sep
            subprocess.run([sys.executable, os.path.join(HERE, "..", "fonts", "make_fonts.py"), "--out", fonts],
                           check=True)
            add_tree(z, fonts)
    print(f"wrote {args.out}")
    if args.remake:
        write_remake(args.remake_out or os.path.join(os.path.dirname(os.path.abspath(args.out)), "zzzz-plus-remake.pk3"),
                     args.remake, args.remake_mappings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
