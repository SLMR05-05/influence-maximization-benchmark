#!/usr/bin/env python3
"""Status bar."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from datetime import datetime
from im_research.gui.core.theme import *
from im_research.core.theme_config import get_theme
class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, height=28, corner_radius=0,
                         fg_color=STATUS_BG, border_width=1,
                         border_color=BORDER_COLOR, **kw)
        self.pack_propagate(False)

        curr = get_theme()
        self._info_lbl = ctk.CTkLabel(
            self,
            text=f"● WSL2 Ubuntu 24.04  │  C++ Core OpenMP Ready  │  pybind11 Active  │  Theme: {curr.capitalize()}",
            font=FONT_SMALL, text_color=STATUS_FG, anchor="w"
        )
        self._info_lbl.pack(side="left", padx=14)

        self._clock = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=STATUS_FG, anchor="e")
        self._clock.pack(side="right", padx=14)
        self._tick()

    def update_theme_display(self, mode: str):
        self._info_lbl.configure(
            text=f"● WSL2 Ubuntu 24.04  │  C++ Core OpenMP Ready  │  pybind11 Active  │  Theme: {mode.capitalize()}"
        )

    def _tick(self):
        self._clock.configure(text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.after(1000, self._tick)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW APPLICATION
