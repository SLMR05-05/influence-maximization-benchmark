#!/usr/bin/env python3
"""Page module."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import json
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.results_store import set_latest_run
from im_research.gui.components.diffusion_simulator import (
    ALGO_LABELS,
    ALGO_OPTIONS,
    CPP_CORE_AVAILABLE,
    DATASET_NAMES,
    compute_layout,
    load_graph_for_sim,
    load_networkx_graph,
    run_celf_on_graph,
    run_cpp_ga_on_graph,
    run_simulation_on_graph,
)

CHART_BG = "#0b1120"
CHART_EDGE = "#1e293b"
CHART_GRID = "#1e293b"
CHART_TEXT = "#94a3b8"


def _json_safe(value):
    """Convert numpy/tuple/set values into plain JSON-serializable Python types."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, bool, int, float)) or value is None:
        return value
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass
    if hasattr(value, "tolist"):
        try:
            return _json_safe(value.tolist())
        except Exception:
            pass
    return str(value)
CHART_MUTED = "#64748b"

NODE_INACTIVE = "#334155"
NODE_INACTIVE_EDGE = "#475569"
NODE_ACTIVE = "#38bdf8"
NODE_ACTIVE_EDGE = "#0ea5e9"
NODE_SEED = "#f59e0b"
NODE_SEED_EDGE = "#fbbf24"
NODE_NEW = "#22c55e"
NODE_NEW_EDGE = "#4ade80"

ALGO_DESCRIPTIONS = {
    "celf": "Greedy / CELF với cận tối ưu (1 - 1/e)",
    "ga": "Genetic Algorithm baseline (C++)",
    "iga": "Improved Genetic Algorithm (đề xuất)",
}


def _fmt_int(value) -> str:
    return f"{int(value):,}".replace(",", ".")


class PageExperiments(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, corner_radius=0, **kw)
        self._alive = True
        self._graph = None
        self._meta = {}
        self._pos = {}
        self._timeline = []
        self._step = 0
        self._playing = False
        self._play_job = None
        self._resize_job = None
        self._outcomes = {}
        self._name_to_code = {}
        self._running = False
        self._speed = 5
        self._checkboxes = []
        self.ga_entries = []
        self.algo_checks = {}
        self._build()
        self.after(60, self._load_preview)

    def _build(self):
        self._build_config_card()
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)
        self._build_graph_card(content)
        self._build_results_card(content)

    def _numbered_header(self, parent, number, title, subtitle=""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(
            row, text=str(number), width=24, height=24, corner_radius=6,
            fg_color=BLUE, text_color="#ffffff",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 8))
        text_box = ctk.CTkFrame(row, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            text_box, text=title.upper(),
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG, anchor="w",
        ).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(
                text_box, text=subtitle,
                font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
            ).pack(anchor="w", pady=(1, 0))
        return row

    def _build_config_card(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self._numbered_header(
            inner, 1, "Configuration & Algorithm Selection",
            "Cấu hình tham số, chọn thuật toán và khởi chạy mô phỏng lan truyền",
        )

        fields = ctk.CTkFrame(inner, fg_color="transparent")
        fields.pack(fill="x", pady=(10, 4))
        for column in range(4):
            fields.grid_columnconfigure(column, weight=1, uniform="field")

        def add_field(column, label, builder):
            box = ctk.CTkFrame(fields, fg_color="transparent")
            box.grid(row=0, column=column, sticky="ew",
                     padx=(0 if column == 0 else 10, 0))
            ctk.CTkLabel(
                box, text=label, font=FONT_SMALL,
                text_color=SUBTEXT_FG, anchor="w",
            ).pack(anchor="w")
            widget = builder(box)
            widget.pack(fill="x", pady=(3, 0))
            return widget

        def menu_style():
            return dict(
                height=32, corner_radius=8, font=FONT_MAIN,
                fg_color=("#f1f5f9", "#1e293b"),
                button_color=("#e2e8f0", "#334155"),
                button_hover_color=("#cbd5e1", "#475569"),
                text_color=HEADER_FG,
                dropdown_fg_color=CARD_BG,
                dropdown_text_color=HEADER_FG,
                dropdown_hover_color=INACTIVE_HOVER,
            )

        def entry_style():
            return dict(
                height=32, corner_radius=8, font=FONT_MAIN,
                border_width=1, border_color=BORDER_COLOR,
                fg_color=("#f8fafc", "#0b1120"),
                text_color=HEADER_FG,
            )

        self.ds_var = ctk.StringVar(value="Karate Club")
        self.ds_menu = add_field(
            0, "Bộ dữ liệu (Dataset)",
            lambda parent: ctk.CTkOptionMenu(
                parent, variable=self.ds_var, values=DATASET_NAMES,
                command=self._on_dataset_change, **menu_style(),
            ),
        )

        self.model_var = ctk.StringVar(value="IC (WC)")

        def model_display(parent):
            box = ctk.CTkFrame(
                parent, height=32, corner_radius=8,
                border_width=1, border_color=BORDER_COLOR,
                fg_color=("#f8fafc", "#0b1120"),
            )
            box.pack_propagate(False)
            ctk.CTkLabel(
                box, text="IC (WC)", font=FONT_MAIN,
                text_color=HEADER_FG,
            ).pack(side="left", padx=10)
            ctk.CTkLabel(
                box, text="cố định", font=FONT_SMALL,
                text_color=SUBTEXT_FG,
            ).pack(side="right", padx=10)
            return box

        self.model_display = add_field(
            1, "Mô hình lan truyền (Diffusion)", model_display,
        )
        Tooltip(
            self.model_display,
            "Cố định IC (Weighted Cascade): p(u→v) = 1/deg(v).",
        )

        self.k_var = ctk.StringVar(value="10")
        self.k_entry = add_field(
            2, "Kích thước hạt giống (k)",
            lambda parent: ctk.CTkEntry(
                parent, textvariable=self.k_var, **entry_style(),
            ),
        )

        self.mc_var = ctk.StringVar(value="100")
        self.mc_entry = add_field(
            3, "Số lần Monte Carlo",
            lambda parent: ctk.CTkEntry(
                parent, textvariable=self.mc_var, **entry_style(),
            ),
        )

        ga_head = ctk.CTkFrame(inner, fg_color="transparent")
        ga_head.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(
            ga_head, text="Tham số GA (C++)",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left")
        ctk.CTkLabel(
            ga_head, text="Có thể nhập tay; GA C++ dùng trực tiếp các giá trị này",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left", padx=(8, 0))

        ga_fields = ctk.CTkFrame(inner, fg_color="transparent")
        ga_fields.pack(fill="x", pady=(2, 2))
        for column in range(3):
            ga_fields.grid_columnconfigure(column, weight=1, uniform="ga")

        self.ga_n_var = ctk.StringVar(value="50")
        self.ga_q_var = ctk.StringVar(value="5")
        self.ga_pc_var = ctk.StringVar(value="0.90")
        self.ga_pm_var = ctk.StringVar(value="0.10")
        self.ga_e_var = ctk.StringVar(value="2")
        self.ga_tmax_var = ctk.StringVar(value="100")

        def add_ga_field(row, column, label, variable, tooltip):
            box = ctk.CTkFrame(ga_fields, fg_color="transparent")
            box.grid(
                row=row, column=column, sticky="ew",
                padx=(0 if column == 0 else 10, 0), pady=(0, 4),
            )
            ctk.CTkLabel(
                box, text=label, font=FONT_SMALL,
                text_color=SUBTEXT_FG, anchor="w",
            ).pack(anchor="w")
            entry = ctk.CTkEntry(
                box, textvariable=variable, **entry_style(),
            )
            entry.pack(fill="x", pady=(3, 0))
            Tooltip(entry, tooltip)
            self.ga_entries.append(entry)
            return entry

        self.ga_n_entry = add_ga_field(
            0, 0, "N (QUẦN THỂ)", self.ga_n_var,
            "Kích thước quần thể N của GA C++.",
        )
        self.ga_q_entry = add_ga_field(
            0, 1, "q (TOURNAMENT)", self.ga_q_var,
            "Số cá thể tham gia tournament chọn cha mẹ.",
        )
        self.ga_pc_entry = add_ga_field(
            0, 2, "PC (LAI GHÉP)", self.ga_pc_var,
            "Xác suất lai ghép Pc, trong khoảng 0..1.",
        )
        self.ga_pm_entry = add_ga_field(
            1, 0, "PM (ĐỘT BIẾN)", self.ga_pm_var,
            "Xác suất đột biến Pm, trong khoảng 0..1.",
        )
        self.ga_e_entry = add_ga_field(
            1, 1, "E (ELITE)", self.ga_e_var,
            "Số cá thể tốt nhất được giữ lại mỗi thế hệ.",
        )
        self.ga_tmax_entry = add_ga_field(
            1, 2, "TMAX (VÒNG LẶP)", self.ga_tmax_var,
            "Số thế hệ tối đa Tmax.",
        )

        algo_head = ctk.CTkFrame(inner, fg_color="transparent")
        algo_head.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(
            algo_head, text="Thuật toán (Algorithm)",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left")
        ctk.CTkLabel(
            algo_head, text="Chọn một hoặc nhiều thuật toán để so sánh",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left", padx=(8, 0))

        algo_grid = ctk.CTkFrame(inner, fg_color="transparent")
        algo_grid.pack(fill="x", pady=(2, 2))
        for column in range(3):
            algo_grid.grid_columnconfigure(column, weight=1, uniform="algo")

        for index, (code, name) in enumerate(ALGO_OPTIONS):
            row, column = divmod(index, 3)
            variable = ctk.BooleanVar(value=(code == "ga"))
            self.algo_checks[code] = variable
            checkbox = ctk.CTkCheckBox(
                algo_grid, text=name, variable=variable, font=FONT_MAIN,
                text_color=HEADER_FG, checkmark_color="#ffffff",
                fg_color=BLUE, hover_color=ACTIVE_HOVER,
                border_color=("#94a3b8", "#475569"),
                checkbox_width=18, checkbox_height=18, corner_radius=4,
            )
            checkbox.grid(row=row, column=column, sticky="w",
                          padx=(0, 8), pady=3)
            Tooltip(checkbox, ALGO_DESCRIPTIONS.get(code, name))
            self._checkboxes.append(checkbox)

        run_row = ctk.CTkFrame(inner, fg_color="transparent")
        run_row.pack(fill="x", pady=(6, 0))

        self.run_btn = ctk.CTkButton(
            run_row, text="▶  EXECUTE SIMULATION",
            font=("Segoe UI", 12, "bold"),
            fg_color=GREEN, hover_color="#059669",
            height=38, corner_radius=8, width=220,
            command=self._execute_simulation,
        )
        self.run_btn.pack(side="left")

        progress_box = ctk.CTkFrame(run_row, fg_color="transparent")
        progress_box.pack(side="left", fill="x", expand=True, padx=(16, 0))

        progress_top = ctk.CTkFrame(progress_box, fg_color="transparent")
        progress_top.pack(fill="x")
        self.progress_lbl = ctk.CTkLabel(
            progress_top, text="Progress: 0%",
            font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
        )
        self.progress_lbl.pack(side="left")
        self.status_lbl = ctk.CTkLabel(
            progress_top, text="Sẵn sàng",
            font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="e",
        )
        self.status_lbl.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            progress_box, height=12, corner_radius=6,
            progress_color=GREEN, fg_color=("#e2e8f0", "#1e293b"),
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(4, 0))

    def _build_graph_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        self._numbered_header(
            inner, 2, "Network Diffusion Simulation",
            "Trực quan hóa từng bước lan truyền của cá thể tốt nhất trên đồ thị 2D",
        )

        badges = ctk.CTkFrame(inner, fg_color="transparent")
        badges.pack(fill="x", pady=(6, 6))
        self.graph_badge = ctk.CTkLabel(
            badges, text="Đang tải đồ thị...",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        )
        self.graph_badge.pack(side="left")

        legend = ctk.CTkFrame(badges, fg_color="transparent")
        legend.pack(side="right")
        for color, text in [
            (NODE_SEED, "Hạt giống"),
            (NODE_ACTIVE, "Đã kích hoạt"),
            (NODE_INACTIVE, "Chưa kích hoạt"),
        ]:
            ctk.CTkFrame(legend, width=8, height=8, corner_radius=4,
                         fg_color=color).pack(side="left", padx=(8, 3))
            ctk.CTkLabel(
                legend, text=text, font=("Segoe UI", 9),
                text_color=SUBTEXT_FG,
            ).pack(side="left")

        canvas_wrap = ctk.CTkFrame(inner, fg_color=CHART_BG, corner_radius=8)
        canvas_wrap.pack(fill="both", expand=True)
        self.graph_canvas = tk.Canvas(
            canvas_wrap, bg=CHART_BG, highlightthickness=0, bd=0, height=180,
        )
        self.graph_canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self.graph_canvas.bind("<Configure>", self._on_canvas_configure)

        controls = ctk.CTkFrame(inner, fg_color="transparent")
        controls.pack(fill="x", pady=(8, 0))
        button_box = ctk.CTkFrame(controls, fg_color="transparent")
        button_box.pack(side="left")

        for symbol, tip, command in [
            ("⏮", "Về bước đầu", self._go_first),
            ("▶", "Phát mô phỏng", self._play),
            ("⏸", "Tạm dừng", self._pause),
            ("⏭", "Bước tiếp theo", self._next_step),
            ("↺", "Đặt lại", self._reset_animation),
        ]:
            button = ctk.CTkButton(
                button_box, text=symbol, width=30, height=30,
                corner_radius=7, font=("Segoe UI Symbol", 14),
                fg_color=("#f1f5f9", "#1e293b"),
                hover_color=("#e2e8f0", "#334155"),
                text_color=HEADER_FG,
                border_width=1, border_color=BORDER_COLOR,
                command=command,
            )
            button.pack(side="left", padx=(0, 3))
            Tooltip(button, tip)

        self.step_lbl = ctk.CTkLabel(
            controls, text="Bước: 0 / 0",
            font=("Segoe UI", 10, "bold"), text_color=HEADER_FG,
        )
        self.step_lbl.pack(side="left", padx=(8, 0))

        speed_box = ctk.CTkFrame(controls, fg_color="transparent")
        speed_box.pack(side="right")
        ctk.CTkLabel(
            speed_box, text="Tốc độ", font=FONT_SMALL,
            text_color=SUBTEXT_FG,
        ).pack(side="left", padx=(0, 4))
        self.speed_slider = ctk.CTkSlider(
            speed_box, from_=1, to=10, number_of_steps=9,
            width=80, command=self._on_speed_change,
            progress_color=BLUE,
        )
        self.speed_slider.set(5)
        self.speed_slider.pack(side="left")

    def _build_results_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.grid(row=0, column=1, sticky="nsew")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        header_row = ctk.CTkFrame(inner, fg_color="transparent")
        header_row.pack(fill="x")

        header_left = ctk.CTkFrame(header_row, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            header_left, text="3", width=24, height=24, corner_radius=6,
            fg_color=BLUE, text_color="#ffffff",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 8))
        header_text = ctk.CTkFrame(header_left, fg_color="transparent")
        header_text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            header_text, text="SIMULATION RESULTS",
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            header_text, text="Kết quả lan truyền và tham số tiến hóa",
            font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
        ).pack(anchor="w", pady=(1, 0))

        header_right = ctk.CTkFrame(header_row, fg_color="transparent")
        header_right.pack(side="right")
        ctk.CTkLabel(
            header_right, text="Hiển thị:",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left", padx=(0, 4))

        self.result_algo_var = ctk.StringVar(value="—")
        self.result_algo_menu = ctk.CTkOptionMenu(
            header_right, variable=self.result_algo_var,
            values=["—"], width=150, height=28,
            font=FONT_SMALL, command=self._on_result_algo_change,
            state="disabled",
            fg_color=("#f1f5f9", "#1e293b"),
            button_color=("#e2e8f0", "#334155"),
            button_hover_color=("#cbd5e1", "#475569"),
            text_color=HEADER_FG,
            dropdown_fg_color=CARD_BG,
            dropdown_text_color=HEADER_FG,
            dropdown_hover_color=INACTIVE_HOVER,
        )
        self.result_algo_menu.pack(side="left")

        stats = ctk.CTkFrame(inner, fg_color="transparent")
        stats.pack(fill="x", pady=(4, 0))
        for column in range(2):
            stats.grid_columnconfigure(column, weight=1, uniform="stat")

        tiles = [
            ("algorithm", "Thuật toán", "—"),
            ("dataset", "Bộ dữ liệu", "—"),
            ("seeds", "Hạt giống", "—"),
            ("spread", "Lan truyền cuối", "—"),
            ("ratio", "Tỷ lệ lan truyền", "—"),
            ("time", "Thời gian thực thi", "—"),
        ]
        self.stat_values = {}
        for index, (key, title, default) in enumerate(tiles):
            row, column = divmod(index, 2)
            tile = ctk.CTkFrame(
                stats, fg_color=("#f8fafc", "#0b1120"), corner_radius=8,
                border_width=1, border_color=BORDER_COLOR,
            )
            tile.grid(row=row, column=column, sticky="nsew",
                      padx=(0 if column == 0 else 6, 0), pady=(0, 2))
            content_row = ctk.CTkFrame(tile, fg_color="transparent")
            content_row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(
                content_row, text=title.upper(),
                font=("Segoe UI", 8, "bold"),
                text_color=SUBTEXT_FG, anchor="w",
            ).pack(side="left")
            value_label = ctk.CTkLabel(
                content_row, text=default, font=("Segoe UI", 11, "bold"),
                text_color=HEADER_FG, anchor="e",
            )
            value_label.pack(side="right")
            self.stat_values[key] = value_label

        self._seed_tooltip = Tooltip(self.stat_values["seeds"], "Chưa có dữ liệu")

    def on_show(self):
        if not self._alive:
            return
        self.after(60, self._render_graph)

    def _load_preview(self):
        if not self._alive:
            return
        self._load_dataset(self.ds_var.get())

    def _load_dataset(self, name):
        try:
            graph, meta = load_graph_for_sim(name)
        except Exception as error:
            self._graph = None
            self._meta = {}
            self._pos = {}
            self._show_canvas_message(f"Không thể tải đồ thị: {error}")
            self.graph_badge.configure(text=f"{name} · lỗi tải dữ liệu")
            self.status_lbl.configure(
                text=f"Lỗi tải dữ liệu: {error}", text_color=RED,
            )
            return

        self._graph = graph
        self._meta = meta
        self._pos = compute_layout(graph)
        self._timeline = []
        self._step = 0
        self._playing = False
        self._update_graph_badge()
        self._reset_results_display()
        self._render_graph()
        self._update_step_label()
        self.status_lbl.configure(text="Sẵn sàng", text_color=SUBTEXT_FG)

    def _update_graph_badge(self):
        meta = self._meta
        if not meta:
            self.graph_badge.configure(text="Chưa có đồ thị")
            return
        text = (
            f"{meta.get('name', '')} · {_fmt_int(meta.get('n', 0))} đỉnh"
            f" · {_fmt_int(meta.get('m', 0))} cạnh"
        )
        if meta.get("reduced"):
            full_n = _fmt_int(meta.get("full_n", meta.get("n", 0)))
            text += f"  ·  hiển thị rút gọn từ {full_n} đỉnh"
            if CPP_CORE_AVAILABLE:
                text += "  ·  GA C++ chạy toàn bộ đồ thị"
        self.graph_badge.configure(text=text)

    def _reset_results_display(self):
        self._outcomes = {}
        self._name_to_code = {}
        self.result_algo_menu.configure(values=["—"], state="disabled")
        self.result_algo_var.set("—")
        for key, label in self.stat_values.items():
            label.configure(text="—", text_color=HEADER_FG)
        self.stat_values["dataset"].configure(text=self.ds_var.get())
        self._seed_tooltip.text = "Chưa có dữ liệu"

    def _on_dataset_change(self, value):
        if self._running:
            return
        self._pause()
        self._load_dataset(value)

    def _on_canvas_configure(self, event=None):
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.after(70, self._render_graph)

    def _show_canvas_message(self, text):
        canvas = self.graph_canvas
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        canvas.create_text(
            width / 2, height / 2,
            text=text, fill=CHART_MUTED,
            font=("Segoe UI", 11),
            width=max(120, width - 40),
        )

    def _render_graph(self):
        canvas = self.graph_canvas
        if canvas is None:
            return
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 30 or height < 30:
            return

        if self._graph is None or not self._pos:
            canvas.create_text(
                width / 2, height / 2,
                text="Chưa có đồ thị để hiển thị",
                fill=CHART_MUTED, font=("Segoe UI", 11),
            )
            return

        pad = 20

        def point(node):
            x, y = self._pos.get(node, (0.5, 0.5))
            return (
                pad + x * (width - 2 * pad),
                pad + (1 - y) * (height - 2 * pad),
            )

        timeline = self._timeline
        step = self._step

        active = set()
        if timeline:
            for nodes in timeline[:step + 1]:
                active.update(nodes)
        seeds = set(timeline[0]) if timeline else set()
        newly_active = set(timeline[step]) if timeline and 0 <= step < len(timeline) else set()

        for u, v in self._graph.edges():
            x1, y1 = point(u)
            x2, y2 = point(v)
            canvas.create_line(x1, y1, x2, y2, fill=CHART_EDGE, width=1)

        if step > 0 and newly_active:
            previous = set()
            for nodes in timeline[:step]:
                previous.update(nodes)
            drawn = set()
            for node in newly_active:
                for parent in self._graph.neighbors(node):
                    if parent not in previous:
                        continue
                    key = (parent, node) if parent < node else (node, parent)
                    if key in drawn:
                        continue
                    drawn.add(key)
                    x1, y1 = point(parent)
                    x2, y2 = point(node)
                    canvas.create_line(
                        x1, y1, x2, y2, fill=NODE_NEW_EDGE, width=2,
                    )

        total_nodes = self._graph.number_of_nodes()
        radius = 10 if total_nodes <= 60 else (7 if total_nodes <= 150 else 5)

        for node in self._graph.nodes():
            x, y = point(node)
            if node in seeds:
                canvas.create_oval(
                    x - radius - 3, y - radius - 3,
                    x + radius + 3, y + radius + 3,
                    fill="", outline=NODE_SEED_EDGE, width=2,
                )
                canvas.create_oval(
                    x - radius, y - radius, x + radius, y + radius,
                    fill=NODE_SEED, outline=NODE_SEED_EDGE, width=1,
                )
            elif node in newly_active and step > 0:
                canvas.create_oval(
                    x - radius, y - radius, x + radius, y + radius,
                    fill=NODE_NEW, outline=NODE_NEW_EDGE, width=1,
                )
            elif node in active:
                canvas.create_oval(
                    x - radius, y - radius, x + radius, y + radius,
                    fill=NODE_ACTIVE, outline=NODE_ACTIVE_EDGE, width=1,
                )
            else:
                canvas.create_oval(
                    x - radius, y - radius, x + radius, y + radius,
                    fill=NODE_INACTIVE, outline=NODE_INACTIVE_EDGE, width=1,
                )

        if timeline:
            canvas.create_text(
                width - 12, 12,
                text=f"Bước {step + 1}/{len(timeline)}",
                fill=CHART_TEXT, font=("Segoe UI", 9, "bold"),
                anchor="ne",
            )

    def _update_step_label(self):
        total = len(self._timeline)
        current = self._step + 1 if total else 0
        self.step_lbl.configure(text=f"Bước: {current} / {total}")

    def _go_first(self):
        self._pause()
        if not self._timeline:
            return
        self._step = 0
        self._update_step_label()
        self._render_graph()

    def _next_step(self):
        self._pause()
        if not self._timeline:
            return
        if self._step < len(self._timeline) - 1:
            self._step += 1
            self._update_step_label()
            self._render_graph()

    def _reset_animation(self):
        self._pause()
        self._step = 0
        self._update_step_label()
        self._render_graph()

    def _play(self):
        if not self._timeline:
            return
        self._pause()
        if self._step >= len(self._timeline) - 1:
            self._step = 0
            self._update_step_label()
            self._render_graph()
        self._playing = True
        self._schedule_next_frame()

    def _schedule_next_frame(self):
        if not self._playing or not self._timeline:
            return
        if self._step >= len(self._timeline) - 1:
            self._playing = False
            return
        delay = max(120, int(1200 / max(1, self._speed)))
        self._play_job = self.after(delay, self._advance_frame)

    def _advance_frame(self):
        if not self._playing or not self._timeline:
            return
        if self._step < len(self._timeline) - 1:
            self._step += 1
            self._update_step_label()
            self._render_graph()
            self._schedule_next_frame()
        else:
            self._playing = False

    def _pause(self):
        self._playing = False
        if self._play_job is not None:
            try:
                self.after_cancel(self._play_job)
            except Exception:
                pass
            self._play_job = None

    def _on_speed_change(self, value):
        self._speed = max(1, int(round(float(value))))

    def _on_result_algo_change(self, name):
        code = self._name_to_code.get(name)
        if code and code in self._outcomes:
            self._display_outcome(code)

    def _display_outcome(self, code):
        outcome = self._outcomes.get(code)
        if not outcome:
            return

        self.result_algo_var.set(outcome["name"])
        self.stat_values["algorithm"].configure(
            text=outcome["name"], text_color=BLUE,
        )
        self.stat_values["dataset"].configure(text=outcome["dataset"])
        self.stat_values["seeds"].configure(
            text=f"{len(outcome['seeds'])} hạt giống",
        )
        self._seed_tooltip.text = (
            "IDs: " + ", ".join(str(node) for node in outcome["seeds"])
        )
        self.stat_values["spread"].configure(
            text=f"{outcome['final_spread']} / {outcome['total_nodes']}",
        )
        self.stat_values["ratio"].configure(
            text=f"{outcome['ratio'] * 100:.2f}%", text_color=GREEN,
        )
        self.stat_values["time"].configure(
            text=f"{outcome['execution_time']:.3f} s",
        )

        self._timeline = outcome["timeline"]
        self._step = 0
        self._update_step_label()
        self._render_graph()

    def _set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for widget in (
            self.ds_menu, self.k_entry,
            self.mc_entry, self.run_btn,
            *self.ga_entries,
        ):
            widget.configure(state=state)
        for checkbox in self._checkboxes:
            checkbox.configure(state=state)

    def _schedule_ui(self, callback, *args):
        if not self._alive:
            return

        def apply():
            if self._alive:
                callback(*args)

        try:
            self.after(0, apply)
        except Exception:
            pass

    def _post_progress(self, value, text):
        if not self._alive:
            return

        def apply():
            if not self._alive:
                return
            value_clamped = max(0.0, min(1.0, float(value)))
            self.progress_bar.set(value_clamped)
            self.progress_lbl.configure(text=f"Progress: {value_clamped * 100:.0f}%")
            self.status_lbl.configure(text=text, text_color=ORANGE)

        try:
            self.after(0, apply)
        except Exception:
            pass

    def _execute_simulation(self):
        if self._running:
            return

        selected = [code for code, variable in self.algo_checks.items() if variable.get()]
        if not selected:
            messagebox.showwarning(
                "Chưa chọn thuật toán",
                "Vui lòng chọn ít nhất một thuật toán để chạy mô phỏng.",
            )
            return

        try:
            k = int(self.k_var.get().strip())
            mc = int(self.mc_var.get().strip())
            n_pop = int(self.ga_n_var.get().strip())
            q_tour = int(self.ga_q_var.get().strip())
            elite = int(self.ga_e_var.get().strip())
            tmax = int(self.ga_tmax_var.get().strip())
            pc = float(self.ga_pc_var.get().strip().replace(",", "."))
            pm = float(self.ga_pm_var.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror(
                "Tham số không hợp lệ",
                "k, N, q, E, Tmax phải là số nguyên; Pc, Pm phải là số thực.",
            )
            return

        if k <= 0 or mc <= 0:
            messagebox.showerror(
                "Tham số không hợp lệ",
                "Kích thước hạt giống (k) và số lần Monte Carlo phải lớn hơn 0.",
            )
            return

        ga_errors = []
        if n_pop < 2:
            ga_errors.append("N phải lớn hơn hoặc bằng 2.")
        if q_tour < 1 or q_tour > n_pop:
            ga_errors.append("q phải nằm trong khoảng 1..N.")
        if elite < 0 or elite >= n_pop:
            ga_errors.append("E phải nằm trong khoảng 0..N-1.")
        if tmax < 1:
            ga_errors.append("Tmax phải lớn hơn hoặc bằng 1.")
        if not 0.0 <= pc <= 1.0:
            ga_errors.append("Pc phải nằm trong khoảng 0..1.")
        if not 0.0 <= pm <= 1.0:
            ga_errors.append("Pm phải nằm trong khoảng 0..1.")
        if ga_errors:
            messagebox.showerror(
                "Tham số GA không hợp lệ",
                "\n".join(ga_errors),
            )
            return

        if self._graph is None:
            messagebox.showerror(
                "Chưa có đồ thị",
                "Không có đồ thị để mô phỏng. Vui lòng chọn lại bộ dữ liệu.",
            )
            return

        total_nodes = self._graph.number_of_nodes()
        if k > total_nodes:
            k = total_nodes
            self.k_var.set(str(k))

        ga_params = {
            "N": n_pop,
            "q": q_tour,
            "Pc": pc,
            "Pm": pm,
            "E": elite,
            "Tmax": tmax,
        }

        self._pause()
        self._running = True
        self._set_controls_enabled(False)
        self.progress_bar.set(0)
        self.progress_lbl.configure(text="Progress: 0%")
        self.status_lbl.configure(text="Đang khởi tạo mô phỏng...", text_color=ORANGE)

        worker = threading.Thread(
            target=self._run_worker,
            args=(
                self._graph, dict(self._meta), self.ds_var.get(),
                self.model_var.get(), k, mc, selected, ga_params,
            ),
            daemon=True,
        )
        worker.start()

    def _run_worker(self, graph, meta, dataset, model, k, mc, selected, params):
        outcomes = {}
        baseline = {}
        errors = {}
        baseline_codes = (
            ["celf"]
            if len(selected) == 1 and selected[0] != "celf"
            else []
        )
        run_codes = list(selected) + baseline_codes
        total = len(run_codes)

        try:
            for index, code in enumerate(run_codes):
                is_baseline = code not in selected
                label = ALGO_LABELS.get(code, code)
                if is_baseline:
                    label += " (baseline)"
                self._post_progress(
                    index / total,
                    f"Đang chạy {label} ({index + 1}/{total})...",
                )

                def report(phase, base=index / total, span=1 / total, name=label):
                    self._post_progress(
                        base + phase * span,
                        f"Đang chạy {name}...",
                    )

                try:
                    if code == "ga" and CPP_CORE_AVAILABLE:
                        outcome = run_cpp_ga_on_graph(
                            dataset, model, k, mc, params,
                            progress=report,
                        )
                    elif code == "celf" and CPP_CORE_AVAILABLE:
                        outcome = run_celf_on_graph(
                            dataset, model, k, mc, progress=report,
                        )
                    else:
                        outcome = run_simulation_on_graph(
                            graph, meta, dataset, model, k, mc, code,
                            progress=report, params=params,
                        )
                    if is_baseline:
                        baseline[code] = outcome
                    else:
                        outcomes[code] = outcome
                except Exception as error:
                    if not is_baseline:
                        errors[code] = str(error)

            save_error = None
            if outcomes:
                try:
                    self._save_results(
                        outcomes, dataset, model, k, mc, baseline,
                    )
                except Exception as error:
                    save_error = str(error)

            self._schedule_ui(self._post_complete, outcomes, errors, save_error)
        except Exception as error:
            self._schedule_ui(self._post_error, str(error))

    def _post_complete(self, outcomes, errors, save_error=None):
        if not self._alive:
            return

        self._running = False
        self._set_controls_enabled(True)
        self.progress_bar.set(1.0)
        self.progress_lbl.configure(text="Progress: 100%")

        if not outcomes:
            self.status_lbl.configure(text="Mô phỏng thất bại", text_color=RED)
            detail = "\n".join(errors.values()) or "Không có kết quả."
            messagebox.showerror("Lỗi mô phỏng", detail)
            return

        self._outcomes = outcomes
        self._name_to_code = {
            outcome["name"]: code for code, outcome in outcomes.items()
        }
        names = [outcomes[code]["name"] for code in outcomes]
        self.result_algo_menu.configure(values=names, state="normal")

        best_code = max(outcomes, key=lambda item: outcomes[item]["mean_spread"])
        self.result_algo_var.set(outcomes[best_code]["name"])
        self._display_outcome(best_code)

        if errors:
            self.status_lbl.configure(
                text=f"Hoàn tất {len(outcomes)}/{len(outcomes) + len(errors)} thuật toán",
                text_color=ORANGE,
            )
        else:
            self.status_lbl.configure(
                text="Hoàn tất · nhấn ▶ để xem lan truyền",
                text_color=GREEN,
            )

        if save_error:
            messagebox.showwarning(
                "Chưa lưu được kết quả",
                "Kết quả đã chạy xong nhưng không ghi được vào thư mục runs/:\n"
                f"{save_error}",
            )

    def _post_error(self, message):
        if not self._alive:
            return
        self._running = False
        self._set_controls_enabled(True)
        self.status_lbl.configure(text="Lỗi mô phỏng", text_color=RED)
        messagebox.showerror("Lỗi mô phỏng", message)

    def _save_results(self, outcomes, dataset, model, k, mc, baseline=None):
        """Persist one experiment run so the Results / Comparison pages can show it."""
        runs_dir = PROJECT_ROOT / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        def build_rows(items):
            ordered = sorted(
                items.values(),
                key=lambda outcome: outcome["mean_spread"],
                reverse=True,
            )
            rows = []
            for rank, outcome in enumerate(ordered, start=1):
                spreads = outcome.get("spreads", [])
                best_spread = max(spreads) if spreads else outcome["mean_spread"]
                rows.append({
                    "algorithm": outcome["name"],
                    "code": outcome["code"],
                    "algorithm_name": outcome.get("algorithm_name", outcome["name"]),
                    "model": outcome.get("model", model),
                    "mean_spread": round(outcome["mean_spread"], 2),
                    "std_spread": round(outcome["std_spread"], 2),
                    "final_spread": round(outcome.get("final_spread", 0), 2),
                    "best_spread": round(best_spread, 2),
                    "mean_ratio": round(outcome.get("mean_ratio", 0.0), 4),
                    "ratio": round(outcome.get("ratio", 0.0), 4),
                    "total_nodes": outcome.get("total_nodes", 0),
                    "mean_time": round(outcome["execution_time"], 3),
                    "rank": f"#{rank}",
                    "seeds": [int(node) for node in outcome.get("seeds", [])],
                    "params": outcome.get("params", {}),
                    "individuals": outcome.get("individuals", []),
                    "online_bound": outcome.get("online_bound"),
                    "seed": outcome.get("seed"),
                    "generations": outcome.get("generations"),
                })
            return rows, ordered

        summary, ordered = build_rows(outcomes)
        baseline_summary, _ = build_rows(baseline or {})

        details = {}
        for outcome in ordered:
            details[outcome["name"]] = {
                "spreads": [round(float(value), 4) for value in outcome.get("spreads", [])],
                "times": [round(float(outcome["execution_time"]), 4)],
                "seeds": [[int(node) for node in outcome.get("seeds", [])]],
                "params": outcome.get("params", {}),
                "individuals": outcome.get("individuals", []),
            }

        payload = {
            "dataset": dataset,
            "k": k,
            "model": model,
            "mc": mc,
            "mc_val": mc,
            "runs": 1,
            "timestamp": timestamp,
            "params": ordered[0].get("params", {}) if ordered else {},
            "summary": summary,
            "baseline": baseline_summary,
            "details": details,
        }

        payload = _json_safe(payload)
        set_latest_run(payload)

        latest_path = runs_dir / "latest_results.json"
        with open(latest_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        experiment_dir = runs_dir / f"EXP_{timestamp}"
        experiment_dir.mkdir(parents=True, exist_ok=True)
        with open(experiment_dir / "summary.json", "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        history_path = runs_dir / "results_history.json"
        history = []
        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                if isinstance(loaded, list):
                    history = loaded
            except Exception:
                history = []
        history.append(payload)
        with open(history_path, "w", encoding="utf-8") as handle:
            json.dump(history, handle, indent=2, ensure_ascii=False)

        return timestamp

    def destroy(self):
        self._alive = False
        self._pause()
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
            self._resize_job = None
        super().destroy()
