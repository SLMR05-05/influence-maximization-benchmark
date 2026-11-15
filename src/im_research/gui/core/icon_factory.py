"""
Procedural Icon Generator for IM-Benchmark-Lab GUI.
Generates crisp antialiased outline & filled icons matching the design specification.
Supports adaptive multi-theme (Light & Dark mode via CTkImage).
"""

from __future__ import annotations
import math
from PIL import Image, ImageDraw, ImageChops
import customtkinter as ctk

# Color palette
BLUE_LIGHT    = "#1a73e8"
CYAN_DARK     = "#00e5ff"
GRAY_LIGHT    = "#475569"
SILVER_DARK   = "#cbd5e1"
WHITE         = "#ffffff"

def _canvas(size=128):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))

def _downscale(img, target_size=24):
    return img.resize((target_size, target_size), Image.Resampling.LANCZOS)

def draw_atom(size=128, color="#1a73e8", stroke_width=6):
    """Draws atomic orbital logo with nucleus and orbits."""
    im = _canvas(size)
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
    
    # 3 orbital electrons symmetrically placed along orbits
    electrons = [
        (cx + 42, cy - 8),
        (cx - 30, cy + 34),
        (cx - 24, cy - 36),
    ]
    for ex, ey in electrons:
        d.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=color)
    return im

def draw_home(size=128, color=WHITE, stroke_width=7, filled=False):
    """Draws clean home outline icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    if filled:
        d.polygon([(64, 22), (24, 58), (34, 58), (34, 106), (54, 106), (54, 76), (74, 76), (74, 106), (94, 106), (94, 58), (104, 58)], fill=color)
    else:
        # Roof
        d.line([(22, 60), (64, 24), (106, 60)], fill=color, width=stroke_width, joint="curve")
        # Chimney
        d.line([(82, 36), (82, 48)], fill=color, width=stroke_width - 1)
        # Walls
        d.line([(34, 58), (34, 106), (94, 106), (94, 58)], fill=color, width=stroke_width, joint="curve")
        # Door
        d.line([(54, 106), (54, 76), (74, 76), (74, 106)], fill=color, width=stroke_width - 1)
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
    """Draws central hub node connected to 5 peripheral nodes without hardcoded background fills."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    r_center = 12
    nodes = [
        (34, 34, 8),
        (94, 32, 8),
        (100, 88, 9),
        (34, 92, 8),
        (66, 102, 7),
    ]
    # Edge lines
    for x, y, r in nodes:
        d.line([(cx, cy), (x, y)], fill=color, width=stroke_width)
    # Peripheral nodes
    for x, y, r in nodes:
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    # Central hub
    d.ellipse([cx - r_center, cy - r_center, cx + r_center, cy + r_center], fill=color)
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
    """Draws settings gear/cog icon with connected teeth."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    teeth_count = 8
    # 8 teeth connecting into the ring (from r=34 to r=54)
    for i in range(teeth_count):
        deg = i * (360 / teeth_count)
        rad = math.radians(deg)
        x1 = cx + math.cos(rad) * 34
        y1 = cy + math.sin(rad) * 34
        x2 = cx + math.cos(rad) * 54
        y2 = cy + math.sin(rad) * 54
        d.line([(x1, y1), (x2, y2)], fill=color, width=10)
    
    # Outer ring
    r_outer = 40
    d.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], outline=color, width=stroke_width)
    # Inner hole
    r_inner = 16
    d.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], outline=color, width=stroke_width)
    return im

def draw_sun(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws sun icon for light mode."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    r_sun = 22
    d.ellipse([cx - r_sun, cy - r_sun, cx + r_sun, cy + r_sun], outline=color, width=stroke_width)
    # 8 rays
    ray_in, ray_out = 34, 48
    for i in range(8):
        rad = math.radians(i * 45)
        x1 = cx + math.cos(rad) * ray_in
        y1 = cy + math.sin(rad) * ray_in
        x2 = cx + math.cos(rad) * ray_out
        y2 = cy + math.sin(rad) * ray_out
        d.line([(x1, y1), (x2, y2)], fill=color, width=stroke_width, joint="curve")
    return im

def draw_moon(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws clean crescent moon icon for dark mode."""
    im = _canvas(size)
    moon_layer = _canvas(size)
    md = ImageDraw.Draw(moon_layer)
    md.ellipse([26, 24, 102, 100], fill=color)
    
    cut_layer = _canvas(size)
    cd = ImageDraw.Draw(cut_layer)
    cd.ellipse([46, 18, 116, 94], fill=(0, 0, 0, 255))
    
    mask = cut_layer.split()[-1]
    moon_alpha = moon_layer.split()[-1]
    final_alpha = ImageChops.subtract(moon_alpha, mask)
    moon_layer.putalpha(final_alpha)
    im.alpha_composite(moon_layer)
    return im

def draw_chip(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws CPU processor chip icon with sharp pins and core die."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    # Chip body
    d.rounded_rectangle([32, 32, 96, 96], radius=10, outline=color, width=stroke_width)
    # Inner core die
    d.rounded_rectangle([48, 48, 80, 80], radius=4, outline=color, width=5)
    # Pins (3 on each of the 4 sides, length 14, width 6)
    pin_len = 14
    for p in [46, 64, 82]:
        d.line([(p, 32 - pin_len), (p, 32)], fill=color, width=6)
        d.line([(p, 96), (p, 96 + pin_len)], fill=color, width=6)
        d.line([(32 - pin_len, p), (32, p)], fill=color, width=6)
        d.line([(96, p), (96 + pin_len, p)], fill=color, width=6)
    return im

def draw_plus(size=128, color=GRAY_LIGHT, stroke_width=8):
    """Draws plus / add icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = size / 2, size / 2
    r = 34
    d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=stroke_width)
    d.line([(cx, cy - r), (cx, cy + r)], fill=color, width=stroke_width)
    return im

def draw_trash(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws trash can / delete icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    # Lid
    d.line([(34, 38), (94, 38)], fill=color, width=stroke_width)
    d.line([(52, 38), (52, 28), (76, 28), (76, 38)], fill=color, width=stroke_width, joint="curve")
    # Can body
    d.line([(42, 42), (48, 104), (80, 104), (86, 42)], fill=color, width=stroke_width, joint="curve")
    # Inner ribs
    d.line([(56, 52), (56, 94)], fill=color, width=stroke_width - 2)
    d.line([(72, 52), (72, 94)], fill=color, width=stroke_width - 2)
    return im

def draw_refresh(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws circular arrow reload icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    r = 38
    d.arc([cx - r, cy - r, cx + r, cy + r], start=40, end=320, fill=color, width=stroke_width)
    d.polygon([(94, 30), (108, 52), (84, 52)], fill=color)
    return im

def draw_play(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws right-pointing play triangle icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    d.polygon([(44, 32), (96, 64), (44, 96)], fill=color)
    return im

def draw_check(size=128, color=GRAY_LIGHT, stroke_width=8):
    """Draws checkmark icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    d.line([(32, 64), (54, 88), (98, 40)], fill=color, width=stroke_width, joint="curve")
    return im

def draw_info(size=128, color=GRAY_LIGHT, stroke_width=7):
    """Draws circular info icon."""
    im = _canvas(size)
    d = ImageDraw.Draw(im)
    cx, cy = 64, 64
    r = 44
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=stroke_width)
    d.ellipse([cx - 4, cy - 24, cx + 4, cy - 16], fill=color)
    d.line([(cx, cy - 6), (cx, cy + 22)], fill=color, width=stroke_width)
    return im


class IconSet:
    """Provides CTkImage objects for active, inactive, and hover states with safe fallbacks."""
    def __init__(self, target_size=20):
        self.target_size = target_size
        self._cache = {}
        self._init_all()

    def _init_all(self):
        # Atom Logo: Blue in light mode, Cyan in dark mode
        logo_light = _downscale(draw_atom(size=128, color=BLUE_LIGHT), 36)
        logo_dark  = _downscale(draw_atom(size=128, color=CYAN_DARK), 36)
        self.logo = ctk.CTkImage(light_image=logo_light, dark_image=logo_dark, size=(36, 36))
        self._cache["atom"] = {"inactive": self.logo, "active": self.logo, "hover": self.logo}
        self._cache["logo"] = {"inactive": self.logo, "active": self.logo, "hover": self.logo}

        # Generators for items
        items = [
            ("home",       draw_home),
            ("line_chart", draw_line_chart),
            ("bar_chart",  draw_bar_chart),
            ("network",    draw_network),
            ("flask",      draw_flask),
            ("document",   draw_document),
            ("settings",   draw_settings),
            ("sun",        draw_sun),
            ("moon",       draw_moon),
            ("chip",       draw_chip),
            ("plus",       draw_plus),
            ("trash",      draw_trash),
            ("refresh",    draw_refresh),
            ("play",       draw_play),
            ("check",      draw_check),
            ("info",       draw_info),
        ]

        for name, fn in items:
            img_inactive_light = _downscale(fn(color=GRAY_LIGHT), self.target_size)
            img_inactive_dark  = _downscale(fn(color=SILVER_DARK), self.target_size)
            img_active = _downscale(fn(color=WHITE), self.target_size)
            img_hover_light = _downscale(fn(color="#0f172a"), self.target_size)
            img_hover_dark  = _downscale(fn(color=WHITE), self.target_size)

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
                "hover": ctk.CTkImage(
                    light_image=img_hover_light,
                    dark_image=img_hover_dark,
                    size=(self.target_size, self.target_size)
                ),
            }

    def get(self, name: str, active: bool = False, state: str = None) -> ctk.CTkImage:
        """Retrieves CTkImage by name with intelligent alias mapping and guaranteed fallback."""
        key = str(name).lower().strip()
        alias_map = {
            "chart": "bar_chart",
            "results": "bar_chart",
            "comparison": "bar_chart",
            "stats": "bar_chart",
            "statistics": "bar_chart",
            "reports": "document",
            "report": "document",
            "datasets": "network",
            "dataset": "network",
            "graph": "network",
            "runtime": "chip",
            "system": "chip",
            "cpu": "chip",
            "experiments": "flask",
            "experiment": "flask",
            "lab": "flask",
            "add": "plus",
            "create": "plus",
            "new": "plus",
            "delete": "trash",
            "remove": "trash",
            "reload": "refresh",
            "run": "play",
            "start": "play",
        }
        key = alias_map.get(key, key)
        if key not in self._cache:
            key = "settings"

        if state and state in self._cache.get(key, {}):
            return self._cache[key][state]
        s = "active" if active else "inactive"
        return self._cache[key].get(s, self._cache[key].get("inactive", self.logo))
