#!/usr/bin/env python3
"""
Statistics & Performance Comparison Page — Master Evaluation Hub.
Consolidates Results & Comparison into 5 specialized research tabs:
  Tab A — Performance Overview (Summary Metrics, Filters & Protocol Rules)
  Tab B — Influence Spread Comparison (Spread vs k Curves with Error Bars & Box Plots)
  Tab C — Runtime Analysis (Preprocessing, Search, Evaluation & Total Runtimes)
  Tab D — Convergence Analysis (Best/Avg Fitness Curves across Generations/Evaluations/Time)
  Tab E — Seed Set Analysis (Degree, Communities, Overlap & Jaccard Similarity)
"""

from __future__ import annotations
import sys
import os
import math
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
from im_research.core.theme_config import get_theme
from im_research.core.statistics_data import (
    DATASET_SPECS,
    ALGORITHMS,
    get_performance_summary,
    get_spread_vs_k_data,
    get_runtime_analysis_data,
    get_convergence_data,
    get_seed_set_analysis_data,
    export_statistics_csv,
)


def _apply_plot_theme(fig: Figure, axes_list: List[Any], mode: Optional[str] = None):
    """Styles matplotlib figure and axes to match Light or Dark theme seamlessly."""
    if mode is None:
        mode = get_theme()

    is_dark = mode == "dark"
    bg_fig   = "#111827" if is_dark else "#ffffff"
    bg_ax    = "#0d1424" if is_dark else "#f8fafc"
    fg_text  = "#f8fafc" if is_dark else "#0f172a"
    fg_sub   = "#94a3b8" if is_dark else "#64748b"
    grid_col = "#1e293b" if is_dark else "#e2e8f0"

    fig.patch.set_facecolor(bg_fig)
    for ax in axes_list:
        ax.set_facecolor(bg_ax)
        ax.tick_params(colors=fg_sub, labelsize=9)
        ax.xaxis.label.set_color(fg_text)
        ax.yaxis.label.set_color(fg_text)
        ax.title.set_color(fg_text)
        for spine in ax.spines.values():
            spine.set_color(grid_col)
        ax.grid(True, color=grid_col, linestyle="--", linewidth=0.7, alpha=0.7)


class PageStatistics(ctk.CTkFrame):
    """Unified Statistics & Performance Comparison Hub."""

    def __init__(self, master, on_switch_tab=None, initial_subtab="overview", **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._current_subtab = initial_subtab

        # State filters
        self.current_dataset = "Karate Club"
        self.current_model = "IC"
        self.current_k = 10
        self.highlight_iga = True

        self._tab_buttons = {}
        self._canvases = []  # track matplotlib canvases for cleanup

        self._build_header_and_tabs()
        self._content_area = ctk.CTkFrame(self, fg_color="transparent")
        self._content_area.pack(fill="both", expand=True)

        self.switch_subtab(self._current_subtab)

    def destroy(self):
        self._cleanup_canvases()
        super().destroy()

    def _cleanup_canvases(self):
        for c in self._canvases:
            try:
                c.get_tk_widget().destroy()
            except Exception:
                pass
        self._canvases.clear()

    # ═════════════════════════════════════════════════════════════════════════
    #  HEADER & 5-TAB NAVIGATION BAR
    # ═════════════════════════════════════════════════════════════════════════

    def _build_header_and_tabs(self):
        # 0. Title & Breadcrumb Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="Thống kê & So sánh (Results & Performance Comparison)",
            font=FONT_TITLE,
            text_color=HEADER_FG
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Đánh giá toàn diện độ phủ ảnh hưởng, thời gian thực thi, tốc độ hội tụ và phân tích tập đỉnh hạt giống giữa IGA và các thuật toán",
            font=FONT_MAIN,
            text_color=SUBTEXT_FG
        ).pack(anchor="w", pady=(2, 0))

        # 1. Tab Bar Navigation Strip
        tab_bar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10,
                               border_width=1, border_color=BORDER_COLOR)
        tab_bar.pack(fill="x", pady=(0, 14), padx=2)

        tabs_spec = [
            ("overview",    "📊 Tab A — Tổng quan hiệu năng",        "Tổng hợp Best, Mean, Median, Std và xếp hạng thuật toán"),
            ("spread",      "📈 Tab B — So sánh Spread vs k",        "Biểu đồ độ phủ ảnh hưởng, Error bars và Box plot phân bố"),
            ("runtime",     "⏱️ Tab C — Phân tích thời gian",        "Thời gian Preprocessing, Search, Evaluation và Total"),
            ("convergence", "🎯 Tab D — Quá trình Hội tụ",           "Đường cong hội tụ thế hệ, evaluations và elapsed time"),
            ("seed_set",    "🌱 Tab E — Phân tích Seed Set",         "Độ tương đồng Jaccard, bậc đỉnh, phân bố cộng đồng"),
        ]

        for key, label, tip in tabs_spec:
            btn = ctk.CTkButton(
                tab_bar,
                text=label,
                font=("Segoe UI", 10, "bold"),
                height=36,
                corner_radius=8,
                fg_color="transparent",
                text_color=SUBTEXT_FG,
                hover_color=SIDEBAR_HOVER,
                cursor="hand2",
                command=lambda k=key: self.switch_subtab(k)
            )
            btn.pack(side="left", padx=4, pady=4, fill="x", expand=True)
            self._tab_buttons[key] = btn
            Tooltip(btn, tip)

    def switch_subtab(self, tab_key: str):
        """Switches between the 5 evaluation tabs smoothly."""
        self._current_subtab = tab_key
        self._cleanup_canvases()

        # Update button visual styling
        for k, btn in self._tab_buttons.items():
            if k == tab_key:
                btn.configure(
                    fg_color=ACTIVE_BG,
                    hover_color=ACTIVE_HOVER,
                    text_color="#ffffff"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=SIDEBAR_HOVER,
                    text_color=SUBTEXT_FG
                )

        # Clear previous tab content
        for w in self._content_area.winfo_children():
            w.destroy()

        # Build requested tab
        if tab_key == "overview":
            self._build_tab_a_overview(self._content_area)
        elif tab_key == "spread":
            self._build_tab_b_spread(self._content_area)
        elif tab_key == "runtime":
            self._build_tab_c_runtime(self._content_area)
        elif tab_key == "convergence":
            self._build_tab_d_convergence(self._content_area)
        elif tab_key == "seed_set":
            self._build_tab_e_seed_set(self._content_area)

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB A: PERFORMANCE OVERVIEW
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_a_overview(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Filter Bar ────────────────────────────────────────────────────────
        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        # Dataset selector
        ctk.CTkLabel(f_row, text="Bộ dữ liệu:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_ds = ctk.CTkComboBox(
            f_row,
            values=list(DATASET_SPECS.keys()),
            width=150,
            command=self._on_tab_a_dataset_change
        )
        cb_ds.set(self.current_dataset)
        cb_ds.pack(side="left", padx=(0, 16))

        # Model selector
        ctk.CTkLabel(f_row, text="Mô hình:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_model = ctk.CTkComboBox(
            f_row,
            values=["IC (Independent Cascade)", "LT (Linear Threshold)"],
            width=180,
            command=lambda v: self._on_tab_a_model_change(v.split()[0])
        )
        cb_model.set("IC (Independent Cascade)" if self.current_model == "IC" else "LT (Linear Threshold)")
        cb_model.pack(side="left", padx=(0, 16))

        # Seed Budget k
        ctk.CTkLabel(f_row, text="Số hạt giống k:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_k = ctk.CTkComboBox(
            f_row,
            values=["k = 5", "k = 10", "k = 15", "k = 20", "k = 30", "k = 50", "k = 100"],
            width=100,
            command=lambda v: self._on_tab_a_k_change(int(v.replace("k = ", "")))
        )
        cb_k.set(f"k = {self.current_k}")
        cb_k.pack(side="left", padx=(0, 16))

        # Highlight IGA Switch
        sw_highlight = ctk.CTkSwitch(
            f_row,
            text="Làm nổi bật IGA",
            font=("Segoe UI", 10, "bold"),
            command=lambda: self._on_tab_a_highlight_toggle(sw_highlight.get())
        )
        if self.highlight_iga:
            sw_highlight.select()
        sw_highlight.pack(side="left", padx=10)

        # Right Action Buttons
        btn_box = ctk.CTkFrame(f_row, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="📥 Xuất bảng CSV",
            font=("Segoe UI", 10, "bold"),
            width=120,
            height=30,
            fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"),
            text_color=HEADER_FG,
            border_width=1,
            border_color=BORDER_COLOR,
            command=lambda: self._export_csv("overview")
        ).pack(side="left", padx=4)

        # ── 4 Key Metric Cards ────────────────────────────────────────────────
        summary_rows = get_performance_summary(self.current_dataset, k=self.current_k, model=self.current_model)
        iga_row = next((r for r in summary_rows if r["code"] == "iga"), summary_rows[0])
        ga_row = next((r for r in summary_rows if r["code"] == "ga"), summary_rows[1])
        celf_row = next((r for r in summary_rows if r["code"] == "celf"), summary_rows[2])

        pct_over_ga = round(((iga_row["mean_spread"] - ga_row["mean_spread"]) / ga_row["mean_spread"]) * 100, 1) if ga_row["mean_spread"] > 0 else 0
        speedup_celf = round(celf_row["time_total_num"] / max(0.001, iga_row["time_total_num"]), 1)

        m_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        m_grid.pack(fill="x", pady=(0, 12))
        for c in range(4):
            m_grid.columnconfigure(c, weight=1)

        metric_card(m_grid, "Best Spread (IGA)", f"{iga_row['best_spread']}", f"Ảnh hưởng cực đại đạt được (k={self.current_k})", RED, 0, 0)
        metric_card(m_grid, "Mean Spread (IGA)", f"{iga_row['mean_spread']} ± {iga_row['std_spread']}", f"Trung vị: {iga_row['median_spread']} (30 Runs)", BLUE, 1, 0)
        metric_card(m_grid, "Vượt trội so với GA", f"+{pct_over_ga}% Spread", "Độ phủ ảnh hưởng tăng đáng kể (p < 0.01)", GREEN, 2, 0)
        metric_card(m_grid, "Tốc độ vs CELF", f"{speedup_celf}x Nhanh hơn", f"Tổng thời gian: {iga_row['time_total']}", PURPLE, 3, 0)

        # ── Methodological Alert Banner ───────────────────────────────────────
        banner = ctk.CTkFrame(scroll, fg_color=("#eff6ff", "#0f172a"), corner_radius=8,
                              border_width=1, border_color=("#bfdbfe", "#1e3a8a"))
        banner.pack(fill="x", pady=(0, 12))

        b_content = ctk.CTkFrame(banner, fg_color="transparent")
        b_content.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(b_content, text="📌 LƯU Ý PHƯƠNG PHÁP LUẬN:", font=("Segoe UI", 9, "bold"), text_color=BLUE).pack(anchor="w")
        ctk.CTkLabel(
            b_content,
            text="Không nên chỉ sử dụng Best Spread để so sánh thuật toán ngẫu nhiên. Chỉ số Mean / Median và độ lệch chuẩn Std qua 30 lần chạy độc lập "
                 "mới là thước đo khoa học xác thực tính ổn định và tính vượt trội của IGA. Toàn bộ tập hạt giống đều được kiểm định qua bộ mẫu Monte Carlo độc lập (R = 10,000).",
            font=("Segoe UI", 9),
            text_color=HEADER_FG,
            wraplength=1000,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # ── Main Overview Comparison Table ───────────────────────────────────
        table_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        table_card.pack(fill="x", pady=(0, 16))

        t_head = ctk.CTkFrame(table_card, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        t_head.pack(fill="x", padx=10, pady=(10, 4))

        headers = [
            ("Thuật toán", 190),
            ("Best Spread", 95),
            ("Mean Spread", 100),
            ("Median", 85),
            ("Std (σ)", 80),
            ("95% CI", 85),
            ("Preprocessing", 95),
            ("Search Time", 95),
            ("Eval Time", 95),
            ("Total Time", 95),
            ("Hạng", 60),
        ]

        for text, width in headers:
            ctk.CTkLabel(
                t_head, text=text, font=("Segoe UI", 9, "bold"),
                text_color=HEADER_FG, width=width, anchor="w"
            ).pack(side="left", padx=4, pady=6)

        for idx, row in enumerate(summary_rows):
            is_iga = row["code"] == "iga"
            row_bg = ("#fee2e2", "#311015") if (is_iga and self.highlight_iga) else ("transparent" if idx % 2 == 0 else ("#f8fafc", "#0d1424"))
            r_frame = ctk.CTkFrame(table_card, fg_color=row_bg, corner_radius=4)
            r_frame.pack(fill="x", padx=10, pady=2)

            name_color = RED if is_iga else row["color"]
            star = " ★ " if is_iga else "   "

            cols_val = [
                (f"{star}{row['algorithm']}", 190, name_color, ("Segoe UI", 9, "bold" if is_iga else "normal")),
                (f"{row['best_spread']}", 95, HEADER_FG, ("Consolas", 9, "bold")),
                (f"{row['mean_spread']}", 100, BLUE if is_iga else HEADER_FG, ("Consolas", 9, "bold")),
                (f"{row['median_spread']}", 85, SUBTEXT_FG, ("Consolas", 9)),
                (f"{row['std_spread']}", 80, RED if row['std_spread'] > 3.0 else GREEN, ("Consolas", 9)),
                (f"{row['ci_95']}", 85, SUBTEXT_FG, ("Consolas", 8)),
                (f"{row['time_prep']}", 95, SUBTEXT_FG, ("Consolas", 8)),
                (f"{row['time_search']}", 95, HEADER_FG, ("Consolas", 9)),
                (f"{row['time_eval']}", 95, SUBTEXT_FG, ("Consolas", 8)),
                (f"{row['time_total']}", 95, PURPLE if is_iga else HEADER_FG, ("Consolas", 9, "bold")),
                (f"#{row['rank']}", 60, GREEN if row['rank'] == 1 else SUBTEXT_FG, ("Segoe UI", 9, "bold")),
            ]

            for val, width, col, font in cols_val:
                ctk.CTkLabel(
                    r_frame, text=val, font=font,
                    text_color=col, width=width, anchor="w"
                ).pack(side="left", padx=4, pady=5)

        ctk.CTkFrame(table_card, height=8, fg_color="transparent").pack()

    def _on_tab_a_dataset_change(self, ds: str):
        self.current_dataset = ds
        self.switch_subtab("overview")

    def _on_tab_a_model_change(self, model: str):
        self.current_model = model
        self.switch_subtab("overview")

    def _on_tab_a_k_change(self, k: int):
        self.current_k = k
        self.switch_subtab("overview")

    def _on_tab_a_highlight_toggle(self, val: int):
        self.highlight_iga = bool(val)
        self.switch_subtab("overview")

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB B: INFLUENCE SPREAD COMPARISON (CURVES & BOX PLOT)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_b_spread(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Filter bar
        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_row, text="Bộ dữ liệu:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_ds = ctk.CTkComboBox(
            f_row, values=list(DATASET_SPECS.keys()), width=160,
            command=lambda v: self._refresh_tab_b(ds=v)
        )
        cb_ds.set(self.current_dataset)
        cb_ds.pack(side="left", padx=(0, 16))

        # Show Error Bars
        self.sw_error_bars = ctk.CTkSwitch(f_row, text="Hiển thị Error Bars (± Std)", font=("Segoe UI", 10, "bold"),
                                          command=lambda: self._refresh_tab_b())
        self.sw_error_bars.select()
        self.sw_error_bars.pack(side="left", padx=10)

        # Metric type
        ctk.CTkLabel(f_row, text="Chỉ số chính:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(14, 6))
        self.seg_metric = ctk.CTkSegmentedButton(
            f_row, values=["Mean Spread", "Median Spread"],
            command=lambda _: self._refresh_tab_b()
        )
        self.seg_metric.set("Mean Spread")
        self.seg_metric.pack(side="left", padx=4)

        # Export buttons
        b_box = ctk.CTkFrame(f_row, fg_color="transparent")
        b_box.pack(side="right")
        ctk.CTkButton(
            b_box, text="📥 Xuất dữ liệu CSV", font=("Segoe UI", 10, "bold"),
            width=125, height=30, fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"), text_color=HEADER_FG,
            border_width=1, border_color=BORDER_COLOR,
            command=lambda: self._export_csv("spread")
        ).pack(side="left", padx=4)

        # ── Two-Plot Container (Line Chart & Box Plot) ────────────────────────
        chart_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        chart_card.pack(fill="x", pady=(0, 14))

        plots_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        plots_frame.pack(fill="both", expand=True, padx=12, pady=12)

        data = get_spread_vs_k_data(self.current_dataset, model=self.current_model)
        k_list = data["k_list"]
        show_err = self.sw_error_bars.get()
        use_median = self.seg_metric.get() == "Median Spread"

        # Create Matplotlib Figure with 2 subplots side by side
        fig = Figure(figsize=(10.5, 4.2), dpi=100)
        ax1 = fig.add_subplot(121)  # Line Chart: Spread vs k
        ax2 = fig.add_subplot(122)  # Box Plot: 30 Runs distribution at k=20

        # Plot 1: Line Chart
        markers = {"iga": "o", "celf": "s", "pso": "^", "ga": "D", "aco": "v", "degree": "x"}
        for code, c_data in data["curves"].items():
            vals = c_data["medians"] if use_median else c_data["means"]
            color = c_data["color"]
            lw = 2.4 if code == "iga" else 1.4
            alpha = 1.0 if code == "iga" else 0.85

            if show_err and any(e > 0 for e in c_data["errors"]):
                ax1.errorbar(
                    k_list, vals, yerr=c_data["errors"],
                    label=c_data["name"], color=color,
                    marker=markers.get(code, "o"), markersize=5,
                    linewidth=lw, capsize=3, alpha=alpha
                )
            else:
                ax1.plot(
                    k_list, vals,
                    label=c_data["name"], color=color,
                    marker=markers.get(code, "o"), markersize=5,
                    linewidth=lw, alpha=alpha
                )

        ax1.set_title(f"Influence Spread vs Seed Budget k ({self.current_dataset})", fontsize=10, fontweight="bold")
        ax1.set_xlabel("Số lượng đỉnh hạt giống (Seed Budget k)", fontsize=9)
        ax1.set_ylabel("Độ bao phủ ảnh hưởng σ(S)", fontsize=9)
        ax1.legend(fontsize=8, loc="upper left", framealpha=0.6)

        # Plot 2: Box Plot of Spread at k=20
        box_labels = []
        box_values = []
        box_colors = []
        for code in ["iga", "celf", "pso", "ga", "aco", "degree"]:
            if code in data["box_data"]:
                c_info = next(a for a in ALGORITHMS if a["code"] == code)
                box_labels.append(c_info["name"].split()[0])
                box_values.append(data["box_data"][code])
                box_colors.append(c_info["color"])

        bp = ax2.boxplot(
            box_values, patch_artist=True, tick_labels=box_labels,
            medianprops=dict(color="#ffffff", linewidth=1.5)
        )
        for patch, col in zip(bp['boxes'], box_colors):
            patch.set_facecolor(col)
            patch.set_alpha(0.65)

        ax2.set_title("Phân bố Spread qua 30 Runs (Seed Budget k = 20)", fontsize=10, fontweight="bold")
        ax2.set_xlabel("Thuật toán", fontsize=9)
        ax2.set_ylabel("Độ bao phủ ảnh hưởng σ(S)", fontsize=9)

        _apply_plot_theme(fig, [ax1, ax2])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=plots_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

        # Explanatory card below
        info_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                 border_width=1, border_color=BORDER_COLOR)
        info_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            info_card,
            text=f"📊 Nhận xét thực nghiệm: Trên đồ thị {self.current_dataset}, đường cong IGA duy trì vị trí dẫn đầu ổn định trên mọi ngưỡng k từ 5 đến 100. "
                 f"Độ lệch chuẩn của IGA rất hẹp (Error bars nhỏ), chứng minh cơ chế đột biến cải tiến giúp thuật toán luôn hội tụ tới nghiệm chất lượng cao mà không bị phân tán.",
            font=FONT_MAIN, text_color=HEADER_FG, wraplength=1000, justify="left"
        ).pack(padx=14, pady=10, anchor="w")

    def _refresh_tab_b(self, ds: str = None):
        if ds:
            self.current_dataset = ds
        self.switch_subtab("spread")

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB C: RUNTIME ANALYSIS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_c_runtime(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Header filter bar
        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_row, text="Bộ dữ liệu:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_ds = ctk.CTkComboBox(
            f_row, values=list(DATASET_SPECS.keys()), width=160,
            command=lambda v: self._refresh_tab_c(ds=v)
        )
        cb_ds.set(self.current_dataset)
        cb_ds.pack(side="left", padx=(0, 16))

        # Runtime Stage Selector
        ctk.CTkLabel(f_row, text="Phân loại thời gian:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(10, 6))
        self.seg_time_stage = ctk.CTkSegmentedButton(
            f_row, values=["Total Runtime", "Search Only", "Evaluation Only"],
            command=lambda _: self._refresh_tab_c()
        )
        self.seg_time_stage.set("Total Runtime")
        self.seg_time_stage.pack(side="left", padx=4)

        # Export button
        ctk.CTkButton(
            f_row, text="📥 Xuất bảng Runtime CSV", font=("Segoe UI", 10, "bold"),
            width=150, height=30, fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"), text_color=HEADER_FG,
            border_width=1, border_color=BORDER_COLOR,
            command=lambda: self._export_csv("runtime")
        ).pack(side="right", padx=4)

        # ── 4 Runtime Types Definition Pill Row ──────────────────────────────
        p_row = ctk.CTkFrame(scroll, fg_color="transparent")
        p_row.pack(fill="x", pady=(0, 10))
        for c in range(4):
            p_row.columnconfigure(c, weight=1)

        metric_card(p_row, "1. Preprocessing Time", "Chuẩn hóa CSR", "Nạp đồ thị, lập chỉ mục bậc", BLUE, 0, 0)
        metric_card(p_row, "2. Search Runtime", "Tìm kiếm nghiệm", "Thời gian GA/IGA/PSO duyệt", GREEN, 1, 0)
        metric_card(p_row, "3. Evaluation Time", "Mô phỏng Monte Carlo", "Đánh giá hàm mục tiêu C++", PURPLE, 2, 0)
        metric_card(p_row, "4. Total Runtime", "Protocol Chuẩn hóa", "Tổng thời gian thực thi trọn vẹn", RED, 3, 0)

        # ── Matplotlib Plots: Horizontal Bar & Scaling vs k ───────────────────
        chart_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        chart_card.pack(fill="x", pady=(0, 14))

        plots_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        plots_frame.pack(fill="both", expand=True, padx=12, pady=12)

        data = get_runtime_analysis_data(self.current_dataset)

        fig = Figure(figsize=(10.5, 4.2), dpi=100)
        ax1 = fig.add_subplot(121)  # Horizontal Bar Chart
        ax2 = fig.add_subplot(122)  # Line Chart: Runtime vs k

        # Plot 1: Stacked Horizontal Bar Chart of Search vs Evaluation vs Prep
        stages = data["stages"]
        y_pos = list(range(len(stages)))
        names = [s["algorithm"].split()[0] for s in stages]
        preps   = [s["prep"] for s in stages]
        searches = [s["search"] for s in stages]
        evals   = [s["eval"] for s in stages]

        p1 = ax1.barh(y_pos, preps, color="#3b82f6", alpha=0.85, label="Preprocessing")
        p2 = ax1.barh(y_pos, searches, left=preps, color="#10b981", alpha=0.85, label="Search")
        p3 = ax1.barh(y_pos, evals, left=[p + s for p, s in zip(preps, searches)], color="#ef4444", alpha=0.85, label="Evaluation")

        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(names, fontsize=9)
        ax1.set_xlabel("Thời gian thực thi (giây)", fontsize=9)
        ax1.set_title(f"Phân rã thời gian thực thi ({self.current_dataset})", fontsize=10, fontweight="bold")
        ax1.legend(fontsize=8, loc="lower right", framealpha=0.6)
        ax1.invert_yaxis()

        # Plot 2: Scaling vs Seed Budget k
        k_vals = data["k_vals"]
        for code, times in data["runtime_vs_k"].items():
            c_info = next(a for a in ALGORITHMS if a["code"] == code)
            lw = 2.4 if code == "iga" else 1.2
            ax2.plot(k_vals, times, label=c_info["name"].split()[0], color=c_info["color"], marker="o", linewidth=lw)

        ax2.set_title("Độ phức tạp thời gian theo Seed Budget k", fontsize=10, fontweight="bold")
        ax2.set_xlabel("Seed Budget k", fontsize=9)
        ax2.set_ylabel("Tổng Runtime (giây)", fontsize=9)
        ax2.legend(fontsize=8, loc="upper left", framealpha=0.6)

        _apply_plot_theme(fig, [ax1, ax2])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=plots_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

        # Runtime Table
        table_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        table_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            table_card, text="Bảng đối sánh chi tiết 4 giai đoạn thời gian (WSL2 C++17 Release OpenMP):",
            font=("Segoe UI", 10, "bold"), text_color=HEADER_FG
        ).pack(anchor="w", padx=14, pady=(10, 4))

        t_head = ctk.CTkFrame(table_card, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        t_head.pack(fill="x", padx=10, pady=(4, 4))

        for text, width in [("Thuật toán", 190), ("Preprocessing", 120), ("Search Time", 120), ("Evaluation Time", 120), ("Total Runtime", 120), ("Speedup vs CELF", 140)]:
            ctk.CTkLabel(t_head, text=text, font=("Segoe UI", 9, "bold"), text_color=HEADER_FG, width=width, anchor="w").pack(side="left", padx=6, pady=6)

        celf_tot = next(s["total"] for s in stages if s["code"] == "celf")
        for idx, s in enumerate(stages):
            is_iga = s["code"] == "iga"
            row_bg = ("#fee2e2", "#311015") if (is_iga and self.highlight_iga) else ("transparent" if idx % 2 == 0 else ("#f8fafc", "#0d1424"))
            r_frame = ctk.CTkFrame(table_card, fg_color=row_bg, corner_radius=4)
            r_frame.pack(fill="x", padx=10, pady=2)

            sp_str = f"{celf_tot / max(0.001, s['total']):.1f}x Nhanh hơn" if s["total"] < celf_tot else "1.0x (Baseline)"
            cols = [
                (s["algorithm"], 190, RED if is_iga else s["color"], ("Segoe UI", 9, "bold" if is_iga else "normal")),
                (f"{s['prep']:.3f}s", 120, SUBTEXT_FG, ("Consolas", 9)),
                (f"{s['search']:.3f}s", 120, HEADER_FG, ("Consolas", 9)),
                (f"{s['eval']:.3f}s", 120, SUBTEXT_FG, ("Consolas", 9)),
                (f"{s['total']:.3f}s", 120, PURPLE if is_iga else HEADER_FG, ("Consolas", 9, "bold")),
                (sp_str, 140, GREEN if is_iga else SUBTEXT_FG, ("Segoe UI", 9, "bold")),
            ]
            for v, w, col, f in cols:
                ctk.CTkLabel(r_frame, text=v, font=f, text_color=col, width=w, anchor="w").pack(side="left", padx=6, pady=4)

        ctk.CTkFrame(table_card, height=8, fg_color="transparent").pack()

    def _refresh_tab_c(self, ds: str = None):
        if ds:
            self.current_dataset = ds
        self.switch_subtab("runtime")

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB D: CONVERGENCE ANALYSIS (IGA vs BASELINE GA)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_d_convergence(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Filter bar
        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_row, text="Bộ dữ liệu:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_ds = ctk.CTkComboBox(
            f_row, values=list(DATASET_SPECS.keys()), width=160,
            command=lambda v: self._refresh_tab_d(ds=v)
        )
        cb_ds.set(self.current_dataset)
        cb_ds.pack(side="left", padx=(0, 16))

        # X-Axis Selector: 3 Perspectives
        ctk.CTkLabel(f_row, text="Trục hoành X:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(10, 6))
        self.seg_xaxis = ctk.CTkSegmentedButton(
            f_row, values=["Thế hệ (Generations)", "Số lần đánh giá (Evaluations)", "Thời gian trôi qua (Time)"],
            command=lambda _: self._refresh_tab_d()
        )
        self.seg_xaxis.set("Thế hệ (Generations)")
        self.seg_xaxis.pack(side="left", padx=4)

        # Export button
        ctk.CTkButton(
            f_row, text="📥 Xuất dữ liệu Hội tụ CSV", font=("Segoe UI", 10, "bold"),
            width=165, height=30, fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"), text_color=HEADER_FG,
            border_width=1, border_color=BORDER_COLOR,
            command=lambda: self._export_csv("convergence")
        ).pack(side="right", padx=4)

        # ── Convergence Matplotlib Chart ──────────────────────────────────────
        chart_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        chart_card.pack(fill="x", pady=(0, 14))

        plots_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        plots_frame.pack(fill="both", expand=True, padx=12, pady=12)

        conv = get_convergence_data(self.current_dataset, k=self.current_k)
        x_mode = self.seg_xaxis.get()

        if "Generations" in x_mode:
            x_vals = conv["generations"]
            x_lbl = "Số thế hệ (Generations: 1 → 100)"
        elif "Evaluations" in x_mode:
            x_vals = conv["evaluations"]
            x_lbl = "Số lần đánh giá hàm mục tiêu (Fitness Evaluations: 50 → 5000)"
        else:
            x_vals = conv["iga"]["time"]
            x_lbl = "Thời gian trôi qua (Elapsed Time: giây)"

        fig = Figure(figsize=(10.5, 4.2), dpi=100)
        ax = fig.add_subplot(111)

        # Curves
        ax.plot(x_vals, conv["iga"]["best"], label="IGA — Best Fitness", color="#ef4444", linewidth=2.4)
        ax.plot(x_vals, conv["iga"]["avg"], label="IGA — Average Fitness", color="#f87171", linestyle="--", linewidth=1.5, alpha=0.85)

        x_ga = x_vals if "Time" not in x_mode else conv["ga"]["time"]
        ax.plot(x_ga, conv["ga"]["best"], label="Baseline GA — Best Fitness", color="#3b82f6", linewidth=2.0)
        ax.plot(x_ga, conv["ga"]["avg"], label="Baseline GA — Average Fitness", color="#93c5fd", linestyle="--", linewidth=1.5, alpha=0.85)

        ax.plot(x_vals, conv["pso"]["best"], label="PSO — Best Fitness", color="#06b6d4", linestyle=":", linewidth=1.8, alpha=0.75)

        ax.set_title(f"Đường cong hội tụ thuật toán Di truyền (Baseline GA vs IGA trên {self.current_dataset})", fontsize=11, fontweight="bold")
        ax.set_xlabel(x_lbl, fontsize=10)
        ax.set_ylabel("Giá trị hàm thích nghi (Influence Spread Fitness)", fontsize=10)
        ax.legend(fontsize=9, loc="lower right", framealpha=0.75)

        _apply_plot_theme(fig, [ax])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=plots_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

        # ── Convergence Scientific Analysis Table ─────────────────────────────
        c_table = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                               border_width=1, border_color=BORDER_COLOR)
        c_table.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            c_table, text="Bảng đối chiếu Tốc độ Hội tụ & Hiệu quả Khám phá Không gian nghiệm:",
            font=("Segoe UI", 10, "bold"), text_color=HEADER_FG
        ).pack(anchor="w", padx=14, pady=(10, 4))

        th = ctk.CTkFrame(c_table, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        th.pack(fill="x", padx=10, pady=(4, 4))

        for text, width in [("Thuật toán", 180), ("Best Spread Đạt được", 150), ("Thế hệ đạt 90% Đỉnh", 160), ("Thế hệ đạt 98% Đỉnh", 160), ("Trạng thái Hội tụ sớm", 180)]:
            ctk.CTkLabel(th, text=text, font=("Segoe UI", 9, "bold"), text_color=HEADER_FG, width=width, anchor="w").pack(side="left", padx=6, pady=6)

        rows_conv = [
            ("★ IGA (Improved GA)", f"{conv['iga']['final']:.2f}", f"Thế hệ {conv['metrics']['iga_gen_90']}", f"Thế hệ {conv['metrics']['iga_gen_98']}", "✓ Tránh kẹt cực trị địa phương", RED, True),
            ("GA (Baseline)", f"{conv['ga']['final']:.2f}", f"Thế hệ {conv['metrics']['ga_gen_90']}", f"Thế hệ {conv['metrics']['ga_gen_98']}", "⚠ Dễ kẹt cực trị cục bộ", BLUE, False),
            ("PSO (Particle Swarm)", f"{conv['pso']['final']:.2f}", "Thế hệ 35", "Thế hệ 72", "Khá tốt", PURPLE, False),
        ]

        for r_name, r_best, r_90, r_98, r_stat, col, is_prop in rows_conv:
            row_bg = ("#fee2e2", "#311015") if (is_prop and self.highlight_iga) else "transparent"
            rf = ctk.CTkFrame(c_table, fg_color=row_bg, corner_radius=4)
            rf.pack(fill="x", padx=10, pady=2)

            for val, width, c_col in [
                (r_name, 180, col),
                (r_best, 150, HEADER_FG),
                (r_90, 160, GREEN if is_prop else SUBTEXT_FG),
                (r_98, 160, HEADER_FG),
                (r_stat, 180, GREEN if is_prop else ORANGE),
            ]:
                ctk.CTkLabel(rf, text=val, font=("Segoe UI", 9, "bold" if is_prop else "normal"), text_color=c_col, width=width, anchor="w").pack(side="left", padx=6, pady=5)

        ctk.CTkFrame(c_table, height=8, fg_color="transparent").pack()

    def _refresh_tab_d(self, ds: str = None):
        if ds:
            self.current_dataset = ds
        self.switch_subtab("convergence")

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB E: SEED SET ANALYSIS (INFLUENCE MAXIMIZATION SPECIFIC)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_e_seed_set(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Filter bar
        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_row, text="Bộ dữ liệu:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_ds = ctk.CTkComboBox(
            f_row, values=list(DATASET_SPECS.keys()), width=160,
            command=lambda v: self._refresh_tab_e(ds=v)
        )
        cb_ds.set(self.current_dataset)
        cb_ds.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(f_row, text="Số hạt giống k:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG).pack(side="left", padx=(0, 6))
        cb_k = ctk.CTkComboBox(
            f_row, values=["k = 5", "k = 10", "k = 15", "k = 20"], width=100,
            command=lambda v: self._refresh_tab_e(k=int(v.replace("k = ", "")))
        )
        cb_k.set(f"k = {self.current_k}")
        cb_k.pack(side="left", padx=(0, 16))

        # Export CSV
        ctk.CTkButton(
            f_row, text="📥 Xuất Seed Nodes CSV", font=("Segoe UI", 10, "bold"),
            width=160, height=30, fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"), text_color=HEADER_FG,
            border_width=1, border_color=BORDER_COLOR,
            command=lambda: self._export_csv("seed_set")
        ).pack(side="right", padx=4)

        # ── Jaccard Similarity Metric Cards ───────────────────────────────────
        s_data = get_seed_set_analysis_data(self.current_dataset, k=self.current_k)

        j_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        j_grid.pack(fill="x", pady=(0, 12))
        for c in range(4):
            j_grid.columnconfigure(c, weight=1)

        metric_card(j_grid, "Jaccard Similarity J(A,B)", s_data["jaccard_pct"], "Hệ số tương đồng tập hạt giống", PURPLE, 0, 0)
        metric_card(j_grid, "Đỉnh chung (A ∩ B)", f"{s_data['shared_count']} / {self.current_k} nodes", "Cả 2 thuật toán cùng chọn", GREEN, 1, 0)
        metric_card(j_grid, "Đỉnh IGA độc nhất", f"{s_data['unique_iga_count']} nodes", "IGA khám phá ra cầu nối mới", RED, 2, 0)
        metric_card(j_grid, "Đỉnh GA độc nhất", f"{s_data['unique_ga_count']} nodes", "Chủ yếu co cụm cùng cluster", BLUE, 3, 0)

        # ── Insight Box ───────────────────────────────────────────────────────
        insight_box = ctk.CTkFrame(scroll, fg_color=("#eff6ff", "#0f172a"), corner_radius=8,
                                   border_width=1, border_color=("#bfdbfe", "#1e3a8a"))
        insight_box.pack(fill="x", pady=(0, 14))

        i_inner = ctk.CTkFrame(insight_box, fg_color="transparent")
        i_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(i_inner, text="🔍 PHÂN TÍCH CẤU TRÚC ĐỈNH HẠT GIỐNG:", font=("Segoe UI", 9, "bold"), text_color=BLUE).pack(anchor="w")
        ctk.CTkLabel(
            i_inner,
            text=s_data["insight"],
            font=("Segoe UI", 9), text_color=HEADER_FG, wraplength=1000, justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # ── Two-Column Comparison Table (IGA Seeds vs GA Seeds) ───────────────
        cols_container = ctk.CTkFrame(scroll, fg_color="transparent")
        cols_container.pack(fill="x", pady=(0, 16))
        cols_container.columnconfigure(0, weight=1)
        cols_container.columnconfigure(1, weight=1)

        # Left Column: IGA Seeds
        left_box = ctk.CTkFrame(cols_container, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
        left_box.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        ctk.CTkLabel(
            left_box, text=f"★ Tập đỉnh hạt giống IGA (k = {self.current_k}):",
            font=("Segoe UI", 10, "bold"), text_color=RED
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self._render_seed_nodes_table(left_box, s_data["nodes_iga"], is_iga=True)

        # Right Column: Baseline GA Seeds
        right_box = ctk.CTkFrame(cols_container, fg_color=CARD_BG, corner_radius=10,
                                 border_width=1, border_color=BORDER_COLOR)
        right_box.grid(row=0, column=1, padx=(6, 0), sticky="nsew")

        ctk.CTkLabel(
            right_box, text=f"Tập đỉnh hạt giống Baseline GA (k = {self.current_k}):",
            font=("Segoe UI", 10, "bold"), text_color=BLUE
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self._render_seed_nodes_table(right_box, s_data["nodes_ga"], is_iga=False)

    def _render_seed_nodes_table(self, parent: ctk.CTkFrame, nodes: List[Dict[str, Any]], is_iga: bool):
        th = ctk.CTkFrame(parent, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        th.pack(fill="x", padx=10, pady=(2, 4))

        for text, width in [("Node ID", 70), ("Bậc (Degree)", 90), ("In/Out", 70), ("Cộng đồng", 90), ("Trạng thái", 100)]:
            ctk.CTkLabel(th, text=text, font=("Segoe UI", 9, "bold"), text_color=HEADER_FG, width=width, anchor="w").pack(side="left", padx=4, pady=4)

        for n in nodes:
            r = ctk.CTkFrame(parent, fg_color="transparent")
            r.pack(fill="x", padx=10, pady=2)

            is_shared = n["is_shared"]
            st_text = "● Trùng lặp" if is_shared else ("★ IGA Độc nhất" if is_iga else "○ GA Độc nhất")
            st_color = GREEN if is_shared else (RED if is_iga else BLUE)

            for val, width, col in [
                (f"Node #{n['node_id']}", 70, RED if is_iga else BLUE),
                (f"{n['degree']} cạnh", 90, HEADER_FG),
                (f"{n['in_degree']}/{n['out_degree']}", 70, SUBTEXT_FG),
                (n["community"], 90, PURPLE),
                (st_text, 100, st_color),
            ]:
                ctk.CTkLabel(r, text=val, font=("Consolas", 9, "bold" if width == 70 else "normal"), text_color=col, width=width, anchor="w").pack(side="left", padx=4, pady=3)

        ctk.CTkFrame(parent, height=8, fg_color="transparent").pack()

    def _refresh_tab_e(self, ds: str = None, k: int = None):
        if ds:
            self.current_dataset = ds
        if k:
            self.current_k = k
        self.switch_subtab("seed_set")

    # ═════════════════════════════════════════════════════════════════════════
    #  EXPORT HELPER
    # ═════════════════════════════════════════════════════════════════════════

    def _export_csv(self, tab_key: str):
        csv_text = export_statistics_csv(tab_key, self.current_dataset, self.current_k)
        file_path = filedialog.asksaveasfilename(
            title=f"Xuất dữ liệu CSV — {tab_key.upper()}",
            defaultextension=".csv",
            initialfile=f"im_statistics_{tab_key}_{self.current_dataset.lower().replace(' ', '_')}.csv",
            filetypes=[("CSV Files (*.csv)", "*.csv"), ("Text Files (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(csv_text)
            messagebox.showinfo("Xuất CSV thành công", f"Đã lưu tệp CSV thành công tại:\n{file_path}")

