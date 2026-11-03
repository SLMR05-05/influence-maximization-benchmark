#!/usr/bin/env python3
"""UI helper functions."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
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

