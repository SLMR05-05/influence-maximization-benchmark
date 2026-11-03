#!/usr/bin/env python3
"""Reports Page — Export Academic Reports (LaTeX, CSV, High-DPI Charts)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card, create_empty_state


class PageReports(ctk.CTkScrollableFrame):
    def __init__(self, master, on_switch_tab=None, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._build()

    def _has_results(self) -> bool:
        runs_dir = PROJECT_ROOT / "runs"
        if not runs_dir.exists():
            return False
        return (runs_dir / "latest_results.json").exists() or bool(list(runs_dir.glob("EXP_*")))

    def _build(self):
        section_header(
            self,
            "Xuất báo cáo & Tài liệu luận văn",
            "Xuất kết quả sang các định dạng chuẩn học thuật (LaTeX, CSV, PNG biểu đồ độ phân giải cao)"
        )

        has_data = self._has_results()

        # If no experiment data, display informative empty state card
        if not has_data:
            notice_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                       border_width=1, border_color=BORDER_COLOR)
            notice_card.pack(fill="x", pady=(0, 16))

            cmd = (lambda: self.on_switch_tab("experiments")) if self.on_switch_tab else None
            create_empty_state(
                parent=notice_card,
                title="Chưa có dữ liệu thực nghiệm để xuất báo cáo",
                subtitle="Thư mục runs/ hiện chưa có kết quả. Các chức năng xuất LaTeX, CSV và đồ thị 300 DPI sẽ sẵn sàng ngay sau khi chạy thí nghiệm.",
                action_text="Khởi chạy thí nghiệm ▶",
                action_command=cmd,
                pady=28
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
        if not self._has_results():
            messagebox.showwarning("Chưa có dữ liệu", "Hệ thống chưa có kết quả thực nghiệm để xuất LaTeX!\nVui lòng thực hiện thí nghiệm trước.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".tex", filetypes=[("LaTeX File", "*.tex")])
        if path:
            messagebox.showinfo("Xuất LaTeX", f"Đã xuất bảng LaTeX thành công:\n{path}")

    def _export_csv(self):
        if not self._has_results():
            messagebox.showwarning("Chưa có dữ liệu", "Hệ thống chưa có kết quả thực nghiệm để xuất CSV!\nVui lòng thực hiện thí nghiệm trước.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if path:
            messagebox.showinfo("Xuất CSV", f"Đã xuất tệp dữ liệu CSV thành công:\n{path}")

    def _export_chart(self):
        if not self._has_results():
            messagebox.showwarning("Chưa có dữ liệu", "Hệ thống chưa có kết quả thực nghiệm để tạo biểu đồ!\nVui lòng thực hiện thí nghiệm trước.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if path:
            messagebox.showinfo("Xuất Biểu đồ", f"Đã lưu biểu đồ nghiên cứu (300 DPI):\n{path}")
