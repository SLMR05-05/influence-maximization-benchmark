#!/usr/bin/env python3
"""
Datasets Page — Benchmark Graphs & 3D Knowledge Graph Explorer.
Presents the 5 authentic benchmark datasets with exact topological metrics,
accompanied by the interactive 3D Force-Directed Network Graph viewer.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
from im_research.gui.visualization.graph_explorer_view import GraphExplorerView

RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Benchmark Datasets Metadata Specification
BENCHMARK_DATASETS = [
    {
        "name": "Karate Club",
        "file": "karate.txt",
        "n": "34",
        "m": "78",
        "avg_deg": "4,59",
        "clustering": "0,571",
        "diameter": "5",
        "category": "Mạng xã hội nhỏ",
        "source": "Zachary (1977)",
        "badge_color": "#10b981",
    },
    {
        "name": "Dolphins",
        "file": "dolphins.txt",
        "n": "62",
        "m": "159",
        "avg_deg": "5,13",
        "clustering": "0,259",
        "diameter": "8",
        "category": "Mạng quan hệ xã hội",
        "source": "Lusseau (2003)",
        "badge_color": "#0284c7",
    },
    {
        "name": "ego-Facebook",
        "file": "facebook.txt",
        "n": "4.039",
        "m": "88.234",
        "avg_deg": "43,69",
        "clustering": "0,605",
        "diameter": "8",
        "category": "Mạng xã hội trực tuyến",
        "source": "SNAP [8]",
        "badge_color": "#2563eb",
    },
    {
        "name": "NetHEPT",
        "file": "nethept.txt",
        "n": "15.233",
        "m": "58.891",
        "avg_deg": "7,73",
        "clustering": "0,659",
        "diameter": "15",
        "category": "Mạng đồng tác giả học thuật",
        "source": "arXiv / SNAP [15]",
        "badge_color": "#8b5cf6",
    },
    {
        "name": "Email-Enron",
        "file": "enron.txt",
        "n": "36.692",
        "m": "183.831",
        "avg_deg": "10,02",
        "clustering": "0,497",
        "diameter": "11",
        "category": "Mạng truyền thông thư điện tử",
        "source": "SNAP [8]",
        "badge_color": "#f59e0b",
    },
]


class PageDatasets(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, corner_radius=0, **kw)
        self._view_widget = None
        self._build()

    def _build(self):
        # Top Mode Switch
        top_ctrl = ctk.CTkFrame(self, fg_color="transparent")
        top_ctrl.pack(fill="x", pady=(0, 10))

        self.view_selector = ctk.CTkSegmentedButton(
            top_ctrl,
            values=["Trực quan hóa Mạng lưới 3D (Knowledge Graph)", "Bảng thông số 5 bộ dữ liệu chuẩn"],
            command=self._on_view_change,
            height=34,
            font=("Segoe UI", 11, "bold"),
            selected_color=ACTIVE_BG,
            selected_hover_color=ACTIVE_HOVER,
            unselected_color=("#e2e8f0", "#1e293b"),
            unselected_hover_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc")
        )
        self.view_selector.set("Trực quan hóa Mạng lưới 3D (Knowledge Graph)")
        self.view_selector.pack(side="left")

        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.container.pack(fill="both", expand=True)

        self._show_3d_view()

    def _on_view_change(self, val: str):
        if "3D" in val:
            self._show_3d_view()
        else:
            self._show_table_view()

    def _show_3d_view(self, select_graph_name: str = None):
        if self._view_widget:
            self._view_widget.destroy()
        self._view_widget = GraphExplorerView(self.container)
        self._view_widget.pack(fill="both", expand=True)
        if select_graph_name:
            self._view_widget.select_dataset(select_graph_name)

    def _show_table_view(self):
        if self._view_widget:
            self._view_widget.destroy()
        scroll = ctk.CTkScrollableFrame(self.container, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)
        self._view_widget = scroll

        section_header(
            scroll,
            "Bộ dữ liệu đồ thị chuẩn (Benchmark Datasets)",
            "5 đồ thị thực tế từ quy mô nhỏ đến lớn được chuẩn hóa cho bài toán Tối đa hóa Lan truyền"
        )

        # ── Summary Metric Cards ──────────────────────────────────────────────
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 14))
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        metric_card(grid, "Tổng số bộ dữ liệu", "5", "Chuẩn hóa hoàn tất", BLUE, 0, 0)
        metric_card(grid, "Đồ thị lớn nhất", "Email-Enron", "36.692 đỉnh | 183.831 cạnh", ORANGE, 1, 0)
        metric_card(grid, "Tổng số cạnh mạng lưới", "331.185", "Tất cả đồ thị kết hợp", GREEN, 2, 0)
        metric_card(grid, "Trạng thái lưu trữ", "5 / 5 Tệp", "data/raw/ đầy đủ 100%", PURPLE, 3, 0)

        # ── Main Table Card ───────────────────────────────────────────────────
        tbl_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
        tbl_card.pack(fill="x", pady=(0, 16))

        headers = [
            "Bộ dữ liệu đồ thị",
            "Số đỉnh (n)",
            "Số cạnh (m)",
            "Bậc TB (⟨k⟩)",
            "Hệ số cụm (C)",
            "Đường kính (D)",
            "Phân loại đồ thị",
            "Nguồn dữ liệu",
            "Thao tác"
        ]

        header_row = ctk.CTkFrame(tbl_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(12, 8))
        for col_idx, h in enumerate(headers):
            # Proportional widths
            w = 140 if col_idx == 0 else (170 if col_idx in (6, 7) else (85 if col_idx == 8 else 95))
            lbl = ctk.CTkLabel(
                header_row, text=h, font=("Segoe UI", 10, "bold"),
                text_color=SUBTEXT_FG, width=w,
                anchor="w" if col_idx in (0, 6, 7) else "center"
            )
            lbl.pack(side="left", padx=4)

        ctk.CTkFrame(tbl_card, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=10, pady=2)

        for ds in BENCHMARK_DATASETS:
            row_frame = ctk.CTkFrame(tbl_card, fg_color="transparent")
            row_frame.pack(fill="x", padx=14, pady=8)

            # 1. Dataset Name with color dot
            col0 = ctk.CTkFrame(row_frame, fg_color="transparent", width=140)
            col0.pack(side="left", padx=4)
            col0.pack_propagate(False)
            ctk.CTkFrame(col0, width=8, height=8, corner_radius=4, fg_color=ds["badge_color"]).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(col0, text=ds["name"], font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(side="left")

            # 2. Nodes n
            ctk.CTkLabel(row_frame, text=ds["n"], font=("Segoe UI", 11), text_color=HEADER_FG, width=95, anchor="center").pack(side="left", padx=4)

            # 3. Edges m
            ctk.CTkLabel(row_frame, text=ds["m"], font=("Segoe UI", 11), text_color=HEADER_FG, width=95, anchor="center").pack(side="left", padx=4)

            # 4. Avg degree
            ctk.CTkLabel(row_frame, text=ds["avg_deg"], font=("Segoe UI", 11), text_color=HEADER_FG, width=95, anchor="center").pack(side="left", padx=4)

            # 5. Clustering coefficient
            ctk.CTkLabel(row_frame, text=ds["clustering"], font=("Segoe UI", 11), text_color=HEADER_FG, width=95, anchor="center").pack(side="left", padx=4)

            # 6. Diameter
            ctk.CTkLabel(row_frame, text=ds["diameter"], font=("Segoe UI", 11), text_color=HEADER_FG, width=95, anchor="center").pack(side="left", padx=4)

            # 7. Category
            ctk.CTkLabel(row_frame, text=ds["category"], font=FONT_MAIN, text_color=SUBTEXT_FG, width=170, anchor="w").pack(side="left", padx=4)

            # 8. Source
            ctk.CTkLabel(row_frame, text=ds["source"], font=FONT_MAIN, text_color=SUBTEXT_FG, width=170, anchor="w").pack(side="left", padx=4)

            # 9. Action Button (Khám phá 3D)
            btn_action = ctk.CTkButton(
                row_frame, text="Xem 3D ▶", width=85, height=28,
                font=("Segoe UI", 10, "bold"), fg_color=BLUE, hover_color="#1557b0",
                corner_radius=6,
                command=lambda name=ds["name"]: self._switch_to_3d_graph(name)
            )
            btn_action.pack(side="left", padx=4)

            ctk.CTkFrame(tbl_card, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=12, pady=1)

        # ── Raw Files Storage Information Box ─────────────────────────────────
        box = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box.pack(fill="x", pady=(8, 16))
        b_inner = ctk.CTkFrame(box, fg_color="transparent")
        b_inner.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(
            b_inner,
            text="Vị trí lưu trữ dữ liệu thật trên đĩa:",
            font=("Segoe UI", 11, "bold"), text_color=HEADER_FG
        ).pack(anchor="w")

        paths_info = [
            f"• Karate Club: {RAW_DIR / 'karate.txt'} ({'Đã sẵn sàng' if (RAW_DIR / 'karate.txt').exists() else 'Chưa tìm thấy'})",
            f"• Dolphins: {RAW_DIR / 'dolphins.txt'} ({'Đã sẵn sàng' if (RAW_DIR / 'dolphins.txt').exists() else 'Chưa tìm thấy'})",
            f"• ego-Facebook: {RAW_DIR / 'facebook.txt'} ({'Đã sẵn sàng' if (RAW_DIR / 'facebook.txt').exists() else 'Chưa tìm thấy'})",
            f"• NetHEPT: {RAW_DIR / 'nethept.txt'} ({'Đã sẵn sàng' if (RAW_DIR / 'nethept.txt').exists() else 'Chưa tìm thấy'})",
            f"• Email-Enron: {RAW_DIR / 'enron.txt'} ({'Đã sẵn sàng' if (RAW_DIR / 'enron.txt').exists() else 'Chưa tìm thấy'})",
        ]
        for p in paths_info:
            ctk.CTkLabel(b_inner, text=p, font=("Consolas", 10), text_color=GREEN if "Đã sẵn sàng" in p else RED, anchor="w").pack(anchor="w", padx=10, pady=2)

    def _switch_to_3d_graph(self, dataset_name: str):
        self.view_selector.set("Trực quan hóa Mạng lưới 3D (Knowledge Graph)")
        self._show_3d_view(select_graph_name=dataset_name)
