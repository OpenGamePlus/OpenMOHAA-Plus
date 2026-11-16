#!/usr/bin/env python3
# Copyright (C) 2026 the OpenMOHAA Plus contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build plus/zzz-plus.pk3, the fork's data pack (menus, fonts, menu art).

  python3 misc/plus-pk3/build_pk3.py --out plus/zzz-plus.pk3 [--skip-fonts]

The pk3 holds misc/plus-pk3/data/**, the fonts from misc/fonts/make_fonts.py (unless --skip-fonts),
ART-LICENSE.md, the menu background as two 2048x2048 textures, textures/menu_plus/bg_l.tga and
bg_r.tga: the halves of art/background.jpg (3840x1600), each stretched anamorphically, and two
256x4 alpha gradients drawn by the menus: bar.tga (the dark left bar) and hover.tga (a highlighted
entry), and the pulldown field, textures/menu_plus/field.tga (see pulldown_field), with clear.tga, the
transparent pulldown arrow that only sets the clickable area, and checkbox_off.tga / checkbox_on.tga. Requires Pillow (python3 -m pip install pillow).
"""
import argparse
import io
import os
import subprocess
import sys
import tempfile
import zipfile

from PIL import Image, ImageDraw

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


def bar_alpha(x):
    """Opacity of the bar at x of its 300 virtual units: 0.9 to 0.65 over 0-200, then fading to 0 at 300."""
    return 0.9 - 0.25 * x / 200 if x < 200 else 0.65 * max(0.0, (300 - x) / 100)


def gradients():
    """(name, TGA bytes) of the bar and hover gradients, 256x4, left to right."""
    for name, rgb, alpha in (("bar", (10, 10, 8), lambda u: bar_alpha(u * 300)),
                             ("hover", (240, 191, 97), lambda u: 0.45 * (1 - u))):
        img = Image.new("RGBA", (256, 4))
        img.putdata([rgb + (round(255 * alpha(i / 255)),) for i in range(256)] * 4)
        out = io.BytesIO()
        img.save(out, "TGA")
        yield f"textures/menu_plus/{name}.tga", out.getvalue()


def pulldown_field():
    """(name, TGA bytes) of the pulldown field drawn over the 160x24 virtual units of a pulldown:
    border, dark see-through fill, a divider and a down arrow in the 24-unit cell at the right.
    White, so the widget's fgcolor tints it; 1024x128 (power of two), drawn in units."""
    w, h, uw, uh = 1024, 128, 160, 24
    sx, sy = w / uw, h / uh
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    white = (255, 255, 255)
    d.rectangle((0, 0, w - 1, h - 1), fill=(0, 0, 0, 110))
    t = 1.0                                                     # border, in units
    for box in ((0, 0, uw, t), (0, uh - t, uw, uh), (0, 0, t, uh), (uw - t, 0, uw, uh)):
        d.rectangle((round(box[0] * sx), round(box[1] * sy), round(box[2] * sx) - 1, round(box[3] * sy) - 1),
                    fill=white + (150,))
    x = uw - 24                                                 # divider of the arrow cell
    d.rectangle((round(x * sx), round(4 * sy), round((x + 0.8) * sx) - 1, round((uh - 4) * sy) - 1),
                fill=white + (110,))
    cx, cy = uw - 12, uh / 2
    d.polygon([(round((cx - 5) * sx), round((cy - 2.5) * sy)), (round((cx + 5) * sx), round((cy - 2.5) * sy)),
               (round(cx * sx), round((cy + 3) * sy))], fill=white + (255,))
    for name, image in (("field", img), ("clear", Image.new("RGBA", (8, 8), (0, 0, 0, 0)))):
        out = io.BytesIO()
        image.save(out, "TGA")
        yield f"textures/menu_plus/{name}.tga", out.getvalue()


def checkbox():
    """(name, TGA bytes) of the checkbox, off and on: the field's border and fill, a tick when on.
    White, so the widget's fgcolor tints it; 64x64 over its 24x24 virtual units."""
    for name, tick in (("checkbox_off", False), ("checkbox_on", True)):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, 63, 63), fill=(0, 0, 0, 110), outline=(255, 255, 255, 150), width=3)
        if tick:
            d.line([(14, 34), (27, 47), (50, 17)], fill=(255, 255, 255, 255), width=8, joint="curve")
        out = io.BytesIO()
        img.save(out, "TGA")
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
        for name, data in [*tiles(), *gradients(), *pulldown_field(), *checkbox()]:
            z.writestr(name, data)
        z.write(os.path.join(HERE, "ART-LICENSE.md"), "ART-LICENSE.md")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
