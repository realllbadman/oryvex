"""Import real product photos → static/images/vials/<slug>.png.

Removes the near-white studio background (only the region connected to the
image border, so interior label/glass whites are kept) and writes a trimmed,
transparent PNG sized for the site.

Usage:
  python3 scripts/import_photos.py [--preview SLUG]
Edit MAPPING below to point each source file at a product slug.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

HOME = os.path.expanduser("~")
SRC = os.path.join(HOME, "Downloads", "oryvex")
if not os.path.isdir(SRC):                 # fall back to the Downloads root
    SRC = os.path.join(HOME, "Downloads")
OUT = os.path.join("static", "images", "vials")
os.makedirs(OUT, exist_ok=True)

# source filename → product slug
MAPPING = {
    # ── Sep 8 re-shoot: one consistent vial design across the whole catalog.
    # Supersedes every earlier batch. Silver flip-off caps on lyophilised vials,
    # red pumps on the mist applicators, identical label geometry throughout.
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.14.jpeg": "5-amino-1mq",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.15.jpeg": "bpc-157",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.16.jpeg": "ahk-cu",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.17.jpeg": "ara-290",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.18.jpeg": "bacteriostatic-water",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.19.jpeg": "bpc-157-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.20 (1).jpeg": "cjc-1295-no-dac",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.20 (2).jpeg": "cjc-1295-ipamorelin",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.20.jpeg": "cagrilintide",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.21 (1).jpeg": "foxo4-dri",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.21 (2).jpeg": "ghk-cu",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.21 (3).jpeg": "glow",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.21.jpeg": "epithalon",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.22 (1).jpeg": "glp-2",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.22 (2).jpeg": "glp-3rt",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.22 (3).jpeg": "glutathione",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.22.jpeg": "glp-1t",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.23 (1).jpeg": "dsip-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.23 (2).jpeg": "igf1-lr3",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.23 (3).jpeg": "ipamorelin",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.23 (4).jpeg": "kisspeptin",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.23.jpeg": "dsip",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.24 (1).jpeg": "kpv",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.24 (2).jpeg": "kpv-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.24 (3).jpeg": "ll-37",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.24.jpeg": "klow",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25 (1).jpeg": "mt-1",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25 (2).jpeg": "mt-2",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25 (3).jpeg": "mt-2-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25.jpeg": "mots-c",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.26 (1).jpeg": "nad-plus",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.26 (2).jpeg": "peg-mgf",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.26 (3).jpeg": "pinealon",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.26.jpeg": "n-acetyl-epitalon",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.27 (1).jpeg": "pt-141-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.27 (2).jpeg": "selank",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.27 (3).jpeg": "selank-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.27.jpeg": "pt-141",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.28 (1).jpeg": "semax-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.28 (2).jpeg": "slu-pp-332",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.28 (3).jpeg": "ss31",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.28.jpeg": "semax",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.29 (1).jpeg": "tesamorelin",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.29 (2).jpeg": "thymosin-alpha-1",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.29 (3).jpeg": "wolverine-blend",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.29.jpeg": "tb-500",
}

MAXDIM = 900          # cap output size
LIGHT = 170           # min per-channel value considered "background-light"
SAT = 30              # max (max-min channel) considered "neutral" (unsaturated)
EDGE = 13             # gradient above this = vial silhouette → flood stops here
TOL = 30              # per-channel distance from a sampled backdrop colour

# Products whose body is nearly the same tone as the backdrop need a tighter
# match, or the flood fill walks straight through them.
TIGHT = {"mots-c": 12}

# Some products are nearly the same tone as the studio backdrop (a white pump
# head on a white sweep), so no flood fill can separate them cleanly. For those
# we keep the photo intact and just recolour the backdrop to the card panel
# grey, which is visually identical to a cutout on the site.
# (Sep 8 re-shoot: the KPV applicator now has a red pump head, so it cuts out
# cleanly like the rest — nothing needs this fallback at the moment.)
KEEP_BG: set[str] = set()
PANEL = (236, 236, 236)


def match_backdrop(im: Image.Image) -> Image.Image:
    """Shift the whole image so its backdrop lands on the card panel grey."""
    im = im.convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w, _ = a.shape
    ph, pw = max(2, h // 20), max(2, w // 20)
    corners = np.concatenate([
        a[:ph, :pw].reshape(-1, 3), a[:ph, -pw:].reshape(-1, 3),
        a[-ph:, :pw].reshape(-1, 3), a[-ph:, -pw:].reshape(-1, 3),
    ])
    bg = np.median(corners, axis=0)
    a = np.clip(a + (np.array(PANEL, dtype=np.float32) - bg), 0, 255)
    out = Image.fromarray(a.astype(np.uint8), "RGB").convert("RGBA")
    return out


def remove_bg(im: Image.Image, tol: int = TOL) -> Image.Image:
    """Edge-barrier flood fill from the border.

    A pixel is "passable" background only if it's light, neutral AND lies in a
    low-gradient area — so the flood consumes the white backdrop and its soft
    shadow but STOPS at the vial's silhouette instead of eating into the white
    label (which is what caused the ragged edges). The alpha is then feathered
    to anti-alias the cut.
    """
    im = im.convert("RGB")
    a = np.asarray(im).astype(np.int16)
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    gray = a.mean(axis=2)

    # gradient magnitude (edge map)
    gxr = np.zeros_like(gray); gyr = np.zeros_like(gray)
    gxr[:, :-1] = np.abs(gray[:, 1:] - gray[:, :-1])
    gyr[:-1, :] = np.abs(gray[1:, :] - gray[:-1, :])
    grad = gxr + gyr

    # Sample the actual backdrop from the four corners. Studio backdrops are
    # often vignetted well below LIGHT, so an absolute threshold alone leaves
    # grey patches; matching the sampled colour adapts per image.
    h0, w0 = gray.shape
    ph, pw = max(2, h0 // 20), max(2, w0 // 20)
    corners = np.concatenate([
        a[:ph, :pw].reshape(-1, 3), a[:ph, -pw:].reshape(-1, 3),
        a[-ph:, :pw].reshape(-1, 3), a[-ph:, -pw:].reshape(-1, 3),
    ])
    bg_ref = np.median(corners, axis=0)
    near_bg = (np.abs(a - bg_ref).max(axis=2) <= tol)

    neutral = ((mx - mn) <= SAT)
    passable = (near_bg | (mn >= LIGHT)) & neutral & (grad < EDGE)

    h, w = passable.shape
    bg = np.zeros((h, w), dtype=bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if passable[y, x] and not bg[y, x]:
                bg[y, x] = True; dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if passable[y, x] and not bg[y, x]:
                bg[y, x] = True; dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and passable[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; dq.append((ny, nx))

    # grow the cut 1px into the (non-passable) edge ring so no white halo remains,
    # but only into light/neutral pixels — the dark vial body stops it.
    lightneutral = (near_bg | (mn >= LIGHT)) & neutral
    grown = bg.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        shifted = np.zeros_like(bg)
        if dy == 1:   shifted[1:, :] = bg[:-1, :]
        elif dy == -1: shifted[:-1, :] = bg[1:, :]
        elif dx == 1: shifted[:, 1:] = bg[:, :-1]
        else:          shifted[:, :-1] = bg[:, 1:]
        grown |= shifted & lightneutral
    bg = grown

    alpha = np.where(bg, 0, 255).astype(np.uint8)
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.8))
    out = np.dstack([a.astype(np.uint8), np.asarray(alpha_img)])
    return Image.fromarray(out, "RGBA")


def process(src_path: str, slug: str = "") -> Image.Image:
    im = Image.open(src_path)
    im.thumbnail((MAXDIM, MAXDIM), Image.LANCZOS)
    if slug in KEEP_BG:
        return match_backdrop(im)
    rgba = remove_bg(im, TIGHT.get(slug, TOL))
    bbox = rgba.getbbox()          # trim transparent margins
    if bbox:
        rgba = rgba.crop(bbox)
    return rgba


def main():
    preview = None
    if "--preview" in sys.argv:
        preview = sys.argv[sys.argv.index("--preview") + 1]

    done = 0
    for fname, slug in MAPPING.items():
        if preview and slug != preview:
            continue
        src = os.path.join(SRC, fname)
        if not os.path.exists(src):
            print(f"  MISSING {fname}")
            continue
        img = process(src, slug)
        dest = os.path.join(OUT, f"{slug}.png")
        if preview:
            dest = os.path.join(OUT, f"_preview_{slug}.png")
        img.save(dest)
        print(f"  {slug:16} ← {fname}  ({img.width}x{img.height})")
        done += 1
    print(f"done: {done}")


if __name__ == "__main__":
    main()
