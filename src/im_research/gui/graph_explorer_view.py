"""
3D Knowledge Graph & Network Explorer View.
Replicates the dark cyber aesthetic of modern interactive knowledge graphs:
- 3D force-directed layout with continuous orbital rotation.
- Glowing cyan/electric blue lines and vertices.
- Seed node highlighting and interactive diffusion wave simulation.
- Node Inspector sidebar with topological metrics and neighbor links.
- 1-click WebGL GPU ultra-mode export to browser.
"""

from __future__ import annotations
import math
from typing import Optional, List, Dict
import tkinter as tk

import networkx as nx
import customtkinter as ctk

from im_research.gui.graph_3d_canvas import Graph3DCanvas
from im_research.gui.webgl_exporter import export_and_open_webgl

# Adaptive Theme Palette for Graph Explorer View (Light & Dark)
DARK_BG       = ("#f8f9fa", "#06090e")
DARK_PANEL    = ("#ffffff", "#0b0f19")
BORDER_DARK   = ("#e8eaed", "#162032")
ACCENT_CYAN   = ("#0284c7", "#00e5ff")
ACCENT_BLUE   = ("#0369a1", "#38bdf8")
ACCENT_SEED   = "#ff3366"
TEXT_WHITE    = ("#0f172a", "#f8fafc")
TEXT_MUTED    = ("#64748b", "#94a3b8")
CARD_INNER    = ("#f1f5f9", "#101726")
BTN_BG        = ("#e2e8f0", "#1e293b")
BTN_HOVER     = ("#cbd5e1", "#334155")

class GraphExplorerView(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=DARK_BG, corner_radius=0, **kw)
        self.current_graph_name = None
        self.current_graph: Optional[nx.Graph] = None
        self._build_ui()
        self._show_empty_state()

    def _build_ui(self):
        # ── Top Control Bar ───────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color=DARK_PANEL, height=54, corner_radius=0,
                               border_width=1, border_color=BORDER_DARK)
        top_bar.pack(side="top", fill="x")
        top_bar.pack_propagate(False)

        # Title & Icon
        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left", padx=(18, 14), pady=8)
        dot = ctk.CTkFrame(title_box, width=10, height=10, corner_radius=5, fg_color=ACCENT_CYAN)
        dot.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_box, text="Knowledge Graph 3D", font=("Segoe UI", 14, "bold"), text_color=TEXT_WHITE).pack(side="left")

        # Dataset selector
        self.dataset_var = ctk.StringVar(value="Chưa có dữ liệu")
        ds_menu = ctk.CTkOptionMenu(
            top_bar, variable=self.dataset_var, width=210, height=32,
            fg_color=("#e2e8f0", "#131b2e"),
            button_color=("#cbd5e1", "#1e293b"),
            button_hover_color=("#94a3b8", "#334155"),
            text_color=TEXT_WHITE,
            dropdown_fg_color=("#ffffff", "#0f172a"),
            dropdown_text_color=TEXT_WHITE,
            dropdown_hover_color=("#e2e8f0", "#1e293b"),
            corner_radius=6,
            values=[
                "Chưa có dữ liệu",
            ],
            command=self._on_dataset_change
        )
        ds_menu.pack(side="left", padx=10, pady=10)

        # Action Buttons (Right)
        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.pack(side="right", padx=16, pady=8)

        # 1. Diffusion Pulse Button
        ctk.CTkButton(
            btn_box, text="Lan truyền (Pulse)", width=140, height=32,
            font=("Segoe UI", 11, "bold"), fg_color="#e11d48", hover_color="#be123c",
            text_color="#ffffff",
            corner_radius=6, command=self._trigger_pulse
        ).pack(side="left", padx=4)

        # 2. Reset Camera Button
        ctk.CTkButton(
            btn_box, text="Reset Camera", width=120, height=32,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#e2e8f0", "#1e293b"),
            hover_color=("#cbd5e1", "#334155"),
            text_color=TEXT_WHITE,
            corner_radius=6, command=self._reset_camera
        ).pack(side="left", padx=4)

        # 3. WebGL GPU Browser Mode
        ctk.CTkButton(
            btn_box, text="WebGL 3D (Browser)", width=145, height=32,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#0284c7", "#0369a1"),
            hover_color=("#0369a1", "#0284c7"),
            text_color="#ffffff",
            corner_radius=6, command=self._open_webgl
        ).pack(side="left", padx=4)

        # ── Main 3-Column Workspace ───────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color=DARK_BG, corner_radius=0)
        body.pack(side="top", fill="both", expand=True)

        # A. Left Sidebar: Controls & Communities
        self.left_sidebar = ctk.CTkScrollableFrame(
            body, width=230, fg_color=DARK_PANEL, corner_radius=0,
            border_width=1, border_color=BORDER_DARK
        )
        self.left_sidebar.pack(side="left", fill="y")
        self._build_left_sidebar()

        # B. Right Sidebar: Node Inspector & Topology Stats
        self.right_sidebar = ctk.CTkScrollableFrame(
            body, width=250, fg_color=DARK_PANEL, corner_radius=0,
            border_width=1, border_color=BORDER_DARK
        )
        self.right_sidebar.pack(side="right", fill="y")
        self._build_right_sidebar()

        # C. Center: 3D Canvas
        self.canvas_3d = Graph3DCanvas(body, on_node_selected=self._on_node_selected)
        self.canvas_3d.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------ #
    #  Left Sidebar Builder                                              #
    # ------------------------------------------------------------------ #

    def _build_left_sidebar(self):
        ctk.CTkLabel(self.left_sidebar, text="ĐIỀU KHIỂN GÓC NHÌN", font=("Segoe UI", 11, "bold"),
                     text_color=ACCENT_CYAN, anchor="w").pack(fill="x", pady=(10, 8), padx=10)

        # Auto-spin Switch
        self.spin_switch = ctk.CTkSwitch(
            self.left_sidebar, text="Tự động xoay 3D", font=("Segoe UI", 11),
            text_color=TEXT_WHITE, progress_color=ACCENT_CYAN,
            command=self._toggle_spin
        )
        self.spin_switch.select()
        self.spin_switch.pack(anchor="w", padx=10, pady=5)

        # Glow Halo Switch
        self.glow_switch = ctk.CTkSwitch(
            self.left_sidebar, text="Vầng sáng hào quang", font=("Segoe UI", 11),
            text_color=TEXT_WHITE, progress_color=ACCENT_CYAN,
            command=self._toggle_glow
        )
        self.glow_switch.select()
        self.glow_switch.pack(anchor="w", padx=10, pady=5)

        # Node Labels Switch
        self.labels_switch = ctk.CTkSwitch(
            self.left_sidebar, text="Hiện nhãn đỉnh (v_id)", font=("Segoe UI", 11),
            text_color=TEXT_WHITE, progress_color=ACCENT_CYAN,
            command=self._toggle_labels
        )
        self.labels_switch.select()
        self.labels_switch.pack(anchor="w", padx=10, pady=5)

        # Sliders
        ctk.CTkLabel(self.left_sidebar, text="Tốc độ xoay 3D:", font=("Segoe UI", 10),
                     text_color=TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=(12, 2))
        self.speed_slider = ctk.CTkSlider(
            self.left_sidebar, from_=0.0, to=0.03, number_of_steps=30,
            progress_color=ACCENT_CYAN, command=self._on_speed_change
        )
        self.speed_slider.set(0.008)
        self.speed_slider.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(self.left_sidebar, text="Thu phóng (Zoom):", font=("Segoe UI", 10),
                     text_color=TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=(10, 2))
        self.zoom_slider = ctk.CTkSlider(
            self.left_sidebar, from_=0.4, to=2.5, number_of_steps=30,
            progress_color=ACCENT_CYAN, command=self._on_zoom_change
        )
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(fill="x", padx=10, pady=2)

        # Separator
        ctk.CTkFrame(self.left_sidebar, height=1, fg_color=BORDER_DARK).pack(fill="x", padx=10, pady=16)

        # Community Colors Legend
        ctk.CTkLabel(self.left_sidebar, text="PHÂN CỤM CỘNG ĐỒNG", font=("Segoe UI", 11, "bold"),
                     text_color=ACCENT_CYAN, anchor="w").pack(fill="x", pady=(0, 8), padx=10)

        comms = [
            ("Hạt giống (Seeds S)", ACCENT_SEED),
            ("Đỉnh trung tâm (Hubs)", ("#0284c7", "#ffffff")),
            ("Cụm cộng đồng 1", "#00e5ff"),
            ("Cụm cộng đồng 2", "#818cf8"),
            ("Cụm cộng đồng 3", "#a855f7"),
            ("Cụm cộng đồng 4", "#34d399"),
        ]
        for name, col in comms:
            row = ctk.CTkFrame(self.left_sidebar, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)
            dot = ctk.CTkFrame(row, width=10, height=10, corner_radius=5, fg_color=col)
            dot.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=name, font=("Segoe UI", 10), text_color=TEXT_WHITE).pack(side="left")

        # Instructions
        ctk.CTkFrame(self.left_sidebar, height=1, fg_color=BORDER_DARK).pack(fill="x", padx=10, pady=16)
        ctk.CTkLabel(self.left_sidebar, text="HƯỚNG DẪN TƯƠNG TÁC", font=("Segoe UI", 11, "bold"),
                     text_color=ACCENT_CYAN, anchor="w").pack(fill="x", padx=10, pady=(0, 6))
        tips = [
            "• Chuột trái + kéo: Xoay khối cầu 3D",
            "• Cuộn chuột: Phóng to / thu nhỏ",
            "• Nhấp đỉnh: Xem thuộc tính chi tiết",
            "• Rà chuột: Nổi bật mạng lân cận (ego)",
        ]
        for t in tips:
            ctk.CTkLabel(self.left_sidebar, text=t, font=("Segoe UI", 9),
                         text_color=TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=1)

    # ------------------------------------------------------------------ #
    #  Right Sidebar Builder (Node Inspector)                            #
    # ------------------------------------------------------------------ #

    def _build_right_sidebar(self):
        ctk.CTkLabel(self.right_sidebar, text="THÔNG SỐ MẠNG TOÀN CỤC", font=("Segoe UI", 11, "bold"),
                     text_color=ACCENT_CYAN, anchor="w").pack(fill="x", pady=(10, 8), padx=10)

        # Global stats card
        self.stat_card = ctk.CTkFrame(self.right_sidebar, fg_color=CARD_INNER, corner_radius=8,
                                      border_width=1, border_color=BORDER_DARK)
        self.stat_card.pack(fill="x", padx=10, pady=(0, 14))

        self.lbl_nodes = ctk.CTkLabel(self.stat_card, text="Số đỉnh (n): —", font=("Segoe UI", 10), text_color=TEXT_WHITE, anchor="w")
        self.lbl_nodes.pack(fill="x", padx=12, pady=(8, 2))
        self.lbl_edges = ctk.CTkLabel(self.stat_card, text="Số cạnh (m): —", font=("Segoe UI", 10), text_color=TEXT_WHITE, anchor="w")
        self.lbl_edges.pack(fill="x", padx=12, pady=2)
        self.lbl_avg_deg = ctk.CTkLabel(self.stat_card, text="Bậc trung bình: —", font=("Segoe UI", 10), text_color=TEXT_WHITE, anchor="w")
        self.lbl_avg_deg.pack(fill="x", padx=12, pady=2)
        self.lbl_density = ctk.CTkLabel(self.stat_card, text="Mật độ mạng: —", font=("Segoe UI", 10), text_color=TEXT_WHITE, anchor="w")
        self.lbl_density.pack(fill="x", padx=12, pady=(2, 8))

        ctk.CTkFrame(self.right_sidebar, height=1, fg_color=BORDER_DARK).pack(fill="x", padx=10, pady=6)

        # Node Details Inspector
        ctk.CTkLabel(self.right_sidebar, text="CHI TIẾT ĐỈNH ĐƯỢC CHỌN", font=("Segoe UI", 11, "bold"),
                     text_color=ACCENT_CYAN, anchor="w").pack(fill="x", pady=(8, 6), padx=10)

        self.inspector_card = ctk.CTkFrame(self.right_sidebar, fg_color=CARD_INNER, corner_radius=8,
                                          border_width=1, border_color=BORDER_DARK)
        self.inspector_card.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_node_id = ctk.CTkLabel(self.inspector_card, text="Đỉnh: v0", font=("Segoe UI", 13, "bold"),
                                       text_color=ACCENT_CYAN, anchor="w")
        self.lbl_node_id.pack(fill="x", padx=12, pady=(10, 4))

        self.lbl_node_status = ctk.CTkLabel(self.inspector_card, text="Trạng thái: Hạt giống (Seed S)", font=("Segoe UI", 10),
                                            text_color=ACCENT_SEED, anchor="w")
        self.lbl_node_status.pack(fill="x", padx=12, pady=2)

        self.lbl_node_deg = ctk.CTkLabel(self.inspector_card, text="Bậc liên kết: 16", font=("Segoe UI", 10),
                                         text_color=TEXT_WHITE, anchor="w")
        self.lbl_node_deg.pack(fill="x", padx=12, pady=2)

        self.lbl_node_clust = ctk.CTkLabel(self.inspector_card, text="Gom cụm: 0.1500", font=("Segoe UI", 10),
                                           text_color=TEXT_WHITE, anchor="w")
        self.lbl_node_clust.pack(fill="x", padx=12, pady=2)

        self.lbl_node_comm = ctk.CTkLabel(self.inspector_card, text="Cộng đồng: Nhóm 1", font=("Segoe UI", 10),
                                          text_color=TEXT_WHITE, anchor="w")
        self.lbl_node_comm.pack(fill="x", padx=12, pady=(2, 10))

        # Neighbor list container
        ctk.CTkLabel(self.right_sidebar, text="DANH SÁCH ĐỈNH LÂN CẬN (1-HOP)", font=("Segoe UI", 10, "bold"),
                     text_color=TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=(8, 4))

        self.neighbor_box = ctk.CTkScrollableFrame(self.right_sidebar, height=160, fg_color=CARD_INNER,
                                                  border_width=1, border_color=BORDER_DARK)
        self.neighbor_box.pack(fill="x", padx=10, pady=(0, 10))

    # ------------------------------------------------------------------ #
    #  Actions & Event Callbacks                                         #
    # ------------------------------------------------------------------ #

    def load_selected_graph(self, display_name: str):
        """Show empty state — no sample data."""
        self.current_graph = None
        self.current_graph_name = None
        self.lbl_nodes.configure(text="Số đỉnh (n): —")
        self.lbl_edges.configure(text="Số cạnh (m): —")
        self.lbl_avg_deg.configure(text="Bậc trung bình: —")
        self.lbl_density.configure(text="Mật độ mạng: —")

    def _show_empty_state(self):
        """Display empty state in the 3D canvas area."""
        empty_label = ctk.CTkLabel(
            self, text="\U0001f4ed Chua co du lieu do thi\nTai bo du lieu de truc quan hoa",
            font=("Segoe UI", 14), text_color=TEXT_MUTED
        )
        empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def _on_dataset_change(self, choice: str):
        self.load_selected_graph(choice)

    def _trigger_pulse(self):
        self.canvas_3d.trigger_diffusion_simulation()

    def _reset_camera(self):
        self.canvas_3d.reset_camera()
        self.zoom_slider.set(1.0)

    def _open_webgl(self):
        if self.current_graph:
            export_and_open_webgl(
                self.current_graph,
                dataset_name=self.current_graph_name,
                seed_nodes=self.canvas_3d.seed_nodes
            )

    def _toggle_spin(self):
        self.canvas_3d.auto_spin = bool(self.spin_switch.get())

    def _toggle_glow(self):
        self.canvas_3d.show_glow = bool(self.glow_switch.get())
        self.canvas_3d.redraw()

    def _toggle_labels(self):
        self.canvas_3d.show_labels = bool(self.labels_switch.get())
        self.canvas_3d.redraw()

    def _on_speed_change(self, val):
        self.canvas_3d.spin_speed = float(val)

    def _on_zoom_change(self, val):
        self.canvas_3d.zoom = float(val)
        self.canvas_3d.redraw()

    def _on_node_selected(self, node_id: int, info: dict):
        """Updates right sidebar node inspector."""
        is_seed = info.get("is_seed", False)
        is_active = info.get("is_activated", False)

        status_text = "Hạt giống (Seed S)" if is_seed else ("Đã kích hoạt" if is_active else "Chưa kích hoạt")
        status_col = ACCENT_SEED if is_seed else ("#fbbf24" if is_active else TEXT_MUTED)

        self.lbl_node_id.configure(text=f"Đỉnh: v{node_id}")
        self.lbl_node_status.configure(text=f"Trạng thái: {status_text}", text_color=status_col)
        self.lbl_node_deg.configure(text=f"Bậc liên kết: {info.get('degree', 0)}")
        self.lbl_node_clust.configure(text=f"Gom cụm: {info.get('clustering', 0.0):.4f}")
        self.lbl_node_comm.configure(text=f"Cộng đồng: Nhóm {info.get('community', 0) + 1}")

        # Update neighbors
        for child in self.neighbor_box.winfo_children():
            child.destroy()

        neighbors = info.get("neighbors", [])
        if not neighbors:
            ctk.CTkLabel(self.neighbor_box, text="Không có lân cận", font=("Segoe UI", 9), text_color=TEXT_MUTED).pack()
        else:
            for nb in neighbors[:30]:
                btn = ctk.CTkButton(
                    self.neighbor_box, text=f"• Đỉnh v{nb} (bậc {self.current_graph.degree(nb)})",
                    font=("Segoe UI", 9), anchor="w", height=22,
                    fg_color="transparent", hover_color=("#e2e8f0", "#1e293b"), text_color=ACCENT_BLUE,
                    command=lambda u=nb: self._focus_node(u)
                )
                btn.pack(fill="x", pady=1)

    def _focus_node(self, node_id: int):
        self.canvas_3d._selected_node = node_id
        if self.current_graph:
            info = self.canvas_3d._get_node_info(node_id)
            self._on_node_selected(node_id, info)
        self.canvas_3d.redraw()

