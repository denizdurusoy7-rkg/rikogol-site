#!/usr/bin/env python3
"""Derive every web asset of rikogol.com from the originals kept in the repo.

Originals (never modified here):
  press/files/rikogol-key-art.jpg        3840x1240 key art (Steam library hero)
  press/files/rikogol-logo.png           1280x362 transparent logo
  press/files/rikogol-icon-1024.png      app icon
  press/files/rikogol-*-capsule.jpg      live Steam capsules
  press/files/rikogol-screenshot-NN.jpg  live Steam screenshots, 1920x1080
  assets/video/rikogol-trailer.mp4       web trailer (see encode_trailer below)

Outputs: assets/img/**, assets/fonts/*.woff2, favicon.ico.

Needs Pillow with WebP support. Fonts (--fonts DIR) also need fontTools + brotli;
the TTF sources live in the game repo (Assets/_Game/Art/Fonts, tools/keyart/fonts).

  python3 tools/make_assets.py                 # images + poster
  python3 tools/make_assets.py --fonts DIR     # also subset fonts to woff2
  python3 tools/make_assets.py --trailer SRC   # also re-encode the trailer from SRC

Trailer source: the English trailer from the Steam appdetails `movies` HLS stream
(1080p60, 50 s), downloaded once with ffmpeg -i <hls video> -i <hls audio> -c copy.
"""
import argparse
import os
import subprocess
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = os.path.join(ROOT, "press", "files")
IMG = os.path.join(ROOT, "assets", "img")


def out(*parts):
    path = os.path.join(IMG, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def resize(im, width):
    if im.width == width:
        return im.copy()
    height = round(im.height * width / im.width)
    return im.resize((width, height), Image.LANCZOS)


def save_webp(im, path, quality, alpha=False):
    if not alpha and im.mode != "RGB":
        im = im.convert("RGB")
    im.save(path, "WEBP", quality=quality, method=6)
    return os.path.getsize(path)


def report(path, size):
    print(f"  {os.path.relpath(path, ROOT)}  {size // 1024} KB")


def hero():
    src = Image.open(os.path.join(FILES, "rikogol-key-art.jpg"))
    for w in (960, 1440, 1920, 2560):
        p = out("hero", f"rikogol-hero-{w}.webp")
        report(p, save_webp(resize(src, w), p, 74))


def logo():
    src = Image.open(os.path.join(FILES, "rikogol-logo.png")).convert("RGBA")
    for w in (480, 720, 960, 1280):
        p = out("logo", f"rikogol-logo-{w}.webp")
        report(p, save_webp(resize(src, w), p, 88, alpha=True))


def screenshots():
    for n in range(1, 17):
        src = Image.open(os.path.join(FILES, f"rikogol-screenshot-{n:02d}.jpg"))
        for w, q in ((640, 76), (960, 78), (1280, 80)):
            p = out("screens", f"rikogol-screenshot-{n:02d}-{w}.webp")
            size = save_webp(resize(src, w), p, q)
            if size > 250 * 1024:
                sys.exit(f"{p} is {size} bytes, over the 250 KB budget")
            report(p, size)


def press_previews():
    for name, w in (("header-capsule", 460), ("main-capsule", 616),
                    ("vertical-capsule", 374), ("key-art", 960)):
        src = Image.open(os.path.join(FILES, f"rikogol-{name}.jpg"))
        p = out("press", f"rikogol-{name}-{w}.webp")
        report(p, save_webp(resize(src, w), p, 80))
    src = Image.open(os.path.join(FILES, "rikogol-logo.png")).convert("RGBA")
    p = out("press", "rikogol-logo-480.webp")
    report(p, save_webp(resize(src, 480), p, 88, alpha=True))
    src = Image.open(os.path.join(FILES, "rikogol-icon-1024.png")).convert("RGBA")
    p = out("press", "rikogol-icon-256.webp")
    report(p, save_webp(resize(src, 256), p, 88, alpha=True))


def icons():
    src = Image.open(os.path.join(FILES, "rikogol-icon-1024.png")).convert("RGBA")
    for w in (32, 64, 192, 512):
        p = out("icons", f"icon-{w}.png")
        resize(src, w).save(p, "PNG", optimize=True)
        report(p, os.path.getsize(p))
    # iOS masks the icon itself and shows transparency as black: flatten onto the pitch green.
    flat = Image.new("RGBA", src.size, (39, 101, 65, 255))
    flat.alpha_composite(src)
    p = out("icons", "apple-touch-icon.png")
    resize(flat.convert("RGB"), 180).save(p, "PNG", optimize=True)
    report(p, os.path.getsize(p))
    ico = os.path.join(ROOT, "favicon.ico")
    src.save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    report(ico, os.path.getsize(ico))


def poster():
    video = os.path.join(ROOT, "assets", "video", "rikogol-trailer.mp4")
    png = os.path.join(ROOT, "assets", "video", "_poster.png")
    # 12.0 s: both full teams lined up for an 11v11 kick-off, no text card on screen.
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "12.0",
                    "-i", video, "-frames:v", "1", png], check=True)
    im = Image.open(png)
    p = os.path.join(ROOT, "assets", "video", "rikogol-trailer-poster.webp")
    report(p, save_webp(im, p, 80))
    p = os.path.join(ROOT, "assets", "video", "rikogol-trailer-poster.jpg")
    im.convert("RGB").save(p, "JPEG", quality=84, optimize=True, progressive=True)
    report(p, os.path.getsize(p))
    os.remove(png)


def encode_trailer(src):
    """H.264 High, 1280x720 at the source 60 fps, two-pass 1.7 Mb/s + AAC 128 kb/s, faststart.
    Measured on the 50 s trailer: 11.7 MB, visually identical to the 1080p source at 1:1 crops."""
    dst = os.path.join(ROOT, "assets", "video", "rikogol-trailer.mp4")
    common = ["-vf", "scale=1280:720:flags=lanczos,fps=60", "-c:v", "libx264", "-preset", "slow",
              "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-b:v", "1700k"]
    log = os.path.join(ROOT, "assets", "video", "_x264pass")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src] + common +
                   ["-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src] + common +
                   ["-maxrate", "2600k", "-bufsize", "3400k", "-pass", "2", "-passlogfile", log,
                    "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-ar", "48000",
                    "-movflags", "+faststart", dst], check=True)
    for f in os.listdir(os.path.dirname(log)):
        if f.startswith("_x264pass"):
            os.remove(os.path.join(os.path.dirname(log), f))
    size = os.path.getsize(dst)
    if size > 12 * 1000 * 1000:
        sys.exit(f"trailer is {size} bytes, over the 12 MB budget")
    report(dst, size)


# Latin (incl. Turkish, French, German, Portuguese, Spanish), punctuation, Cyrillic.
LATIN = "U+0000-00FF,U+0131,U+0152-0153,U+0100-017F,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
CYRILLIC = "U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116"


def fonts(src_dir):
    from fontTools import subset  # noqa: needs fontTools + brotli

    jobs = (
        ("Oswald-Bold.ttf", "oswald-bold.woff2", LATIN + "," + CYRILLIC),
        ("Manrope-Regular.ttf", "manrope-regular.woff2", LATIN + "," + CYRILLIC),
        ("Kanit-BlackItalic.ttf", "kanit-blackitalic.woff2", LATIN),  # Kanit has no Cyrillic
    )
    for ttf, woff2, ranges in jobs:
        dst = os.path.join(ROOT, "assets", "fonts", woff2)
        subset.main([os.path.join(src_dir, ttf), f"--unicodes={ranges}", "--layout-features=*",
                     "--name-IDs=*", "--name-legacy", "--name-languages=*", "--flavor=woff2",
                     f"--output-file={dst}"])
        report(dst, os.path.getsize(dst))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", help="directory holding the OFL TTF sources")
    ap.add_argument("--trailer", help="source video to re-encode into assets/video")
    a = ap.parse_args()
    if a.trailer:
        encode_trailer(a.trailer)
    hero()
    logo()
    screenshots()
    press_previews()
    icons()
    poster()
    if a.fonts:
        fonts(a.fonts)


if __name__ == "__main__":
    main()
