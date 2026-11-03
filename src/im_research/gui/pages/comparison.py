#!/usr/bin/env python3
"""Comparison Page — Relative Performance & Statistical Validation."""
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


class PageComparison(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._build()

    def _build(self):
        section_header(
            self,
            "So sánh thuật toán & Kiểm định thống kê",
            "Đo lường hiệu quả tương đối và kiểm định Wilcoxon Signed-Rank Test (mức ý nghĩa α = 0.05)"
        )

        # Relative Performance Bar Chart
        bar_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
        bar_card.pack(fill="x", pady=(0, 16), padx=2)
        ctk.CTkLabel(bar_card, text="Hiệu quả lan truyền chuẩn hóa (% so với thuật toán tốt nhất)",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(12, 10))

        results_file = PROJECT_ROOT / "runs" / "latest_results.json"
        bars = []
        if results_file.exists():
            try:
                import json
                with open(results_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                summary = data.get("summary", [])
                if summary:
                    best_spread = max(r.get("mean_spread", 1.0) for r in summary)
                    for r in summary:
                        ratio = r.get("mean_spread", 0.0) / best_spread if best_spread > 0 else 1.0
                        code = r.get("code", "").lower()
                        col = RED if "iga" in code else (BLUE if "celf" in code else (ORANGE if "ga" in code else PURPLE))
                        bars.append((r.get("algorithm", r.get("name", "N/A")), ratio, col))
            except Exception:
                pass

        if bars:
            chart_container = ctk.CTkFrame(bar_card, fg_color="transparent")
            chart_container.pack(fill="x", padx=16, pady=8)
            for algo, ratio, col in bars:
                row = ctk.CTkFrame(chart_container, fg_color="transparent")
                row.pack(fill="x", pady=4)
                ctk.CTkLabel(row, text=algo, width=160, font=("Segoe UI", 11, "bold"), text_color=col, anchor="w").pack(side="left")
                p_bar = ctk.CTkProgressBar(row, width=420, height=14, progress_color=col)
                p_bar.set(ratio)
                p_bar.pack(side="left", padx=8)
                ctk.CTkLabel(row, text=f"{ratio * 100:.1f}%", font=("Segoe UI", 11), text_color=HEADER_FG).pack(side="left")
        else:
            empty_frame = ctk.CTkFrame(bar_card, fg_color="transparent")
            empty_frame.pack(pady=30)
            ctk.CTkLabel(empty_frame, text="Chưa có dữ liệu so sánh mới nhất", font=("Segoe UI", 13, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
            ctk.CTkLabel(empty_frame, text="Chạy thí nghiệm tại trang 'Thí nghiệm' để tạo dữ liệu đối sánh tự động.", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()
        
        ctk.CTkFrame(bar_card, height=12, fg_color="transparent").pack()

        # Wilcoxon Test Summary Table
        w_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER_COLOR)
        w_card.pack(fill="x", pady=(0, 16), padx=2)
        ctk.CTkLabel(w_card, text="Kiểm định cặp Wilcoxon Signed-Rank (IGA vs Baselines, n = 30 runs)",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(12, 10))

        # Check if statistical report exists
        stat_file = PROJECT_ROOT / "runs" / "statistical_analysis.json"
        if stat_file.exists():
            pass
        else:
            empty_frame = ctk.CTkFrame(w_card, fg_color="transparent")
            empty_frame.pack(pady=30)
            ctk.CTkLabel(empty_frame, text="Chưa có dữ liệu kiểm định Wilcoxon", font=("Segoe UI", 13, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
            ctk.CTkLabel(empty_frame, text="Chạy thí nghiệm với số lần lặp Runs >= 30 để tự động tính toán p-value.", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()
        
        ctk.CTkFrame(w_card, height=12, fg_color="transparent").pack()
