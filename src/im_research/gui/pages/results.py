#!/usr/bin/env python3
"""Results Page — Influence Spread & Execution Times."""
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


class PageResults(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._build()

    def _build(self):
        section_header(
            self,
            "Kết quả lan truyền (Influence Spread Results)",
            "Đánh giá độ bao phủ trung bình qua Monte Carlo Simulation độc lập (R = 10,000)"
        )

        tbl = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                           border_width=1, border_color=BORDER_COLOR)
        tbl.pack(fill="x", pady=(0, 16))

        headers = ["Thuật toán", "Dataset", "k", "Spread trung bình (σ)", "Độ lệch chuẩn (std)", "Thời gian (s)", "Hạng"]
        for c, h in enumerate(headers):
            tbl.columnconfigure(c, weight=1 if c in (0, 3) else 0)
            ctk.CTkLabel(tbl, text=h, font=("Segoe UI", 10, "bold"),
                         text_color=SUBTEXT_FG).grid(row=0, column=c, padx=12, pady=10, sticky="w")

        ctk.CTkFrame(tbl, height=1, fg_color=BORDER_COLOR).grid(
            row=1, column=0, columnspan=len(headers), sticky="ew", padx=8)

        # Try loading latest real experiment results from runs/latest_results.json
        results_file = PROJECT_ROOT / "runs" / "latest_results.json"
        display_rows = []
        if results_file.exists():
            try:
                import json
                with open(results_file, "r", encoding="utf-8") as f:
                    res_data = json.load(f)
                ds_name = res_data.get("dataset", "Karate Club")
                k_val = str(res_data.get("k", "10"))
                for row in res_data.get("summary", []):
                    code = row.get("code", "").lower()
                    col = RED if "iga" in code else (BLUE if "celf" in code else GREEN)
                    display_rows.append((
                        row.get("algorithm", row.get("name", "N/A")),
                        ds_name,
                        k_val,
                        f"{row.get('mean_spread', 0.0):.2f}",
                        f"± {row.get('std_spread', 0.0):.2f}",
                        f"{row.get('mean_time', 0.0):.3f}s",
                        str(row.get("rank", "-")),
                        col
                    ))
            except Exception:
                pass

        if display_rows:
            for r_idx, (algo, ds, k, sp, std, tm, rk, col) in enumerate(display_rows, start=2):
                ctk.CTkLabel(tbl, text=algo, font=("Segoe UI", 11, "bold"), text_color=col).grid(row=r_idx, column=0, padx=12, pady=8, sticky="w")
                ctk.CTkLabel(tbl, text=ds, font=FONT_MAIN, text_color=HEADER_FG).grid(row=r_idx, column=1, padx=12, pady=8, sticky="w")
                ctk.CTkLabel(tbl, text=k, font=FONT_MAIN, text_color=HEADER_FG).grid(row=r_idx, column=2, padx=12, pady=8, sticky="w")
                ctk.CTkLabel(tbl, text=sp, font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).grid(row=r_idx, column=3, padx=12, pady=8, sticky="w")
                ctk.CTkLabel(tbl, text=std, font=FONT_MAIN, text_color=SUBTEXT_FG).grid(row=r_idx, column=4, padx=12, pady=8, sticky="w")
                ctk.CTkLabel(tbl, text=tm, font=FONT_MAIN, text_color=HEADER_FG).grid(row=r_idx, column=5, padx=12, pady=8, sticky="w")
                ctk.CTkLabel(tbl, text=rk, font=("Segoe UI", 11, "bold"), text_color=BLUE).grid(row=r_idx, column=6, padx=12, pady=8, sticky="w")
        else:
            empty_frame = ctk.CTkFrame(tbl, fg_color="transparent")
            empty_frame.grid(row=2, column=0, columnspan=len(headers), pady=40, sticky="ew")
            ctk.CTkLabel(empty_frame, text="Chưa có kết quả thực nghiệm mới nhất", font=("Segoe UI", 13, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
            ctk.CTkLabel(empty_frame, text="Chuyển sang trang 'Thí nghiệm' để thiết lập tham số và khởi chạy.", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()
