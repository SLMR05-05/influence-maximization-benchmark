#!/usr/bin/env python3
"""Dashboard Page — Platform Overview, Metrics & Algorithm Library."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card, create_empty_state

ALGORITHMS = [
    {
        "name": "IGA (Improved Genetic Algorithm)",
        "group": "Metaheuristic (Đề xuất)",
        "complexity": "O(G · pop · k · MC)",
        "description": "Thuật toán đề xuất: Lai ghép thích nghi 2 điểm, đột biến đa thức, bảo tồn cá thể ưu tú",
        "status": "Sẵn sàng",
        "color": RED,
    },
    {
        "name": "CELF (Cost-Effective Lazy Forward)",
        "group": "Greedy Approximation",
        "complexity": "O(k · |V| · MC)",
        "description": "Chuẩn cận tối ưu (1 - 1/e): Tận dụng tính cận mô-đun để tỉa nhánh đánh giá lười",
        "status": "Sẵn sàng",
        "color": BLUE,
    },
    {
        "name": "GA (Standard Genetic Algorithm)",
        "group": "Metaheuristic Baseline",
        "complexity": "O(G · pop · k · MC)",
        "description": "Thuật giải di truyền tiêu chuẩn: Chọn lọc bánh xe roulette, đột biến phân bố đều",
        "status": "Sẵn sàng",
        "color": ORANGE,
    },
    {
        "name": "Degree Discount",
        "group": "Topological Heuristic",
        "complexity": "O(k log |V| + |E|)",
        "description": "Heuristic đồ thị: Giảm bậc lân cận của đỉnh đã chọn để hạn chế trùng lặp lan truyền",
        "status": "Sẵn sàng",
        "color": GREEN,
    },
    {
        "name": "PageRank",
        "group": "Graph Centrality",
        "complexity": "O(I · (|V| + |E|))",
        "description": "Thước đo độ trung tâm ngẫu nhiên: Random walk với hệ số cản d = 0.85",
        "status": "Sẵn sàng",
        "color": PURPLE,
    },
    {
        "name": "Degree (Max Degree)",
        "group": "Baseline Heuristic",
        "complexity": "O(|V| log k)",
        "description": "Heuristic cơ sở: Lựa chọn k đỉnh có bậc liên kết cao nhất trên toàn đồ thị",
        "status": "Sẵn sàng",
        "color": SUBTEXT_FG,
    },
]


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

        # Count real runs in runs directory
        runs_dir = PROJECT_ROOT / "runs"
        exp_count = len(list(runs_dir.glob("EXP_*"))) if runs_dir.exists() else 0

        # ── Stat Cards Grid ───────────────────────────────────────────────────
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 14))
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        metric_card(grid, "Tổng số thí nghiệm", str(exp_count), f"{exp_count} lượt chạy hoàn thành", BLUE if exp_count > 0 else SUBTEXT_FG, 0, 0)
        metric_card(grid, "Bộ dữ liệu chuẩn", "5 / 5", "Dữ liệu gốc sẵn sàng", GREEN, 1, 0)
        metric_card(grid, "C++ Core Engine", "OpenMP", "Đa luồng song song", PURPLE, 2, 0)
        metric_card(grid, "Thuật toán thư viện", "6", "IGA + 5 Baselines", RED, 3, 0)

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

        # ── Recent Experiments Card (Shows Empty State Image if no runs) ──────
        section_header(self, "Thí nghiệm gần nhất (Recent Experiments)", "Lượt chạy thực nghiệm mới nhất được ghi nhận")
        exp_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
        exp_card.pack(fill="x", pady=(0, 16))

        latest_results = PROJECT_ROOT / "runs" / "latest_results.json"
        if latest_results.exists() and exp_count > 0:
            pass
        else:
            create_empty_state(
                parent=exp_card,
                title="Chưa có lượt chạy thí nghiệm nào",
                subtitle="Hệ thống đã chuẩn bị sẵn 5 bộ dữ liệu gốc và lõi C++ OpenMP. Hãy tạo lượt chạy mới để ghi nhận dữ liệu.",
                action_text="Khởi chạy thí nghiệm ngay ▶",
                action_command=lambda: self.on_switch_tab("experiments"),
                pady=28
            )

        # ── Benchmark Algorithms Overview Table ───────────────────────────────
        section_header(self, "Danh sách thuật toán trong thư viện", "Phân loại theo cơ chế tối ưu hóa và độ phức tạp tính toán")

        tbl = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                           border_width=1, border_color=BORDER_COLOR)
        tbl.pack(fill="x", pady=(0, 16))

        headers = ["Thuật toán", "Nhóm", "Độ phức tạp", "Mô tả cơ chế", "Trạng thái"]
        for c, h in enumerate(headers):
            tbl.columnconfigure(c, weight=2 if c == 3 else (1 if c == 0 else 0))
            ctk.CTkLabel(tbl, text=h, font=("Segoe UI", 10, "bold"),
                         text_color=SUBTEXT_FG).grid(row=0, column=c, padx=14, pady=10, sticky="w")

        ctk.CTkFrame(tbl, height=1, fg_color=BORDER_COLOR).grid(
            row=1, column=0, columnspan=len(headers), sticky="ew", padx=8)

        for r_idx, algo in enumerate(ALGORITHMS, start=2):
            ctk.CTkLabel(tbl, text=algo["name"], font=("Segoe UI", 11, "bold"), text_color=algo["color"]).grid(row=r_idx, column=0, padx=14, pady=8, sticky="w")
            ctk.CTkLabel(tbl, text=algo["group"], font=FONT_MAIN, text_color=HEADER_FG).grid(row=r_idx, column=1, padx=14, pady=8, sticky="w")
            ctk.CTkLabel(tbl, text=algo["complexity"], font=("Consolas", 10), text_color=SUBTEXT_FG).grid(row=r_idx, column=2, padx=14, pady=8, sticky="w")
            ctk.CTkLabel(tbl, text=algo["description"], font=FONT_MAIN, text_color=SUBTEXT_FG).grid(row=r_idx, column=3, padx=14, pady=8, sticky="w")
            ctk.CTkLabel(tbl, text=algo["status"], font=("Segoe UI", 10, "bold"), text_color=GREEN).grid(row=r_idx, column=4, padx=14, pady=8, sticky="w")
            ctk.CTkFrame(tbl, height=1, fg_color=BORDER_COLOR).grid(row=r_idx+1, column=0, columnspan=len(headers), sticky="ew", padx=10, pady=1)
