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
    # ── batch 1: Sep 6, 21:43 — all label strengths verified against the catalog ──
    "WhatsApp Image 2026-09-06 at 21.43.23.jpeg":     "bpc-157",
    "WhatsApp Image 2026-09-06 at 21.43.24.jpeg":     "5-amino-1mq",
    "WhatsApp Image 2026-09-06 at 21.43.24 (1).jpeg": "ara-290",
    "WhatsApp Image 2026-09-06 at 21.43.24 (2).jpeg": "bacteriostatic-water",
    # 21.43.24 (3) is a second BPC-157 take — unused, kept as a spare
    "WhatsApp Image 2026-09-06 at 21.43.25.jpeg":     "bpc-157-mist-applicator",
    "WhatsApp Image 2026-09-06 at 21.43.25 (1).jpeg": "cagrilintide",

    # ── batch 2: Sep 6, 22:11 — only the label strengths that exist in the ladder ──
    "WhatsApp Image 2026-09-06 at 22.11.50 (1).jpeg": "cjc-1295-ipamorelin",   # 10mg
    "WhatsApp Image 2026-09-06 at 22.11.50.jpeg":     "cjc-1295-no-dac",       # 10mg (tier 2)
    "WhatsApp Image 2026-09-06 at 22.11.51 (4).jpeg": "glp-1t",                # 10mg
    "WhatsApp Image 2026-09-06 at 22.11.52 (1).jpeg": "glp-3rt",               # 10mg (tier 2)
    "WhatsApp Image 2026-09-06 at 22.11.53 (4).jpeg": "kpv-mist-applicator",   # 10mg
    "WhatsApp Image 2026-09-06 at 22.11.54 (1).jpeg": "mots-c",                # 10mg
    "WhatsApp Image 2026-09-06 at 22.11.54.jpeg":     "ll-37",                 # 5mg
    # Strength on the label does not match the product's smallest size — kept
    # anyway at the owner's request (photo quality over milligram accuracy).
    "WhatsApp Image 2026-09-06 at 22.11.50 (2).jpeg": "dsip",          # label 5MG  · sold 10mg
    "WhatsApp Image 2026-09-06 at 22.11.51 (1).jpeg": "foxo4-dri",     # label 5MG  · sold 10mg
    "WhatsApp Image 2026-09-06 at 22.11.51 (2).jpeg": "ghk-cu",        # label 5MG  · sold 50/100mg
    "WhatsApp Image 2026-09-06 at 22.11.51 (3).jpeg": "glow",          # label 5MG  · sold 70mg
    "WhatsApp Image 2026-09-06 at 22.11.51.jpeg":     "epithalon",     # label 5MG  · sold 10/40mg
    "WhatsApp Image 2026-09-06 at 22.11.52 (2).jpeg": "glutathione",   # label 5MG  · sold 600/1500mg
    "WhatsApp Image 2026-09-06 at 22.11.52 (3).jpeg": "igf1-lr3",      # label 10MG · sold 1mg
    "WhatsApp Image 2026-09-06 at 22.11.52.jpeg":     "glp-2",         # label 5MG  · sold 10mg
    "WhatsApp Image 2026-09-06 at 22.11.53 (2).jpeg": "klow",          # label 5MG  · sold 80mg
    "WhatsApp Image 2026-09-06 at 22.11.53 (3).jpeg": "kpv",           # label 5MG  · sold 10/30mg
    "WhatsApp Image 2026-09-06 at 22.11.53.jpeg":     "ipamorelin",    # label 5MG  · sold 10mg
    "WhatsApp Image 2026-09-06 at 22.11.53 (1).jpeg": "kisspeptin",    # label 5MG  · sold 10mg
    #   ^ NOTE: this label misspells the compound as "KISSPETIN" (missing a P).
    #     Installed at the owner's request — replace when a corrected render exists.
    # ── batch 3: Sep 7, 10:23 ──
    "WhatsApp Image 2026-09-07 at 10.23.58.jpeg":     "adamax",          # 10MG · sold 5mg
    "WhatsApp Image 2026-09-07 at 10.24.06.jpeg":     "peg-mgf",         # 10MG · sold 2mg
    "WhatsApp Image 2026-09-07 at 10.24.06 (1).jpeg": "nad-plus",        # 10MG · sold 500/1000mg
    "WhatsApp Image 2026-09-07 at 10.24.07.jpeg":     "pinealon",        # 10MG · sold 10mg  ✓
    "WhatsApp Image 2026-09-07 at 10.24.07 (1).jpeg": "wolverine-blend", # 10MG · sold 5mg/5mg
    "WhatsApp Image 2026-09-07 at 10.31.57.jpeg":     "ss31",            # 10MG · sold 10mg  ✓
    # ── batch 4: Sep 7, 12:18 ──
    "WhatsApp Image 2026-09-07 at 12.18.23.jpeg":     "selank",            # 10MG · sold 10mg  OK
    "WhatsApp Image 2026-09-07 at 12.18.23 (1).jpeg": "slu-pp-332",        # label reads "SLU-PP-32" (missing a 3)
    "WhatsApp Image 2026-09-07 at 12.18.23 (2).jpeg": "tb-500",            # 10MG · sold 10mg  OK
    "WhatsApp Image 2026-09-07 at 12.18.24.jpeg":     "thymosin-alpha-1",  # 10MG · sold 10mg  OK
    "WhatsApp Image 2026-09-07 at 12.18.24 (1).jpeg": "pt-141",            # 10MG · sold 10mg  OK
    "WhatsApp Image 2026-09-07 at 12.18.24 (2).jpeg": "mt-1",              # 10MG · sold 10mg  OK
    "WhatsApp Image 2026-09-07 at 12.18.25.jpeg":     "mt-2",              # 10MG · sold 10mg  OK
    "WhatsApp Image 2026-09-07 at 12.18.25 (1).jpeg": "n-acetyl-epitalon", # label reads "N-ACTEYL" · 10MG vs 5mg
    "WhatsApp Image 2026-09-07 at 12.18.25 (2).jpeg": "ahk-cu",            # 100MG · sold 100mg  OK
    # Unused spares: 21.43.24 (3) is a second BPC-157 take, 22.11.50 (3) a second DSIP.

    # ── batch 3: Sep 7, 12.18 ──
    "WhatsApp Image 2026-09-07 at 12.18.23.jpeg":     "selank",            # 10mg ✓
    "WhatsApp Image 2026-09-07 at 12.18.23 (1).jpeg": "slu-pp-332",        # 10mg ✓ · label reads "SLU-PP-32"
    "WhatsApp Image 2026-09-07 at 12.18.23 (2).jpeg": "tb-500",            # 10mg ✓
    "WhatsApp Image 2026-09-07 at 12.18.24.jpeg":     "thymosin-alpha-1",  # 10mg ✓
    "WhatsApp Image 2026-09-07 at 12.18.24 (1).jpeg": "pt-141",            # 10mg ✓
    "WhatsApp Image 2026-09-07 at 12.18.24 (2).jpeg": "mt-1",              # 10mg ✓
    "WhatsApp Image 2026-09-07 at 12.18.25.jpeg":     "mt-2",              # 10mg ✓
    "WhatsApp Image 2026-09-07 at 12.18.25 (1).jpeg": "n-acetyl-epitalon", # label 10MG · sold 5mg · reads "N-ACTEYL"
    "WhatsApp Image 2026-09-07 at 12.18.25 (2).jpeg": "ahk-cu",            # 100mg ✓

    # ── batch 4: Sep 7, 15.35 — the last 7; every strength matches the catalog ──
    "WhatsApp Image 2026-09-07 at 15.35.45.jpeg":     "semax",                   # 10mg ✓
    "WhatsApp Image 2026-09-07 at 15.35.45 (1).jpeg": "tesamorelin",             # 2mg  ✓
    "WhatsApp Image 2026-09-07 at 15.35.46.jpeg":     "dsip-mist-applicator",    # 5mg  ✓
    "WhatsApp Image 2026-09-07 at 15.35.46 (2).jpeg": "mt-2-mist-applicator",    # 10mg ✓
    "WhatsApp Image 2026-09-07 at 15.35.46 (3).jpeg": "pt-141-mist-applicator",  # 10mg ✓
    "WhatsApp Image 2026-09-07 at 15.35.47.jpeg":     "selank-mist-applicator",  # 5mg  ✓
    "WhatsApp Image 2026-09-07 at 15.35.47 (1).jpeg": "semax-mist-applicator",   # 5mg  ✓
    # 15.35.46 (1) is a second DSIP applicator take labelled 10MG — unused,
    # the product is sold in 5mg and the 5MG take above is the correct one.

}

MAXDIM = 900          # cap output size
LIGHT = 206           # min per-channel value considered "background-light"
SAT = 30              # max (max-min channel) considered "neutral" (unsaturated)
EDGE = 13             # gradient above this = vial silhouette → flood stops here
TOL = 26              # per-channel distance from the sampled backdrop colour

# Products whose body is nearly the same tone as the backdrop need a tighter
# match, or the flood fill walks straight through them.
TIGHT = {"mots-c": 12}

# Some products are nearly the same tone as the studio backdrop (a white pump
# head on a white sweep), so no flood fill can separate them cleanly. For those
# we keep the photo intact and just recolour the backdrop to the card panel
# grey, which is visually identical to a cutout on the site.
KEEP_BG = {"kpv-mist-applicator"}
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
