#!/usr/bin/env python3
"""Prepare the "Kuki" cookie PNGs for the site.

The source artwork (in SRC_DIR) are hand-drawn line illustrations exported as
PNGs with real per-pixel alpha, but each drawing sits in the middle of a huge,
mostly-transparent canvas. This script crops each image tightly to its alpha
bounding box (with a little padding) at FULL native resolution/quality — no
downscaling, no re-vectorizing — so the art looks crisp on the site.

The site recolors these to the current theme color at runtime (see
buildKukiSvgDataUri()/recolorKukiImages() in index.html) by wrapping the
cropped PNG in an SVG <mask>, so no color processing happens here.

Run:  python3 scripts/build_kuki.py
Out:  assets/kuki/kuki1.png .. kuki8.png  and  assets/kuki/mochikuk3.png
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = "/Users/zen/Desktop/kuki"
OUT_DIR = os.path.join(ROOT, "assets", "kuki")
PAD = 24  # padding (px, at native resolution) kept around the cropped art

SOURCES = [
    ("Untitled_Artwork 49.png", "kuki1.png"),
    ("Untitled_Artwork 50.png", "kuki2.png"),
    ("Untitled_Artwork 51.png", "kuki3.png"),
    ("Untitled_Artwork 52.png", "kuki4.png"),
    ("Untitled_Artwork 53.png", "kuki5.png"),
    ("Untitled_Artwork 54.png", "kuki6.png"),
    ("Untitled_Artwork 55.png", "kuki7.png"),
    ("Untitled_Artwork 56.png", "kuki8.png"),
    ("Mochikuk3.png", "mochikuk3.png"),
]


def crop_to_alpha_bbox(im, pad=PAD, alpha_threshold=8):
    im = im.convert("RGBA")
    alpha = im.split()[3]
    # Threshold faint anti-aliased noise out of the bbox calculation
    mask = alpha.point(lambda a: 255 if a > alpha_threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(im.width, r + pad)
    b = min(im.height, b + pad)
    return im.crop((l, t, r, b))


def main():
    if not os.path.isdir(SRC_DIR):
        print(f"Source dir not found: {SRC_DIR}")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    for src_name, out_name in SOURCES:
        src_path = os.path.join(SRC_DIR, src_name)
        if not os.path.isfile(src_path):
            print(f"  SKIP (missing): {src_name}")
            continue
        im = Image.open(src_path)
        cropped = crop_to_alpha_bbox(im)
        out_path = os.path.join(OUT_DIR, out_name)
        cropped.save(out_path, "PNG", optimize=True)
        kb = os.path.getsize(out_path) / 1024
        print(f"  OK  {src_name} -> assets/kuki/{out_name} "
              f"({cropped.width}x{cropped.height}, {kb:.0f} KB)")
    print("Done.")


if __name__ == "__main__":
    main()
