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
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.17.jpeg": "ara-290",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.18.jpeg": "bacteriostatic-water",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.19.jpeg": "bpc-157-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.20 (2).jpeg": "cjc-1295-ipamorelin",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.20.jpeg": "cagrilintide",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.22.jpeg": "glp-1t",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.23 (1).jpeg": "dsip-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.24 (2).jpeg": "kpv-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.24 (3).jpeg": "ll-37",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25 (1).jpeg": "mt-1",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25 (2).jpeg": "mt-2",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25 (3).jpeg": "mt-2-mist-applicator",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.25.jpeg": "mots-c",
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.26 (3).jpeg": "pinealon",
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
    "WhatsApp Unknown 2026-09-08 at 07.41.28/WhatsApp Image 2026-09-08 at 07.39.29.jpeg": "tb-500",

    # ── Sep 8, 08.44 re-render: corrected strengths. Supersedes the 07.39
    #    takes for these 20 slugs; every label verified against the ladder.
    "WhatsApp Image 2026-09-08 at 08.44.39 (1).jpeg": "ahk-cu",                        # 100MG
    "WhatsApp Image 2026-09-08 at 08.44.39 (2).jpeg": "cjc-1295-no-dac",               # 5MG
    "WhatsApp Image 2026-09-08 at 08.44.39.jpeg": "adamax",                        # 5MG
    "WhatsApp Image 2026-09-08 at 08.44.40 (1).jpeg": "epithalon",                     # 10MG
    "WhatsApp Image 2026-09-08 at 08.44.40 (2).jpeg": "foxo4-dri",                     # 10MG
    "WhatsApp Image 2026-09-08 at 08.44.40 (3).jpeg": "ghk-cu",                        # 50MG
    "WhatsApp Image 2026-09-08 at 08.44.40.jpeg": "dsip",                          # 10MG
    "WhatsApp Image 2026-09-08 at 08.44.41 (1).jpeg": "glp-2",                         # 10MG
    "WhatsApp Image 2026-09-08 at 08.44.41 (2).jpeg": "glp-3rt",                       # 5MG
    "WhatsApp Image 2026-09-08 at 08.44.41 (3).jpeg": "glutathione",                   # 600MG
    "WhatsApp Image 2026-09-08 at 08.44.41.jpeg": "glow",                          # 70MG
    "WhatsApp Image 2026-09-08 at 08.44.42 (1).jpeg": "ipamorelin",                    # 10MG
    "WhatsApp Image 2026-09-08 at 08.44.42 (2).jpeg": "kisspeptin",                    # 10MG
    "WhatsApp Image 2026-09-08 at 08.44.42 (3).jpeg": "klow",                          # 80MG
    "WhatsApp Image 2026-09-08 at 08.44.42.jpeg": "igf1-lr3",                      # 1MG
    "WhatsApp Image 2026-09-08 at 08.44.43 (1).jpeg": "n-acetyl-epitalon",             # 5MG
    "WhatsApp Image 2026-09-08 at 08.44.43 (2).jpeg": "nad-plus",                      # 500MG
    "WhatsApp Image 2026-09-08 at 08.44.43.jpeg": "kpv",                           # 10MG
    "WhatsApp Image 2026-09-08 at 08.44.44 (1).jpeg": "wolverine-blend",               # 5MG/5MG
    "WhatsApp Image 2026-09-08 at 08.44.44.jpeg": "peg-mgf",                       # 2MG
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
# Slugs that still need a hard alpha cut (backdrop unlike the panel grey).
CUT_OUT: set[str] = set()
PANEL = (236, 236, 236)


def match_backdrop(im: Image.Image) -> Image.Image:
    """Flat-field the studio backdrop onto the card panel grey.

    These frames carry a vertical gradient (~182 at the top of the sweep, ~232
    at the bottom), so one global shift leaves a visible ramp inside the tile.
    Estimate the backdrop per row from the left/right margins — always sweep,
    never product — smooth it, and shift each row onto PANEL. The product itself
    is never touched.
    """
    im = im.convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w, _ = a.shape
    m = max(4, w // 12)

    margins = np.concatenate([a[:, :m, :], a[:, -m:, :]], axis=1)
    row_bg = np.median(margins, axis=1)

    k = max(3, h // 40) | 1
    pad = np.pad(row_bg, ((k // 2, k // 2), (0, 0)), mode="edge")
    kern = np.ones(k, dtype=np.float32) / k
    row_bg = np.stack([np.convolve(pad[:, c], kern, mode="valid") for c in range(3)], axis=1)

    a = a + (np.array(PANEL, dtype=np.float32) - row_bg)[:, None, :]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def trim_and_square(im: Image.Image, margin: float = 0.07) -> Image.Image:
    """Crop to the product (its shadow included), then pad to a PANEL square."""
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    diff = np.abs(a - np.array(PANEL, dtype=np.int16)).max(axis=2)
    ys, xs = np.where(diff > 10)
    if len(xs):
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        px, py = int((x1 - x0) * margin), int((y1 - y0) * margin)
        im = im.crop((max(0, x0 - px), max(0, y0 - py),
                      min(im.width, x1 + px), min(im.height, y1 + py)))
    side = max(im.size)
    canvas = Image.new("RGB", (side, side), PANEL)
    canvas.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    return canvas


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
    """Normalise a studio photo onto the card panel — no alpha cut.

    Flood-fill cutouts were damaging the vials: clear glass and the white label
    are both close to the backdrop tone, so the fill leaked in through the glass
    and chewed the label edge, leaving a detached shadow blob behind. These
    backdrops are clean and even, so flat-fielding them to the panel colour
    looks like a perfect cutout with none of the damage.

    remove_bg() stays for photos shot on a backdrop unlike the panel grey.
    Nothing in the current set needs it.
    """
    im = Image.open(src_path)
    im.thumbnail((MAXDIM, MAXDIM), Image.LANCZOS)
    if slug in CUT_OUT:
        rgba = remove_bg(im, TIGHT.get(slug, TOL))
        bbox = rgba.getbbox()
        return rgba.crop(bbox) if bbox else rgba
    return trim_and_square(match_backdrop(im))


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
            # Sources are transient (WhatsApp downloads get cleared out); the
            # cut-out PNGs under static/images/vials/ are the committed asset,
            # so a missing source is only a note, not a failure.
            if os.path.exists(os.path.join(OUT, f"{slug}.png")):
                print(f"  skip    {slug:24} (source gone, existing PNG kept)")
            else:
                print(f"  MISSING {slug:24} ← {fname}")
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
