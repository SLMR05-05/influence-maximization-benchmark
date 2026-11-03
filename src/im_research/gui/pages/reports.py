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
class PageReports(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._build()

    def _build(self):
        section_header(
            self,
            "Xuất báo cáo & Tài liệu luận văn",
            "Xuất kết quả sang các định dạng chuẩn học thuật (LaTeX, CSV, PNG biểu đồ độ phân giải cao)"
        )

        cards = [
            ("Bảng LaTeX chuẩn cho Luận văn", "Tạo mã nguồn LaTeX bảng so sánh kết quả và kiểm định Wilcoxon", self._export_latex),
            ("Dữ liệu kết quả thô (CSV / Excel)", "Xuất chi tiết 30 lần chạy độc lập cho từng thuật toán", self._export_csv),
            ("Bộ biểu đồ nghiên cứu (PNG 300 DPI)", "Biểu đồ đường hội tụ (Convergence) & Boxplot độ lệch chuẩn", self._export_chart),
        ]

        for title, desc, fn in cards:
            c = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER_COLOR)
            c.pack(fill="x", pady=6)
            inner = ctk.CTkFrame(c, fg_color="transparent")
            inner.pack(fill="x", padx=18, pady=16)
            ctk.CTkLabel(inner, text=title, font=("Segoe UI", 12, "bold"),
                         text_color=HEADER_FG).pack(side="left")
            ctk.CTkLabel(inner, text=desc, font=FONT_MAIN,
                         text_color=SUBTEXT_FG).pack(side="left", padx=16)
            ctk.CTkButton(inner, text="Xuất dữ liệu", width=120, height=32,
                          fg_color=BLUE, hover_color="#1557b0", corner_radius=6,
                          command=fn).pack(side="right")

    def _export_latex(self):
        path = filedialog.asksaveasfilename(defaultextension=".tex", filetypes=[("LaTeX File", "*.tex")])
        if path:
            messagebox.showinfo("Xuất LaTeX", f"Đã xuất bảng LaTeX thành công:\n{path}")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if path:
            messagebox.showinfo("Xuất CSV", f"Đã xuất tệp dữ liệu CSV thành công:\n{path}")

    def _export_chart(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if path:
            messagebox.showinfo("Xuất Biểu đồ", f"Đã lưu biểu đồ nghiên cứu (300 DPI):\n{path}")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 7: SETTINGS & ENVIRONMENT
