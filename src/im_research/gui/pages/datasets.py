#!/usr/bin/env python3
"""
Datasets Page — Benchmark Graphs & 3D Knowledge Graph Explorer.
Presents authentic benchmark and custom datasets with exact topological metrics,
accompanied by dataset management (Import, Auto-analysis, Deletion) and
the interactive 3D Force-Directed Network Graph viewer.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
from im_research.gui.components.ic_config_view import ICConfigView
from im_research.gui.visualization.graph_explorer_view import GraphExplorerView
from im_research.data.config_loader import (
    load_all_dataset_configs,
    generate_config_from_edgelist,
    delete_dataset_config,
    _format_vi_number,
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Fallback Benchmark Datasets Metadata Specification
BENCHMARK_DATASETS = [
    {
        "name": "Karate Club",
        "file": "karate.txt",
        "raw_path": str(RAW_DIR / "karate.txt"),
        "raw_n": 34,
        "raw_m": 78,
        "raw_avg_deg": 4.59,
        "raw_clustering": 0.571,
        "n": "34",
        "m": "78",
        "avg_deg": "4,59",
        "clustering": "0,571",
        "diameter": "5",
        "category": "Mạng xã hội nhỏ",
        "source": "Zachary (1977)",
        "badge_color": "#10b981",
        "is_protected": True,
        "exists_on_disk": (RAW_DIR / "karate.txt").exists(),
    },
    {
        "name": "Dolphins",
        "file": "dolphins.txt",
        "raw_path": str(RAW_DIR / "dolphins.txt"),
        "raw_n": 62,
        "raw_m": 159,
        "raw_avg_deg": 5.13,
        "raw_clustering": 0.259,
        "n": "62",
        "m": "159",
        "avg_deg": "5,13",
        "clustering": "0,259",
        "diameter": "8",
        "category": "Mạng quan hệ xã hội",
        "source": "Lusseau (2003)",
        "badge_color": "#0284c7",
        "is_protected": True,
        "exists_on_disk": (RAW_DIR / "dolphins.txt").exists(),
    },
    {
        "name": "ego-Facebook",
        "file": "facebook.txt",
        "raw_path": str(RAW_DIR / "facebook.txt"),
        "raw_n": 4039,
        "raw_m": 88234,
        "raw_avg_deg": 43.69,
        "raw_clustering": 0.605,
        "n": "4.039",
        "m": "88.234",
        "avg_deg": "43,69",
        "clustering": "0,605",
        "diameter": "8",
        "category": "Mạng xã hội trực tuyến",
        "source": "SNAP [8]",
        "badge_color": "#2563eb",
        "is_protected": True,
        "exists_on_disk": (RAW_DIR / "facebook.txt").exists(),
    },
    {
        "name": "NetHEPT",
        "file": "nethept.txt",
        "raw_path": str(RAW_DIR / "nethept.txt"),
        "raw_n": 15233,
        "raw_m": 58891,
        "raw_avg_deg": 7.73,
        "raw_clustering": 0.659,
        "n": "15.233",
        "m": "58.891",
        "avg_deg": "7,73",
        "clustering": "0,659",
        "diameter": "15",
        "category": "Mạng đồng tác giả học thuật",
        "source": "arXiv / SNAP [15]",
        "badge_color": "#8b5cf6",
        "is_protected": True,
        "exists_on_disk": (RAW_DIR / "nethept.txt").exists(),
    },
    {
        "name": "Email-Enron",
        "file": "enron.txt",
        "raw_path": str(RAW_DIR / "enron.txt"),
        "raw_n": 36692,
        "raw_m": 183831,
        "raw_avg_deg": 10.02,
        "raw_clustering": 0.497,
        "n": "36.692",
        "m": "183.831",
        "avg_deg": "10,02",
        "clustering": "0,497",
        "diameter": "11",
        "category": "Mạng truyền thông thư điện tử",
        "source": "SNAP [8]",
        "badge_color": "#f59e0b",
        "is_protected": True,
        "exists_on_disk": (RAW_DIR / "enron.txt").exists(),
    },
]


class ImportDatasetModal(ctk.CTkToplevel):
    """Modal dialog for importing external graph edge-lists and computing topology metrics."""
    def __init__(self, master, on_success_callback=None):
        super().__init__(master)
        self.title("Nhập bộ dữ liệu đồ thị mới (Graph Dataset Import)")
        self.geometry("540x510")
        self.resizable(False, False)
        self.configure(fg_color=BG_APP)
        self.transient(master)
        self.grab_set()

        self.on_success_callback = on_success_callback
        self.selected_file_path: Optional[Path] = None

        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(18, 12))
        ctk.CTkLabel(hdr, text="Nhập bộ dữ liệu đồ thị mới", font=("Segoe UI", 15, "bold"), text_color=HEADER_FG).pack(anchor="w")
        ctk.CTkLabel(
            hdr,
            text="Hệ thống sẽ tự động phân tích số đỉnh (n), cạnh (m), bậc TB và hệ số cụm",
            font=FONT_MAIN, text_color=SUBTEXT_FG
        ).pack(anchor="w", pady=(2, 0))

        # Form Card
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", padx=20, pady=(0, 14))

        # 1. File Picker
        f_box = ctk.CTkFrame(card, fg_color="transparent")
        f_box.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(f_box, text="Tệp danh sách cạnh (.txt / .edgelist / .csv):", font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(anchor="w", pady=(0, 4))

        f_row = ctk.CTkFrame(f_box, fg_color="transparent")
        f_row.pack(fill="x")
        self.ent_file = ctk.CTkEntry(f_row, placeholder_text="Chưa chọn tệp...", height=32, state="readonly")
        self.ent_file.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(f_row, text="Duyệt tệp...", width=95, height=32, fg_color=BLUE, hover_color="#1557b0", command=self._browse_file).pack(side="right")

        # 2. Dataset Name
        n_box = ctk.CTkFrame(card, fg_color="transparent")
        n_box.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(n_box, text="Tên bộ dữ liệu:", font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(anchor="w", pady=(0, 4))
        self.ent_name = ctk.CTkEntry(n_box, placeholder_text="Ví dụ: Polblogs, Wiki-Vote, Twitter-Sample...", height=32)
        self.ent_name.pack(fill="x")

        # 3. Category / Classification
        c_box = ctk.CTkFrame(card, fg_color="transparent")
        c_box.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(c_box, text="Phân loại mạng lưới:", font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(anchor="w", pady=(0, 4))
        self.cat_var = ctk.StringVar(value="Mạng xã hội")
        self.opt_category = ctk.CTkOptionMenu(
            c_box, variable=self.cat_var, height=32,
            values=[
                "Mạng xã hội",
                "Mạng quan hệ xã hội",
                "Mạng xã hội trực tuyến",
                "Mạng đồng tác giả học thuật",
                "Mạng truyền thông thư điện tử",
                "Mạng liên kết web / Thông tin",
                "Đồ thị mạng phức hợp",
            ]
        )
        self.opt_category.pack(fill="x")

        # 4. Source
        s_box = ctk.CTkFrame(card, fg_color="transparent")
        s_box.pack(fill="x", padx=16, pady=(8, 16))
        ctk.CTkLabel(s_box, text="Nguồn dữ liệu / Tác giả:", font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(anchor="w", pady=(0, 4))
        self.ent_source = ctk.CTkEntry(s_box, placeholder_text="Ví dụ: SNAP Stanford, Mark Newman, Tự tạo...", height=32)
        self.ent_source.pack(fill="x")

        # Status Label
        self.lbl_status = ctk.CTkLabel(self, text="", font=FONT_MAIN, text_color=SUBTEXT_FG)
        self.lbl_status.pack(fill="x", padx=20, pady=(0, 10))

        # Action Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(
            btn_box, text="Hủy", width=90, height=34,
            fg_color=("#e2e8f0", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            hover_color=("#cbd5e1", "#475569"),
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        self.btn_submit = ctk.CTkButton(
            btn_box, text="🚀 Phân tích & Lưu bộ dữ liệu", height=34,
            fg_color=GREEN, hover_color="#059669",
            text_color="#ffffff",
            font=("Segoe UI", 11, "bold"),
            command=self._submit
        )
        self.btn_submit.pack(side="right")

    def _browse_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Chọn tệp danh sách cạnh đồ thị (Edge-list)",
            filetypes=[
                ("Tệp đồ thị danh sách cạnh", "*.txt *.edges *.edgelist *.csv"),
                ("Tất cả tệp", "*.*")
            ]
        )
        if path:
            self.selected_file_path = Path(path)
            self.ent_file.configure(state="normal")
            self.ent_file.delete(0, "end")
            self.ent_file.insert(0, str(self.selected_file_path))
            self.ent_file.configure(state="readonly")
            if not self.ent_name.get().strip():
                stem = self.selected_file_path.stem.replace("_", " ").replace("-", " ").title()
                self.ent_name.insert(0, stem)

    def _submit(self):
        if not self.selected_file_path or not self.selected_file_path.exists():
            messagebox.showwarning("Thiếu tệp dữ liệu", "Vui lòng chọn tệp danh sách cạnh đồ thị (.txt).", parent=self)
            return

        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("Thiếu tên bộ dữ liệu", "Vui lòng nhập tên cho bộ dữ liệu đồ thị.", parent=self)
            return

        category = self.cat_var.get()
        source = self.ent_source.get().strip() or "Tải lên từ người dùng"

        self.lbl_status.configure(text="⏳ Đang đọc đồ thị và tính toán các chỉ số topo học (n, m, k, C)...", text_color=BLUE)
        self.btn_submit.configure(state="disabled")
        self.update_idletasks()

        try:
            cfg = generate_config_from_edgelist(
                name=name,
                edgelist_path=self.selected_file_path,
                category=category,
                source=source,
            )
            messagebox.showinfo(
                "Nhập dữ liệu thành công",
                f"Đã phân tích và lưu bộ dữ liệu '{cfg['name']}':\n"
                f"• Số đỉnh (n): {cfg['num_nodes']:,}\n"
                f"• Số cạnh (m): {cfg['num_edges']:,}\n"
                f"• Bậc trung bình: {cfg['average_degree']}\n"
                f"• Hệ số cụm: {cfg['clustering_coefficient']}\n"
                f"• Cấu hình đã lưu: configs/datasets/{cfg['identifier']}.yaml",
                parent=self
            )
            if self.on_success_callback:
                self.on_success_callback(cfg["name"])
            self.destroy()
        except Exception as e:
            self.lbl_status.configure(text=f"❌ Lỗi: {e}", text_color=RED)
            self.btn_submit.configure(state="normal")
            messagebox.showerror("Lỗi phân tích đồ thị", f"Không thể phân tích tệp đồ thị:\n{e}", parent=self)


class PageDatasets(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, corner_radius=0, **kw)
        self._view_widget = None
        self._build()

    def _build(self):
        # Top Mode Switch
        top_ctrl = ctk.CTkFrame(self, fg_color="transparent")
        top_ctrl.pack(fill="x", pady=(0, 10))

        self.view_selector = ctk.CTkSegmentedButton(
            top_ctrl,
            values=[
                "Mạng lưới 3D (Knowledge Graph)",
                "Bảng danh mục bộ dữ liệu",
                "Cấu hình lan truyền (IC)",
            ],
            command=self._on_view_change,
            height=34,
            font=("Segoe UI", 11, "bold"),
            selected_color=ACTIVE_BG,
            selected_hover_color=ACTIVE_HOVER,
            unselected_color=("#e2e8f0", "#1e293b"),
            unselected_hover_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc")
        )
        self.view_selector.set("Mạng lưới 3D (Knowledge Graph)")
        self.view_selector.pack(side="left")

        # Container
        self.container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.container.pack(fill="both", expand=True)

        self._show_3d_view()

    def _on_view_change(self, val: str):
        if "Cấu hình" in val:
            self._show_ic_config_view()
        elif "3D" in val:
            self._show_3d_view()
        else:
            self._show_table_view()

    def _show_ic_config_view(self):
        if self._view_widget:
            self._view_widget.destroy()
        self._view_widget = ICConfigView(self.container)
        self._view_widget.pack(fill="both", expand=True)

    def _show_3d_view(self, select_graph_name: str = None):
        if self._view_widget:
            self._view_widget.destroy()
        self._view_widget = GraphExplorerView(self.container)
        self._view_widget.pack(fill="both", expand=True)
        if select_graph_name:
            self._view_widget.select_dataset(select_graph_name)

    def _show_table_view(self):
        if self._view_widget:
            self._view_widget.destroy()
        scroll = ctk.CTkScrollableFrame(self.container, fg_color=BG_APP)
        scroll.pack(fill="both", expand=True)
        self._view_widget = scroll

        # Load dynamically from configs/datasets/*.yaml
        datasets = load_all_dataset_configs()
        if not datasets:
            datasets = BENCHMARK_DATASETS

        # ── Top Action & Title Bar ────────────────────────────────────────────
        hdr_row = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(0, 12))

        title_box = ctk.CTkFrame(hdr_row, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            title_box,
            text="Bộ dữ liệu đồ thị chuẩn & Tùy chỉnh (Graph Datasets)",
            font=("Segoe UI", 16, "bold"), text_color=HEADER_FG, anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text=f"Quản lý {len(datasets)} mạng phức hợp được chuẩn hóa với các đặc trưng topo học phục vụ Tối đa hóa Lan truyền",
            font=FONT_MAIN, text_color=SUBTEXT_FG, anchor="w"
        ).pack(anchor="w", pady=(2, 0))

        act_box = ctk.CTkFrame(hdr_row, fg_color="transparent")
        act_box.pack(side="right", padx=(10, 0))

        btn_reload = ctk.CTkButton(
            act_box, text="🔄 Làm mới", width=100, height=32,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#e2e8f0", "#1e293b"),
            hover_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            command=self._show_table_view
        )
        btn_reload.pack(side="left", padx=4)

        btn_add = ctk.CTkButton(
            act_box, text="➕ Thêm bộ dữ liệu mới", width=180, height=32,
            font=("Segoe UI", 11, "bold"),
            fg_color=GREEN, hover_color="#059669",
            text_color="#ffffff",
            command=self._open_import_dialog
        )
        btn_add.pack(side="left", padx=4)

        # ── Summary Metric Cards ──────────────────────────────────────────────
        total_ds = len(datasets)
        max_ds = max(datasets, key=lambda d: d.get("raw_n", 0)) if datasets else None
        max_ds_name = max_ds["name"] if max_ds else "—"
        max_ds_sub = f"{max_ds['n']} đỉnh | {max_ds['m']} cạnh" if max_ds else "—"
        total_edges = sum(d.get("raw_m", 0) for d in datasets)
        ready_count = sum(1 for d in datasets if d.get("exists_on_disk", False))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 14))
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        metric_card(grid, "Tổng số bộ dữ liệu", str(total_ds), "Đã nạp vào hệ thống", BLUE, 0, 0)
        metric_card(grid, "Đồ thị lớn nhất", max_ds_name, max_ds_sub, ORANGE, 1, 0)
        metric_card(grid, "Tổng số cạnh mạng lưới", _format_vi_number(total_edges), "Tất cả đồ thị kết hợp", GREEN, 2, 0)
        metric_card(grid, "Trạng thái lưu trữ", f"{ready_count} / {total_ds} Tệp", f"data/raw/ ({'100% đầy đủ' if ready_count == total_ds else f'Sẵn sàng {ready_count}/{total_ds}'})", PURPLE, 3, 0)

        # ── Main Table Card ───────────────────────────────────────────────────
        tbl_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
        tbl_card.pack(fill="x", pady=(0, 16))

        headers = [
            "Bộ dữ liệu đồ thị",
            "Số đỉnh (n)",
            "Số cạnh (m)",
            "Bậc TB (⟨k⟩)",
            "Hệ số cụm (C)",
            "Đường kính (D)",
            "Phân loại đồ thị",
            "Nguồn dữ liệu",
            "Thao tác"
        ]

        header_row = ctk.CTkFrame(tbl_card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(12, 8))
        for col_idx, h in enumerate(headers):
            # Proportional widths
            w = 140 if col_idx == 0 else (160 if col_idx in (6, 7) else (120 if col_idx == 8 else 90))
            lbl = ctk.CTkLabel(
                header_row, text=h, font=("Segoe UI", 10, "bold"),
                text_color=SUBTEXT_FG, width=w,
                anchor="w" if col_idx in (0, 6, 7) else "center"
            )
            lbl.pack(side="left", padx=4)

        ctk.CTkFrame(tbl_card, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=10, pady=2)

        for ds in datasets:
            row_frame = ctk.CTkFrame(tbl_card, fg_color="transparent")
            row_frame.pack(fill="x", padx=14, pady=8)

            # 1. Dataset Name with color dot
            col0 = ctk.CTkFrame(row_frame, fg_color="transparent", width=140)
            col0.pack(side="left", padx=4)
            col0.pack_propagate(False)
            ctk.CTkFrame(col0, width=8, height=8, corner_radius=4, fg_color=ds.get("badge_color", BLUE)).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(col0, text=ds["name"], font=("Segoe UI", 11, "bold"), text_color=HEADER_FG).pack(side="left")

            # 2. Nodes n
            ctk.CTkLabel(row_frame, text=ds["n"], font=("Segoe UI", 11), text_color=HEADER_FG, width=90, anchor="center").pack(side="left", padx=4)

            # 3. Edges m
            ctk.CTkLabel(row_frame, text=ds["m"], font=("Segoe UI", 11), text_color=HEADER_FG, width=90, anchor="center").pack(side="left", padx=4)

            # 4. Avg degree
            ctk.CTkLabel(row_frame, text=ds["avg_deg"], font=("Segoe UI", 11), text_color=HEADER_FG, width=90, anchor="center").pack(side="left", padx=4)

            # 5. Clustering coefficient
            ctk.CTkLabel(row_frame, text=ds["clustering"], font=("Segoe UI", 11), text_color=HEADER_FG, width=90, anchor="center").pack(side="left", padx=4)

            # 6. Diameter
            ctk.CTkLabel(row_frame, text=ds["diameter"], font=("Segoe UI", 11), text_color=HEADER_FG, width=90, anchor="center").pack(side="left", padx=4)

            # 7. Category
            ctk.CTkLabel(row_frame, text=ds["category"], font=FONT_MAIN, text_color=SUBTEXT_FG, width=160, anchor="w").pack(side="left", padx=4)

            # 8. Source
            ctk.CTkLabel(row_frame, text=ds["source"], font=FONT_MAIN, text_color=SUBTEXT_FG, width=160, anchor="w").pack(side="left", padx=4)

            # 9. Action Buttons (Khám phá 3D & Xóa nếu là custom dataset)
            act_col = ctk.CTkFrame(row_frame, fg_color="transparent", width=120)
            act_col.pack(side="left", padx=4)

            btn_action = ctk.CTkButton(
                act_col, text="Xem 3D ▶", width=75, height=28,
                font=("Segoe UI", 10, "bold"), fg_color=BLUE, hover_color="#1557b0",
                corner_radius=6,
                command=lambda name=ds["name"]: self._switch_to_3d_graph(name)
            )
            btn_action.pack(side="left", padx=(0, 4))

            # Delete button for non-protected custom datasets
            if not ds.get("is_protected", False):
                btn_del = ctk.CTkButton(
                    act_col, text="🗑️", width=28, height=28,
                    font=("Segoe UI", 10), fg_color="#ef4444", hover_color="#dc2626",
                    text_color="#ffffff", corner_radius=6,
                    command=lambda ident=ds.get("identifier", ds["name"].lower()), name=ds["name"]: self._confirm_delete(ident, name)
                )
                btn_del.pack(side="left")
                Tooltip(btn_del, f"Xóa bộ dữ liệu tùy chỉnh '{ds['name']}'")

            ctk.CTkFrame(tbl_card, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=12, pady=1)

        # ── Raw Files Storage Information Box ─────────────────────────────────
        box = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box.pack(fill="x", pady=(8, 16))
        b_inner = ctk.CTkFrame(box, fg_color="transparent")
        b_inner.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(
            b_inner,
            text="Vị trí lưu trữ dữ liệu thật trên đĩa (Disk Storage Status):",
            font=("Segoe UI", 11, "bold"), text_color=HEADER_FG
        ).pack(anchor="w")

        for ds in datasets:
            raw_p = ds.get("raw_path", str(RAW_DIR / ds.get("file", "")))
            is_exist = Path(raw_p).exists()
            status_text = "Đã sẵn sàng" if is_exist else "Chưa tìm thấy tệp raw"
            color = GREEN if is_exist else RED
            line_txt = f"• {ds['name']}: {raw_p} ({status_text})"
            ctk.CTkLabel(b_inner, text=line_txt, font=("Consolas", 10), text_color=color, anchor="w").pack(anchor="w", padx=10, pady=2)

    def _open_import_dialog(self):
        ImportDatasetModal(self, on_success_callback=lambda new_name: self._on_dataset_imported(new_name))

    def _on_dataset_imported(self, new_name: str):
        self._show_table_view()

    def _confirm_delete(self, identifier: str, name: str):
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa bộ dữ liệu '{name}' khỏi hệ thống?", parent=self):
            try:
                delete_dataset_config(identifier)
                messagebox.showinfo("Thành công", f"Đã xóa cấu hình bộ dữ liệu '{name}'.", parent=self)
                self._show_table_view()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa bộ dữ liệu: {e}", parent=self)

    def _switch_to_3d_graph(self, dataset_name: str):
        self.view_selector.set("Mạng lưới 3D (Knowledge Graph)")
        self._show_3d_view(select_graph_name=dataset_name)
