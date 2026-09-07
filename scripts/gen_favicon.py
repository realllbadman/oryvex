"""Generate the Oryvex favicon set (crimson mark, white 'O').

  static/favicon.ico              multi-size ICO for the browser tab
  static/images/favicon.png       32x32 PNG
  static/images/apple-touch-icon.png  180x180 PNG
Run: python3 scripts/gen_favicon.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

CRIMSON = (227, 53, 72)
DEEP = (198, 42, 56)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT_IMG = os.path.join("static", "images")
os.makedirs(OUT_IMG, exist_ok=True)


def mark(size: int, radius_ratio: float = 0.24) -> Image.Image:
    """Crimson rounded tile with a white ring-and-dot 'O' monogram."""
    s = size * 4                                   # supersample
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # rounded crimson tile with a subtle vertical gradient
    grad = Image.new("RGB", (1, s))
    for y in range(s):
        t = y / (s - 1)
        grad.putpixel((0, y), tuple(int(CRIMSON[i] + (DEEP[i] - CRIMSON[i]) * t) for i in range(3)))
    grad = grad.resize((s, s))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1],
                                           radius=int(s * radius_ratio), fill=255)
    img.paste(grad, (0, 0), mask)

    # the 'O' — a heavy white ring, matching the wordmark's weight
    pad = s * 0.235
    ring = s * 0.135
    d.ellipse([pad, pad, s - pad, s - pad], outline=(255, 255, 255, 255), width=int(ring))

    return img.resize((size, size), Image.LANCZOS)


def main():
    mark(180).save(os.path.join(OUT_IMG, "apple-touch-icon.png"))
    mark(32).save(os.path.join(OUT_IMG, "favicon.png"))
    # ICO with the sizes browsers actually pick from
    sizes = [16, 32, 48, 64, 128, 256]
    imgs = [mark(n, 0.22 if n <= 32 else 0.24) for n in sizes]
    imgs[-1].save(os.path.join("static", "favicon.ico"),
                  format="ICO", sizes=[(n, n) for n in sizes])
    print("wrote static/favicon.ico, static/images/favicon.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
