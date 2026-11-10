#!/usr/bin/env python3
"""Settings Page — Configuration, Hyperparameters & Environment Info."""
import sys
import platform
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
from im_research.core.diffusion_config import get_ic_config


class PageSettings(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._build()

    def _build(self):
        ic_config = get_ic_config()
        section_header(
            self,
            "Cài đặt hệ thống & Môi trường tính toán",
            "Tùy chỉnh giao diện, Lõi tính toán C++, Siêu tham số thuật toán, Đường dẫn và Thông tin môi trường"
        )

        # ── 1. Appearance & Theme ─────────────────────────────────────────────
        self._card("1. Giao diện & Chủ đề (Appearance & Theme)")
        theme_row = ctk.CTkFrame(self, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(theme_row, text="Chế độ:", font=FONT_MAIN, width=200, anchor="w", text_color=SUBTEXT_FG).pack(side="left")
        curr = get_theme()
        self.theme_menu = ctk.CTkOptionMenu(
            theme_row, width=220,
            values=["Sáng (Light)", "Tối (Dark)", "Theo hệ thống (System)"],
            command=self._on_theme
        )
        self.theme_menu.set("Tối (Dark)" if curr == "dark" else ("Sáng (Light)" if curr == "light" else "Theo hệ thống (System)"))
        self.theme_menu.pack(side="left")

        # ── 2. C++ Engine ─────────────────────────────────────────────────────
        self._card("2. C++ Engine (Lõi tính toán song song)")
        for lbl, val in [
            ("Lõi tính toán:", "C++17 OpenMP CSR Fast Evaluator"),
            ("Chế độ biên dịch:", "Release (-O3 -march=native -fopenmp)"),
            ("Số luồng OpenMP:", f"Auto ({os.cpu_count() or 8} threads)"),
            ("R_search (MC Search):", f"{ic_config['mc_search']:,}"),
            ("R_val (MC Validation):", f"{ic_config['mc_validation']:,}"),
            ("Môi trường thực thi:", "WSL2 Ubuntu 24.04 LTS"),
        ]:
            self._row(lbl, val)

        # ── 3. Experiment Defaults ────────────────────────────────────────────
        self._card("3. Experiment Defaults (Mặc định thí nghiệm)")
        for lbl, val in [
            ("Dataset mặc định:", "Karate Club"),
            ("Mô hình lan truyền:", f"IC (Independent Cascade, p={ic_config['edge_probability']:g})"),
            ("Giá trị k khảo sát:", "5, 10, 15, 20, 25, 30, 40, 50"),
            ("Số lần lặp độc lập (Runs):", "30"),
            ("Ngân sách đánh giá (Max evals):", "10,000"),
            ("Tự động lưu điểm kiểm tra:", "Bật"),
        ]:
            self._row(lbl, val)

        # ── 4. Algorithm Hyperparameters ───────────────────────────────────────
        self._card("4. Algorithm Hyperparameters (Siêu tham số thuật toán)")
        for lbl, val in [
            ("IGA — Kích thước quần thể (pop_size):", "50"),
            ("IGA — Số thế hệ tối đa (max_gen):", "200"),
            ("IGA — Tỷ lệ lai ghép thích nghi (crossover_rate):", "0.85"),
            ("IGA — Xác suất đột biến cơ sở (pm_base):", "0.10"),
            ("IGA — Ngưỡng phân hóa đa dạng (threshold_div):", "0.30"),
            ("IGA — Số cá thể ưu tú bảo tồn (elite_count):", "2"),
            ("GA Baseline — Kích thước quần thể:", "50"),
            ("GA Baseline — Số thế hệ tối đa:", "200"),
            ("GA Baseline — Xác suất đột biến ngẫu nhiên:", "0.10"),
            ("PageRank — Hệ số cản ngẫu nhiên (damping):", "0.85"),
            ("Degree Discount — Xác suất truyền p:", "0.10"),
        ]:
            self._row(lbl, val)

        # ── 5. Dataset & Paths ────────────────────────────────────────────────
        self._card("5. Dataset & Paths (Cấu trúc thư mục & Đường dẫn hệ thống)")
        for lbl, val in [
            ("Thư mục gốc dự án (Workspace Root):", "./ (Thư mục làm việc hiện tại)"),
            ("Thư mục dữ liệu chuẩn (Benchmark Datasets):", "data/raw/"),
            ("Thư mục kết quả thực nghiệm:", "runs/"),
            ("Cơ sở dữ liệu cấu hình & tham số SQLite:", "data/config.db"),
            ("Thư mục kịch bản & siêu tham số:", "configs/"),
            ("Thư mục mã nguồn C++ Core (OpenMP):", "cpp_core/"),
            ("Thư mục xuất báo cáo & luận văn:", "runs/reports/"),
            ("Trạng thái 5 bộ dữ liệu benchmark chuẩn:", "100% Sẵn sàng (Karate, Dolphins, Facebook, NetHEPT, Enron)"),
        ]:
            self._row(lbl, val)

        # ── 6. Environment Info ──────────────────────────────────────────────
        self._card("6. Environment Info (Thông tin môi trường)")
        for lbl, val in [
            ("Python GUI runtime:", f"{platform.python_version()} ({platform.architecture()[0]})"),
            ("Hệ điều hành:", f"{platform.system()} {platform.release()}"),
            ("Bộ vi xử lý:", platform.processor() or "x86_64"),
            ("Số lõi CPU logic:", str(os.cpu_count() or "N/A")),
            ("Giao diện đồ họa:", "CustomTkinter 5.2+ (Adaptive Multi-Theme)"),
            ("Lõi đồ họa mạng lưới 3D:", "Tkinter Canvas 3D Perspective + Three.js WebGL"),
        ]:
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
        ctk.CTkLabel(r, text=lbl, font=FONT_MAIN, width=320, anchor="w", text_color=SUBTEXT_FG).pack(side="left")
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
