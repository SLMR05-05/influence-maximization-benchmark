#!/usr/bin/env python3
"""UI helper functions and empty state illustration generator."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from im_research.gui.core.theme import *

def section_header(parent, title: str, subtitle: str = ""):
    box = ctk.CTkFrame(parent, fg_color="transparent")
    box.pack(fill="x", pady=(0, 14))
    ctk.CTkLabel(box, text=title, font=FONT_TITLE, text_color=HEADER_FG).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(box, text=subtitle, font=FONT_MAIN, text_color=SUBTEXT_FG).pack(anchor="w", pady=(2, 0))


def metric_card(parent, title, value, subtitle="", color=BLUE, col=0, row=0):
    card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                        border_width=1, border_color=BORDER_COLOR)
    card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
    ctk.CTkLabel(card, text=str(value), font=FONT_CARD, text_color=color).pack(padx=16, pady=(14, 0))
    ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(padx=16, pady=(2, 0))
    if subtitle:
        ctk.CTkLabel(card, text=subtitle, font=FONT_SMALL, text_color=SUBTEXT_FG).pack(padx=16, pady=(0, 12))
    return card


_EMPTY_IMAGE_CACHE = None

def get_empty_state_image(target_size=(130, 130)) -> ctk.CTkImage:
    """Generates an antialiased empty state vector illustration for Light & Dark mode."""
    global _EMPTY_IMAGE_CACHE
    if _EMPTY_IMAGE_CACHE is not None:
        return _EMPTY_IMAGE_CACHE

    def _draw(is_dark: bool, size=260):
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx, cy = size / 2, size / 2

        bg_circle = "#1e293b" if is_dark else "#f1f5f9"
        border_col = "#334155" if is_dark else "#e2e8f0"
        paper_bg = "#131c31" if is_dark else "#ffffff"
        back_paper = "#0f172a" if is_dark else "#f8fafc"
        accent = "#38bdf8" if is_dark else "#1a73e8"
        accent_mag = "#00e5ff" if is_dark else "#0284c7"
        line_col = "#334155" if is_dark else "#cbd5e1"

        # Background circular aura
        d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100], fill=bg_circle, outline=border_col, width=2)
        # Back floating paper
        d.rounded_rectangle([cx - 48, cy - 62, cx + 58, cy + 42], radius=12, fill=back_paper, outline=line_col, width=2)
        # Front paper
        d.rounded_rectangle([cx - 62, cy - 44, cx + 44, cy + 62], radius=12, fill=paper_bg, outline=accent, width=2)
        # Title bar & content lines
        d.line([(cx - 46, cy - 24), (cx + 12, cy - 24)], fill=accent, width=4)
        d.line([(cx - 46, cy - 8), (cx + 28, cy - 8)], fill=line_col, width=3)
        d.line([(cx - 46, cy + 8), (cx + 8, cy + 8)], fill=line_col, width=3)
        d.line([(cx - 46, cy + 24), (cx - 8, cy + 24)], fill=line_col, width=3)
        # Magnifying glass on corner
        mx, my = cx + 38, cy + 34
        d.ellipse([mx - 24, my - 24, mx + 24, my + 24], fill=paper_bg, outline=accent_mag, width=3)
        d.line([(mx + 17, my + 17), (mx + 36, my + 36)], fill=accent_mag, width=6)
        # Sparkle inside magnifier
        d.line([(mx - 8, my), (mx + 8, my)], fill=accent_mag, width=2)
        d.line([(mx, my - 8), (mx, my + 8)], fill=accent_mag, width=2)

        return im

    img_l = _draw(is_dark=False)
    img_d = _draw(is_dark=True)
    _EMPTY_IMAGE_CACHE = ctk.CTkImage(light_image=img_l, dark_image=img_d, size=target_size)
    return _EMPTY_IMAGE_CACHE


def create_empty_state(parent, title: str, subtitle: str, action_text: str = None, action_command=None, pady=28):
    """
    Renders a unified empty state container featuring the graphical empty illustration,
    descriptive text, and an optional action button.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(pady=pady, fill="x")

    # Graphic Illustration Image
    img = get_empty_state_image()
    ctk.CTkLabel(frame, image=img, text="").pack(pady=(0, 10))

    # Title & Subtitle
    ctk.CTkLabel(frame, text=title, font=("Segoe UI", 13, "bold"), text_color=HEADER_FG).pack(pady=(2, 4))
    ctk.CTkLabel(frame, text=subtitle, font=FONT_MAIN, text_color=SUBTEXT_FG).pack(pady=(0, 12))

    # Optional CTA Action Button
    if action_text and action_command:
        ctk.CTkButton(
            frame,
            text=action_text,
            font=("Segoe UI", 11, "bold"),
            fg_color=BLUE,
            hover_color="#1557b0",
            corner_radius=8,
            width=190,
            height=34,
            command=action_command
        ).pack(pady=(4, 0))

    return frame
