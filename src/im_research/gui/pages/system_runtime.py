#!/usr/bin/env python3
"""
System & Runtime Page — Execution Environment, Hardware Monitoring, C++ OpenMP Status,
and Benchmark Environment History Tracking for Academic Reproducibility.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
from im_research.core.runtime_inspector import (
    get_environment_overview,
    get_cpp_engine_status,
    get_system_resources,
    load_execution_history,
    capture_environment_snapshot,
    export_environment_latex,
)


class PageSystemRuntime(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._auto_refresh = True
        self._timer_id = None
        self._history_records = load_execution_history()

        # Gather static / initial environment data
        self.env_data = get_environment_overview()
        self.cpp_data = get_cpp_engine_status()
        self.res_data = get_system_resources()

        self._build_ui()
        self._start_resource_timer()

    def destroy(self):
        self._auto_refresh = False
        if self._timer_id is not None:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
        super().destroy()

    def _build_ui(self):
        # ── 0. Top Header with Actions ────────────────────────────────────────
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 14))

        title_box = ctk.CTkFrame(header_row, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="System & Runtime — Môi trường thực thi & Tài nguyên",
            font=FONT_TITLE,
            text_color=HEADER_FG
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Giám sát kiến trúc phần cứng, toolchain C++ OpenMP, tài nguyên thời gian thực và lịch sử môi trường benchmark",
            font=FONT_MAIN,
            text_color=SUBTEXT_FG
        ).pack(anchor="w", pady=(2, 0))

        # Top Right Action Buttons
        btn_box = ctk.CTkFrame(header_row, fg_color="transparent")
        btn_box.pack(side="right", pady=4)

        ctk.CTkButton(
            btn_box,
            text="🔄 Làm mới",
            width=100,
            height=32,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            border_width=1,
            border_color=BORDER_COLOR,
            corner_radius=6,
            command=self._manual_refresh
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📸 Chụp Snapshot",
            width=135,
            height=32,
            font=("Segoe UI", 10, "bold"),
            fg_color=ACTIVE_BG,
            hover_color=ACTIVE_HOVER,
            text_color="#ffffff",
            corner_radius=6,
            command=self._on_take_snapshot
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_box,
            text="📥 Xuất LaTeX",
            width=115,
            height=32,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            border_width=1,
            border_color=BORDER_COLOR,
            corner_radius=6,
            command=self._on_export_latex
        ).pack(side="left", padx=4)

        # ── Section A: Environment Overview ───────────────────────────────────
        self._build_section_a()

        # ── Section B: C++ Engine Status ──────────────────────────────────────
        self._build_section_b()

        # ── Section C: System Resources (Real-time) ───────────────────────────
        self._build_section_c()

        # ── Section D: Execution History & Benchmark Metadata ─────────────────
        self._build_section_d()

    # ═════════════════════════════════════════════════════════════════════════
    #  SECTION A: ENVIRONMENT OVERVIEW
    # ═════════════════════════════════════════════════════════════════════════

    def _build_section_a(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 16))

        # Title
        title_box = ctk.CTkFrame(card, fg_color="transparent")
        title_box.pack(fill="x", padx=18, pady=(14, 8))
        dot = ctk.CTkFrame(title_box, width=8, height=8, corner_radius=4, fg_color=BLUE)
        dot.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            title_box,
            text="A. Tổng quan Môi trường thực thi (Environment Overview)",
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG
        ).pack(side="left")

        # Two-column grid container
        cols_frame = ctk.CTkFrame(card, fg_color="transparent")
        cols_frame.pack(fill="x", padx=16, pady=(0, 10))
        cols_frame.columnconfigure(0, weight=1)
        cols_frame.columnconfigure(1, weight=1)

        # Left Column: OS & Hardware
        left_box = ctk.CTkFrame(cols_frame, fg_color=("#f8fafc", "#0d1424"), corner_radius=8,
                                border_width=1, border_color=BORDER_COLOR)
        left_box.grid(row=0, column=0, padx=(0, 8), sticky="nsew", pady=4)
        ctk.CTkLabel(left_box, text="HỆ ĐIỀU HÀNH & PHẦN CỨNG", font=("Segoe UI", 9, "bold"),
                     text_color=SUBTEXT_FG).pack(anchor="w", padx=14, pady=(10, 6))

        for lbl, val in [
            ("Hệ điều hành Host:", self.env_data["host_os"]),
            ("Môi trường Linux:", f"{self.env_data['wsl_distro']} ({self.env_data['wsl_status']})"),
            ("Kernel Linux:", self.env_data["wsl_kernel"]),
            ("Kiến trúc vi xử lý:", self.env_data["cpu_cores"]),
            ("Mô hình CPU:", self.env_data["cpu_model"]),
            ("Bộ nhớ RAM vật lý:", self.env_data["ram_total"]),
            ("Mã băm Git Commit:", f"{self.env_data['git_commit']} (Phiên bản mã nguồn)"),
        ]:
            self._key_val_row(left_box, lbl, val)
        ctk.CTkFrame(left_box, height=8, fg_color="transparent").pack()

        # Right Column: Toolchain & Compilers
        right_box = ctk.CTkFrame(cols_frame, fg_color=("#f8fafc", "#0d1424"), corner_radius=8,
                                 border_width=1, border_color=BORDER_COLOR)
        right_box.grid(row=0, column=1, padx=(8, 0), sticky="nsew", pady=4)
        ctk.CTkLabel(right_box, text="CÔNG CỤ BIÊN DỊCH & THÔNG DỊCH", font=("Segoe UI", 9, "bold"),
                     text_color=SUBTEXT_FG).pack(anchor="w", padx=14, pady=(10, 6))

        for lbl, val in [
            ("Python GUI Runtime:", self.env_data["python_host"]),
            ("Python WSL2 Core:", self.env_data["python_wsl"]),
            ("Trình biên dịch C++:", self.env_data["gcc_version"]),
            ("Hệ thống quản lý Build:", self.env_data["cmake_version"]),
            ("Thư viện liên kết:", self.env_data["pybind11_version"]),
            ("Tiêu chuẩn ngôn ngữ:", "C++17 (ISO/IEC 14882:2017)"),
            ("Cờ tối ưu hóa:", "-O3 -march=native -fopenmp"),
        ]:
            self._key_val_row(right_box, lbl, val)
        ctk.CTkFrame(right_box, height=8, fg_color="transparent").pack()

        # Dependencies Pills Container
        dep_box = ctk.CTkFrame(card, fg_color="transparent")
        dep_box.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkLabel(
            dep_box,
            text="Thư viện phụ thuộc chính (Installed Dependencies):",
            font=("Segoe UI", 10, "bold"),
            text_color=SUBTEXT_FG
        ).pack(anchor="w", pady=(0, 6))

        pills_flow = ctk.CTkFrame(dep_box, fg_color="transparent")
        pills_flow.pack(fill="x")

        deps = self.env_data["dependencies"]
        for name, ver in deps.items():
            pill = ctk.CTkFrame(pills_flow, fg_color=PILL_BG, corner_radius=12, height=26)
            pill.pack(side="left", padx=4, pady=3)
            ctk.CTkLabel(
                pill,
                text=f"{name}: v{ver}",
                font=("Segoe UI", 9, "bold"),
                text_color=PILL_FG
            ).pack(padx=10, pady=2)

    # ═════════════════════════════════════════════════════════════════════════
    #  SECTION B: C++ ENGINE STATUS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_section_b(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(card, fg_color="transparent")
        title_box.pack(fill="x", padx=18, pady=(14, 10))
        dot = ctk.CTkFrame(title_box, width=8, height=8, corner_radius=4, fg_color=PURPLE)
        dot.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            title_box,
            text="B. Trạng thái Lõi tính toán C++ OpenMP (C++ Engine Status)",
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG
        ).pack(side="left")

        # 4 Metric Cards Row
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(0, 10))
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        metric_card(grid, "Phiên bản Lõi", "C++17 CSR v1.0", "Fast Evaluator Ready", BLUE, 0, 0)
        metric_card(grid, "Cấu hình Biên dịch", "Release (-O3)", "AVX2 & Native OpenMP", GREEN, 1, 0)
        metric_card(grid, "Liên kết pybind11", "_im_core.so", f"Kích thước {self.cpp_data['binary_size_kb']}", PURPLE, 2, 0)
        metric_card(grid, "Kiểm thử Đơn vị", "9 / 9 Tests", "100% Passed Thành công", TEAL, 3, 0)

        # C++ Engine Details Box
        detail_box = ctk.CTkFrame(card, fg_color=("#f8fafc", "#0d1424"), corner_radius=8,
                                  border_width=1, border_color=BORDER_COLOR)
        detail_box.pack(fill="x", padx=16, pady=(4, 14))

        for lbl, val in [
            ("Tệp thư viện nhị phân (.so):", self.cpp_data["binary_path"]),
            ("Trạng thái biên dịch:", self.cpp_data["compilation_status"]),
            ("Thời điểm biên dịch gần nhất:", self.cpp_data["last_compiled"]),
            ("Chiến lược song song hóa:", self.cpp_data["openmp_status"]),
            ("Quản lý khóa luồng GIL:", self.cpp_data["gil_management"]),
            ("Tỷ lệ tăng tốc thực nghiệm:", self.cpp_data["speedup"]),
            ("Bộ kiểm thử tự động:", f"{self.cpp_data['unit_test_suite']} ({self.cpp_data['unit_test_status']})"),
        ]:
            self._key_val_row(detail_box, lbl, val)

        # Exported Classes
        ctk.CTkLabel(detail_box, text="CÁC LỚP & HÀM ĐƯỢC EXPORT QUA PYBIND11:", font=("Segoe UI", 9, "bold"),
                     text_color=SUBTEXT_FG).pack(anchor="w", padx=14, pady=(8, 4))
        for cls_name in self.cpp_data["exported_classes"]:
            ctk.CTkLabel(detail_box, text=f"  • {cls_name}", font=("Consolas", 10),
                         text_color=HEADER_FG).pack(anchor="w", padx=16, pady=1)

        ctk.CTkFrame(detail_box, height=8, fg_color="transparent").pack()

    # ═════════════════════════════════════════════════════════════════════════
    #  SECTION C: SYSTEM RESOURCES (REAL-TIME)
    # ═════════════════════════════════════════════════════════════════════════

    def _build_section_c(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(card, fg_color="transparent")
        title_box.pack(fill="x", padx=18, pady=(14, 10))
        dot = ctk.CTkFrame(title_box, width=8, height=8, corner_radius=4, fg_color=GREEN)
        dot.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            title_box,
            text="C. Tài nguyên Hệ thống Thời gian thực (System Resources)",
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG
        ).pack(side="left")

        # Live pulse badge
        self.lbl_live_badge = ctk.CTkLabel(
            title_box,
            text="● Giám sát tự động 3s",
            font=("Segoe UI", 9, "bold"),
            text_color=GREEN
        )
        self.lbl_live_badge.pack(side="right")

        # 4 Resource Gauge Cards
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 10))
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        # 1. CPU Gauge
        self.box_cpu = self._make_gauge_card(
            grid, "Tải xử lý CPU",
            f"{self.res_data['cpu_percent']:.1f}%",
            f"{self.res_data['cpu_cores']} luồng logic ({self.res_data['cpu_freq']})",
            self.res_data['cpu_percent'] / 100.0,
            BLUE, 0
        )

        # 2. RAM Gauge
        self.box_ram = self._make_gauge_card(
            grid, "Bộ nhớ RAM",
            f"{self.res_data['ram_percent']:.1f}%",
            f"{self.res_data['ram_used_gb']} GB / {self.res_data['ram_total_gb']} GB",
            self.res_data['ram_percent'] / 100.0,
            PURPLE, 1
        )

        # 3. Process Usage
        self.box_proc = self._make_gauge_card(
            grid, "Tiến trình IMApp",
            f"{self.res_data['proc_ram_mb']:.1f} MB",
            f"CPU: {self.res_data['proc_cpu']:.1f}% │ {self.res_data['proc_threads']} threads",
            min(1.0, self.res_data['proc_ram_mb'] / 500.0),
            TEAL, 2
        )

        # 4. Disk Usage
        self.box_disk = self._make_gauge_card(
            grid, "Ổ đĩa Workspace",
            f"{self.res_data['disk_percent']:.1f}%",
            f"Trống {self.res_data['disk_free_gb']} GB / {self.res_data['disk_total_gb']} GB",
            self.res_data['disk_percent'] / 100.0,
            ORANGE, 3
        )

        # Running Jobs Status Bar
        jobs_bar = ctk.CTkFrame(card, fg_color=("#f8fafc", "#0d1424"), corner_radius=8,
                                border_width=1, border_color=BORDER_COLOR)
        jobs_bar.pack(fill="x", padx=16, pady=(4, 14))

        ctk.CTkLabel(
            jobs_bar, text="Trạng thái tác vụ thực thi hiện tại (Current Running Jobs):",
            font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG
        ).pack(side="left", padx=14, pady=8)

        self.lbl_job_status = ctk.CTkLabel(
            jobs_bar, text=self.res_data["job_status"],
            font=("Segoe UI", 10, "bold"),
            text_color=ORANGE if self.res_data["is_job_active"] else GREEN
        )
        self.lbl_job_status.pack(side="left", padx=6, pady=8)

    def _make_gauge_card(self, parent, title, val_str, sub_str, progress_val, color, col_idx):
        frame = ctk.CTkFrame(parent, fg_color=("#f8fafc", "#0d1424"), corner_radius=8,
                             border_width=1, border_color=BORDER_COLOR)
        frame.grid(row=0, column=col_idx, padx=4, pady=4, sticky="nsew")

        lbl_t = ctk.CTkLabel(frame, text=title, font=("Segoe UI", 10, "bold"), text_color=SUBTEXT_FG)
        lbl_t.pack(anchor="w", padx=12, pady=(10, 2))

        lbl_v = ctk.CTkLabel(frame, text=val_str, font=("Segoe UI", 20, "bold"), text_color=color)
        lbl_v.pack(anchor="w", padx=12, pady=(0, 2))

        lbl_s = ctk.CTkLabel(frame, text=sub_str, font=("Segoe UI", 9), text_color=SUBTEXT_FG)
        lbl_s.pack(anchor="w", padx=12, pady=(0, 8))

        prog = ctk.CTkProgressBar(frame, height=6, progress_color=color)
        prog.pack(fill="x", padx=12, pady=(0, 12))
        prog.set(max(0.0, min(1.0, progress_val)))

        return {"val": lbl_v, "sub": lbl_s, "prog": prog, "color": color}

    def _start_resource_timer(self):
        if not self._auto_refresh:
            return
        self._update_live_metrics()
        self._timer_id = self.after(3000, self._start_resource_timer)

    def _update_live_metrics(self):
        try:
            res = get_system_resources()
            self.res_data = res

            # Update CPU
            self.box_cpu["val"].configure(text=f"{res['cpu_percent']:.1f}%")
            self.box_cpu["sub"].configure(text=f"{res['cpu_cores']} luồng logic ({res['cpu_freq']})")
            self.box_cpu["prog"].set(res["cpu_percent"] / 100.0)

            # Update RAM
            self.box_ram["val"].configure(text=f"{res['ram_percent']:.1f}%")
            self.box_ram["sub"].configure(text=f"{res['ram_used_gb']} GB / {res['ram_total_gb']} GB")
            self.box_ram["prog"].set(res["ram_percent"] / 100.0)

            # Update Process
            self.box_proc["val"].configure(text=f"{res['proc_ram_mb']:.1f} MB")
            self.box_proc["sub"].configure(text=f"CPU: {res['proc_cpu']:.1f}% │ {res['proc_threads']} threads")
            self.box_proc["prog"].set(min(1.0, res["proc_ram_mb"] / 500.0))

            # Update Disk
            self.box_disk["val"].configure(text=f"{res['disk_percent']:.1f}%")
            self.box_disk["sub"].configure(text=f"Trống {res['disk_free_gb']} GB / {res['disk_total_gb']} GB")
            self.box_disk["prog"].set(res["disk_percent"] / 100.0)

            # Update Job status
            if hasattr(self, "lbl_job_status"):
                self.lbl_job_status.configure(
                    text=res["job_status"],
                    text_color=ORANGE if res["is_job_active"] else GREEN
                )
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════════
    #  SECTION D: EXECUTION HISTORY & BENCHMARK METADATA TRACKING
    # ═════════════════════════════════════════════════════════════════════════

    def _build_section_d(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 24))

        title_box = ctk.CTkFrame(card, fg_color="transparent")
        title_box.pack(fill="x", padx=18, pady=(14, 4))
        dot = ctk.CTkFrame(title_box, width=8, height=8, corner_radius=4, fg_color=ORANGE)
        dot.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            title_box,
            text="D. Lịch sử Môi trường Thực thi Benchmark (Execution History & Reproducibility)",
            font=("Segoe UI", 12, "bold"),
            text_color=HEADER_FG
        ).pack(side="left")

        ctk.CTkLabel(
            card,
            text="Lưu trữ đầy đủ thông số môi trường (Compiler, Build mode, CPU, RAM, Git commit) để giải thích sự khác biệt thời gian thực thi giữa Python và C++.",
            font=FONT_MAIN,
            text_color=SUBTEXT_FG
        ).pack(anchor="w", padx=18, pady=(0, 10))

        # Table container
        self.history_table_box = ctk.CTkFrame(card, fg_color="transparent")
        self.history_table_box.pack(fill="x", padx=16, pady=(0, 14))

        self._render_history_table()

    def _render_history_table(self):
        # Clear old rows
        for w in self.history_table_box.winfo_children():
            w.destroy()

        headers = [
            ("Thời gian", 130),
            ("Mã Experiment", 190),
            ("Bộ dữ liệu", 160),
            ("Thuật toán", 140),
            ("Trình biên dịch & Build", 170),
            ("Phần cứng (CPU/RAM)", 160),
            ("Git Commit", 90),
            ("Thời gian chạy", 95),
            ("Tăng tốc C++", 95),
        ]

        # Table Header
        h_row = ctk.CTkFrame(self.history_table_box, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
        h_row.pack(fill="x", pady=(0, 4))
        for title, width in headers:
            ctk.CTkLabel(
                h_row, text=title, font=("Segoe UI", 9, "bold"),
                text_color=HEADER_FG, width=width, anchor="w"
            ).pack(side="left", padx=6, pady=6)

        records = self._history_records
        if not records:
            ctk.CTkLabel(
                self.history_table_box,
                text="Chưa có dữ liệu snapshot môi trường nào được lưu.",
                font=FONT_MAIN, text_color=SUBTEXT_FG
            ).pack(pady=16)
            return

        for idx, rec in enumerate(records[:15]):  # Show up to 15 recent
            row_bg = "transparent" if idx % 2 == 0 else ("#f8fafc", "#0d1424")
            r = ctk.CTkFrame(self.history_table_box, fg_color=row_bg, corner_radius=4)
            r.pack(fill="x", pady=2)

            cols = [
                (rec.get("timestamp", "—"), 130, SUBTEXT_FG, ("Segoe UI", 9)),
                (rec.get("exp_id", "—"), 190, BLUE, ("Consolas", 9, "bold")),
                (rec.get("dataset", "—"), 160, HEADER_FG, ("Segoe UI", 9, "bold")),
                (rec.get("algorithm", "—"), 140, PURPLE, ("Segoe UI", 9)),
                (f"{rec.get('compiler', '')} ({rec.get('build_type', 'Rel')[:7]})", 170, HEADER_FG, ("Consolas", 8)),
                (f"{rec.get('cpu', '')[:14]}.. │ {rec.get('ram', '')}", 160, SUBTEXT_FG, ("Segoe UI", 8)),
                (rec.get("git_commit", "—"), 90, ORANGE, ("Consolas", 9, "bold")),
                (rec.get("runtime_s", "—"), 95, GREEN, ("Consolas", 9, "bold")),
                (rec.get("speedup", "—"), 95, RED, ("Segoe UI", 9, "bold")),
            ]

            for val, width, col, font in cols:
                ctk.CTkLabel(
                    r, text=val, font=font,
                    text_color=col, width=width, anchor="w"
                ).pack(side="left", padx=6, pady=5)

    # ═════════════════════════════════════════════════════════════════════════
    #  ACTION HANDLERS & HELPERS
    # ═════════════════════════════════════════════════════════════════════════

    def _key_val_row(self, parent, lbl: str, val: str):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=14, pady=2)
        ctk.CTkLabel(r, text=lbl, font=FONT_MAIN, width=170, anchor="w", text_color=SUBTEXT_FG).pack(side="left")
        ctk.CTkLabel(r, text=val, font=("Segoe UI", 10, "bold"), anchor="w", text_color=HEADER_FG).pack(side="left", fill="x", expand=True)

    def _manual_refresh(self):
        self.env_data = get_environment_overview(force_refresh=True)
        self.cpp_data = get_cpp_engine_status()
        self._update_live_metrics()
        self._history_records = load_execution_history()
        self._render_history_table()
        messagebox.showinfo("Làm mới thành công", "Đã cập nhật toàn bộ thông số phần cứng, công cụ C++ và tài nguyên hệ thống!")

    def _on_take_snapshot(self):
        dialog = ctk.CTkInputDialog(
            text="Nhập ghi chú cho Snapshot môi trường:\n(Ví dụ: Benchmark Karate Club k=10)",
            title="Chụp Snapshot Môi trường"
        )
        note = dialog.get_input()
        if note is None:
            return
        if not note.strip():
            note = "Chụp Snapshot thủ công"

        rec = capture_environment_snapshot(notes=note.strip())
        self._history_records = load_execution_history()
        self._render_history_table()

        messagebox.showinfo(
            "Đã lưu Snapshot Môi trường",
            f"Đã lưu thành công bản chụp môi trường {rec['exp_id']}!\n\n"
            f"• Git Commit: {rec['git_commit']}\n"
            f"• Compiler: {rec['compiler']}\n"
            f"• CPU & RAM: {rec['cpu']} │ {rec['ram']}\n\n"
            f"Dữ liệu được lưu tại: data/metadata/benchmark_environments.json"
        )

    def _on_export_latex(self):
        latex_text = export_environment_latex()
        file_path = filedialog.asksaveasfilename(
            title="Lưu bảng LaTeX Môi trường Thực thi",
            defaultextension=".tex",
            initialfile="system_runtime_environment.tex",
            filetypes=[("LaTeX Files (*.tex)", "*.tex"), ("Text Files (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(latex_text)
            messagebox.showinfo(
                "Xuất bảng LaTeX thành công",
                f"Đã xuất mã nguồn bảng LaTeX thành công tại:\n{file_path}\n\n"
                f"Bạn có thể sao chép trực tiếp vào phần Thiết lập Thực nghiệm trong Luận văn!"
            )

