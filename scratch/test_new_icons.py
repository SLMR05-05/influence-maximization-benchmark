import math
from PIL import Image, ImageDraw

def _canvas(size=128):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))

def draw_plus(size=128, color="#ffffff", stroke_width=8):
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = size / 2, size / 2
    r = 36
    d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=stroke_width)
    d.line([(cx, cy - r), (cx, cy + r)], fill=color, width=stroke_width)
    return im

def draw_trash(size=128, color="#ffffff", stroke_width=7):
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    # Lid
    d.line([(36, 38), (92, 38)], fill=color, width=stroke_width)
    d.line([(52, 38), (52, 28), (76, 28), (76, 38)], fill=color, width=stroke_width, joint="curve")
    # Can body
    d.line([(42, 42), (48, 104), (80, 104), (86, 42)], fill=color, width=stroke_width, joint="curve")
    # Vertical rib lines
    d.line([(56, 52), (56, 94)], fill=color, width=stroke_width - 2)
    d.line([(72, 52), (72, 94)], fill=color, width=stroke_width - 2)
    return im

def draw_refresh(size=128, color="#ffffff", stroke_width=7):
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    r = 38
    # Arc from 40 to 320 degrees
    d.arc([cx - r, cy - r, cx + r, cy + r], start=40, end=320, fill=color, width=stroke_width)
    # Arrow head at start of arc (around top right)
    d.polygon([(94, 30), (106, 50), (84, 52)], fill=color)
    return im

def draw_play(size=128, color="#ffffff", stroke_width=7):
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    # Right-pointing triangle
    pts = [(44, 32), (96, 64), (44, 96)]
    d.polygon(pts, fill=color)
    return im

for name, fn in [("plus", draw_plus), ("trash", draw_trash), ("refresh", draw_refresh), ("play", draw_play)]:
    im = fn()
    print(name, im.size)
print("New icons tested successfully!")
