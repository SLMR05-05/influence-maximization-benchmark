#!/usr/bin/env python3
"""
Statistics & Performance Comparison Page — Master Evaluation Hub.

Every number rendered by this page comes from real experiment outputs in
``runs/``. Tabs render an empty state when the required measurements were not
recorded by the experiment runner.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from tkinter import messagebox, filedialog

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import metric_card, create_empty_state
from im_research.core.theme_config import is_dark_mode
from im_research.core.statistics_data import (
    get_available_datasets,
    get_available_k_values,
    get_available_models,
    get_latest_run_selection,
    get_performance_summary,
    get_spread_vs_k_data,
    get_runtime_analysis_data,
    get_convergence_data,
    get_seed_set_analysis_data,
    export_statistics_csv,
)


def _apply_plot_theme(fig: Figure, axes_list: List[Any], mode: Optional[str] = None):
    """Styles matplotlib figure and axes to match Light or Dark theme seamlessly."""
    if mode is not None and mode in ("dark", "light"):
        is_dark = mode == "dark"
    else:
        is_dark = is_dark_mode()
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


def _short_name(name: str) -> str:
    return str(name).split()[0] if name else ""


def _display(value: Any, digits: int = 2) -> str:
    """Renders a recorded value, using an em dash when it is missing."""
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


class PageStatistics(ctk.CTkFrame):
    """Unified Statistics & Performance Comparison Hub."""

    def __init__(self, master, on_switch_tab=None, initial_subtab="overview", **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._current_subtab = initial_subtab

        # State filters (seeded from the most recent real run, any model)
        latest = get_latest_run_selection()
        models = get_available_models()
        if latest and latest.get("model"):
            self.current_model = latest["model"]
            self.current_dataset = latest.get("dataset") or ""
            self.current_k = latest.get("k") or 0
        elif models:
            self.current_model = models[0]
            available = get_available_datasets(self.current_model)
            self.current_dataset = available[0] if available else ""
            self.current_k = 0
        else:
            self.current_model = ""
            self.current_dataset = ""
            self.current_k = 0
        available_k = get_available_k_values(self.current_dataset, self.current_model) \
            if self.current_dataset else []
        if self.current_k not in available_k:
            self.current_k = available_k[-1] if available_k else 0
        self.highlight_iga = True

        # UI state that must survive tab rebuilds
        self._metric_mode = "Mean Spread"
        self._show_errors = True
        self._x_mode = "Thế hệ (Generations)"

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
        for canvas in self._canvases:
            try:
                canvas.get_tk_widget().destroy()
            except Exception:
                pass
        self._canvases.clear()

    def _sync_selection(self):
        """Keeps the current filters valid against the data that actually exists."""
        datasets = get_available_datasets(self.current_model)
        if datasets and self.current_dataset not in datasets:
            self.current_dataset = datasets[0]
        k_values = get_available_k_values(self.current_dataset, self.current_model) \
            if self.current_dataset else []
        if k_values and self.current_k not in k_values:
            self.current_k = k_values[0]
        return datasets, k_values

    def _on_model_change(self, model: str):
        """Switches to a propagation model that actually has recorded runs."""
        self.current_model = model
        latest = get_latest_run_selection(model)
        if latest:
            self.current_dataset = latest.get("dataset") or ""
            self.current_k = latest.get("k") or 0
        else:
            datasets = get_available_datasets(model)
            self.current_dataset = datasets[0] if datasets else ""
            self.current_k = 0
        k_values = get_available_k_values(self.current_dataset, model) \
            if self.current_dataset else []
        if self.current_k not in k_values:
            self.current_k = k_values[-1] if k_values else 0
        self.switch_subtab(self._current_subtab)

    # ═════════════════════════════════════════════════════════════════════════
    #  HEADER & 5-TAB NAVIGATION BAR
    # ═════════════════════════════════════════════════════════════════════════

    def _build_header_and_tabs(self):
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
            text="Phân tích kết quả thực nghiệm đã ghi trong thư mục runs/ — độ phủ ảnh hưởng, thời gian chạy, hội tụ và tập hạt giống",
            font=FONT_MAIN,
            text_color=SUBTEXT_FG
        ).pack(anchor="w", pady=(2, 0))

        tab_bar = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10,
                               border_width=1, border_color=BORDER_COLOR)
        tab_bar.pack(fill="x", pady=(0, 14), padx=2)

        tabs_spec = [
            ("overview",    " Tổng quan hiệu năng",        "Best, Mean, Median, Std và xếp hạng thuật toán"),
            ("spread",      " So sánh Spread vs k",        "Đường cong độ phủ, error bars và phân bố các lần chạy"),
            ("runtime",     " Phân tích thời gian",        "Thời gian thực thi đo được của từng thuật toán"),
            ("convergence", " Quá trình Hội tụ",           "Đường cong hội tụ theo thế hệ và số lần đánh giá"),
            ("seed_set",    " Phân tích Seed Set",         "Độ tương đồng Jaccard và tần suất chọn đỉnh hạt giống"),
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

    def switch_subtab(self, tab_key: str, force_reload: bool = False):
        """Switches between the 5 evaluation tabs smoothly.

        ``force_reload`` is accepted for compatibility with callers that request
        a refresh; tab content is always rebuilt from the current run data.
        """
        self._current_subtab = tab_key
        self._cleanup_canvases()

        for key, btn in self._tab_buttons.items():
            if key == tab_key:
                btn.configure(fg_color=ACTIVE_BG, hover_color=ACTIVE_HOVER, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", hover_color=SIDEBAR_HOVER, text_color=SUBTEXT_FG)

        for widget in self._content_area.winfo_children():
            widget.destroy()

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

    # ── Shared UI helpers ────────────────────────────────────────────────────

    def _empty_state(self, parent, subtitle: str):
        command = (lambda: self.on_switch_tab("experiments")) if self.on_switch_tab else None
        create_empty_state(
            parent=parent,
            title="Chưa có dữ liệu thực nghiệm",
            subtitle=subtitle,
            action_text="Khởi chạy thí nghiệm mới ▶" if command else None,
            action_command=command,
            pady=36,
        )

    def _model_selector(self, parent, values: List[str], on_change):
        ctk.CTkLabel(
            parent, text="Mô hình:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG
        ).pack(side="left", padx=(0, 6))
        current = self.current_model if self.current_model in values else (values[0] if values else "")
        combo = ctk.CTkComboBox(parent, values=values or [current], width=140, command=on_change)
        combo.set(current)
        combo.pack(side="left", padx=(0, 14))
        return combo

    def _dataset_selector(self, parent, values: List[str], on_change):
        ctk.CTkLabel(
            parent, text="Bộ dữ liệu:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG
        ).pack(side="left", padx=(0, 6))
        combo = ctk.CTkComboBox(parent, values=values, width=160, command=on_change)
        combo.set(self.current_dataset)
        combo.pack(side="left", padx=(0, 16))
        return combo

    def _k_selector(self, parent, values: List[int], on_change):
        ctk.CTkLabel(
            parent, text="Số hạt giống k:", font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG
        ).pack(side="left", padx=(0, 6))
        combo = ctk.CTkComboBox(
            parent, values=[f"k = {value}" for value in values], width=100, command=on_change
        )
        combo.set(f"k = {self.current_k}")
        combo.pack(side="left", padx=(0, 16))
        return combo

    def _export_button(self, parent, label: str, tab_key: str):
        ctk.CTkButton(
            parent,
            text=label,
            font=("Segoe UI", 10, "bold"),
            width=150,
            height=30,
            fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"),
            text_color=HEADER_FG,
            border_width=1,
            border_color=BORDER_COLOR,
            command=lambda: self._export_csv(tab_key),
        ).pack(side="right", padx=4)

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB A: PERFORMANCE OVERVIEW
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_a_overview(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        datasets, k_values = self._sync_selection()
        if not datasets:
            self._empty_state(
                scroll,
                "Chưa có lần chạy thí nghiệm nào trong runs/. Hãy chạy thí nghiệm để xem thống kê.",
            )
            return

        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        self._model_selector(f_row, get_available_models(), self._on_model_change)
        self._dataset_selector(f_row, datasets, self._on_tab_a_dataset_change)
        self._k_selector(f_row, k_values, lambda v: self._on_tab_a_k_change(int(v.replace("k = ", ""))))

        sw_highlight = ctk.CTkSwitch(
            f_row,
            text="Làm nổi bật IGA",
            font=("Segoe UI", 10, "bold"),
            command=lambda: self._on_tab_a_highlight_toggle(sw_highlight.get())
        )
        if self.highlight_iga:
            sw_highlight.select()
        sw_highlight.pack(side="left", padx=10)

        self._export_button(f_row, "📥 Xuất bảng CSV", "overview")

        summary_rows = get_performance_summary(
            self.current_dataset, k=self.current_k, model=self.current_model
        )
        if not summary_rows:
            card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 16))
            self._empty_state(
                card,
                f"Chưa có kết quả cho {self.current_dataset} với k = {self.current_k}.",
            )
            return

        top_row = summary_rows[0]
        runner_up = summary_rows[1] if len(summary_rows) > 1 else None

        pct_over_runner_up = None
        if (
            runner_up
            and top_row["mean_spread"] is not None
            and runner_up["mean_spread"] not in (None, 0)
        ):
            pct_over_runner_up = (
                (top_row["mean_spread"] - runner_up["mean_spread"])
                / runner_up["mean_spread"] * 100
            )

        fastest_row = min(
            (
                row for row in summary_rows
                if row["time_mean_num"] is not None and row["time_mean_num"] > 0
            ),
            key=lambda row: row["time_mean_num"],
            default=None,
        )
        time_ratio = None
        if (
            fastest_row
            and top_row["time_mean_num"] is not None
            and fastest_row["time_mean_num"] > 0
        ):
            time_ratio = top_row["time_mean_num"] / fastest_row["time_mean_num"]

        top_name = _short_name(top_row["algorithm"])
        mean_value = "—" if top_row["mean_spread"] is None else f"{top_row['mean_spread']}"
        if top_row["std_spread"] is not None:
            mean_value += f" ± {top_row['std_spread']}"
        median_value = (
            f"Trung vị: {top_row['median_spread']} ({top_row['runs']} runs)"
            if top_row["median_spread"] is not None
            else f"Không đủ mẫu để tính trung vị ({top_row['runs']} runs)"
        )

        m_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        m_grid.pack(fill="x", pady=(0, 12))
        for column in range(4):
            m_grid.columnconfigure(column, weight=1)

        metric_card(
            m_grid, f"Best Spread ({top_name})",
            "—" if top_row["best_spread"] is None else f"{top_row['best_spread']}",
            f"Giá trị cao nhất trong {top_row['runs']} lần chạy (k={self.current_k})",
            RED, 0, 0,
        )
        metric_card(
            m_grid, f"Mean Spread ({top_name})",
            mean_value,
            median_value,
            BLUE, 1, 0,
        )
        metric_card(
            m_grid, f"So với {_short_name(runner_up['algorithm'])}" if runner_up else "So với hạng 2",
            f"{pct_over_runner_up:+.1f}%" if pct_over_runner_up is not None else "—",
            (
                f"Chênh lệch Mean Spread: {top_row['mean_spread']} vs {runner_up['mean_spread']}"
                if pct_over_runner_up is not None
                else "Cần ít nhất 2 thuật toán có Mean Spread"
            ),
            GREEN, 2, 0,
        )
        metric_card(
            m_grid, "Thời gian hạng 1 / nhanh nhất",
            f"{time_ratio:.2f}x" if time_ratio is not None else "—",
            (
                f"{top_name} chia cho {_short_name(fastest_row['algorithm'])}"
                if time_ratio is not None
                else "Chưa đủ dữ liệu thời gian"
            ),
            PURPLE, 3, 0,
        )

        banner = ctk.CTkFrame(scroll, fg_color=("#eff6ff", "#0f172a"), corner_radius=8,
                              border_width=1, border_color=("#bfdbfe", "#1e3a8a"))
        banner.pack(fill="x", pady=(0, 12))
        b_content = ctk.CTkFrame(banner, fg_color="transparent")
        b_content.pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(b_content, text="📌 LƯU Ý PHƯƠNG PHÁP:", font=("Segoe UI", 9, "bold"),
                     text_color=BLUE).pack(anchor="w")
        ctk.CTkLabel(
            b_content,
            text="Mean / Median / Std và khoảng tin cậy 95% được tính trực tiếp từ các lần chạy độc lập ghi trong runs/. "
                 "Best Spread chỉ là giá trị cao nhất của một lần chạy nên không phản ánh độ ổn định của thuật toán. "
                 "Trang không dùng điểm tổng hợp/CPI hay giá trị mặc định cho chỉ số bị thiếu.",
            font=("Segoe UI", 9),
            text_color=HEADER_FG,
            wraplength=1000,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

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
            ("Số mẫu", 70),
            ("Time TB", 95),
            ("Hạng", 60),
        ]
        for text, width in headers:
            ctk.CTkLabel(t_head, text=text, font=("Segoe UI", 9, "bold"),
                         text_color=HEADER_FG, width=width, anchor="w").pack(side="left", padx=4, pady=6)

        for idx, row in enumerate(summary_rows):
            is_iga = row["code"] == "iga"
            row_bg = ("#fee2e2", "#311015") if (is_iga and self.highlight_iga) else \
                     ("transparent" if idx % 2 == 0 else ("#f8fafc", "#0d1424"))
            r_frame = ctk.CTkFrame(table_card, fg_color=row_bg, corner_radius=4)
            r_frame.pack(fill="x", padx=10, pady=2)

            name_color = RED if is_iga else row["color"]
            star = " ★ " if is_iga else "   "
            cols_val = [
                (f"{star}{row['algorithm']}", 190, name_color, ("Segoe UI", 9, "bold" if is_iga else "normal")),
                (_display(row["best_spread"]), 95, HEADER_FG, ("Consolas", 9, "bold")),
                (_display(row["mean_spread"]), 100, BLUE if is_iga else HEADER_FG, ("Consolas", 9, "bold")),
                (_display(row["median_spread"]), 85, SUBTEXT_FG, ("Consolas", 9)),
                (_display(row["std_spread"]), 80, RED if (row["std_spread"] or 0) > 0 else GREEN, ("Consolas", 9)),
                (row["ci_95"], 85, SUBTEXT_FG, ("Consolas", 8)),
                (_display(row["runs"]), 70, SUBTEXT_FG, ("Consolas", 9)),
                (row["time_mean"], 95, PURPLE if is_iga else HEADER_FG, ("Consolas", 9, "bold")),
                (f"#{row['rank']}", 60, GREEN if row["rank"] == 1 else SUBTEXT_FG, ("Segoe UI", 9, "bold")),
            ]
            for value, width, column_color, font in cols_val:
                ctk.CTkLabel(r_frame, text=value, font=font, text_color=column_color,
                             width=width, anchor="w").pack(side="left", padx=4, pady=5)

        ctk.CTkFrame(table_card, height=8, fg_color="transparent").pack()

    def _on_tab_a_dataset_change(self, ds: str):
        self.current_dataset = ds
        k_values = get_available_k_values(ds, self.current_model)
        if k_values and self.current_k not in k_values:
            self.current_k = k_values[0]
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

        datasets, _ = self._sync_selection()
        if not datasets:
            self._empty_state(scroll, "Chưa có lần chạy thí nghiệm nào trong runs/.")
            return

        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        self._model_selector(f_row, get_available_models(), self._on_model_change)
        self._dataset_selector(f_row, datasets, lambda v: self._refresh_tab_b(ds=v))

        _, k_values = self._sync_selection()
        self._k_selector(f_row, k_values, lambda v: self._refresh_tab_b(k=int(v.replace("k = ", ""))))

        self.sw_error_bars = ctk.CTkSwitch(
            f_row, text="Hiển thị Error Bars (± Std)", font=("Segoe UI", 10, "bold"),
            command=self._on_tab_b_error_toggle
        )
        if self._show_errors:
            self.sw_error_bars.select()
        self.sw_error_bars.pack(side="left", padx=10)

        ctk.CTkLabel(f_row, text="Chỉ số chính:", font=("Segoe UI", 10, "bold"),
                     text_color=SUBTEXT_FG).pack(side="left", padx=(14, 6))
        self.seg_metric = ctk.CTkSegmentedButton(
            f_row, values=["Mean Spread", "Median Spread"],
            command=self._on_tab_b_metric_change
        )
        self.seg_metric.set(self._metric_mode)
        self.seg_metric.pack(side="left", padx=4)

        self._export_button(f_row, "📥 Xuất dữ liệu CSV", "spread")

        data = get_spread_vs_k_data(self.current_dataset, model=self.current_model, k=self.current_k)
        if not data["curves"]:
            card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 14))
            self._empty_state(card, f"Chưa có dữ liệu spread cho {self.current_dataset}.")
            return

        chart_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        chart_card.pack(fill="x", pady=(0, 14))

        plots_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        plots_frame.pack(fill="both", expand=True, padx=12, pady=12)

        show_errors = self._show_errors
        use_median = self._metric_mode == "Median Spread"

        fig = Figure(figsize=(10.5, 4.2), dpi=100)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)

        markers = ["o", "s", "^", "D", "v", "x", "P", "*", "<", ">"]
        ordered_codes = sorted(data["curves"], key=lambda code: (code != "iga", code))
        for index, code in enumerate(ordered_codes):
            curve = data["curves"][code]
            x_values = curve.get("k_list") or data["k_list"]
            values = curve["medians"] if use_median else curve["means"]
            errors = curve["errors"]
            if use_median:
                points = [
                    (x_value, value, error)
                    for x_value, value, error in zip(x_values, values, errors)
                    if value is not None
                ]
                if not points:
                    continue
                x_values, values, errors = zip(*points)
            linewidth = 2.4 if code == "iga" else 1.4
            alpha = 1.0 if code == "iga" else 0.85
            if show_errors and any(error > 0 for error in errors):
                ax1.errorbar(
                    x_values, values, yerr=errors, label=curve["name"],
                    color=curve["color"], marker=markers[index % len(markers)],
                    markersize=5, linewidth=linewidth, capsize=3, alpha=alpha,
                )
            else:
                ax1.plot(
                    x_values, values, label=curve["name"], color=curve["color"],
                    marker=markers[index % len(markers)], markersize=5,
                    linewidth=linewidth, alpha=alpha,
                )

        ax1.set_title(f"Influence Spread vs Seed Budget k ({self.current_dataset})",
                      fontsize=10, fontweight="bold")
        ax1.set_xlabel("Số lượng đỉnh hạt giống (Seed Budget k)", fontsize=9)
        ax1.set_ylabel("Độ bao phủ ảnh hưởng σ(S)", fontsize=9)
        ax1.legend(fontsize=8, loc="upper left", framealpha=0.6)

        box_labels, box_values, box_colors = [], [], []
        for code in sorted(data["box_data"], key=lambda c: (c != "iga", c)):
            curve = data["curves"].get(code)
            if curve is None:
                continue
            box_labels.append(_short_name(curve["name"]))
            box_values.append(data["box_data"][code])
            box_colors.append(curve["color"])

        if box_values:
            bp = ax2.boxplot(
                box_values, patch_artist=True, tick_labels=box_labels,
                medianprops=dict(color="#ffffff", linewidth=1.5)
            )
            for patch, color in zip(bp["boxes"], box_colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.65)
            ax2.set_title(
                f"Phân bố Spread qua các lần chạy (k = {data['box_k']})",
                fontsize=10, fontweight="bold"
            )
            ax2.set_xlabel("Thuật toán", fontsize=9)
            ax2.set_ylabel("Độ bao phủ ảnh hưởng σ(S)", fontsize=9)
        else:
            ax2.set_title("Không có dữ liệu phân bố theo lần chạy", fontsize=10, fontweight="bold")
            ax2.axis("off")

        _apply_plot_theme(fig, [ax1, ax2] if box_values else [ax1])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=plots_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

    def _refresh_tab_b(self, ds: str = None, k: int = None):
        if ds:
            self.current_dataset = ds
        if k:
            self.current_k = k
        self.switch_subtab("spread", force_reload=True)

    def _on_tab_b_error_toggle(self):
        self._show_errors = bool(self.sw_error_bars.get())
        self._refresh_tab_b()

    def _on_tab_b_metric_change(self, value: str):
        self._metric_mode = value
        self._refresh_tab_b()

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB C: RUNTIME ANALYSIS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_c_runtime(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        datasets, _ = self._sync_selection()
        if not datasets:
            self._empty_state(scroll, "Chưa có lần chạy thí nghiệm nào trong runs/.")
            return

        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        self._model_selector(f_row, get_available_models(), self._on_model_change)
        self._dataset_selector(f_row, datasets, lambda v: self._refresh_tab_c(ds=v))
        _, k_values = self._sync_selection()
        self._k_selector(f_row, k_values, lambda v: self._refresh_tab_c(k=int(v.replace("k = ", ""))))
        self._export_button(f_row, "📥 Xuất bảng Runtime CSV", "runtime")

        data = get_runtime_analysis_data(self.current_dataset, model=self.current_model, k=self.current_k)
        if not data["stages"]:
            card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 14))
            self._empty_state(card, f"Chưa có dữ liệu thời gian cho {self.current_dataset}.")
            return

        chart_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        chart_card.pack(fill="x", pady=(0, 14))

        plots_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        plots_frame.pack(fill="both", expand=True, padx=12, pady=12)

        fig = Figure(figsize=(10.5, 4.2), dpi=100)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)

        stages = [
            stage for stage in data["stages"] if stage["mean_time"] is not None
        ]
        if not stages:
            card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 14))
            self._empty_state(card, f"Lần chạy này không ghi thời gian thực thi cho {self.current_dataset}.")
            return

        names = [_short_name(stage["algorithm"]) for stage in stages]
        mean_times = [stage["mean_time"] for stage in stages]
        positions = list(range(len(stages)))
        bars = ax1.barh(positions, mean_times, color=[stage["color"] for stage in stages], alpha=0.85)
        ax1.set_yticks(positions)
        ax1.set_yticklabels(names, fontsize=9)
        ax1.set_xlabel("Thời gian thực thi trung bình (giây)", fontsize=9)
        ax1.set_title(f"Thời gian thực thi trung bình ({self.current_dataset}, k = {self.current_k})",
                      fontsize=10, fontweight="bold")
        ax1.invert_yaxis()
        for bar, value in zip(bars, mean_times):
            ax1.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                     f" {value:.3f}s", va="center", fontsize=8)

        k_values = data["k_vals"]
        stage_meta = {stage["code"]: stage for stage in stages}
        has_runtime_curve = False
        if k_values:
            for code, series in data["runtime_vs_k"].items():
                if not series["k_list"]:
                    continue
                has_runtime_curve = True
                stage = stage_meta.get(code, {})
                ax2.plot(
                    series["k_list"], series["times"],
                    label=_short_name(stage.get("algorithm", code)),
                    color=stage.get("color", BLUE), marker="o",
                    linewidth=2.4 if code == "iga" else 1.2,
                )

            ax2.set_title("Thời gian theo Seed Budget k", fontsize=10, fontweight="bold")
            ax2.set_xlabel("Seed Budget k", fontsize=9)
            ax2.set_ylabel("Runtime trung bình (giây)", fontsize=9)
            if has_runtime_curve:
                ax2.legend(fontsize=8, loc="upper left", framealpha=0.6)
            else:
                ax2.axis("off")
        else:
            ax2.axis("off")

        _apply_plot_theme(fig, [ax1, ax2] if has_runtime_curve else [ax1])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=plots_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

        table_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        table_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            table_card, text="Bảng thời gian thực thi đo được:",
            font=("Segoe UI", 10, "bold"), text_color=HEADER_FG
        ).pack(anchor="w", padx=14, pady=(10, 4))

        t_head = ctk.CTkFrame(table_card, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        t_head.pack(fill="x", padx=10, pady=(4, 4))
        for text, width in [("Thuật toán", 190), ("Thời gian TB", 140),
                            ("Số lần chạy", 120), ("So với nhanh nhất", 160)]:
            ctk.CTkLabel(t_head, text=text, font=("Segoe UI", 9, "bold"), text_color=HEADER_FG,
                         width=width, anchor="w").pack(side="left", padx=6, pady=6)

        fastest = min(
            (stage["mean_time"] for stage in stages if stage["mean_time"] > 0),
            default=0.0,
        )
        for idx, stage in enumerate(stages):
            is_iga = stage["code"] == "iga"
            row_bg = ("#fee2e2", "#311015") if (is_iga and self.highlight_iga) else \
                     ("transparent" if idx % 2 == 0 else ("#f8fafc", "#0d1424"))
            r_frame = ctk.CTkFrame(table_card, fg_color=row_bg, corner_radius=4)
            r_frame.pack(fill="x", padx=10, pady=2)

            if fastest > 0 and stage["mean_time"] > 0:
                relative = f"{stage['mean_time'] / fastest:.2f}x"
            else:
                relative = "—"
            cols = [
                (stage["algorithm"], 190, RED if is_iga else stage["color"],
                 ("Segoe UI", 9, "bold" if is_iga else "normal")),
                (f"{stage['mean_time']:.4f}s", 140, PURPLE if is_iga else HEADER_FG, ("Consolas", 9, "bold")),
                (str(stage["runs"]), 120, SUBTEXT_FG, ("Consolas", 9)),
                (relative, 160, GREEN if is_iga else SUBTEXT_FG, ("Segoe UI", 9)),
            ]
            for value, width, color, font in cols:
                ctk.CTkLabel(r_frame, text=value, font=font, text_color=color,
                             width=width, anchor="w").pack(side="left", padx=6, pady=4)

        ctk.CTkFrame(table_card, height=8, fg_color="transparent").pack()

    def _refresh_tab_c(self, ds: str = None, k: int = None):
        if ds:
            self.current_dataset = ds
        if k:
            self.current_k = k
        self.switch_subtab("runtime", force_reload=True)

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB D: CONVERGENCE ANALYSIS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_d_convergence(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        datasets, _ = self._sync_selection()
        if not datasets:
            self._empty_state(scroll, "Chưa có lần chạy thí nghiệm nào trong runs/.")
            return

        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        self._model_selector(f_row, get_available_models(), self._on_model_change)
        self._dataset_selector(f_row, datasets, lambda v: self._refresh_tab_d(ds=v))
        _, k_values = self._sync_selection()
        self._k_selector(f_row, k_values, lambda v: self._refresh_tab_d(k=int(v.replace("k = ", ""))))

        ctk.CTkLabel(f_row, text="Trục hoành X:", font=("Segoe UI", 10, "bold"),
                     text_color=SUBTEXT_FG).pack(side="left", padx=(10, 6))
        self.seg_xaxis = ctk.CTkSegmentedButton(
            f_row, values=["Thế hệ (Generations)", "Số lần đánh giá (Evaluations)"],
            command=self._on_tab_d_xaxis_change
        )
        self.seg_xaxis.set(self._x_mode)
        self.seg_xaxis.pack(side="left", padx=4)

        self._export_button(f_row, "📥 Xuất dữ liệu Hội tụ CSV", "convergence")

        conv = get_convergence_data(self.current_dataset, k=self.current_k, model=self.current_model)
        if not conv:
            card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 14))
            self._empty_state(
                card,
                "Lần chạy này không ghi lịch sử hội tụ. Hãy chạy lại thí nghiệm để thu thập dữ liệu hội tụ.",
            )
            return

        chart_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER_COLOR)
        chart_card.pack(fill="x", pady=(0, 14))

        plots_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        plots_frame.pack(fill="both", expand=True, padx=12, pady=12)

        use_evaluations = "Evaluations" in self._x_mode

        fig = Figure(figsize=(10.5, 4.2), dpi=100)
        ax = fig.add_subplot(111)

        ordered = sorted(conv["series"].items(), key=lambda item: (item[0] != "iga", item[0]))
        for code, series in ordered:
            x_values = series["evaluations"] if use_evaluations else series["generations"]
            linewidth = 2.4 if code == "iga" else 1.8
            ax.plot(x_values, series["best"], label=f"{_short_name(series['name'])} — Best",
                    color=series["color"], linewidth=linewidth)
            ax.plot(x_values, series["avg"], label=f"{_short_name(series['name'])} — Average",
                    color=series["color"], linestyle="--", linewidth=1.2, alpha=0.7)

        ax.set_title(f"Đường cong hội tụ trên {self.current_dataset} (k = {self.current_k})",
                     fontsize=11, fontweight="bold")
        ax.set_xlabel(
            "Số lần đánh giá hàm mục tiêu (Fitness Evaluations)" if use_evaluations
            else "Số thế hệ (Generations)"
        )
        ax.set_ylabel("Giá trị hàm thích nghi (Influence Spread Fitness)", fontsize=10)
        ax.legend(fontsize=8, loc="lower right", framealpha=0.75)

        _apply_plot_theme(fig, [ax])
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=plots_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

        c_table = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                               border_width=1, border_color=BORDER_COLOR)
        c_table.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            c_table, text="Bảng đối chiếu tốc độ hội tụ (tính từ lịch sử của lần chạy gần nhất):",
            font=("Segoe UI", 10, "bold"), text_color=HEADER_FG
        ).pack(anchor="w", padx=14, pady=(10, 4))

        th = ctk.CTkFrame(c_table, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        th.pack(fill="x", padx=10, pady=(4, 4))
        for text, width in [("Thuật toán", 180), ("Mean Spread (kiểm định)", 160),
                            ("Thế hệ đạt 90% đỉnh", 160), ("Thế hệ đạt 98% đỉnh", 160),
                            ("Evaluations TB", 150)]:
            ctk.CTkLabel(th, text=text, font=("Segoe UI", 9, "bold"), text_color=HEADER_FG,
                         width=width, anchor="w").pack(side="left", padx=6, pady=6)

        for idx, (code, series) in enumerate(ordered):
            is_iga = code == "iga"
            row_bg = ("#fee2e2", "#311015") if (is_iga and self.highlight_iga) else \
                     ("transparent" if idx % 2 == 0 else ("#f8fafc", "#0d1424"))
            rf = ctk.CTkFrame(c_table, fg_color=row_bg, corner_radius=4)
            rf.pack(fill="x", padx=10, pady=2)

            values = [
                (series["name"], 180, RED if is_iga else series["color"]),
                (_display(series["final"]), 160, HEADER_FG),
                (f"Thế hệ {series['gen_90']}" if series["gen_90"] is not None else "—",
                 160, GREEN if is_iga else SUBTEXT_FG),
                (f"Thế hệ {series['gen_98']}" if series["gen_98"] is not None else "—",
                 160, HEADER_FG),
                (
                    f"{series['total_evaluations']:,}".replace(",", ".")
                    if series["total_evaluations"] is not None else "—",
                    150,
                    SUBTEXT_FG,
                ),
            ]
            for value, width, color in values:
                ctk.CTkLabel(rf, text=value, font=("Segoe UI", 9, "bold" if is_iga else "normal"),
                             text_color=color, width=width, anchor="w").pack(side="left", padx=6, pady=5)

        ctk.CTkFrame(c_table, height=8, fg_color="transparent").pack()

    def _refresh_tab_d(self, ds: str = None, k: int = None):
        if ds:
            self.current_dataset = ds
        if k:
            self.current_k = k
        self.switch_subtab("convergence", force_reload=True)

    def _on_tab_d_xaxis_change(self, value: str):
        self._x_mode = value
        self._refresh_tab_d()

    # ═════════════════════════════════════════════════════════════════════════
    #  TAB E: SEED SET ANALYSIS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_e_seed_set(self, container: ctk.CTkFrame):
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        datasets, k_values = self._sync_selection()
        if not datasets:
            self._empty_state(scroll, "Chưa có lần chạy thí nghiệm nào trong runs/.")
            return

        filter_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                   border_width=1, border_color=BORDER_COLOR)
        filter_card.pack(fill="x", pady=(0, 12))

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=14, pady=10)

        self._model_selector(f_row, get_available_models(), self._on_model_change)
        self._dataset_selector(f_row, datasets, lambda v: self._refresh_tab_e(ds=v))
        self._k_selector(f_row, k_values, lambda v: self._refresh_tab_e(k=int(v.replace("k = ", ""))))
        self._export_button(f_row, "📥 Xuất Seed Nodes CSV", "seed_set")

        s_data = get_seed_set_analysis_data(
            self.current_dataset, k=self.current_k, model=self.current_model
        )
        if not s_data:
            card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 14))
            self._empty_state(card, f"Lần chạy này không lưu tập hạt giống cho {self.current_dataset}.")
            return

        name_a = _short_name(s_data["algorithm_a"])
        name_b = _short_name(s_data["algorithm_b"])

        j_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        j_grid.pack(fill="x", pady=(0, 12))
        for column in range(4):
            j_grid.columnconfigure(column, weight=1)

        metric_card(j_grid, "Jaccard Similarity J(A,B)", s_data["jaccard_pct"],
                    (f"Trung bình trên {s_data['paired_runs']} cặp lần chạy"
                     if s_data["paired_runs"] else "Không có cặp lần chạy để so sánh"),
                    PURPLE, 0, 0)
        metric_card(
            j_grid, "Đỉnh chung (A ∩ B)",
            (f"{s_data['shared_count']:.1f} / {self.current_k}"
             if s_data["shared_count"] is not None else "—"),
            ("Số đỉnh trung bình cả hai cùng chọn"
             if s_data["shared_count"] is not None else "Cần dữ liệu của hai thuật toán"),
            GREEN, 1, 0,
        )
        metric_card(
            j_grid, f"Đỉnh {name_a} độc nhất",
            (f"{s_data['unique_a_count']:.1f}"
             if s_data["unique_a_count"] is not None else "—"),
            ("Số đỉnh trung bình chỉ thuật toán này chọn"
             if s_data["unique_a_count"] is not None else "Cần thuật toán thứ hai để đối chiếu"),
            RED, 2, 0,
        )
        metric_card(
            j_grid, f"Đỉnh {name_b} độc nhất",
            (f"{s_data['unique_b_count']:.1f}"
             if s_data["unique_b_count"] is not None else "—"),
            ("Số đỉnh trung bình chỉ thuật toán này chọn"
             if s_data["unique_b_count"] is not None else "Cần thuật toán thứ hai để đối chiếu"),
            BLUE, 3, 0,
        )

        insight_box = ctk.CTkFrame(scroll, fg_color=("#eff6ff", "#0f172a"), corner_radius=8,
                                   border_width=1, border_color=("#bfdbfe", "#1e3a8a"))
        insight_box.pack(fill="x", pady=(0, 14))

        i_inner = ctk.CTkFrame(insight_box, fg_color="transparent")
        i_inner.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(i_inner, text="🔍 PHÂN TÍCH TẬP ĐỈNH HẠT GIỐNG:",
                     font=("Segoe UI", 9, "bold"), text_color=BLUE).pack(anchor="w")
        ctk.CTkLabel(
            i_inner, text=s_data["insight"], font=("Segoe UI", 9), text_color=HEADER_FG,
            wraplength=1000, justify="left"
        ).pack(anchor="w", pady=(2, 0))

        cols_container = ctk.CTkFrame(scroll, fg_color="transparent")
        cols_container.pack(fill="x", pady=(0, 16))
        cols_container.columnconfigure(0, weight=1)
        cols_container.columnconfigure(1, weight=1)

        left_box = ctk.CTkFrame(cols_container, fg_color=CARD_BG, corner_radius=10,
                                border_width=1, border_color=BORDER_COLOR)
        left_box.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        ctk.CTkLabel(
            left_box, text=f"★ {s_data['algorithm_a']} (k = {self.current_k}):",
            font=("Segoe UI", 10, "bold"), text_color=RED
        ).pack(anchor="w", padx=12, pady=(10, 6))
        self._render_seed_nodes_table(left_box, s_data["nodes_a"], is_iga=True)

        right_box = ctk.CTkFrame(cols_container, fg_color=CARD_BG, corner_radius=10,
                                 border_width=1, border_color=BORDER_COLOR)
        right_box.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
        ctk.CTkLabel(
            right_box, text=f"{s_data['algorithm_b']} (k = {self.current_k}):",
            font=("Segoe UI", 10, "bold"), text_color=BLUE
        ).pack(anchor="w", padx=12, pady=(10, 6))
        self._render_seed_nodes_table(right_box, s_data["nodes_b"], is_iga=False)

    def _render_seed_nodes_table(self, parent: ctk.CTkFrame, nodes: List[Dict[str, Any]], is_iga: bool):
        th = ctk.CTkFrame(parent, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        th.pack(fill="x", padx=10, pady=(2, 4))
        for text, width in [("Node ID", 100), ("Tần suất chọn", 150), ("Trạng thái", 130)]:
            ctk.CTkLabel(th, text=text, font=("Segoe UI", 9, "bold"), text_color=HEADER_FG,
                         width=width, anchor="w").pack(side="left", padx=4, pady=4)

        if not nodes:
            ctk.CTkLabel(parent, text="Không có dữ liệu seed set.",
                         font=("Segoe UI", 9), text_color=SUBTEXT_FG).pack(anchor="w", padx=12, pady=8)
            return

        for node in nodes:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)

            is_shared = node["is_shared"]
            if is_shared is None:
                status_text = "— Chưa đối chiếu"
                status_color = SUBTEXT_FG
            elif is_shared:
                status_text = "● Trùng lặp"
                status_color = GREEN
            else:
                status_text = "★ Độc nhất" if is_iga else "○ Độc nhất"
                status_color = RED if is_iga else BLUE

            values = [
                (f"Node #{node['node_id']}", 100, RED if is_iga else BLUE),
                (f"{node['frequency']}/{node['runs']} lần", 150, HEADER_FG),
                (status_text, 130, status_color),
            ]
            for value, width, color in values:
                ctk.CTkLabel(row, text=value, font=("Consolas", 9), text_color=color,
                             width=width, anchor="w").pack(side="left", padx=4, pady=3)

        ctk.CTkFrame(parent, height=8, fg_color="transparent").pack()

    def _refresh_tab_e(self, ds: str = None, k: int = None):
        if ds:
            self.current_dataset = ds
        if k:
            self.current_k = k
        self.switch_subtab("seed_set", force_reload=True)

    # ═════════════════════════════════════════════════════════════════════════
    #  EXPORT HELPER
    # ═════════════════════════════════════════════════════════════════════════

    def _export_csv(self, tab_key: str):
        csv_text = export_statistics_csv(
            tab_key, self.current_dataset, self.current_k, model=self.current_model
        )
        if not csv_text:
            messagebox.showwarning(
                "Không có dữ liệu",
                "Không có dữ liệu thực nghiệm để xuất cho tab này."
            )
            return

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
