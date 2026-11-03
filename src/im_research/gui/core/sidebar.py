#!/usr/bin/env python3
"""Sidebar navigation."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.icon_factory import IconSet


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, icon_set: IconSet, on_navigate, **kw):
        super().__init__(
            master,
            width=68,
            corner_radius=0,
            fg_color=SIDEBAR_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            **kw
        )
        self.pack_propagate(False)
        self.icon_set = icon_set
        self.on_navigate = on_navigate
        self._buttons = {}
        self._active_key = None
        self._build()

    def _build(self):
        # ── Brand Logo Icon (Top) ─────────────────────────────────────────────
        logo_btn = ctk.CTkButton(
            self,
            text="",
            image=self.icon_set.get("atom", active=True),
            width=46,
            height=46,
            corner_radius=12,
            fg_color="transparent",
            hover_color=INACTIVE_HOVER,
            cursor="hand2",
            command=lambda: self.activate("dashboard"),
        )
        logo_btn.pack(pady=(16, 20))
        Tooltip(logo_btn, "IM-Benchmark-Lab — Trang chủ")

        # ── Navigation Buttons ────────────────────────────────────────────────
        for key, tooltip_text, icon_name in NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text="",
                image=self.icon_set.get(icon_name, active=False),
                width=46,
                height=46,
                corner_radius=12,
                fg_color="transparent",
                hover_color=INACTIVE_HOVER,
                cursor="hand2",
                command=lambda k=key: self.activate(k),
            )
            btn.pack(pady=4)
            Tooltip(btn, tooltip_text)
            self._buttons[key] = (btn, icon_name)

        # ── Bottom Spacer & Settings Icon ──────────────────────────────────────
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # Settings icon button (navigates to Settings page)
        settings_btn = ctk.CTkButton(
            self,
            text="",
            image=self.icon_set.get("settings", active=False),
            width=46,
            height=46,
            corner_radius=12,
            fg_color="transparent",
            hover_color=INACTIVE_HOVER,
            cursor="hand2",
            command=lambda: self.activate("settings"),
        )
        settings_btn.pack(side="bottom", pady=(0, 16))
        Tooltip(settings_btn, "Cài đặt hệ thống (Settings)")
        self._buttons["settings"] = (settings_btn, "settings")

    def activate(self, key: str):
        if self._active_key == key:
            return

        # Deactivate previous
        if self._active_key and self._active_key in self._buttons:
            old_btn, old_icon = self._buttons[self._active_key]
            old_btn.configure(
                fg_color="transparent",
                image=self.icon_set.get(old_icon, active=False)
            )

        # Activate new
        if key in self._buttons:
            new_btn, new_icon = self._buttons[key]
            new_btn.configure(
                fg_color=ACTIVE_BG,
                hover_color=ACTIVE_BG,
                image=self.icon_set.get(new_icon, active=True)
            )
        self._active_key = key
        self.on_navigate(key)

    def update_theme_icon(self, mode: str):
        # Refresh current icons if needed
        pass
