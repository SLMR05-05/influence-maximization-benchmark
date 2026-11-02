"""
Procedural Icon Generator for IM-Benchmark-Lab GUI.
Generates crisp antialiased outline & filled icons matching the design specification.
Supports adaptive multi-theme (Light & Dark mode via CTkImage).
"""

import math
from PIL import Image, ImageDraw
import customtkinter as ctk

# Color palette
BLUE_LIGHT    = "#1a73e8"
CYAN_DARK     = "#00e5ff"
GRAY_LIGHT    = "#3c4043"
SILVER_DARK   = "#cbd5e1"
WHITE         = "#ffffff"

def _canvas(size=128):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))

def _downscale(img, target_size=26):
    return img.resize((target_size, target_size), Image.Resampling.LANCZOS)

def draw_atom(size=128, color="#1a73e8", stroke_width=6):
    """Draws atomic orbital logo with nucleus and orbits."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = size / 2, size / 2
    
    # 3 orbital ellipses rotated at 0, 60, 120 deg
    rx, ry = 48, 18
    for angle in [0, 60, 120]:
        orbit_layer = _canvas(size)
        od = ImageDraw.Draw(orbit_layer)
        od.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=color, width=stroke_width)
        rotated = orbit_layer.rotate(angle, resample=Image.Resampling.BICUBIC, center=(cx, cy))
        im.alpha_composite(rotated)
    
    d = ImageDraw.Draw(im)
    r_nuc = 11
    d.ellipse([cx - r_nuc, cy - r_nuc, cx + r_nuc, cy + r_nuc], fill=color)
    d.ellipse([20, 36, 32, 48], fill=color)
    return im

def draw_home(size=128, color=WHITE, stroke_width=7, filled=True):
    """Draws home icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    if filled:
        d.polygon([(64, 22), (22, 60), (32, 60), (32, 106), (54, 106), (54, 76), (74, 76), (74, 106), (96, 106), (96, 60), (106, 60)], fill=color)
    else:
        d.line([(22, 60), (64, 22), (106, 60)], fill=color, width=stroke_width, joint="curve")
        d.line([(32, 58), (32, 106), (54, 106), (54, 78), (74, 78), (74, 106), (96, 106), (96, 58)], fill=color, width=stroke_width, joint="curve")
    return im

def draw_line_chart(size=128, color=GRAY_LIGHT, stroke_width=8):
    """Draws line chart with upward trend and arrow."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    d.line([(24, 22), (24, 104), (106, 104)], fill=color, width=stroke_width, joint="curve")
    points = [(30, 88), (52, 64), (72, 74), (98, 36)]
    d.line(points, fill=color, width=stroke_width, joint="curve")
    d.line([(80, 36), (98, 36), (98, 54)], fill=color, width=stroke_width, joint="curve")
    return im

def draw_bar_chart(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws 3 outline vertical bars (low, tall, medium)."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([24, 62, 46, 106], radius=4, outline=color, width=stroke_width)
    d.rounded_rectangle([52, 30, 74, 106], radius=4, outline=color, width=stroke_width)
    d.rounded_rectangle([80, 48, 102, 106], radius=4, outline=color, width=stroke_width)
    return im

def draw_network(size=128, color=GRAY_LIGHT, stroke_width=6):
    """Draws central hub node connected to 4-5 peripheral nodes."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    r_center = 12
    nodes = [
        (32, 34, 9),
        (96, 32, 9),
        (100, 88, 10),
        (34, 92, 9),
        (64, 104, 8),
    ]
    for x, y, r in nodes:
        d.line([(cx, cy), (x, y)], fill=color, width=stroke_width)
    d.ellipse([cx - r_center, cy - r_center, cx + r_center, cy + r_center], outline=color, width=stroke_width, fill=color if color == WHITE else "#ffffff")
    if color != WHITE:
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=color)
    for x, y, r in nodes:
        d.ellipse([x - r, y - r, x + r, y + r], outline=color, width=stroke_width, fill=color if color == WHITE else "#ffffff")
    return im

def draw_flask(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws laboratory beaker / flask icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    d.line([(48, 22), (80, 22)], fill=color, width=stroke_width)
    d.line([(54, 22), (54, 48)], fill=color, width=stroke_width)
    d.line([(74, 22), (74, 48)], fill=color, width=stroke_width)
    d.line([(54, 48), (24, 104), (104, 104), (74, 48)], fill=color, width=stroke_width, joint="curve")
    d.ellipse([60, 80, 68, 88], fill=color)
    d.ellipse([72, 70, 78, 76], fill=color)
    return im

def draw_document(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws report document icon with lines."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    d.line([(76, 22), (30, 22), (30, 108), (98, 108), (98, 44), (76, 22)], fill=color, width=stroke_width, joint="curve")
    d.line([(76, 22), (76, 44), (98, 44)], fill=color, width=stroke_width, joint="curve")
    d.line([(44, 62), (84, 62)], fill=color, width=stroke_width)
    d.line([(44, 78), (74, 78)], fill=color, width=stroke_width)
    return im

def draw_settings(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws settings gear/cog icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    teeth_count = 6
    for i in range(teeth_count):
        deg = i * (360 / teeth_count)
        rad = math.radians(deg)
        x1 = cx + math.cos(rad) * 44
        y1 = cy + math.sin(rad) * 44
        x2 = cx + math.cos(rad) * 54
        y2 = cy + math.sin(rad) * 54
        d.line([(x1, y1), (x2, y2)], fill=color, width=12)
    r_outer = 40
    d.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], outline=color, width=stroke_width)
    r_inner = 16
    d.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], outline=color, width=stroke_width)
    return im

class IconSet:
    """Provides CTkImage objects for active (blue/white) and inactive (light/dark adapt) states."""
    def __init__(self, target_size=24):
        self.target_size = target_size
        self._cache = {}
        self._init_all()

    def _init_all(self):
        # Atom Logo: Blue in light mode, Cyan in dark mode
        logo_light = _downscale(draw_atom(size=128, color=BLUE_LIGHT), 36)
        logo_dark  = _downscale(draw_atom(size=128, color=CYAN_DARK), 36)
        self.logo = ctk.CTkImage(light_image=logo_light, dark_image=logo_dark, size=(36, 36))

        # Generators for items
        items = [
            ("home",       draw_home),
            ("line_chart", draw_line_chart),
            ("bar_chart",  draw_bar_chart),
            ("network",    draw_network),
            ("flask",      draw_flask),
            ("document",   draw_document),
            ("settings",   draw_settings),
        ]

        for name, fn in items:
            # Inactive icon: dark gray in light mode, bright silver in dark mode
            img_inactive_light = _downscale(fn(color=GRAY_LIGHT), self.target_size)
            img_inactive_dark  = _downscale(fn(color=SILVER_DARK), self.target_size)

            # Active icon: white on active blue background
            img_active = _downscale(fn(color=WHITE), self.target_size)

            self._cache[name] = {
                "inactive": ctk.CTkImage(
                    light_image=img_inactive_light,
                    dark_image=img_inactive_dark,
                    size=(self.target_size, self.target_size)
                ),
                "active": ctk.CTkImage(
                    light_image=img_active,
                    dark_image=img_active,
                    size=(self.target_size, self.target_size)
                ),
            }

    def get(self, name: str, active: bool = False) -> ctk.CTkImage:
        state = "active" if active else "inactive"
        return self._cache[name][state]
