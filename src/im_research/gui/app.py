#!/usr/bin/env python3
"""
IM-Benchmark-Lab — Influence Maximization Research Platform
Main Desktop Application using CustomTkinter
Modern sidebar matching laboratory research specification.
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog

# Add project root and src to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from im_research.core.theme_config import get_theme, set_theme
from im_research.gui.icon_factory import IconSet
from im_research.gui.graph_explorer_view import GraphExplorerView

# ── Appearance & Theme ────────────────────────────────────────────────────────
INITIAL_THEME = get_theme()  # "light", "dark", or "system"
ctk.set_appearance_mode(INITIAL_THEME)
ctk.set_default_color_theme("blue")

# ── Color Palette (Adaptive Light & Dark Tuples) ──────────────────────────────
BG_APP         = ("#f8f9fa", "#0b0f19")
SIDEBAR_BG     = ("#ffffff", "#0f172a")
ACTIVE_BG      = "#1a73e8"      # Blue rounded active button
INACTIVE_HOVER = ("#f1f3f4", "#1e293b")
BORDER_COLOR   = ("#e8eaed", "#1e293b")
CARD_BG        = ("#ffffff", "#131c31")
HEADER_FG      = ("#202124", "#f8fafc")
SUBTEXT_FG     = ("#5f6368", "#94a3b8")
STATUS_BG      = ("#e8f0fe", "#0a101d")
STATUS_FG      = ("#174ea6", "#38bdf8")
DIVIDER        = ("#e8eaed", "#1e293b")
BLUE           = "#1a73e8"
GREEN          = "#1e8e3e"
ORANGE         = "#f9ab00"
RED          = "#d93025"
PURPLE       = "#9334e6"
TEAL         = "#007b83"

FONT_MAIN   = ("Segoe UI", 11)
FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_CARD   = ("Segoe UI", 26, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)

# ── Nav items: (key, tooltip_label, icon_name) ────────────────────────────────
NAV_ITEMS = [
    ("dashboard",   "Tổng quan (Dashboard)",           "home"),
    ("results",     "Kết quả lan truyền (Results)",    "line_chart"),
    ("comparison",  "So sánh thuật toán (Comparison)", "bar_chart"),
    ("datasets",    "Bộ dữ liệu (Datasets)",           "network"),
    ("experiments", "Thí nghiệm (Experiments)",       "flask"),
    ("reports",     "Báo cáo & Luận văn (Reports)",    "document"),
    ("settings",    "Cài đặt hệ thống (Settings)",     "settings"),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  TOOLTIP HELPER
# ═══════════════════════════════════════════════════════════════════════════════
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tw:
            return
        x = self.widget.winfo_rootx() + 68
        y = self.widget.winfo_rooty() + 8
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.attributes("-topmost", True)
        frame = tk.Frame(self.tw, bg="#202124", padx=10, pady=5)
        frame.pack()
        lbl = tk.Label(
            frame, text=self.text, bg="#202124", fg="#ffffff",
            font=("Segoe UI", 9, "bold"), relief="flat"
        )
        lbl.pack()

    def hide(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR (Icon-only with Active Blue Pill)
# ═══════════════════════════════════════════════════════════════════════════════
class Sidebar(ctk.CTkFrame):
    def __init__(self, master, icon_set: IconSet, on_navigate, **kw):
        super().__init__(
            master, width=72, corner_radius=0,
            fg_color=SIDEBAR_BG, border_width=1,
            border_color=BORDER_COLOR, **kw
        )
        self.pack_propagate(False)
        self.icon_set = icon_set
        self.on_navigate = on_navigate
        self._buttons: dict[str, tuple[ctk.CTkButton, str]] = {}
        self._active_key = None
        self._build()

    def _build(self):
        # ── Atom Logo (Top) ───────────────────────────────────────────────────
        logo_btn = ctk.CTkButton(
            self, text="", image=self.icon_set.logo,
            width=50, height=50, corner_radius=12,
            fg_color="transparent", hover=False
        )
        logo_btn.pack(pady=(16, 12))
        Tooltip(logo_btn, "IM-Benchmark-Lab (Influence Maximization)")

        # Thin separator below logo
        ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=14, pady=(0, 14))

        # ── Nav Buttons ───────────────────────────────────────────────────────
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

        # ── Bottom Spacer & Quick Theme Toggle ────────────────────────────────
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        curr_mode = get_theme()
        btn_symbol = "◐" if curr_mode == "light" else "◑"
        self.theme_btn = ctk.CTkButton(
            self,
            text=btn_symbol,
            font=("Segoe UI", 16),
            width=46,
            height=46,
            corner_radius=12,
            fg_color="transparent",
            hover_color=INACTIVE_HOVER,
            cursor="hand2",
            command=self._quick_toggle_theme,
        )
        self.theme_btn.pack(side="bottom", pady=(0, 16))
        self.theme_tooltip = Tooltip(self.theme_btn, f"Đổi giao diện: Sáng / Tối (Hiện tại: {curr_mode.capitalize()})")

    def _quick_toggle_theme(self):
        curr = get_theme()
        new_mode = "dark" if curr == "light" else "light"
        set_theme(new_mode)
        ctk.set_appearance_mode(new_mode)
        self.update_theme_icon(new_mode)

        # Notify root window to update status bar
        top = self.winfo_toplevel()
        if hasattr(top, "on_theme_changed"):
            top.on_theme_changed(new_mode)

    def update_theme_icon(self, mode: str):
        symbol = "◐" if mode == "light" else "◑"
        self.theme_btn.configure(text=symbol)
        self.theme_tooltip.text = f"Đổi giao diện: Sáng / Tối (Hiện tại: {mode.capitalize()})"

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
        new_btn, new_icon = self._buttons[key]
        new_btn.configure(
            fg_color=ACTIVE_BG,
            hover_color=ACTIVE_BG,
            image=self.icon_set.get(new_icon, active=True)
        )
        self._active_key = key
        self.on_navigate(key)


# ═══════════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def section_header(parent, title: str, subtitle: str = ""):
    box = ctk.CTkFrame(parent, fg_color="transparent")
    box.pack(fill="x", pady=(0, 14))
    ctk.CTkLabel(box, text=title, font=FONT_TITLE, text_color=HEADER_FG).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(box, text=subtitle, font=FONT_MAIN, text_color=SUBTEXT_FG).pack(anchor="w", pady=(2, 0))


def metric_card(parent, title, value, subtitle="", color=BLUE, col=0, row=0):
    card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                        border_width=1, border_color=BORDER_COLOR)
    card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
    ctk.CTkLabel(card, text=str(value), font=FONT_CARD, text_color=color).pack(padx=16, pady=(14, 0))
    ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(padx=16, pady=(2, 0))
    if subtitle:
        ctk.CTkLabel(card, text=subtitle, font=FONT_SMALL, text_color=SUBTEXT_FG).pack(padx=16, pady=(0, 12))
    return card


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 1: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
class PageDashboard(ctk.CTkScrollableFrame):
    def __init__(self, master, on_switch_tab, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._build()

    def _build(self):
        section_header(
            self,
            "Tổng quan nghiên cứu (Dashboard)",
            "Nền tảng thực nghiệm & đánh giá thuật toán Metaheuristic cho bài toán Tối đa hóa Lan truyền (IM)"
        )

        # ── Stat Cards Grid ───────────────────────────────────────────────────
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 14))
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        metric_card(grid, "Thuật toán so sánh", "—", "Chưa có dữ liệu", SUBTEXT_FG, 0, 0)
        metric_card(grid, "Bộ dữ liệu chuẩn", "—", "Chưa có dữ liệu", SUBTEXT_FG, 1, 0)
        metric_card(grid, "C++ Core Engine", "—", "Chưa có dữ liệu", SUBTEXT_FG, 2, 0)
        metric_card(grid, "Mô hình lan truyền", "—", "Chưa có dữ liệu", SUBTEXT_FG, 3, 0)

        # ── Quick Action Banner ───────────────────────────────────────────────
        banner = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                              border_width=1, border_color=BORDER_COLOR)
        banner.pack(fill="x", pady=(0, 16))
        b_inner = ctk.CTkFrame(banner, fg_color="transparent")
        b_inner.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            b_inner,
            text="Khởi chạy thí nghiệm chuẩn so sánh IGA với các baseline",
            font=("Segoe UI", 13, "bold"), text_color=HEADER_FG
        ).pack(side="left")

        ctk.CTkButton(
            b_inner, text="Đến trang Thí nghiệm ▶",
            font=("Segoe UI", 11, "bold"),
            fg_color=BLUE, hover_color="#1557b0",
            corner_radius=8, width=180, height=36,
            command=lambda: self.on_switch_tab("experiments")
        ).pack(side="right")

        # ── Benchmark Algorithms Overview Table ───────────────────────────────
        section_header(self, "Danh sách thuật toán trong thư viện", "Phân loại theo cơ chế tối ưu hóa")

        tbl = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                           border_width=1, border_color=BORDER_COLOR)
        tbl.pack(fill="x", pady=(0, 16))

        headers = ["Thuật toán", "Nhóm", "Độ phức tạp", "Mô tả cơ chế", "Trạng thái"]
        for c, h in enumerate(headers):
            tbl.columnconfigure(c, weight=1 if c in (0, 3) else 0)
            ctk.CTkLabel(tbl, text=h, font=("Segoe UI", 10, "bold"),
                         text_color=SUBTEXT_FG).grid(row=0, column=c, padx=14, pady=10, sticky="w")

        ctk.CTkFrame(tbl, height=1, fg_color=BORDER_COLOR).grid(
            row=1, column=0, columnspan=len(headers), sticky="ew", padx=8)

        # Empty state — no algorithm data yet
        empty_frame = ctk.CTkFrame(tbl, fg_color="transparent")
        empty_frame.grid(row=2, column=0, columnspan=len(headers), pady=40, sticky="ew")
        ctk.CTkLabel(empty_frame, text="📭", font=("Segoe UI", 48), text_color=SUBTEXT_FG).pack()
        ctk.CTkLabel(empty_frame, text="Chưa có dữ liệu thuật toán", font=("Segoe UI", 14, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
        ctk.CTkLabel(empty_frame, text="Thêm thuật toán vào thư viện để bắt đầu", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 2: RESULTS (Convergence & Spread)
# ═══════════════════════════════════════════════════════════════════════════════
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

        headers = ["Thuật toán", "Dataset", "k", "Spread trung bình (σ)", "Độ lệch chuẩn (std)", "Thời gian (s)", "Rank"]
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
                        row["algorithm"],
                        ds_name,
                        k_val,
                        f"{row['mean_spread']:.2f}",
                        f"± {row['std_spread']:.2f}",
                        f"{row['mean_time']:.3f}s",
                        row["rank"],
                        col
                    ))
            except Exception:
                pass

        # Empty state — no results yet
        empty_frame = ctk.CTkFrame(tbl, fg_color="transparent")
        empty_frame.grid(row=2, column=0, columnspan=len(headers), pady=40, sticky="ew")
        ctk.CTkLabel(empty_frame, text="📭", font=("Segoe UI", 48), text_color=SUBTEXT_FG).pack()
        ctk.CTkLabel(empty_frame, text="Chưa có kết quả thực nghiệm", font=("Segoe UI", 14, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
        ctk.CTkLabel(empty_frame, text="Chạy thí nghiệm để xem kết quả lan truyền", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 3: COMPARISON (Charts & Wilcoxon)
# ═══════════════════════════════════════════════════════════════════════════════
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
        ctk.CTkLabel(bar_card, text="Hiệu quả lan truyền chuẩn hóa (% so với tối ưu)",
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
                    best_spread = max(r["mean_spread"] for r in summary)
                    for r in summary:
                        ratio = r["mean_spread"] / best_spread if best_spread > 0 else 1.0
                        code = r.get("code", "").lower()
                        col = RED if "iga" in code else (BLUE if "celf" in code else (ORANGE if "ga" in code else PURPLE))
                        bars.append((r["algorithm"], ratio, col))
            except Exception:
                pass

        # Empty state — no comparison data yet
        empty_frame = ctk.CTkFrame(bar_card, fg_color="transparent")
        empty_frame.pack(pady=40)
        ctk.CTkLabel(empty_frame, text="📭", font=("Segoe UI", 48), text_color=SUBTEXT_FG).pack()
        ctk.CTkLabel(empty_frame, text="Chưa có dữ liệu so sánh", font=("Segoe UI", 14, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
        ctk.CTkLabel(empty_frame, text="Chạy thí nghiệm để xem biểu đồ so sánh", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()
        ctk.CTkFrame(bar_card, height=12, fg_color="transparent").pack()

        # Wilcoxon Test Summary Table
        w_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER_COLOR)
        w_card.pack(fill="x", pady=(0, 16), padx=2)
        ctk.CTkLabel(w_card, text="Kiểm định cặp Wilcoxon Signed-Rank (IGA vs Baselines, n = 30 runs)",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(12, 10))

        # Empty state — no statistical data yet
        empty_frame = ctk.CTkFrame(w_card, fg_color="transparent")
        empty_frame.pack(pady=40)
        ctk.CTkLabel(empty_frame, text="📭", font=("Segoe UI", 48), text_color=SUBTEXT_FG).pack()
        ctk.CTkLabel(empty_frame, text="Chưa có dữ liệu kiểm định", font=("Segoe UI", 14, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
        ctk.CTkLabel(empty_frame, text="Chạy thí nghiệm và phân tích thống kê để xem kết quả", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()
        ctk.CTkFrame(w_card, height=12, fg_color="transparent").pack()


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 4: DATASETS & 3D KNOWLEDGE GRAPH EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
class PageDatasets(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, corner_radius=0, **kw)
        self._view_widget = None
        self._build()

    def _build(self):
        # Top Mode Switch
        top_ctrl = ctk.CTkFrame(self, fg_color="transparent")
        top_ctrl.pack(fill="x", pady=(0, 8))

        self.view_selector = ctk.CTkSegmentedButton(
            top_ctrl,
            values=["Trực quan hóa Mạng lưới 3D (Knowledge Graph)", "Bảng thông số 5 bộ dữ liệu chuẩn"],
            command=self._on_view_change,
            height=34, font=("Segoe UI", 11, "bold"),
            selected_color=BLUE, selected_hover_color="#1557b0"
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

    def _show_3d_view(self):
        if self._view_widget:
            self._view_widget.destroy()
        self._view_widget = GraphExplorerView(self.container)
        self._view_widget.pack(fill="both", expand=True)

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

        # Empty state — no dataset data yet
        empty_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        empty_frame.pack(pady=40)
        ctk.CTkLabel(empty_frame, text="📭", font=("Segoe UI", 48), text_color=SUBTEXT_FG).pack()
        ctk.CTkLabel(empty_frame, text="Chưa có dữ liệu bộ dữ liệu", font=("Segoe UI", 14, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
        ctk.CTkLabel(empty_frame, text="Tải bộ dữ liệu để xem thống kê", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 5: EXPERIMENTS (Configuration & Runner)
# ═══════════════════════════════════════════════════════════════════════════════
class PageExperiments(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._log_text = None
        self._build()

    def _build(self):
        section_header(
            self,
            "Thiết lập & Khởi chạy thí nghiệm",
            "Cấu hình các tham số môi trường, chọn thuật toán và khởi chạy qua WSL2 C++ Engine"
        )

        form = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        form.pack(fill="x", pady=(0, 14))
        form.columnconfigure(1, weight=1)

        def make_row(lbl, r):
            ctk.CTkLabel(form, text=lbl, font=FONT_MAIN, text_color=SUBTEXT_FG,
                         anchor="w").grid(row=r, column=0, padx=16, pady=8, sticky="w")

        # Dataset Select
        make_row("Bộ dữ liệu (Graph):", 0)
        self.ds_var = ctk.StringVar(value="Karate Club")
        ctk.CTkOptionMenu(
            form, variable=self.ds_var, width=240,
            values=["Karate Club", "Dolphins", "ego-Facebook", "NetHEPT", "Email-Enron"]
        ).grid(row=0, column=1, padx=16, pady=8, sticky="w")

        # Model Select
        make_row("Mô hình lan truyền:", 1)
        self.model_var = ctk.StringVar(value="IC (Independent Cascade, p=0.1)")
        ctk.CTkOptionMenu(
            form, variable=self.model_var, width=240,
            values=["IC (Independent Cascade, p=0.1)", "LT (Linear Threshold)"]
        ).grid(row=1, column=1, padx=16, pady=8, sticky="w")

        # Seed set size k
        make_row("Kích thước tập hạt giống (k):", 2)
        self.k_var = ctk.StringVar(value="10")
        ctk.CTkEntry(form, textvariable=self.k_var, width=120).grid(
            row=2, column=1, padx=16, pady=8, sticky="w")

        # MC repetitions (Search phase)
        make_row("Số lần mô phỏng MC (Search):", 3)
        self.mc_var = ctk.StringVar(value="200")
        ctk.CTkEntry(form, textvariable=self.mc_var, width=120).grid(
            row=3, column=1, padx=16, pady=8, sticky="w")

        # Repetitions / Independent runs
        make_row("Số lần lặp độc lập (Runs):", 4)
        self.runs_var = ctk.StringVar(value="30")
        ctk.CTkEntry(form, textvariable=self.runs_var, width=120).grid(
            row=4, column=1, padx=16, pady=8, sticky="w")

        # Algorithm selection checklist
        make_row("Thuật toán thực thi:", 5)
        algo_box = ctk.CTkFrame(form, fg_color="transparent")
        algo_box.grid(row=5, column=1, padx=16, pady=8, sticky="w")

        self.algo_checks = {}
        algos = [
            ("iga", "IGA (Proposed)", True),
            ("celf", "CELF (Greedy)", True),
            ("ga", "Baseline GA", True),
            ("degree_discount", "Degree Discount", True),
            ("pagerank", "PageRank", True),
            ("degree", "Degree Centrality", True),
        ]
        for idx, (code, name, def_val) in enumerate(algos):
            var = ctk.BooleanVar(value=def_val)
            self.algo_checks[code] = var
            ctk.CTkCheckBox(algo_box, text=name, variable=var, font=FONT_MAIN,
                            text_color=HEADER_FG, checkmark_color=BLUE).grid(
                                row=idx // 3, column=idx % 3, padx=8, pady=4, sticky="w")

        # Run Button
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 12))

        ctk.CTkButton(
            btn_row, text="▶  Khởi chạy thí nghiệm (Execute in WSL2)",
            font=("Segoe UI", 12, "bold"),
            fg_color=GREEN, hover_color="#137333",
            height=40, corner_radius=8,
            command=self._execute_experiment
        ).pack(side="left")

        # Execution Log Box
        section_header(self, "Nhật ký thực thi (Execution Log)", "Theo dõi tiến trình trực tiếp từ C++ OpenMP Batch Evaluator")
        self._log_text = ctk.CTkTextbox(
            self, height=220, font=FONT_MONO,
            fg_color="#1e1e24", text_color="#a6e3a1",
            border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self._log_text.pack(fill="x", pady=(0, 16))
        self._log("Hệ thống đã sẵn sàng. Chọn tham số và nhấn Khởi chạy thí nghiệm.")

    def _log(self, text: str):
        def _do():
            if self._log_text:
                ts = datetime.now().strftime("%H:%M:%S")
                self._log_text.configure(state="normal")
                self._log_text.insert("end", f"[{ts}] {text}\n")
                self._log_text.see("end")
                self._log_text.configure(state="disabled")
        self.after(0, _do)

    def _execute_experiment(self):
        import shutil
        wsl_bin = (
            shutil.which("wsl")
            or shutil.which("wsl.exe")
            or r"C:\Windows\System32\wsl.exe"
            or r"C:\Users\LENOVO\AppData\Local\Microsoft\WindowsApps\wsl.exe"
        )
        if not os.path.exists(wsl_bin) and not shutil.which("wsl"):
            self._log(f"❌ Không tìm thấy trình thực thi WSL tại: {wsl_bin}")
            return

        ds = self.ds_var.get()
        model_str = self.model_var.get()
        model_code = "IC" if "IC" in model_str else "LT"
        k = self.k_var.get().strip() or "10"
        mc = self.mc_var.get().strip() or "200"
        runs = self.runs_var.get().strip() or "1"
        selected = [k_algo for k_algo, v in self.algo_checks.items() if v.get()]

        clean_ds = ds.split()[0]
        self._log(f"Bắt đầu thí nghiệm: Dataset={ds}, Model={model_code}, k={k}, MC={mc}, Runs={runs}")
        self._log(f"Thuật toán tham gia: {', '.join(selected)}")
        self._log("Đang kích hoạt môi trường WSL2 & C++ OpenMP Batch Evaluator...")

        # Run in thread so GUI doesn't freeze
        import threading
        def worker():
            algo_args = " ".join(f"--algo {a}" for a in selected)
            bash_script = (
                "cd '/mnt/d/Khanh/Đồ án chuyên ngành' && "
                "source .venv/bin/activate && "
                f"python -m im_research.experiments.runner --dataset '{clean_ds}' --model {model_code} --k {k} --mc {mc} --runs {runs} {algo_args}"
            )
            cmd = [wsl_bin, "-d", "Ubuntu", "--", "bash", "-c", bash_script]
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, encoding="utf-8", errors="replace"
                )
                for line in proc.stdout:
                    text_line = line.strip()
                    if text_line:
                        self._log(text_line)
                proc.wait()
                if proc.returncode == 0:
                    self._log("✓ Thí nghiệm hoàn tất thành công! Đã lưu kết quả vào thư mục runs/")
                else:
                    self._log(f"⚠ Quá trình kết thúc với mã thoát: {proc.returncode}")
            except Exception as e:
                self._log(f"❌ Lỗi khi khởi chạy: {e}")

        threading.Thread(target=worker, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 6: REPORTS & EXPORT
# ═══════════════════════════════════════════════════════════════════════════════
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
# ═══════════════════════════════════════════════════════════════════════════════
class PageSettings(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._build()

    def _build(self):
        section_header(
            self,
            "Cài đặt hệ thống & Môi trường tính toán",
            "Tùy chỉnh giao diện Sáng / Tối, xem phần cứng và cấu hình siêu tham số thuật toán IGA"
        )

        # ── 1. Appearance & Theme Settings Card ───────────────────────────────
        theme_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                  border_width=1, border_color=BORDER_COLOR)
        theme_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(theme_card, text="Chủ đề & Giao diện (Theme & Appearance)",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(theme_card, text="Tùy chọn chế độ Sáng (Light) / Tối (Dark) — Tự động lưu cấu hình vĩnh viễn vào dự án",
                     font=FONT_SMALL, text_color=SUBTEXT_FG).pack(anchor="w", padx=16, pady=(0, 12))

        theme_row = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(theme_row, text="Chế độ giao diện (Appearance Mode):", font=FONT_MAIN, width=260, anchor="w",
                     text_color=SUBTEXT_FG).pack(side="left")

        curr_mode = get_theme()
        curr_label = "Tối (Dark)" if curr_mode == "dark" else ("Theo hệ thống (System)" if curr_mode == "system" else "Sáng (Light)")

        self.theme_menu = ctk.CTkOptionMenu(
            theme_row, width=220, height=32,
            values=["Sáng (Light)", "Tối (Dark)", "Theo hệ thống (System)"],
            command=self._on_theme_changed
        )
        self.theme_menu.set(curr_label)
        self.theme_menu.pack(side="left")

        # Hardware & Platform Information
        info_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                 border_width=1, border_color=BORDER_COLOR)
        info_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(info_card, text="Cấu hình Môi trường Nghiên cứu",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(14, 8))

        # Empty state — no system info configured yet
        empty_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        empty_frame.pack(pady=20)
        ctk.CTkLabel(empty_frame, text="📭", font=("Segoe UI", 48), text_color=SUBTEXT_FG).pack()
        ctk.CTkLabel(empty_frame, text="Chưa có thông tin hệ thống", font=("Segoe UI", 14, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
        ctk.CTkLabel(empty_frame, text="Cấu hình môi trường để hiển thị thông số", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()

        # IGA Default Hyperparameters
        param_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                  border_width=1, border_color=BORDER_COLOR)
        param_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(param_card, text="Siêu tham số mặc định cho IGA (Proposed Algorithm)",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(14, 8))

        # Empty state — no IGA params configured yet
        empty_frame = ctk.CTkFrame(param_card, fg_color="transparent")
        empty_frame.pack(pady=20)
        ctk.CTkLabel(empty_frame, text="📭", font=("Segoe UI", 48), text_color=SUBTEXT_FG).pack()
        ctk.CTkLabel(empty_frame, text="Chưa có tham số IGA", font=("Segoe UI", 14, "bold"), text_color=SUBTEXT_FG).pack(pady=(8, 2))
        ctk.CTkLabel(empty_frame, text="Cấu hình siêu tham số để bắt đầu", font=FONT_MAIN, text_color=SUBTEXT_FG).pack()

    def _on_theme_changed(self, choice: str):
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


# ═══════════════════════════════════════════════════════════════════════════════
#  STATUS BAR
# ═══════════════════════════════════════════════════════════════════════════════
class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, height=28, corner_radius=0,
                         fg_color=STATUS_BG, border_width=1,
                         border_color=BORDER_COLOR, **kw)
        self.pack_propagate(False)

        curr = get_theme()
        self._info_lbl = ctk.CTkLabel(
            self,
            text=f"● WSL2 Ubuntu 24.04  │  C++ Core OpenMP Ready  │  pybind11 Active  │  Theme: {curr.capitalize()}",
            font=FONT_SMALL, text_color=STATUS_FG, anchor="w"
        )
        self._info_lbl.pack(side="left", padx=14)

        self._clock = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=STATUS_FG, anchor="e")
        self._clock.pack(side="right", padx=14)
        self._tick()

    def update_theme_display(self, mode: str):
        self._info_lbl.configure(
            text=f"● WSL2 Ubuntu 24.04  │  C++ Core OpenMP Ready  │  pybind11 Active  │  Theme: {mode.capitalize()}"
        )

    def _tick(self):
        self._clock.configure(text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        self.after(1000, self._tick)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class IMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IM-Benchmark-Lab — Influence Maximization Research Platform")
        self.geometry("1360x860")
        self.minsize(980, 680)

        # Initialize procedurally generated icon set
        self.icon_set = IconSet(target_size=24)

        # Page registry
        self.pages = {
            "dashboard":   lambda m: PageDashboard(m, on_switch_tab=self.navigate),
            "results":     PageResults,
            "comparison":  PageComparison,
            "datasets":    PageDatasets,
            "experiments": PageExperiments,
            "reports":     PageReports,
            "settings":    PageSettings,
        }

        self._current_page_key = None
        self._page_widget = None

        self._build_layout()

    def on_theme_changed(self, mode: str):
        """Called when user flips theme anywhere in the application."""
        if hasattr(self, "status_bar"):
            self.status_bar.update_theme_display(mode)
        if hasattr(self, "sidebar"):
            self.sidebar.update_theme_icon(mode)

    def _build_layout(self):
        # ── Sidebar (Left, 72px) ──────────────────────────────────────────────
        self.sidebar = Sidebar(self, icon_set=self.icon_set, on_navigate=self.navigate)
        self.sidebar.pack(side="left", fill="y")

        # ── Main Content Area (Right) ─────────────────────────────────────────
        right_panel = ctk.CTkFrame(self, fg_color=BG_APP, corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)

        # Content container
        self.content_container = ctk.CTkFrame(right_panel, fg_color=BG_APP, corner_radius=0)
        self.content_container.pack(side="top", fill="both", expand=True, padx=24, pady=18)

        # Status Bar (Bottom)
        self.status_bar = StatusBar(right_panel)
        self.status_bar.pack(side="bottom", fill="x")

        # Open Dashboard by default
        self.sidebar.activate("dashboard")

    def navigate(self, key: str):
        if key not in self.pages:
            return

        if self._page_widget:
            self._page_widget.destroy()

        # Build requested page
        factory = self.pages[key]
        self._page_widget = factory(self.content_container)
        self._page_widget.pack(fill="both", expand=True)
        self._current_page_key = key


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = IMApp()
    app.mainloop()
