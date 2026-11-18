"""Image pipeline for winnipegsd.com.

Makes AVIF and WebP copies of every site image at the sizes they actually
render, recompresses the original JPG fallbacks, strips EXIF, and builds the
social share JPG. Safe to re-run any time an image is added or replaced:
edit PLAN below, then run `python3 tools/build-images.py` from the repo root.

Output goes to assets/opt/. Original file names in assets/ never change,
because Google Images and old links may point at them.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets"
OUT = SRC / "opt"

# image file -> widths to generate. Widths come from measuring each image's
# rendered size at 412 px (x2 for phone screens) and 1440 px.
PLAN = {
    "camera-in-line.jpg": [480, 760, 960],
    "camera-monitor.jpg": [480, 760, 960],
    "clay-tile-hero.jpg": [480, 760, 960],
    "clogged-sink.jpg": [480, 760, 960],
    "drain-cleaning-hero.jpg": [480, 760, 960],
    "frozen-sewer-hero.jpg": [480, 760, 960],
    "hydro-jet.jpg": [480, 760, 960],
    "property-manager-hero.jpg": [480, 760, 960],
    "restaurant-hero.jpg": [480, 760, 960],
    "sewer-line-repair-trench.jpg": [480, 760, 960],
    "winnipeg-neighbourhood-map.png": [480, 760, 960],
    "wsd-van.jpg": [480, 760, 960],
    "hero-image.jpg": [520, 800],
    "wsd-logo-primary.png": [128, 256],
}

AVIF_QUALITY = 50
WEBP_QUALITY = 75
JPG_QUALITY = 78
FALLBACK_MAX_WIDTH = 1200  # originals wider than this get shrunk once; smaller ones are left alone


def resized(im, width):
    if im.width <= width:
        return im.copy()
    height = round(im.height * width / im.width)
    return im.resize((width, height), Image.LANCZOS)


def build_derivatives():
    OUT.mkdir(exist_ok=True)
    for name, widths in PLAN.items():
        src = SRC / name
        im = Image.open(src)
        im = im.convert("RGBA" if im.mode in ("RGBA", "P", "LA") and name.endswith(".png") else "RGB")
        stem = src.stem
        for w in widths:
            small = resized(im, w)
            small.save(OUT / f"{stem}-{w}.avif", quality=AVIF_QUALITY)
            small.save(OUT / f"{stem}-{w}.webp", quality=WEBP_QUALITY, method=6)


def recompress_fallbacks():
    """Shrink oversized original JPGs and drop EXIF (GPS included).

    Only touches files wider than FALLBACK_MAX_WIDTH, so re-running the
    script never re-compresses the same file twice.
    """
    for name in PLAN:
        if not name.endswith(".jpg"):
            continue
        path = SRC / name
        im = Image.open(path)
        if im.width <= FALLBACK_MAX_WIDTH:
            continue
        im = resized(im.convert("RGB"), FALLBACK_MAX_WIDTH)
        im.save(path, quality=JPG_QUALITY, optimize=True, progressive=True)


def build_share_image():
    """Social share image: 1200 x 630 JPG under 200 KB (platforms don't read AVIF)."""
    src = SRC / "og-share.png"
    im = Image.open(src).convert("RGB").resize((1200, 630), Image.LANCZOS)
    im.save(SRC / "og-share.jpg", quality=82, optimize=True, progressive=True)


if __name__ == "__main__":
    build_derivatives()
    recompress_fallbacks()
    build_share_image()
    for f in sorted(OUT.iterdir()):
        print(f"{f.name:48} {f.stat().st_size / 1024:7.1f} KB")
