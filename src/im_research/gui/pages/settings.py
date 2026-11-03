#!/usr/bin/env python3
"""Page module."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
class PageSettings(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._build()

    def _build(self):
        section_header(
            self,
            "Cài đặt hệ thống & Môi trường tính toán",
            "Tùy chỉnh giao diện, C++ Engine, Experiment Defaults, Algorithm Hyperparameters, Paths, Output, Performance, Notifications"
        )

        # ── 1. Appearance & Theme ─────────────────────────────────────────────
        self._card("1. Giao diện & Chủ đề (Appearance & Theme)")
        theme_row = ctk.CTkFrame(self, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(theme_row, text="Chế độ:", font=FONT_MAIN, width=200, anchor="w", text_color=SUBTEXT_FG).pack(side="left")
        curr = get_theme()
        self.theme_menu = ctk.CTkOptionMenu(theme_row, width=220, values=["Sáng (Light)", "Tối (Dark)", "Theo hệ thống (System)"], command=self._on_theme)
        self.theme_menu.set("Tối (Dark)" if curr == "dark" else ("Sáng (Light)" if curr == "light" else "Theo hệ thống (System)"))
        self.theme_menu.pack(side="left")

        # ── 2. C++ Engine ─────────────────────────────────────────────────────
        self._card("2. C++ Engine (Lõi tính toán)")
        for lbl, val in [("Đường dẫn build:", "cpp_core/build/"), ("Chế độ biên dịch:", "Release (-O3 -march=native -fopenmp)"), ("Số luồng OpenMP:", "Auto (12)"), ("R_search (MC Search):", "200"), ("R_val (MC Validation):", "10000"), ("Timeout (giây):", "300")]:
            self._row(lbl, val)

        # ── 3. Experiment Defaults ────────────────────────────────────────────
        self._card("3. Experiment Defaults (Mặc định thí nghiệm)")
        for lbl, val in [("Dataset mặc định:", "Karate Club"), ("Mô hình lan truyền:", "IC (p=0.1)"), ("Giá trị k mặc định:", "5,10,15,20,25,30,40,50"), ("Số lần lặp độc lập:", "30"), ("Ngân sách đánh giá (Max evals):", "10000"), ("Auto-save checkpoint:", "Bật"), ("Resume on crash:", "Bật")]:
            self._row(lbl, val)

        # ── 4. Algorithm Hyperparameters ───────────────────────────────────────
        self._card("4. Algorithm Hyperparameters (Siêu tham số)")
        for lbl, val in [("GA — population:", "50"), ("GA — generations:", "200"), ("GA — mutation_rate:", "0.10"), ("PSO — swarm_size:", "30"), ("PSO — inertia:", "0.7"), ("ACO — ant_count:", "20"), ("ACO — evaporation:", "0.5")]:
            self._row(lbl, val)

        # ── 5. Dataset & Paths ────────────────────────────────────────────────
        self._card("5. Dataset & Paths (Đường dẫn & Dữ liệu)")
        for lbl, val in [("Workspace root:", "D:/Khanh/Đồ án chuyên ngành"), ("Thư mục runs/:", "runs/"), ("Thư mục data/:", "data/"), ("Thư mục configs/:", "configs/"), ("Auto-download datasets:", "Bật"), ("Cache parsed graphs:", "Bật")]:
            self._row(lbl, val)

        # ── 6. Output & Reporting ─────────────────────────────────────────────
        self._card("6. Output & Reporting (Xuất báo cáo)")
        for lbl, val in [("Định dạng xuất:", "CSV, Excel, PDF, LaTeX"), ("DPI biểu đồ:", "300"), ("Font biểu đồ:", "Segoe UI"), ("Ngôn ngữ báo cáo:", "Tiếng Việt"), ("Auto-generate report:", "Bật"), ("Thư mục xuất:", "runs/reports/")]:
            self._row(lbl, val)

        # ── 7. Performance & Benchmark ─────────────────────────────────────────
        self._card("7. Performance & Benchmark (Hiệu năng)")
        for lbl, val in [("Chế độ đo thời gian:", "Wall-clock"), ("Warm-up runs:", "1"), ("GC control:", "Bật"), ("Memory profiling:", "Tắt"), ("Parallel jobs:", "Auto (12)")]:
            self._row(lbl, val)

        # ── 8. Notifications ───────────────────────────────────────────────────
        self._card("8. Notifications (Thông báo)")
        for lbl, val in [("Desktop notification:", "Bật"), ("Sound alert:", "Tắt"), ("Email notification:", "Tắt"), ("Log level:", "INFO")]:
            self._row(lbl, val)

        # ── 9. Keyboard Shortcuts ─────────────────────────────────────────────
        self._card("9. Keyboard Shortcuts (Phím tắt)")
        shortcuts = [("Ctrl+S", "Lưu cấu hình"), ("Ctrl+R", "Chạy experiment"), ("Ctrl+E", "Export kết quả"), ("Ctrl+T", "Toggle theme"), ("F5", "Refresh data"), ("Esc", "Hủy experiment")]
        for key, desc in shortcuts:
            r = ctk.CTkFrame(self, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(r, text=key, font=("Consolas", 10, "bold"), width=120, anchor="w", text_color=BLUE).pack(side="left")
            ctk.CTkLabel(r, text=desc, font=FONT_MAIN, anchor="w", text_color=HEADER_FG).pack(side="left")

        # ── 10. Environment Info ──────────────────────────────────────────────
        self._card("10. Environment Info (Thông tin môi trường)")
        for lbl, val in [("Python:", "3.12.3"), ("g++:", "13.3.0"), ("CMake:", "3.28.3"), ("pybind11:", "3.1.0"), ("RAM:", "16 GB"), ("WSL2:", "Ubuntu 24.04"), ("Database:", "data/config.db")]:
            self._row(lbl, val)

        ctk.CTkFrame(self, height=20, fg_color="transparent").pack()

    def _card(self, title: str):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(12, 8))
        self._current_card = card

    def _row(self, lbl: str, val: str):
        r = ctk.CTkFrame(self._current_card, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=3)
        ctk.CTkLabel(r, text=lbl, font=FONT_MAIN, width=260, anchor="w", text_color=SUBTEXT_FG).pack(side="left")
        ctk.CTkLabel(r, text=val, font=("Segoe UI", 11, "bold"), anchor="w", text_color=HEADER_FG).pack(side="left")

    def _on_theme(self, choice: str):
        if "Tối" in choice or "Dark" in choice:
            mode = "dark"
        elif "hệ thống" in choice or "System" in choice:
            mode = "system"
        else:
            mode = "light"
        set_theme(mode)
        ctk.set_appearance_mode(mode)
        top = self.winfo_toplevel()
        if hasattr(top, "on_theme_changed"):
            top.on_theme_changed(mode)

