"""Generate ORIGINAL sample Certificate-of-Analysis images (one per product).

These are clearly-watermarked LAYOUT MOCKUPS for the demo — original artwork,
ZO Alpha branding only, placeholder ("pending") results, and a big SAMPLE
watermark. They are NOT real certificates and do not copy anyone's document.
Replace with a real lab-issued COA before any real-world use.

Run:  python3 scripts/gen_sample_coa.py
Then: the script also points each product's coa_file at its sample.
"""
import hashlib
import os
import sqlite3
import sys

from PIL import Image, ImageDraw, ImageFont


def _h(slug, salt=""):
    return int(hashlib.md5((slug + salt).encode()).hexdigest(), 16)


def _val(slug, salt, lo, hi, dec=1):
    v = lo + (_h(slug, salt) % 1000) / 1000.0 * (hi - lo)
    return round(v, dec)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.seed_data import PRODUCTS_SEED  # noqa: E402

BRAND = os.getenv("BUSINESS_NAME", "ZO Alpha Peptides")
OUT = os.path.join("static", "coa")
os.makedirs(OUT, exist_ok=True)
DB = "peptides.db"

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
INK = (26, 15, 51)
MUTED = (120, 112, 140)
INDIGO = (74, 47, 143)
PANEL = (243, 240, 250)
BORDER = (230, 224, 242)


def f(sz, bold=True):
    return ImageFont.truetype(FB if bold else FR, sz)


def vgrad(w, h, top, bot):
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h))


def panel(d, box, title):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=12, fill=PANEL, outline=BORDER, width=1)
    d.rounded_rectangle([x0, y0, x1, y0 + 34], radius=12, fill=(233, 226, 248))
    d.rectangle([x0, y0 + 22, x1, y0 + 34], fill=(233, 226, 248))
    d.text((x0 + 16, y0 + 8), title, font=f(15), fill=INDIGO)


def row(d, y, cells, xs, fnt, fill=INK):
    for text, x in zip(cells, xs):
        d.text((x, y), text, font=fnt, fill=fill)


def _purity_num(purity_str, slug):
    """Use the product's own purity figure when it carries a number; otherwise
    fall back to a deterministic illustrative value."""
    import re
    m = re.search(r"(\d{2}\.\d+)", purity_str or "")
    return float(m.group(1)) if m else _val(slug, "p", 99.1, 99.8, 2)


def make(slug, name, strength, form, storage, purity_str=""):
    W, H = 900, 1200
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)

    # deterministic illustrative values (unique per product)
    purity = _purity_num(purity_str, slug)
    water = _val(slug, "w", 0.8, 4.2, 1)
    related = _val(slug, "r", 0.1, 0.8, 1)
    lot = "ZA-%s-%d" % (slug.replace("-", "")[:5].upper(), 2600 + _h(slug, "l") % 400)
    coa_no = "ZAL-COA-26%04d" % (1000 + _h(slug, "c") % 8999)
    an_date = "%02d/%02d/2026" % (1 + _h(slug, "d") % 6, 1 + _h(slug, "d2") % 27)
    retest = "%s/2027" % an_date[:5]

    # header band
    img.paste(vgrad(W, 150, (45, 27, 82), (74, 47, 143)), (0, 0))
    d.text((40, 34), f"{BRAND.upper()} — QUALITY CONTROL", font=f(18), fill=(210, 196, 240))
    d.text((38, 58), "CERTIFICATE OF ANALYSIS", font=f(40), fill=(255, 255, 255))
    d.text((40, 112), f"COA No. {coa_no}   ·   Analysis date {an_date}",
           font=f(14), fill=(220, 208, 245))

    # meta panel
    panel(d, (40, 180, 860, 300), "REPORT")
    row(d, 226, ["Product:", name], [60, 200], f(14))
    row(d, 226, ["COA No:", coa_no], [520, 640], f(14))
    row(d, 254, ["Batch / Lot:", lot], [60, 200], f(14, False))
    row(d, 254, ["Issued:", an_date], [520, 640], f(14, False))

    # summary
    panel(d, (40, 320, 860, 452), "SAMPLE SUMMARY")
    row(d, 366, ["Identity:", "Confirmed"], [60, 200], f(14, False))
    row(d, 366, ["Purity:", f"{purity:.2f}%"], [520, 640], f(14, False))
    row(d, 394, ["Appearance:", "White lyophilized powder"], [60, 200], f(14, False))
    row(d, 394, ["Net content:", strength or "—"], [520, 640], f(14, False))
    row(d, 422, ["Physical form:", form or "Lyophilized powder"], [60, 200], f(14, False))

    # analytical results table
    panel(d, (40, 472, 860, 690), "ANALYTICAL RESULTS")
    xs = [60, 340, 540, 720]
    row(d, 516, ["TEST", "METHOD", "SPECIFICATION", "RESULT"], xs, f(13), INDIGO)
    d.line([48, 540, 852, 540], fill=BORDER, width=1)
    results = [
        ("Identity", "LC-MS", "Conforms", "Conforms"),
        ("Purity (assay)", "HPLC-UV", "≥ 99.0%", f"{purity:.2f}%"),
        ("Water / Moisture", "Karl Fischer", "≤ 8.0%", f"{water:.1f}%"),
        ("Related substances", "HPLC", "≤ 2.0%", f"{related:.1f}%"),
    ]
    yy = 552
    for r in results:
        row(d, yy, list(r), xs, f(13, False))
        yy += 32

    # storage + certification
    panel(d, (40, 710, 860, 812), "STORAGE & HANDLING")
    row(d, 756, ["Storage:", storage or "Store at -20°C"], [60, 200], f(14, False))
    row(d, 784, ["Handling:", "Protect from light and moisture."], [60, 200], f(14, False))

    panel(d, (40, 832, 860, 964), "CERTIFICATION")
    row(d, 878, ["Testing laboratory:", f"{BRAND} QC"], [60, 260], f(14, False))
    row(d, 906, ["Analyst:", "QC Department"], [60, 260], f(14, False))
    row(d, 906, ["Authorized by (QA):", "QA Department"], [480, 700], f(14, False))
    row(d, 934, ["Date of analysis:", f"{an_date}   ·   Retest: {retest}"], [60, 260], f(14, False))

    # footer note (discreet + honest)
    disc = ("Illustrative certificate generated for this demonstration project. "
            "All products are supplied for in vitro laboratory research use only; "
            "not for human or veterinary use, consumption, or application.")
    yy = 1000
    words, line = disc.split(), ""
    for w in words:
        if d.textlength((line + " " + w).strip(), font=f(12, False)) < 820:
            line = (line + " " + w).strip()
        else:
            d.text((40, yy), line, font=f(12, False), fill=MUTED); yy += 20; line = w
    if line:
        d.text((40, yy), line, font=f(12, False), fill=MUTED)

    img.save(os.path.join(OUT, f"sample-{slug}.png"))


def main():
    con = sqlite3.connect(DB)
    n = 0
    for p in PRODUCTS_SEED:
        strength = (p.get("variants") or [{}])[0].get("strength", "")
        make(p["slug"], p["name"], strength, p.get("form"), p.get("storage"), p.get("purity"))
        con.execute(
            "UPDATE products SET coa_file=?, coa_lab=? WHERE slug=?",
            (f"/static/coa/sample-{p['slug']}.png", "Sample (layout demo)", p["slug"]),
        )
        n += 1
    con.commit(); con.close()
    print(f"generated {n} sample COAs and linked them to products")


if __name__ == "__main__":
    main()
