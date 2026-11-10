#!/usr/bin/env python3
"""
Top Application Header Bar for IM-Benchmark-Lab.
Features:
- Dynamic Breadcrumb navigation showing current page context.
- System health & readiness status pills (C++ OpenMP, 5/5 Datasets, Model).
- 1-click Quick Theme Switch button (Sun / Moon).
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.icon_factory import IconSet
from im_research.core.theme_config import get_theme, set_theme

PAGE_TITLES = {
    "dashboard":   "Tổng quan nghiên cứu (Dashboard)",
    "datasets":    "Bộ dữ liệu chuẩn & Mạng lưới 3D",
    "statistics":  "Thống kê & So sánh (Results & Performance Comparison)",
    "results":     "Thống kê & So sánh — Kết quả lan truyền",
    "comparison":  "Thống kê & So sánh — So sánh thuật toán",
    "experiments": "Thiết lập & Khởi chạy thí nghiệm",
    "reports":     "Xuất báo cáo & Luận văn học thuật",
    "runtime":     "System & Runtime — Môi trường thực thi & Tài nguyên",
    "settings":    "Cài đặt hệ thống & Tham số môi trường",
}


class TopHeader(ctk.CTkFrame):
    def __init__(self, master, icon_set: IconSet, on_toggle_theme=None, **kw):
        super().__init__(
            master,
            height=52,
            corner_radius=0,
            fg_color=CARD_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            **kw
        )
        self.pack_propagate(False)
        self.icon_set = icon_set
        self.on_toggle_theme_cb = on_toggle_theme
        self._build()

    def _build(self):
        # ── Left: Breadcrumb Path ─────────────────────────────────────────────
        left_box = ctk.CTkFrame(self, fg_color="transparent")
        left_box.pack(side="left", padx=20, fill="y")

        self.lbl_root = ctk.CTkLabel(
            left_box,
            text="IM-Benchmark-Lab",
            font=("Segoe UI", 11, "bold"),
            text_color=SUBTEXT_FG
        )
        self.lbl_root.pack(side="left")

        self.lbl_slash = ctk.CTkLabel(
            left_box,
            text="  /  ",
            font=("Segoe UI", 11),
            text_color=SUBTEXT_FG
        )
        self.lbl_slash.pack(side="left")

        self.lbl_current_page = ctk.CTkLabel(
            left_box,
            text="Tổng quan nghiên cứu (Dashboard)",
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG
        )
        self.lbl_current_page.pack(side="left")

        # ── Right: Status Pills & Theme Switcher ───────────────────────────────
        right_box = ctk.CTkFrame(self, fg_color="transparent")
        right_box.pack(side="right", padx=16, fill="y")

        # Pill 1: OpenMP Ready
        p1 = ctk.CTkFrame(right_box, fg_color=GREEN_PILL_BG, corner_radius=12, height=26)
        p1.pack(side="left", padx=4, pady=13)
        ctk.CTkLabel(
            p1, text="● C++17 OpenMP Ready",
            font=("Segoe UI", 9, "bold"), text_color=GREEN_PILL_FG
        ).pack(padx=10, pady=2)
        Tooltip(p1, "Lõi tính toán C++ OpenMP CSR song song đa luồng")

        # Pill 2: 5/5 Datasets Ready
        p2 = ctk.CTkFrame(right_box, fg_color=CYAN_PILL_BG, corner_radius=12, height=26)
        p2.pack(side="left", padx=4, pady=13)
        ctk.CTkLabel(
            p2, text="● 5/5 Datasets (100%)",
            font=("Segoe UI", 9, "bold"), text_color=CYAN_PILL_FG
        ).pack(padx=10, pady=2)
        Tooltip(p2, "Đầy đủ 5 bộ benchmark: Karate, Dolphins, Facebook, NetHEPT, Enron")

        # Pill 3: Model IC
        p3 = ctk.CTkFrame(right_box, fg_color=PILL_BG, corner_radius=12, height=26)
        p3.pack(side="left", padx=4, pady=13)
        ctk.CTkLabel(
            p3, text="● Model: IC",
            font=("Segoe UI", 9, "bold"), text_color=PILL_FG
        ).pack(padx=10, pady=2)
        Tooltip(p3, "Independent Cascade — cấu hình p, MC và seed tại Bộ dữ liệu → Cấu hình lan truyền (IC)")

        # Vertical Divider
        ctk.CTkFrame(right_box, width=1, height=22, fg_color=DIVIDER).pack(side="left", padx=8, pady=15)

        # Quick Theme Toggle Icon Button
        curr = get_theme()
        is_dark = curr == "dark"
        icon_name = "sun" if is_dark else "moon"

        self.theme_btn = ctk.CTkButton(
            right_box,
            text="",
            image=self.icon_set.get(icon_name, active=False),
            width=32,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=INACTIVE_HOVER,
            cursor="hand2",
            command=self._on_theme_click
        )
        self.theme_btn.pack(side="left", padx=2, pady=10)
        Tooltip(self.theme_btn, "Chuyển đổi nhanh Giao diện Sáng / Tối")

    def set_page(self, key: str):
        title = PAGE_TITLES.get(key, key.capitalize())
        self.lbl_current_page.configure(text=title)

    def _on_theme_click(self):
        curr = get_theme()
        new_mode = "light" if curr == "dark" else "dark"
        set_theme(new_mode)
        ctk.set_appearance_mode(new_mode)

        self.update_theme_display(new_mode)

        if self.on_toggle_theme_cb:
            self.on_toggle_theme_cb(new_mode)
        else:
            top = self.winfo_toplevel()
            if hasattr(top, "on_theme_changed"):
                top.on_theme_changed(new_mode)

    def update_theme_display(self, mode: str):
        is_dark = mode == "dark"
        icon_name = "sun" if is_dark else "moon"
        if hasattr(self, "theme_btn"):
            self.theme_btn.configure(
                image=self.icon_set.get(icon_name, active=False)
            )

