"""Generate original background art for the storefront (no stock photos).

  static/images/hero-molecules.jpg  — dark crimson molecular network (hero)
  static/images/about-lab.jpg       — abstract laboratory band (about section)

All artwork is drawn procedurally here — nothing is copied from any third party.
Run:  python3 scripts/gen_art.py
"""
import math
import os
import random

import numpy as np

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = os.path.join("static", "images")
os.makedirs(OUT, exist_ok=True)

CRIMSON = (227, 53, 72)
DEEP = (150, 22, 34)
DARK = (32, 6, 10)


def radial_bg(w, h, inner, outer, cx=0.62, cy=0.45, spread=0.95):
    """Dark radial wash used behind both images."""
    img = Image.new("RGB", (w // 6, h // 6))
    px = img.load()
    iw, ih = img.size
    for y in range(ih):
        for x in range(iw):
            dx = (x / iw - cx) / spread
            dy = (y / ih - cy) / spread
            t = min(1.0, math.sqrt(dx * dx + dy * dy) * 1.35)
            t = t ** 0.85
            px[x, y] = tuple(int(inner[i] + (outer[i] - inner[i]) * t) for i in range(3))
    return img.resize((w, h), Image.BICUBIC)


def vgrad(size, top, bottom):
    """Vertical linear gradient."""
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return base.resize((w, h))


def brand_decal(size, text_top="ORYVEX", text_bot="RESEARCH"):
    """The wordmark, rendered to be wrapped onto a sphere face."""
    img = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(img)
    f1 = ImageFont.truetype(FB, max(7, int(size * 0.088)))
    f2 = ImageFont.truetype(FB, max(5, int(size * 0.050)))
    t1 = " ".join(text_top)          # letter-spaced, like the site wordmark
    t2 = "  ".join(text_bot)
    w1 = d.textlength(t1, font=f1); w2 = d.textlength(t2, font=f2)
    y = size * 0.445
    d.text(((size - w1) / 2, y), t1, font=f1, fill=255)
    d.text(((size - w2) / 2, y + size * 0.105), t2, font=f2, fill=205)
    return img


def spherize(mask):
    """Barrel-warp a flat decal so it sits on a curved surface."""
    n = mask.size[0]
    src = np.asarray(mask).astype(np.float32)
    out = np.zeros_like(src)
    ys, xs = np.mgrid[0:n, 0:n]
    u = (xs - n / 2) / (n / 2)
    v = (ys - n / 2) / (n / 2)
    r = np.sqrt(u * u + v * v)
    k = np.where(r < 1, np.sqrt(np.clip(1 - r * r, 0, 1)), 1)
    su = np.clip(((u * (0.78 + 0.22 * k)) * (n / 2) + n / 2), 0, n - 1).astype(int)
    sv = np.clip(((v * (0.78 + 0.22 * k)) * (n / 2) + n / 2), 0, n - 1).astype(int)
    out = src[sv, su]
    out[r >= 0.88] = 0
    return Image.fromarray(out.astype(np.uint8), "L")


def sphere(size, base, light=(255, 190, 195), branded=False):
    """A glossy translucent sphere with a specular highlight, as RGBA."""
    s = size * 3
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    px = img.load()
    r = s / 2
    for y in range(s):
        for x in range(s):
            dx, dy = (x - r) / r, (y - r) / r
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            z = math.sqrt(1 - d2)
            # lambert term from an upper-left key light
            lam = max(0.0, (-dx * 0.45 - dy * 0.55 + z * 0.70))
            rim = (1 - z) ** 2.6            # bright edge (glass)
            spec = max(0.0, lam) ** 26      # tight highlight
            col = []
            for i in range(3):
                v = base[i] * (0.30 + 0.85 * lam)
                v += light[i] * spec * 0.85
                v += light[i] * rim * 0.30
                col.append(int(max(0, min(255, v))))
            a = int(255 * min(1.0, 0.55 + 0.45 * z))
            px[x, y] = (col[0], col[1], col[2], a)
    img = img.resize((size, size), Image.LANCZOS)

    if branded and size >= 90:
        decal = spherize(brand_decal(size)).filter(ImageFilter.GaussianBlur(size / 260))
        # the wordmark reads as a lighter tint printed on the glass
        tint = Image.new("RGBA", (size, size), (255, 214, 218, 255))
        dm = np.asarray(decal).astype(np.float32) * 0.62
        sph_a = np.asarray(img.split()[3]).astype(np.float32) / 255.0
        tint.putalpha(Image.fromarray((dm * sph_a).astype(np.uint8), "L"))
        img = Image.alpha_composite(img, tint)
    return img


def bond(draw, p0, p1, width, colour):
    """A connecting tube between two atom centres."""
    draw.line([p0, p1], fill=colour, width=width)


def hero(w=2000, h=1100):
    img = radial_bg(w, h, (96, 12, 22), DARK, cx=0.58, cy=0.40)

    # soft out-of-focus blobs for depth
    blob = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blob)
    rnd = random.Random(7)
    for _ in range(26):
        r = rnd.randint(70, 300)
        x, y = rnd.randint(-100, w), rnd.randint(-100, h)
        a = rnd.randint(10, 34)
        bd.ellipse([x - r, y - r, x + r, y + r], fill=(214, 40, 58, a))
    img = Image.alpha_composite(img.convert("RGBA"), blob.filter(ImageFilter.GaussianBlur(70)))

    # ── molecular lattice ─────────────────────────────────────────
    rnd = random.Random(21)
    nodes = []
    for _ in range(30):
        x = rnd.randint(int(w * 0.38), w + 120)
        y = rnd.randint(-60, h + 60)
        depth = rnd.random()                     # 0 = far, 1 = near
        r = int(38 + depth * 150)
        nodes.append([x, y, r, depth])
    nodes.sort(key=lambda n: n[3])               # far ones first

    tubes = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    td = ImageDraw.Draw(tubes)
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            d = math.hypot(a[0] - b[0], a[1] - b[1])
            if d < 330 and abs(a[3] - b[3]) < 0.30:
                wdt = max(4, int(10 + 26 * min(a[3], b[3])))
                alpha = int(70 + 120 * min(a[3], b[3]))
                bond(td, (a[0], a[1]), (b[0], b[1]), wdt, (206, 46, 62, alpha))
    img = Image.alpha_composite(img, tubes.filter(ImageFilter.GaussianBlur(2)))

    for x, y, r, depth in nodes:
        sp = sphere(r * 2, (196, 34, 48), branded=(depth > 0.42))
        if depth < 0.34:
            sp = sp.filter(ImageFilter.GaussianBlur(6 - depth * 12))
        img.alpha_composite(sp, (x - r, y - r))

    # vignette so the headline stays legible on the left
    vig = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vig).rectangle([0, 0, int(w * 0.56), h], fill=210)
    vig = vig.filter(ImageFilter.GaussianBlur(240))
    shade = Image.new("RGBA", (w, h), (26, 4, 8, 255))
    shade.putalpha(vig)
    img = Image.alpha_composite(img, shade)

    img.convert("RGB").save(os.path.join(OUT, "hero-molecules.jpg"), quality=88)
    print("wrote static/images/hero-molecules.jpg")


def about(w=1400, h=1050):
    """Placeholder for the About band — a dark, backlit bench macro.

    Deliberately moody and abstract rather than a cartoon lab: it reads as a
    designed graphic until a real photograph is dropped in over the top.
    See docs-product-image-prompt.md for the photo prompt.
    """
    img = Image.new("RGBA", (w, h))
    # deep charcoal room, warm pool of light behind the glassware
    img.paste(vgrad((w, h), (30, 30, 36), (12, 12, 15)), (0, 0))
    img = img.convert("RGBA")

    rnd = random.Random(23)

    # backlight bloom
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([int(w * 0.28), int(h * 0.02), int(w * 0.92), int(h * 0.70)],
               fill=(255, 236, 226, 78))
    gd.ellipse([int(w * 0.44), int(h * 0.16), int(w * 0.76), int(h * 0.56)],
               fill=(255, 246, 240, 74))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(120)))

    # far bokeh
    bok = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bok)
    for _ in range(26):
        r = rnd.randint(26, 92)
        x, y = rnd.randint(int(w * 0.20), w), rnd.randint(0, int(h * 0.60))
        warm = rnd.random() < 0.7
        col = (255, 214, 178, rnd.randint(22, 60)) if warm else (214, 58, 74, rnd.randint(18, 48))
        bd.ellipse([x - r, y - r, x + r, y + r], fill=col)
    img = Image.alpha_composite(img, bok.filter(ImageFilter.GaussianBlur(26)))

    BENCH = int(h * 0.76)

    def vessel(layer, cx, top_y, half_w, fill_rgb, fill_frac=0.55, taper=0.0):
        """Backlit glass: dark body, rim light down both edges, glowing liquid."""
        d = ImageDraw.Draw(layer)
        bw = half_w
        tw = int(half_w * (1 - taper))
        body = [(cx - tw, top_y), (cx + tw, top_y),
                (cx + bw, BENCH), (cx - bw, BENCH)]
        d.polygon(body, fill=(210, 220, 232, 26))
        liq_top = int(BENCH - (BENCH - top_y) * fill_frac)
        lw = int(tw + (bw - tw) * fill_frac)
        d.polygon([(cx - lw, liq_top), (cx + lw, liq_top),
                   (cx + bw - 3, BENCH - 3), (cx - bw + 3, BENCH - 3)],
                  fill=fill_rgb + (150,))
        # rim light
        d.line([(cx - tw, top_y), (cx - bw, BENCH)], fill=(255, 240, 228, 190), width=3)
        d.line([(cx + tw, top_y), (cx + bw, BENCH)], fill=(255, 240, 228, 120), width=2)
        d.line([(cx - tw, top_y), (cx + tw, top_y)], fill=(255, 244, 234, 150), width=2)

    mid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    # a row of tubes, receding
    for i, (dx, hh, col) in enumerate([
            (0.50, 0.34, (226, 96, 70)), (0.565, 0.30, (240, 186, 92)),
            (0.628, 0.33, (120, 200, 150)), (0.690, 0.29, (110, 176, 232)),
            (0.752, 0.32, (214, 58, 74))]):
        vessel(mid, int(w * dx), int(BENCH - h * hh), 17, col, 0.58)
    # two flasks, foreground left
    vessel(mid, int(w * 0.215), int(BENCH - h * 0.30), 96, (232, 140, 52), 0.46, taper=0.74)
    vessel(mid, int(w * 0.355), int(BENCH - h * 0.24), 72, (96, 168, 226), 0.44, taper=0.72)
    # tall crimson cylinder, right
    vessel(mid, int(w * 0.875), int(BENCH - h * 0.40), 38, (214, 58, 74), 0.66, taper=0.10)

    img = Image.alpha_composite(img, mid.filter(ImageFilter.GaussianBlur(0.8)))

    # bench line + reflection
    d = ImageDraw.Draw(img)
    d.line([(0, BENCH), (w, BENCH)], fill=(255, 236, 222, 70), width=2)
    refl = img.crop((0, BENCH - 230, w, BENCH)).transpose(Image.FLIP_TOP_BOTTOM)
    refl.putalpha(48)
    img.alpha_composite(refl.filter(ImageFilter.GaussianBlur(9)), (0, BENCH))

    # brand warmth + vignette
    img = Image.alpha_composite(img, Image.new("RGBA", (w, h), (227, 53, 72, 20)))
    vig = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vig).ellipse([-int(w * 0.20), -int(h * 0.28),
                                 int(w * 1.20), int(h * 1.28)], fill=185)
    vig = ImageOps.invert(vig.filter(ImageFilter.GaussianBlur(140)))
    shade = Image.new("RGBA", (w, h), (6, 6, 9, 255))
    shade.putalpha(vig.point(lambda v: int(v * 0.62)))
    img = Image.alpha_composite(img, shade)

    img.convert("RGB").save(os.path.join(OUT, "about-lab.jpg"), quality=90)
    print("wrote static/images/about-lab.jpg")


if __name__ == "__main__":
    hero()
    about()
