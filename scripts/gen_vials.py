"""Generate style-matched product vial images (one PNG per product).

Original artwork — a cylindrical glass vial with a flip-off cap and a label
carrying the store's own brand name + compound name + strength chip + holo
strip. NOT a copy of any other company's product photography.
Run:  python3 scripts/gen_vials.py
"""
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.seed_data import PRODUCTS_SEED  # noqa: E402

BRAND = os.getenv("BUSINESS_NAME", "ORYVEX RESEARCH").upper()
OUT = os.path.join("static", "images", "vials")
os.makedirs(OUT, exist_ok=True)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

INK = (24, 24, 24)
MUTED = (107, 107, 118)
PURPLE_HI = (227, 53, 72)   # crimson (label band / strength chip)
PURPLE_LO = (198, 42, 56)   # deeper crimson


def font(size, bold=True):
    return ImageFont.truetype(FB if bold else FR, size)


def vgrad(size, top, bottom):
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return base.resize((w, h))


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def paste_grad(canvas, box, top, bottom, radius):
    x0, y0, x1, y1 = box
    size = (x1 - x0, y1 - y0)
    canvas.paste(vgrad(size, top, bottom), (x0, y0), rounded_mask(size, radius))


def holo_strip(w, h):
    """A horizontal rainbow (holographic) strip."""
    import colorsys
    strip = Image.new("RGB", (w, h))
    px = strip.load()
    for x in range(w):
        r, g, b = colorsys.hsv_to_rgb(x / w, 0.55, 1.0)
        for y in range(h):
            px[x, y] = (int(r * 255), int(g * 255), int(b * 255))
    return strip


def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if draw.textlength(trial, font=fnt) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = wd
    if cur:
        lines.append(cur)
    return lines


def fit_name(draw, text, maxw, maxh):
    """Pick the largest font (<=2 lines) that fits the label."""
    for size in range(36, 13, -1):
        fnt = font(size)
        lines = wrap(draw, text, fnt, maxw)
        if len(lines) > 2:
            continue
        line_h = size + 6
        if len(lines) * line_h <= maxh and all(draw.textlength(l, font=fnt) <= maxw for l in lines):
            return fnt, lines, line_h
    fnt = font(14)
    return fnt, wrap(draw, text, fnt, maxw)[:2], 20


def centered(draw, cx, y, text, fnt, fill):
    w = draw.textlength(text, font=fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)


def make_vial(slug, name, strength):
    """Squat pharma-vial proportions, big flip-off cap, tilted pose."""
    W, H = 640, 660
    cx = W // 2

    # vial drawn upright on its own layer, tilted at the end
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)

    bx0, bx1 = cx - 130, cx + 130      # glass body extents (squat & wide)
    by0, by1 = 180, 572

    # ── flip-off cap (big, silver, elliptical top = 3D read) ──
    cpx0, cpx1 = cx - 85, cx + 85
    paste_grad(v, (cpx0, 70, cpx1, 128), (210, 210, 224), (154, 154, 170), 10)
    d.ellipse([cpx0, 48, cpx1, 94], fill=(226, 226, 236), outline=(180, 180, 196), width=2)
    d.ellipse([cpx0 + 16, 57, cpx1 - 16, 85], fill=(242, 242, 250))
    # aluminum crimp ring with ridges
    paste_grad(v, (cx - 97, 128, cx + 97, 168), (190, 190, 204), (142, 142, 160), 12)
    for rx in range(cx - 90, cx + 91, 9):
        d.line([(rx, 131), (rx, 165)], fill=(124, 124, 144, 110), width=2)

    # ── glass body ──
    paste_grad(v, (bx0, by0, bx1, by1), (250, 251, 255), (226, 230, 246), 46)
    # lyophilized powder pool at the bottom
    paste_grad(v, (bx0 + 8, by1 - 66, bx1 - 8, by1 - 6), (240, 238, 250), (212, 206, 236), 22)

    # ── label (wraps the body; clear glass strip above and below) ──
    lx0, lx1, ly0, ly1 = bx0, bx1, 268, 536
    d.rectangle([lx0, ly0, lx1, ly1], fill=(255, 255, 255))
    band_h = 54
    paste_grad(v, (lx0, ly0, lx1, ly0 + band_h), PURPLE_HI, PURPLE_LO, 0)
    # auto-fit the brand wordmark to the band width
    brand_size = 20
    while brand_size > 9 and d.textlength(BRAND, font=font(brand_size)) > (lx1 - lx0) - 20:
        brand_size -= 1
    centered(d, cx, ly0 + (band_h - brand_size) // 2 - 2, BRAND, font(brand_size), (255, 255, 255))

    fnt, lines, lh = fit_name(d, name.upper(), (lx1 - lx0) - 28, 96)
    ty = ly0 + band_h + 22
    for ln in lines:
        centered(d, cx, ty, ln, fnt, INK)
        ty += lh

    # strength chip + purity note
    if strength:
        chip_f = font(17)
        chip_txt = strength.upper()
        cw = d.textlength(chip_txt, font=chip_f) + 28
        px_f = font(11, bold=False)
        px_txt = "| PURITY > 99% HPLC"
        pw = d.textlength(px_txt, font=px_f)
        total = cw + 12 + pw
        sx = cx - total / 2
        cy0 = ty + 8
        d.rounded_rectangle([sx, cy0, sx + cw, cy0 + 34], radius=9, fill=PURPLE_HI)
        d.text((sx + 14, cy0 + 8), chip_txt, font=chip_f, fill=(255, 255, 255))
        d.text((sx + cw + 12, cy0 + 12), px_txt, font=px_f, fill=(120, 112, 140))

    centered(d, cx, ly1 - 44, "Research Use Only", font(11, bold=False), MUTED)
    v.paste(holo_strip(lx1 - lx0, 20), (lx0, ly1 - 20))

    # ── cylindrical shading: darken toward the vertical edges ──
    shade = Image.new("L", (W, 1), 255)
    sp = shade.load()
    for x in range(W):
        rel = min(1.0, max(0.0, (x - bx0) / (bx1 - bx0)))
        sp[x, 0] = int(203 + 52 * math.sin(math.pi * rel))
    shade = shade.resize((W, H))
    rgb = ImageChops.multiply(v.convert("RGB"), Image.merge("RGB", (shade, shade, shade)))
    alpha = v.split()[3]
    v = Image.merge("RGBA", (*rgb.split(), alpha))

    # glass highlight streaks — only above/below the label so text stays legible
    hd = ImageDraw.Draw(v)
    hd.rounded_rectangle([bx0 + 16, by0 + 12, bx0 + 32, ly0 - 8], radius=7, fill=(255, 255, 255, 60))
    hd.rounded_rectangle([bx0 + 16, ly1 + 8, bx0 + 32, by1 - 18], radius=7, fill=(255, 255, 255, 60))

    # ── tilt like a product shot ──
    v = v.crop(v.getbbox())
    v = v.rotate(-12, expand=True, resample=Image.BICUBIC)

    # ── ground shadow under the tilted vial, then composite ──
    rw, rh = v.size
    img = Image.new("RGBA", (rw, rh + 34), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse(
        [rw * 0.16, rh - 26, rw * 0.84, rh + 26], fill=(45, 27, 82, 66))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    img.alpha_composite(v)

    img.save(os.path.join(OUT, f"{slug}.png"))


def main():
    # SAFETY: never overwrite an existing image (which may be a real photo).
    # Only fills in MISSING vials. Use --force to regenerate everything.
    force = "--force" in sys.argv
    n = skipped = 0
    for p in PRODUCTS_SEED:
        out = os.path.join(OUT, f"{p['slug']}.png")
        if os.path.exists(out) and not force:
            skipped += 1
            continue
        variants = p.get("variants") or []
        strength = variants[0]["strength"] if variants else ""
        make_vial(p["slug"], p["name"], strength)
        n += 1
    print(f"generated {n} vial images → {OUT}/  (skipped {skipped} existing; use --force to regenerate)")


if __name__ == "__main__":
    main()
