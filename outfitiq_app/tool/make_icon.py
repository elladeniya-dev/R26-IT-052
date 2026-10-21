"""OutfitIQ app icon: white clothes hanger + sparkles on the brand blue gradient.
Draws at 4x and downsamples for clean edges. Writes three 1024px PNGs:
  app_icon.png            full-bleed square (iOS / legacy / web)
  app_icon_foreground.png transparent glyph inside the adaptive-icon safe zone
  app_icon_background.png gradient only (adaptive background)"""
import math
import os
import sys

from PIL import Image, ImageDraw

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

SIZE = 1024
SS = 4  # supersampling
S = SIZE * SS

TOP = (14, 110, 158)      # 0E6E9E  teal blue
BOTTOM = (7, 59, 90)      # 073B5A  navy
WHITE = (255, 255, 255, 255)
SPARK = (125, 211, 252, 255)  # light sky accent


def gradient():
    img = Image.new("RGBA", (S, S))
    px = img.load()
    # diagonal gradient, light top-left to dark bottom-right
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * (S - 1))
            px[x, y] = (
                int(TOP[0] + (BOTTOM[0] - TOP[0]) * t),
                int(TOP[1] + (BOTTOM[1] - TOP[1]) * t),
                int(TOP[2] + (BOTTOM[2] - TOP[2]) * t),
                255,
            )
    return img


def dot(d, x, y, w, fill):
    r = w / 2
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def line(d, p1, p2, w, fill):
    dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    steps = max(2, int(dist / (w / 8)))
    for i in range(steps + 1):
        t = i / steps
        dot(d, p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t, w, fill)


def curve(d, cx, cy, r, a0, a1, w, fill):
    """Round-brush arc around (cx, cy), degrees, y down."""
    steps = max(8, int(abs(a1 - a0) * math.pi / 180 * r / (w / 8)))
    for i in range(steps + 1):
        ang = math.radians(a0 + (a1 - a0) * i / steps)
        dot(d, cx + r * math.cos(ang), cy + r * math.sin(ang), w, fill)


def star(d, cx, cy, r, fill, squash=0.28):
    """Four-point sparkle with concave sides."""
    pts = []
    for i in range(8):
        ang = math.radians(-90 + i * 45)
        rad = r if i % 2 == 0 else r * squash
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=fill)


def glyph(scale, ox=0, oy=0):
    """Transparent layer with the hanger and sparkles, centred on the canvas."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = SS * scale

    def P(x, y):  # design space is 1024 with centre (512, 512)
        return (S / 2 + (x - 512) * k + ox, S / 2 + (y - 512) * k + oy)

    w = int(54 * k)

    # hanger body: shoulders and bottom bar
    apex = P(512, 478)
    left = P(176, 716)
    right = P(848, 716)
    line(d, apex, left, w, WHITE)
    line(d, apex, right, w, WHITE)
    line(d, left, right, w, WHITE)

    # hook: neck rising from the apex, then a curl open to the lower left
    neck_top = P(512, 392)
    line(d, apex, neck_top, w, WHITE)
    r = 76 * k
    curve(d, neck_top[0] - r, neck_top[1], r, 0, -205, w, WHITE)

    # sparkles ("IQ": the smart part)
    star(d, *P(748, 318), 112 * k, SPARK)
    star(d, *P(856, 214), 48 * k, WHITE)
    star(d, *P(640, 232), 30 * k, WHITE)
    return img


def down(img):
    return img.resize((SIZE, SIZE), Image.LANCZOS)


bg = gradient()

# full icon: glyph fills most of the square
full = bg.copy()
full.alpha_composite(glyph(1.0, ox=int(4 * SS), oy=int(34 * SS)))
down(full).convert("RGB").save(os.path.join(OUT, "app_icon.png"))

# adaptive foreground: shrink into the central safe zone (~62%)
# the launcher-icons tool already insets the foreground 16% per side
down(glyph(1.12, ox=int(4 * SS), oy=int(34 * SS * 1.12))).save(os.path.join(OUT, "app_icon_foreground.png"))
down(bg).convert("RGB").save(os.path.join(OUT, "app_icon_background.png"))
print("done")
