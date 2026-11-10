#!/usr/bin/env python3
"""IC Diffusion Configuration View — editable settings for Independent Cascade.

Embedded as a dedicated view inside PageDatasets.  The view persists its
values in ``data/config.db`` and the Experiments page reads them whenever a
new run is launched.  Linear Threshold is deliberately not exposed because
the C++ engine does not implement it yet.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk

from im_research.core.diffusion_config import (
    DEFAULT_IC_CONFIG,
    get_ic_config,
    reset_ic_config,
    save_ic_config,
)
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header


class ICConfigView(ctk.CTkScrollableFrame):
    """Editable panel for the Independent Cascade diffusion model."""

    def __init__(
        self,
        master,
        on_saved: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kw,
    ):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._on_saved = on_saved
        self._config: Dict[str, Any] = get_ic_config()

        self._p_var = ctk.StringVar(value=self._fmt_p(self._config["edge_probability"]))
        self._mc_search_var = ctk.StringVar(value=str(self._config["mc_search"]))
        self._mc_val_var = ctk.StringVar(value=str(self._config["mc_validation"]))
        self._seed_search_var = ctk.StringVar(value=str(self._config["seed_search"]))
        self._seed_val_var = ctk.StringVar(value=str(self._config["seed_validation"]))

        self._summary_labels: Dict[str, ctk.CTkLabel] = {}
        self._status_label: Optional[ctk.CTkLabel] = None

        self._build()

    # ── Formatting helpers ───────────────────────────────────────────────────
    @staticmethod
    def _fmt_p(value: float) -> str:
        return f"{value:g}"

    def _build(self):
        section_header(
            self,
            "Cấu hình mô hình lan truyền IC",
            "Thiết lập Independent Cascade dùng chung cho mọi thí nghiệm. "
            "Cấu hình được lưu vào data/config.db và tự động nạp ở tab Thí nghiệm.",
        )

        self._build_status_banner()

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", pady=(0, 16))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        self._build_form(body)
        self._build_summary(body)

    # ── Banner ───────────────────────────────────────────────────────────────
    def _build_status_banner(self):
        banner = ctk.CTkFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        banner.pack(fill="x", pady=(0, 14))

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left,
            text="Independent Cascade (IC)",
            font=("Segoe UI", 15, "bold"),
            text_color=HEADER_FG,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="Mô hình lan truyền duy nhất đang được hỗ trợ bởi C++ OpenMP engine.",
            font=FONT_MAIN,
            text_color=SUBTEXT_FG,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        pill = ctk.CTkFrame(inner, fg_color=GREEN_PILL_BG, corner_radius=12, height=28)
        pill.pack(side="right", padx=(12, 0))
        ctk.CTkLabel(
            pill,
            text="● Đang hoạt động",
            font=("Segoe UI", 10, "bold"),
            text_color=GREEN_PILL_FG,
        ).pack(padx=12, pady=4)
        Tooltip(pill, "IC đã được cài đặt trong C++ core. LT chưa được hỗ trợ.")

    # ── Left: editable form ──────────────────────────────────────────────────
    def _build_form(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        card.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Tham số lan truyền",
            font=("Segoe UI", 13, "bold"),
            text_color=HEADER_FG,
            anchor="w",
        ).grid(row=0, column=0, padx=18, pady=(16, 4), sticky="w")

        # Model + probability mechanism (fixed, read-only)
        self._section(card, 1, "Mô hình & cơ chế xác suất")
        self._fixed_row(
            card, 2, "Mô hình lan truyền:", "Independent Cascade (IC)",
            "LT không được hỗ trợ trong phiên bản này.",
        )
        self._fixed_row(
            card, 3, "Cơ chế gán xác suất:", "Uniform — hằng số cho mọi cạnh",
            "Mỗi cạnh có cùng xác suất p, không phụ thuộc bậc đỉnh.",
        )
        self._entry_row(
            card, 4, "Xác suất cạnh p:", self._p_var,
            "Khoảng hợp lệ: 0 < p ≤ 1. Khuyến nghị 0.01 – 0.20.",
            tooltip="Xác suất một đỉnh đang hoạt động kích hoạt được láng giềng của nó trong IC.",
        )

        # Monte Carlo
        self._section(card, 5, "Monte Carlo")
        self._entry_row(
            card, 6, "R_search — MC tìm kiếm:", self._mc_search_var,
            "Số lần mô phỏng cho fitness trong quá trình tối ưu (mặc định 200).",
            tooltip="Càng lớn fitness càng ổn định nhưng thí nghiệm chạy càng chậm.",
        )
        self._entry_row(
            card, 7, "R_val — MC kiểm định:", self._mc_val_var,
            "Số lần mô phỏng độc lập để chấm điểm chính thức (mặc định 1.000).",
            tooltip="Bộ kiểm định dùng seed riêng, không trùng với quá trình tìm kiếm.",
        )

        # Seeds
        self._section(card, 8, "Khởi tạo ngẫu nhiên")
        self._entry_row(
            card, 9, "Seed evaluator (tìm kiếm):", self._seed_search_var,
            "Seed cố định giúp tái lập kết quả tìm kiếm (mặc định 42).",
            tooltip="Evaluator tăng seed nội bộ sau mỗi lần đánh giá để tránh trùng mẫu.",
        )
        self._entry_row(
            card, 10, "Seed evaluator (kiểm định):", self._seed_val_var,
            "Seed độc lập cho bộ kiểm định (mặc định 12.345).",
            tooltip="Tách seed kiểm định khỏi seed tìm kiếm để tránh thiên lệch.",
        )

        # Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=11, column=0, padx=18, pady=(10, 6), sticky="ew")

        ctk.CTkButton(
            actions,
            text="💾  Lưu cấu hình",
            font=("Segoe UI", 11, "bold"),
            fg_color=BLUE,
            hover_color=ACTIVE_HOVER,
            height=36,
            corner_radius=8,
            command=self._save,
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text="↺  Khôi phục mặc định",
            font=("Segoe UI", 11, "bold"),
            fg_color="transparent",
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=HEADER_FG,
            hover_color=SIDEBAR_HOVER,
            height=36,
            corner_radius=8,
            command=self._reset,
        ).pack(side="left", padx=(10, 0))

        self._status_label = ctk.CTkLabel(
            card,
            text="",
            font=FONT_MAIN,
            text_color=SUBTEXT_FG,
            anchor="w",
            wraplength=560,
            justify="left",
        )
        self._status_label.grid(row=12, column=0, padx=18, pady=(0, 16), sticky="w")

    # ── Right: summary / help ────────────────────────────────────────────────
    def _build_summary(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        card.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            card,
            text="Cấu hình đang lưu",
            font=("Segoe UI", 13, "bold"),
            text_color=HEADER_FG,
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(16, 4))

        rows = [
            ("Mô hình", "model", "IC"),
            ("Xác suất p", "edge_probability", self._fmt_p(self._config["edge_probability"])),
            ("R_search", "mc_search", f"{self._config['mc_search']:,}"),
            ("R_val", "mc_validation", f"{self._config['mc_validation']:,}"),
            ("Seed tìm kiếm", "seed_search", str(self._config["seed_search"])),
            ("Seed kiểm định", "seed_validation", str(self._config["seed_validation"])),
        ]
        for label, key, value in rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=4)
            ctk.CTkLabel(
                row, text=label, font=FONT_MAIN, text_color=SUBTEXT_FG, anchor="w"
            ).pack(side="left")
            val_lbl = ctk.CTkLabel(
                row, text=value, font=("Consolas", 11, "bold"),
                text_color=HEADER_FG, anchor="e",
            )
            val_lbl.pack(side="right")
            self._summary_labels[key] = val_lbl

        ctk.CTkFrame(card, height=1, fg_color=DIVIDER).pack(fill="x", padx=18, pady=10)

        ctk.CTkLabel(
            card,
            text="Phạm vi áp dụng",
            font=("Segoe UI", 11, "bold"),
            text_color=HEADER_FG,
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(0, 4))

        ctk.CTkLabel(
            card,
            text=(
                "Tab Thí nghiệm đọc cấu hình này mỗi khi khởi chạy. "
                "Thay đổi p, R_search, R_val hoặc seed tại đây sẽ được "
                "truyền xuống runner Python → C++ evaluator."
            ),
            font=FONT_SMALL,
            text_color=SUBTEXT_FG,
            anchor="w",
            justify="left",
            wraplength=300,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        info = ctk.CTkFrame(card, fg_color=PILL_BG, corner_radius=8)
        info.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkLabel(
            info,
            text=(
                "IC: mỗi đỉnh vừa kích hoạt có đúng một cơ hội "
                "kích hoạt từng láng giềng chưa hoạt động với xác suất p. "
                "Quá trình dừng khi không còn đỉnh mới."
            ),
            font=FONT_SMALL,
            text_color=PILL_FG,
            anchor="w",
            justify="left",
            wraplength=280,
        ).pack(padx=10, pady=8, anchor="w")

    # ── Widget builders ──────────────────────────────────────────────────────
    def _section(self, parent, row: int, title: str):
        ctk.CTkLabel(
            parent,
            text=title,
            font=("Segoe UI", 11, "bold"),
            text_color=BLUE,
            anchor="w",
        ).grid(row=row, column=0, padx=18, pady=(12, 2), sticky="w")

    def _fixed_row(self, parent, row: int, label: str, value: str, hint: str):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=0, padx=18, pady=5, sticky="ew")

        ctk.CTkLabel(
            box, text=label, font=FONT_MAIN, text_color=SUBTEXT_FG,
            width=190, anchor="w",
        ).pack(side="left")

        pill = ctk.CTkFrame(box, fg_color=GREEN_PILL_BG, corner_radius=8)
        pill.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            pill, text=value, font=("Segoe UI", 10, "bold"),
            text_color=GREEN_PILL_FG,
        ).pack(padx=9, pady=3)

        ctk.CTkLabel(
            box, text=hint, font=FONT_SMALL, text_color=SUBTEXT_FG,
            anchor="w", wraplength=250, justify="left",
        ).pack(side="left", fill="x", expand=True)

    def _entry_row(
        self,
        parent,
        row: int,
        label: str,
        variable: ctk.StringVar,
        hint: str,
        tooltip: str = "",
    ):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=row, column=0, padx=18, pady=5, sticky="ew")

        lbl = ctk.CTkLabel(
            box, text=label, font=FONT_MAIN, text_color=SUBTEXT_FG,
            width=190, anchor="w",
        )
        lbl.pack(side="left")

        entry = ctk.CTkEntry(
            box,
            textvariable=variable,
            width=130,
            height=32,
            font=FONT_MONO,
            border_width=1,
            border_color=BORDER_COLOR,
            corner_radius=6,
        )
        entry.pack(side="left", padx=(0, 10))
        if tooltip:
            Tooltip(entry, tooltip)
            Tooltip(lbl, tooltip)

        ctk.CTkLabel(
            box, text=hint, font=FONT_SMALL, text_color=SUBTEXT_FG,
            anchor="w", wraplength=250, justify="left",
        ).pack(side="left", fill="x", expand=True)

    # ── Events ───────────────────────────────────────────────────────────────
    def _collect(self) -> Dict[str, Any]:
        return {
            "model": "IC",
            "probability_mode": "uniform",
            "edge_probability": self._p_var.get(),
            "mc_search": self._mc_search_var.get(),
            "mc_validation": self._mc_val_var.get(),
            "seed_search": self._seed_search_var.get(),
            "seed_validation": self._seed_val_var.get(),
        }

    def _save(self):
        try:
            config = save_ic_config(self._collect())
        except ValueError as exc:
            self._set_status(f"❌ {exc}", RED)
            return
        except Exception as exc:
            self._set_status(f"❌ Không thể lưu cấu hình: {exc}", RED)
            return

        self._config = config
        self._p_var.set(self._fmt_p(config["edge_probability"]))
        self._mc_search_var.set(str(config["mc_search"]))
        self._mc_val_var.set(str(config["mc_validation"]))
        self._seed_search_var.set(str(config["seed_search"]))
        self._seed_val_var.set(str(config["seed_validation"]))
        self._refresh_summary(config)
        self._set_status(
            "✅ Đã lưu cấu hình IC. Tab Thí nghiệm sẽ dùng giá trị mới ở lần chạy kế tiếp.",
            GREEN,
        )
        if self._on_saved:
            self._on_saved(config)

    def _reset(self):
        try:
            config = reset_ic_config()
        except Exception as exc:
            self._set_status(f"❌ Không thể khôi phục cấu hình: {exc}", RED)
            return
        self._config = config
        self._p_var.set(self._fmt_p(config["edge_probability"]))
        self._mc_search_var.set(str(config["mc_search"]))
        self._mc_val_var.set(str(config["mc_validation"]))
        self._seed_search_var.set(str(config["seed_search"]))
        self._seed_val_var.set(str(config["seed_validation"]))
        self._refresh_summary(config)
        self._set_status(
            "↺ Đã khôi phục cấu hình IC mặc định (p=0.1, R_search=200, R_val=1.000).",
            ORANGE,
        )
        if self._on_saved:
            self._on_saved(config)

    def _refresh_summary(self, config: Dict[str, Any]):
        values = {
            "model": "IC",
            "edge_probability": self._fmt_p(config["edge_probability"]),
            "mc_search": f"{config['mc_search']:,}",
            "mc_validation": f"{config['mc_validation']:,}",
            "seed_search": str(config["seed_search"]),
            "seed_validation": str(config["seed_validation"]),
        }
        for key, label in self._summary_labels.items():
            label.configure(text=values.get(key, ""))

    def _set_status(self, text: str, color):
        if self._status_label is not None:
            self._status_label.configure(text=text, text_color=color)
