#!/usr/bin/env python3
"""
Polished Application Status Bar for IM-Benchmark-Lab.
Displays system execution environment, backend status, and live clock.
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from datetime import datetime
from im_research.gui.core.theme import *
from im_research.core.theme_config import get_theme


class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(
            master,
            height=28,
            corner_radius=0,
            fg_color=STATUS_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            **kw
        )
        self.pack_propagate(False)

        curr = get_theme()
        theme_str = "Tối (Dark)" if curr == "dark" else "Sáng (Light)"

        self._info_lbl = ctk.CTkLabel(
            self,
            text=f"● WSL2 Ubuntu 24.04 LTS  │  C++17 OpenMP Engine Ready  │  pybind11 Fast CSR  │  Chủ đề: {theme_str}",
            font=FONT_SMALL,
            text_color=STATUS_FG,
            anchor="w"
        )
        self._info_lbl.pack(side="left", padx=16)

        # Right container for clock & status
        right_box = ctk.CTkFrame(self, fg_color="transparent")
        right_box.pack(side="right", padx=16)

        self._ready_badge = ctk.CTkLabel(
            right_box,
            text="Sẵn sàng thực nghiệm  │  ",
            font=FONT_SMALL,
            text_color=STATUS_FG
        )
        self._ready_badge.pack(side="left")

        self._clock = ctk.CTkLabel(
            right_box,
            text="",
            font=FONT_SMALL,
            text_color=STATUS_FG,
            anchor="e"
        )
        self._clock.pack(side="left")

        self._tick()

    def update_theme_display(self, mode: str):
        theme_str = "Tối (Dark)" if mode == "dark" else "Sáng (Light)"
        self._info_lbl.configure(
            text=f"● WSL2 Ubuntu 24.04 LTS  │  C++17 OpenMP Engine Ready  │  pybind11 Fast CSR  │  Chủ đề: {theme_str}"
        )

    def _tick(self):
        self._clock.configure(text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.after(1000, self._tick)
