#!/usr/bin/env python3
"""
Modern Sidebar Navigation for IM-Benchmark-Lab.
Features:
- Professional 236px width layout with brand identity.
- Atom logo & Research Platform badge.
- Navigation items with both crisp custom vector icons and typography.
- Active pill styling with high-contrast accent.
- 1-click Light / Dark Mode Toggle button.
- Settings navigation and system readiness badge.
"""

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
from im_research.core.theme_config import get_theme, set_theme


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, icon_set: IconSet, on_navigate, on_toggle_theme=None, **kw):
        super().__init__(
            master,
            width=236,
            corner_radius=0,
            fg_color=SIDEBAR_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            **kw
        )
        self.pack_propagate(False)
        self.icon_set = icon_set
        self.on_navigate = on_navigate
        self.on_toggle_theme_cb = on_toggle_theme
        self._buttons = {}
        self._active_key = None
        self._build()

    def _build(self):
        # ── 1. Brand Logo & Header ───────────────────────────────────────────
        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.pack(fill="x", padx=14, pady=(16, 12))

        # Atom Icon in soft pill badge
        logo_badge = ctk.CTkFrame(
            brand_frame,
            width=40,
            height=40,
            corner_radius=10,
            fg_color=PILL_BG
        )
        logo_badge.pack(side="left")
        logo_badge.pack_propagate(False)

        logo_lbl = ctk.CTkLabel(logo_badge, text="", image=self.icon_set.get("atom", active=True))
        logo_lbl.pack(expand=True)

        # Brand Text Labels
        brand_text_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_text_box.pack(side="left", padx=(10, 0), fill="both", expand=True)

        ctk.CTkLabel(
            brand_text_box,
            text="IM-Benchmark-Lab",
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG,
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text_box,
            text="RESEARCH PLATFORM",
            font=("Segoe UI", 7, "bold"),
            text_color=SUBTEXT_FG,
            anchor="w"
        ).pack(anchor="w")

        # Top subtle separator line
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=14, pady=(2, 10))

        # ── 2. Navigation Section Label ───────────────────────────────────────
        nav_lbl = ctk.CTkLabel(
            self,
            text="ĐIỀU HƯỚNG CHÍNH",
            font=("Segoe UI", 8, "bold"),
            text_color=SUBTEXT_FG,
            anchor="w"
        )
        nav_lbl.pack(fill="x", padx=18, pady=(0, 6))

        # ── 3. Navigation Buttons ─────────────────────────────────────────────
        for key, title, icon_name in NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"   {title}",
                image=self.icon_set.get(icon_name, active=False),
                compound="left",
                anchor="w",
                height=40,
                corner_radius=8,
                font=FONT_MAIN,
                fg_color="transparent",
                text_color=SUBTEXT_FG,
                hover_color=INACTIVE_HOVER,
                cursor="hand2",
                command=lambda k=key: self.activate(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._buttons[key] = (btn, icon_name, title)

        # ── 4. Flexible Spacer ────────────────────────────────────────────────
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # ── 5. Bottom Utility Area ────────────────────────────────────
        # Bottom separator
        ctk.CTkFrame(self, height=1, fg_color=DIVIDER).pack(fill="x", padx=14, pady=(8, 10))

        # Quick Theme Toggle Button
        curr_theme = get_theme()
        is_dark = curr_theme == "dark"
        theme_txt = "   Chế độ Sáng" if is_dark else "   Chế độ Tối"
        theme_icon_name = "sun" if is_dark else "moon"

        self.theme_btn = ctk.CTkButton(
            self,
            text=theme_txt,
            image=self.icon_set.get(theme_icon_name, active=False),
            compound="left",
            anchor="w",
            height=38,
            corner_radius=8,
            font=FONT_MAIN,
            fg_color="transparent",
            text_color=SUBTEXT_FG,
            hover_color=INACTIVE_HOVER,
            cursor="hand2",
            command=self._on_quick_theme_toggle,
        )
        self.theme_btn.pack(fill="x", padx=12, pady=2)

        # Settings button
        settings_btn = ctk.CTkButton(
            self,
            text="   Cài đặt hệ thống",
            image=self.icon_set.get("settings", active=False),
            compound="left",
            anchor="w",
            height=38,
            corner_radius=8,
            font=FONT_MAIN,
            fg_color="transparent",
            text_color=SUBTEXT_FG,
            hover_color=INACTIVE_HOVER,
            cursor="hand2",
            command=lambda: self.activate("settings"),
        )
        settings_btn.pack(fill="x", padx=12, pady=2)
        self._buttons["settings"] = (settings_btn, "settings", "Cài đặt hệ thống")

        # System Readiness Pill
        status_box = ctk.CTkFrame(
            self,
            height=28,
            corner_radius=6,
            fg_color=GREEN_PILL_BG,
            border_width=1,
            border_color=BORDER_COLOR
        )
        status_box.pack(fill="x", padx=12, pady=(8, 12))
        status_box.pack_propagate(False)

        ctk.CTkLabel(
            status_box,
            text="● C++ OpenMP Ready  •  v1.0",
            font=("Segoe UI", 8, "bold"),
            text_color=GREEN_PILL_FG
        ).pack(expand=True)

    def activate(self, key: str):
        if self._active_key == key:
            return

        # Deactivate previous button
        if self._active_key and self._active_key in self._buttons:
            old_btn, old_icon, old_title = self._buttons[self._active_key]
            old_btn.configure(
                fg_color="transparent",
                text_color=SUBTEXT_FG,
                font=FONT_MAIN,
                image=self.icon_set.get(old_icon, active=False)
            )

        # Activate new button
        if key in self._buttons:
            new_btn, new_icon, new_title = self._buttons[key]
            new_btn.configure(
                fg_color=ACTIVE_BG,
                hover_color=ACTIVE_HOVER,
                text_color="#ffffff",
                font=FONT_BOLD,
                image=self.icon_set.get(new_icon, active=True)
            )

        self._active_key = key
        self.on_navigate(key)

    def _on_quick_theme_toggle(self):
        curr = get_theme()
        new_mode = "light" if curr == "dark" else "dark"
        set_theme(new_mode)
        ctk.set_appearance_mode(new_mode)

        self.update_theme_icon(new_mode)

        if self.on_toggle_theme_cb:
            self.on_toggle_theme_cb(new_mode)
        else:
            top = self.winfo_toplevel()
            if hasattr(top, "on_theme_changed"):
                top.on_theme_changed(new_mode)

    def update_theme_icon(self, mode: str):
        is_dark = mode == "dark"
        theme_txt = "   Chế độ Sáng" if is_dark else "   Chế độ Tối"
        theme_icon_name = "sun" if is_dark else "moon"
        if hasattr(self, "theme_btn"):
            self.theme_btn.configure(
                text=theme_txt,
                image=self.icon_set.get(theme_icon_name, active=False)
            )
