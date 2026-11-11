#!/usr/bin/env python3
"""Results Page — Influence Spread & Execution Times."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, create_empty_state
from im_research.gui.core.results_store import load_runs, set_latest_run


class PageResults(ctk.CTkScrollableFrame):
    def __init__(self, master, on_switch_tab=None, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._load_error = None
        self._build()

    def on_show(self):
        self._refresh()

    def _refresh(self):
        for child in self.winfo_children():
            child.destroy()
        self._load_error = None
        self._build()
        self.after(50, self._scroll_to_top)

    def _load_runs(self):
        self._load_error = None
        try:
            return load_runs()
        except Exception as error:
            self._load_error = f"Không đọc được dữ liệu kết quả: {error}"
            return []

    def _build(self):
        runs = self._load_runs()
        subtitle = (
            "Lịch sử các lần chạy thí nghiệm · Mỗi thuật toán kèm top 5 cá thể tốt nhất"
        )
        if runs:
            subtitle += f" · Tổng số lần chạy: {len(runs)}"
        section_header(
            self,
            "Kết quả lan truyền (Influence Spread Results)",
            subtitle,
        )

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            toolbar,
            text="Dữ liệu được đọc trực tiếp từ thư mục runs/ sau mỗi lần chạy thí nghiệm.",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left")
        ctk.CTkButton(
            toolbar, text="Làm mới dữ liệu", command=self._refresh,
            font=("Segoe UI", 10, "bold"), fg_color=BLUE,
            hover_color="#1d4ed8", width=120, height=30, corner_radius=8,
        ).pack(side="right")

        if self._load_error:
            ctk.CTkLabel(
                self, text=self._load_error, font=FONT_SMALL,
                text_color=ORANGE, anchor="w",
            ).pack(fill="x", pady=(0, 8))

        if not runs:
            card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 16))
            cmd = (lambda: self.on_switch_tab("experiments")) if self.on_switch_tab else None
            create_empty_state(
                parent=card,
                title="Chưa có kết quả thực nghiệm",
                subtitle="Hệ thống chưa ghi nhận lần chạy thí nghiệm nào. Hãy thiết lập tham số và khởi chạy để xem kết quả tại đây.",
                action_text="Khởi chạy thí nghiệm mới ▶",
                action_command=cmd,
                pady=36,
            )
            return

        for index, run in enumerate(runs, start=1):
            self._build_run_card(run, index)

    def _scroll_to_top(self):
        try:
            self._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _build_run_card(self, run, index):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 14), padx=2)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header, text=f"Lần chạy #{index}",
            font=("Segoe UI", 12, "bold"), text_color=HEADER_FG,
        ).pack(side="left")

        if index == 1:
            ctk.CTkLabel(
                header, text="MỚI NHẤT",
                font=("Segoe UI", 8, "bold"), text_color=PILL_FG,
                fg_color=PILL_BG, corner_radius=6,
            ).pack(side="left", padx=(8, 0), ipadx=6, ipady=2)

        meta_parts = [
            str(run.get("dataset", "—")),
            f"k={run.get('k', '—')}",
            str(run.get("model", "—")),
            f"R={run.get('mc', run.get('mc_val', '—'))}",
        ]
        timestamp = run.get("timestamp")
        if timestamp:
            meta_parts.append(str(timestamp))
        ctk.CTkLabel(
            header, text=" · ".join(meta_parts),
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left", padx=(12, 0))

        summary = run.get("summary", [])
        ctk.CTkLabel(
            header, text=f"{len(summary)} thuật toán",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="right")

        params = run.get("params") or {}
        if params:
            param_text = " · ".join(
                f"{key}={params[key]}" for key in
                ("N", "q", "Pc", "Pm", "E", "Tmax") if key in params
            )
            if param_text:
                ctk.CTkLabel(
                    card, text=f"Tham số GA: {param_text}",
                    font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
                ).pack(fill="x", padx=16, pady=(0, 2))

        if not summary:
            ctk.CTkLabel(
                card, text="Không có dữ liệu thuật toán cho lần chạy này.",
                font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 12))
            return

        for row in summary:
            self._build_algorithm_row(card, row)

    def _build_algorithm_row(self, parent, row):
        code = str(row.get("code", "")).lower()
        color = RED if "iga" in code else (BLUE if "celf" in code else GREEN)

        algo_card = ctk.CTkFrame(
            parent, fg_color=("#f8fafc", "#0b1120"), corner_radius=8,
            border_width=1, border_color=BORDER_COLOR,
        )
        algo_card.pack(fill="x", padx=12, pady=(0, 8))

        head = ctk.CTkFrame(algo_card, fg_color="transparent")
        head.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            head, text=row.get("algorithm", row.get("name", "N/A")),
            font=("Segoe UI", 11, "bold"), text_color=color,
        ).pack(side="left")

        ctk.CTkLabel(
            head,
            text=(
                f"Spread TB: {float(row.get('mean_spread', 0)):.2f}"
                f" ± {float(row.get('std_spread', 0)):.2f}"
            ),
            font=FONT_SMALL, text_color=HEADER_FG,
        ).pack(side="left", padx=(12, 0))

        ratio = row.get("ratio")
        if ratio is not None:
            ctk.CTkLabel(
                head, text=f"Tỷ lệ: {float(ratio) * 100:.2f}%",
                font=FONT_SMALL, text_color=GREEN,
            ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(
            head, text=f"Thời gian: {float(row.get('mean_time', 0)):.3f}s",
            font=FONT_SMALL, text_color=HEADER_FG,
        ).pack(side="left", padx=(12, 0))

        online_bound = row.get("online_bound")
        if online_bound is not None:
            ctk.CTkLabel(
                head, text=f"Cận trên: {float(online_bound):.2f}",
                font=FONT_SMALL, text_color=ORANGE,
            ).pack(side="left", padx=(12, 0))

        seeds = row.get("seeds") or []
        if seeds:
            ctk.CTkLabel(
                head, text=f"k={len(seeds)} hạt giống",
                font=FONT_SMALL, text_color=HEADER_FG,
            ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(
            head, text=f"Hạng: {row.get('rank', '-')}",
            font=("Segoe UI", 10, "bold"), text_color=BLUE,
        ).pack(side="right")

        individuals = row.get("individuals", [])
        if not individuals:
            ctk.CTkLabel(
                algo_card, text="Không có dữ liệu cá thể.",
                font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
            ).pack(fill="x", padx=10, pady=(0, 8))
            return

        ind_head = ctk.CTkFrame(algo_card, fg_color="transparent")
        ind_head.pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(
            ind_head, text="TOP 5 CÁ THỂ (theo fitness tìm kiếm)",
            font=("Segoe UI", 8, "bold"), text_color=SUBTEXT_FG,
        ).pack(side="left")

        container = ctk.CTkFrame(algo_card, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=(0, 8))

        for individual in individuals[:5]:
            rank = individual.get("rank", "-")
            seeds = individual.get("seeds", [])
            seed_text = ", ".join(str(node) for node in seeds)
            display_text = seed_text
            if len(display_text) > 110:
                display_text = display_text[:107] + "..."

            line = ctk.CTkFrame(container, fg_color="transparent")
            line.pack(fill="x", pady=1)

            ctk.CTkLabel(
                line, text=f"#{rank}", width=28,
                font=("Segoe UI", 9, "bold"), text_color=color, anchor="w",
            ).pack(side="left")

            seed_label = ctk.CTkLabel(
                line, text=f"Seeds: {display_text}",
                font=("Segoe UI", 9), text_color=HEADER_FG, anchor="w",
            )
            seed_label.pack(side="left", fill="x", expand=True)
            if display_text != seed_text:
                Tooltip(seed_label, seed_text)

            ctk.CTkLabel(
                line,
                text=f"Spread: {float(individual.get('spread', 0)):.2f}",
                font=("Segoe UI", 9), text_color=SUBTEXT_FG,
            ).pack(side="right", padx=(8, 0))

            ctk.CTkLabel(
                line,
                text=f"Fitness: {float(individual.get('fitness', 0)):.2f}",
                font=("Segoe UI", 9), text_color=SUBTEXT_FG,
            ).pack(side="right", padx=(8, 0))
