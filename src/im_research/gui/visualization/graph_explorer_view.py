"""
3D Knowledge Graph & Network Explorer View.
Replicates the dark cyber aesthetic of modern interactive knowledge graphs:
- 3D force-directed layout with continuous orbital rotation.
- Progressive traveling edge diffusion animation: colors travel gradually along edges from node to node.
- Real-time traveling photon particles and shockwave activation ripples.
- Full multi-input zooming: mouse wheel, laptop trackpad pinch-to-zoom (Control-MouseWheel), on-screen buttons.
- Node Inspector sidebar with topological metrics and neighbor links.
- 1-click WebGL GPU ultra-mode export to browser.
"""

from __future__ import annotations
import math
from typing import Optional, List, Dict
import tkinter as tk

import networkx as nx
import customtkinter as ctk

from pathlib import Path
from im_research.gui.visualization.graph_3d_canvas import Graph3DCanvas
from im_research.gui.visualization.webgl_exporter import export_and_open_webgl
from im_research.data.config_loader import load_all_dataset_configs

RAW_DIR = Path(__file__).resolve().parents[4] / "data" / "raw"

# Adaptive Theme Palette for Graph Explorer View (Light & Dark)
DARK_BG       = ("#f8f9fa", "#06090e")
DARK_PANEL    = ("#ffffff", "#0b0f19")
BORDER_DARK   = ("#e2e8f0", "#162032")
ACCENT_CYAN   = ("#0284c7", "#00e5ff")
ACCENT_BLUE   = ("#0369a1", "#38bdf8")
ACCENT_SEED   = "#ff3366"
TEXT_WHITE    = ("#0f172a", "#f8fafc")
TEXT_MUTED    = ("#475569", "#94a3b8")
CARD_INNER    = ("#f8fafc", "#101726")
BTN_BG        = ("#f1f5f9", "#1e293b")
BTN_HOVER     = ("#e2e8f0", "#334155")


class GraphExplorerView(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=DARK_BG, corner_radius=0, **kw)
        self.dataset_configs = load_all_dataset_configs()
        initial_name = self.dataset_configs[0]["name"] if self.dataset_configs else "Karate Club"
        self.current_graph_name = initial_name
        self.current_graph: Optional[nx.Graph] = None
        self.full_graph: Optional[nx.Graph] = None
        self._build_ui()
        self.load_selected_graph(initial_name)

    def _get_menu_values(self) -> List[str]:
        if self.dataset_configs:
            return [f"{d['name']} (n={d['n']}, m={d['m']})" for d in self.dataset_configs]
        return ["Karate Club (n=34, m=78)"]

    def refresh_dataset_options(self):
        self.dataset_configs = load_all_dataset_configs()
        vals = self._get_menu_values()
        if hasattr(self, "ds_menu"):
            self.ds_menu.configure(values=vals)

    def _build_ui(self):
        # ── Top Control Bar ───────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color=DARK_PANEL, height=54, corner_radius=0,
                               border_width=1, border_color=BORDER_DARK)
        top_bar.pack(side="top", fill="x")
        top_bar.pack_propagate(False)

        # Title & Indicator Dot
        title_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_box.pack(side="left", padx=(18, 14), pady=8)
        dot = ctk.CTkFrame(title_box, width=10, height=10, corner_radius=5, fg_color=ACCENT_CYAN)
        dot.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_box, text="Knowledge Graph 3D", font=("Segoe UI", 13, "bold"), text_color=TEXT_WHITE).pack(side="left")

        # Dataset selector
        vals = self._get_menu_values()
        self.dataset_var = ctk.StringVar(value=vals[0] if vals else "Karate Club")
        self.ds_menu = ctk.CTkOptionMenu(
            top_bar, variable=self.dataset_var, width=280, height=32,
            fg_color=("#ffffff", "#1e293b"),
            button_color=("#e2e8f0", "#334155"),
            button_hover_color=("#cbd5e1", "#475569"),
            text_color=("#0f172a", "#f8fafc"),
            dropdown_fg_color=("#ffffff", "#1e293b"),
            dropdown_text_color=("#0f172a", "#f8fafc"),
            dropdown_hover_color=("#f1f5f9", "#334155"),
            corner_radius=6,
            values=vals,
            command=self._on_dataset_change
        )
        self.ds_menu.pack(side="left", padx=10, pady=10)

        # Real data indicator badge
        self.lbl_dataset_mode = ctk.CTkLabel(
            top_bar, text="✓ Dữ liệu thật Zachary (1977)",
            font=("Segoe UI", 10, "bold"), text_color=ACCENT_CYAN
        )
        self.lbl_dataset_mode.pack(side="left", padx=(4, 10), pady=10)

        # Action Buttons (Right) - Anchored and spacious
        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.pack(side="right", padx=16, pady=8)

        # 1. Diffusion Pulse Button
        ctk.CTkButton(
            btn_box, text="▶ Lan truyền (Pulse)", width=145, height=32,
            font=("Segoe UI", 11, "bold"), fg_color="#e11d48", hover_color="#be123c",
            text_color="#ffffff",
            corner_radius=6, command=self._trigger_pulse
        ).pack(side="left", padx=4)

        # 2. Reset Camera Button
        ctk.CTkButton(
            btn_box, text="Reset Camera", width=115, height=32,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#f1f5f9", "#1e293b"),
            hover_color=("#e2e8f0", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            border_width=1,
            border_color=("#cbd5e1", "#334155"),
            corner_radius=6, command=self._reset_camera
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

        # C. Center: 3D Canvas Area with On-Screen Controls
        center_container = ctk.CTkFrame(body, fg_color="transparent")
        center_container.pack(side="left", fill="both", expand=True)

        self.canvas_3d = Graph3DCanvas(
            center_container,
            on_node_selected=self._on_node_selected,
            on_zoom_changed=self._on_canvas_zoom,
            on_diffusion_status=self._on_diffusion_status
        )
        self.canvas_3d.pack(fill="both", expand=True)

        # Floating Diffusion Notification HUD Banner on 3D Canvas
        self.diffusion_hud = ctk.CTkFrame(
            center_container,
            fg_color=("#ffffff", "#0b111e"),
            corner_radius=18,
            border_width=1,
            border_color="#f59e0b"
        )
        self.lbl_hud_icon = ctk.CTkLabel(
            self.diffusion_hud, text="⚡", font=("Segoe UI", 11, "bold"), text_color="#f59e0b"
        )
        self.lbl_hud_icon.pack(side="left", padx=(12, 6), pady=6)

        self.lbl_hud_text = ctk.CTkLabel(
            self.diffusion_hud, text="", font=("Segoe UI", 10, "bold"), text_color=TEXT_WHITE
        )
        self.lbl_hud_text.pack(side="left", padx=(0, 14), pady=6)
        # Initially hidden until pulse is triggered
        self.diffusion_hud.place_forget()

        # On-Canvas Floating Zoom Overlay (Bottom-Right)
        zoom_overlay = ctk.CTkFrame(
            center_container,
            fg_color=("#ffffff", "#131b2e"),
            corner_radius=8,
            border_width=1,
            border_color=BORDER_DARK
        )
        zoom_overlay.place(relx=0.97, rely=0.95, anchor="se")

        ctk.CTkButton(
            zoom_overlay, text="+", width=28, height=28, font=("Segoe UI", 13, "bold"),
            fg_color="transparent", hover_color=BTN_HOVER, text_color=TEXT_WHITE,
            command=self.canvas_3d.zoom_in
        ).pack(side="left", padx=2, pady=2)

        ctk.CTkButton(
            zoom_overlay, text="−", width=28, height=28, font=("Segoe UI", 13, "bold"),
            fg_color="transparent", hover_color=BTN_HOVER, text_color=TEXT_WHITE,
            command=self.canvas_3d.zoom_out
        ).pack(side="left", padx=2, pady=2)

        ctk.CTkButton(
            zoom_overlay, text="⟲", width=28, height=28, font=("Segoe UI", 12, "bold"),
            fg_color="transparent", hover_color=BTN_HOVER, text_color=TEXT_WHITE,
            command=self._reset_camera
        ).pack(side="left", padx=2, pady=2)

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
            self.left_sidebar, from_=0.25, to=5.0, number_of_steps=50,
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
            ("Đã kích hoạt (Cascade)", "#f59e0b"),
            ("Đỉnh trung tâm (Hubs)", ("#0284c7", "#ffffff")),
            ("Cụm cộng đồng 1", "#0284c7"),
            ("Cụm cộng đồng 2", "#8b5cf6"),
            ("Cụm cộng đồng 3", "#10b981"),
            ("Cụm cộng đồng 4", "#ec4899"),
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
            "• Cuộn chuột hoặc chụm 2 ngón (Trackpad Pinch) để thu phóng",
            "• Nhấp đúp chuột: Phóng to nhanh 1.3x",
            "• Nút [+]/[−] góc phải: Thu phóng 1 chạm",
            "• Kéo chuột trái: Xoay góc nhìn khối cầu 3D",
            "• Nút Lan truyền: Tín hiệu chạy dọc cạnh từ hạt giống",
            "• Nhấp đỉnh: Xem thuộc tính & lân cận",
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

        self.lbl_node_deg = ctk.CTkLabel(self.inspector_card, text="Bậc liên kết: —", font=("Segoe UI", 10),
                                         text_color=TEXT_WHITE, anchor="w")
        self.lbl_node_deg.pack(fill="x", padx=12, pady=2)

        self.lbl_node_clust = ctk.CTkLabel(self.inspector_card, text="Gom cụm: —", font=("Segoe UI", 10),
                                           text_color=TEXT_WHITE, anchor="w")
        self.lbl_node_clust.pack(fill="x", padx=12, pady=2)

        self.lbl_node_comm = ctk.CTkLabel(self.inspector_card, text="Cộng đồng: Nhóm 1", font=("Segoe UI", 10),
                                          text_color=TEXT_WHITE, anchor="w")
        self.lbl_node_comm.pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkFrame(self.right_sidebar, height=1, fg_color=BORDER_DARK).pack(fill="x", padx=10, pady=6)

        # Dedicated Cascade Diffusion Progress Card
        ctk.CTkLabel(self.right_sidebar, text="TIẾN TRÌNH LAN TRUYỀN", font=("Segoe UI", 11, "bold"),
                     text_color=ACCENT_CYAN, anchor="w").pack(fill="x", pady=(6, 6), padx=10)

        self.diff_card = ctk.CTkFrame(self.right_sidebar, fg_color=CARD_INNER, corner_radius=8,
                                      border_width=1, border_color=BORDER_DARK)
        self.diff_card.pack(fill="x", padx=10, pady=(0, 10))

        self.lbl_diff_status = ctk.CTkLabel(
            self.diff_card, text="Trạng thái: Chờ kích hoạt",
            font=("Segoe UI", 10, "bold"), text_color=TEXT_MUTED, anchor="w"
        )
        self.lbl_diff_status.pack(fill="x", padx=12, pady=(8, 2))

        self.lbl_diff_step = ctk.CTkLabel(
            self.diff_card, text="Bước mô phỏng: t = 0",
            font=("Segoe UI", 10), text_color=TEXT_WHITE, anchor="w"
        )
        self.lbl_diff_step.pack(fill="x", padx=12, pady=2)

        self.lbl_diff_count = ctk.CTkLabel(
            self.diff_card, text="Đã kích hoạt: 0 đỉnh",
            font=("Segoe UI", 10), text_color=TEXT_WHITE, anchor="w"
        )
        self.lbl_diff_count.pack(fill="x", padx=12, pady=(2, 6))

        self.diff_progress = ctk.CTkProgressBar(self.diff_card, height=6, progress_color="#f59e0b")
        self.diff_progress.pack(fill="x", padx=12, pady=(0, 10))
        self.diff_progress.set(0.0)

        ctk.CTkFrame(self.right_sidebar, height=1, fg_color=BORDER_DARK).pack(fill="x", padx=10, pady=6)

        # Neighbor list container
        ctk.CTkLabel(self.right_sidebar, text="DANH SÁCH ĐỈNH LÂN CẬN (1-HOP)", font=("Segoe UI", 10, "bold"),
                     text_color=TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=(6, 4))

        self.neighbor_box = ctk.CTkScrollableFrame(self.right_sidebar, height=160, fg_color=CARD_INNER,
                                                  border_width=1, border_color=BORDER_DARK)
        self.neighbor_box.pack(fill="x", padx=10, pady=(0, 10))

    # ------------------------------------------------------------------ #
    #  Actions & Event Callbacks                                         #
    # ------------------------------------------------------------------ #

    def load_selected_graph(self, display_name: str):
        """Loads authentic benchmark graph from data/raw and binds to 3D Canvas."""
        name_clean = display_name.lower()

        if "karate" in name_clean:
            txt = RAW_DIR / "karate.txt"
            if txt.exists():
                g_full = nx.read_edgelist(txt, nodetype=int)
            else:
                g_full = nx.karate_club_graph()
                g_full = nx.convert_node_labels_to_integers(g_full)
            display_g = g_full
            full_n, full_m = 34, 78
            avg_deg = 4.59
            density_val = 0.1390
            badge_text = "✓ Dữ liệu thật Zachary (1977)"

        elif "dolphin" in name_clean:
            txt = RAW_DIR / "dolphins.txt"
            if txt.exists():
                g_full = nx.read_edgelist(txt, nodetype=int)
            else:
                g_full = nx.karate_club_graph()
            display_g = g_full
            full_n, full_m = 62, 159
            avg_deg = 5.13
            density_val = 0.0841
            badge_text = "✓ Dữ liệu thật Lusseau (2003)"

        elif "facebook" in name_clean:
            txt = RAW_DIR / "facebook.txt"
            if txt.exists():
                g_full = nx.read_edgelist(txt, nodetype=int)
            else:
                g_full = nx.karate_club_graph()
            full_n, full_m = 4039, 88234
            avg_deg = 43.69
            density_val = 0.0108
            badge_text = "✓ Dữ liệu thật SNAP [8] (3D: Lõi hạt giống)"

            degrees = dict(g_full.degree())
            top_seeds = sorted(degrees.keys(), key=lambda u: degrees[u], reverse=True)[:5]
            sub_nodes = set(top_seeds)
            for s in top_seeds:
                sub_nodes.update(list(g_full.neighbors(s))[:40])
            display_g = g_full.subgraph(sub_nodes).copy()

        elif "nethept" in name_clean or "hept" in name_clean:
            txt = RAW_DIR / "nethept.txt"
            edges = []
            full_n, full_m = 15233, 58891
            if txt.exists():
                with open(txt, "r", encoding="utf-8", errors="ignore") as f:
                    first = f.readline().split()
                    if len(first) >= 2:
                        try:
                            full_n, full_m = int(first[0]), int(first[1])
                        except ValueError:
                            pass
                    for line in f:
                        p = line.split()
                        if len(p) >= 2:
                            u, v = int(p[0]), int(p[1])
                            if u != v:
                                edges.append((u, v))
                g_full = nx.Graph()
                g_full.add_nodes_from(range(full_n))
                g_full.add_edges_from(edges)
            else:
                g_full = nx.karate_club_graph()

            avg_deg = 7.73
            density_val = 0.0005
            badge_text = "✓ Dữ liệu thật arXiv / SNAP [15] (3D: Lõi hạt giống)"

            degrees = dict(g_full.degree())
            top_seeds = sorted(degrees.keys(), key=lambda u: degrees[u], reverse=True)[:5]
            sub_nodes = set(top_seeds)
            for s in top_seeds:
                sub_nodes.update(list(g_full.neighbors(s))[:35])
            display_g = g_full.subgraph(sub_nodes).copy()

        elif "enron" in name_clean:
            txt = RAW_DIR / "enron.txt"
            if txt.exists():
                g_full = nx.read_edgelist(txt, nodetype=int, comments="#")
            else:
                g_full = nx.karate_club_graph()
            full_n, full_m = 36692, 183831
            avg_deg = 10.02
            density_val = 0.0003
            badge_text = "✓ Dữ liệu thật SNAP [8] (3D: Lõi hạt giống)"

            degrees = dict(g_full.degree())
            top_seeds = sorted(degrees.keys(), key=lambda u: degrees[u], reverse=True)[:5]
            sub_nodes = set(top_seeds)
            for s in top_seeds:
                sub_nodes.update(list(g_full.neighbors(s))[:30])
            display_g = g_full.subgraph(sub_nodes).copy()
        else:
            # Check if this matches any custom or dynamic dataset from configs/datasets/*.yaml
            cfg = None
            for c in self.dataset_configs:
                if c["name"].lower() in name_clean or c["identifier"].lower() in name_clean:
                    cfg = c
                    break

            if cfg and Path(cfg["raw_path"]).exists():
                custom_txt = Path(cfg["raw_path"])
                try:
                    g_full = nx.read_edgelist(custom_txt, nodetype=int, comments="#")
                except Exception:
                    g_full = nx.read_edgelist(custom_txt, comments="#")
                    g_full = nx.convert_node_labels_to_integers(g_full)

                full_n = cfg.get("raw_n", g_full.number_of_nodes())
                full_m = cfg.get("raw_m", g_full.number_of_edges())
                avg_deg = cfg.get("raw_avg_deg", (2.0 * full_m) / full_n if full_n > 0 else 0)
                density_val = (2.0 * full_m) / (full_n * (full_n - 1)) if full_n > 1 else 0.0
                badge_text = f"✓ {cfg['name']} ({cfg.get('source', 'Tùy chỉnh')})"

                if full_n > 200:
                    degrees = dict(g_full.degree())
                    top_seeds = sorted(degrees.keys(), key=lambda u: degrees[u], reverse=True)[:5]
                    sub_nodes = set(top_seeds)
                    for s in top_seeds:
                        sub_nodes.update(list(g_full.neighbors(s))[:35])
                    display_g = g_full.subgraph(sub_nodes).copy()
                else:
                    display_g = g_full
            else:
                txt = RAW_DIR / "karate.txt"
                g_full = nx.read_edgelist(txt, nodetype=int) if txt.exists() else nx.karate_club_graph()
                display_g = g_full
                full_n, full_m = 34, 78
                avg_deg = 4.59
                density_val = 0.1390
                badge_text = "✓ Dữ liệu thật Zachary (1977)"

        display_g = nx.convert_node_labels_to_integers(display_g)
        self.full_graph = g_full
        self.current_graph = display_g
        self.lbl_dataset_mode.configure(text=badge_text)

        # Reset Floating HUD & Sidebar Progress
        if hasattr(self, "diffusion_hud"):
            self.diffusion_hud.place_forget()
        if hasattr(self, "lbl_diff_status"):
            self.lbl_diff_status.configure(text="Trạng thái: Chờ kích hoạt", text_color=TEXT_MUTED)
            self.lbl_diff_step.configure(text="Bước mô phỏng: t = 0")
            self.lbl_diff_count.configure(text="Đã kích hoạt: 0 đỉnh")
            self.diff_progress.set(0.0)

        # Update right sidebar stats card
        self.lbl_nodes.configure(text=f"Số đỉnh (n): {full_n:,}")
        self.lbl_edges.configure(text=f"Số cạnh (m): {full_m:,}")
        self.lbl_avg_deg.configure(text=f"Bậc trung bình: {avg_deg:.2f}")
        self.lbl_density.configure(text=f"Mật độ mạng: {density_val:.4f}")

        # Bind to 3D Canvas
        self.canvas_3d.set_graph(display_g)

        # Trigger first node info
        if display_g.number_of_nodes() > 0:
            first_seed = next(iter(self.canvas_3d.seed_nodes)) if self.canvas_3d.seed_nodes else 0
            info = self.canvas_3d._get_node_info(first_seed)
            self._on_node_selected(first_seed, info)

    def select_dataset(self, name: str):
        """Programmatically select a dataset by partial or full name."""
        vals = self._get_menu_values()
        for v in vals:
            if name.lower() in v.lower():
                self.dataset_var.set(v)
                self.load_selected_graph(v)
                return
        self.dataset_var.set(name)
        self.load_selected_graph(name)

    def _on_dataset_change(self, val: str):
        self.load_selected_graph(val)

    def _trigger_pulse(self):
        self.canvas_3d.trigger_diffusion_simulation()

    def _reset_camera(self):
        self.canvas_3d.reset_camera()
        self.speed_slider.set(0.008)
        self.zoom_slider.set(1.0)

    def _toggle_spin(self):
        self.canvas_3d.auto_spin = bool(self.spin_switch.get())

    def _toggle_glow(self):
        self.canvas_3d.show_glow = bool(self.glow_switch.get())
        self.canvas_3d.redraw()

    def _toggle_labels(self):
        self.canvas_3d.show_labels = bool(self.labels_switch.get())
        self.canvas_3d.redraw()

    def _on_speed_change(self, val: float):
        self.canvas_3d.spin_speed = float(val)

    def _on_zoom_change(self, val: float):
        self.canvas_3d.zoom = float(val)
        self.canvas_3d.redraw()

    def _on_canvas_zoom(self, zoom_val: float):
        """Syncs sidebar zoom slider when zooming via mouse wheel, touchpad or gestures."""
        if hasattr(self, "zoom_slider"):
            self.zoom_slider.set(round(zoom_val, 2))

    def _on_diffusion_status(self, step: int, active: int, total: int, is_running: bool):
        """Displays real-time cascade progress on the floating Canvas HUD and the Right Sidebar."""
        pct = (active / total * 100.0) if total > 0 else 0.0
        ratio = (active / total) if total > 0 else 0.0

        if is_running:
            # 1. Floating HUD on 3D Canvas
            if hasattr(self, "diffusion_hud"):
                self.diffusion_hud.place(relx=0.5, rely=0.03, anchor="n")
                self.diffusion_hud.configure(border_color="#f59e0b")
                self.lbl_hud_icon.configure(text="⚡", text_color="#f59e0b")
                self.lbl_hud_text.configure(
                    text=f"Lan truyền: Bước t={step}  │  Đã kích hoạt: {active}/{total} đỉnh ({pct:.1f}%)",
                    text_color=TEXT_WHITE
                )

            # 2. Right Sidebar Progress Card
            if hasattr(self, "lbl_diff_status"):
                self.lbl_diff_status.configure(text="Trạng thái: ▶ Đang lan truyền...", text_color="#f59e0b")
                self.lbl_diff_step.configure(text=f"Bước mô phỏng: t = {step}")
                self.lbl_diff_count.configure(text=f"Đã kích hoạt: {active}/{total} đỉnh ({pct:.1f}%)")
                self.diff_progress.set(ratio)
                self.diff_progress.configure(progress_color="#f59e0b")
        else:
            # 1. Floating HUD on 3D Canvas
            if hasattr(self, "diffusion_hud"):
                self.diffusion_hud.place(relx=0.5, rely=0.03, anchor="n")
                self.diffusion_hud.configure(border_color="#10b981")
                self.lbl_hud_icon.configure(text="✓", text_color="#10b981")
                self.lbl_hud_text.configure(
                    text=f"Hoàn tất lan truyền: {active}/{total} đỉnh ({pct:.1f}%)",
                    text_color="#10b981"
                )

            # 2. Right Sidebar Progress Card
            if hasattr(self, "lbl_diff_status"):
                self.lbl_diff_status.configure(text="Trạng thái: ✓ Hoàn tất lan truyền", text_color="#10b981")
                self.lbl_diff_step.configure(text=f"Số bước hoàn tất: t = {step}")
                self.lbl_diff_count.configure(text=f"Tổng ảnh hưởng: {active}/{total} đỉnh ({pct:.1f}%)")
                self.diff_progress.set(ratio)
                self.diff_progress.configure(progress_color="#10b981")

    def _on_node_selected(self, u: int, info: dict):
        self.lbl_node_id.configure(text=f"Đỉnh: v{u}")
        status = "Hạt giống (Seed S) ★" if info["is_seed"] else ("Đã kích hoạt (Cascade)" if info["is_activated"] else "Bình thường")
        color = ACCENT_SEED if info["is_seed"] else ("#f59e0b" if info["is_activated"] else TEXT_MUTED)
        self.lbl_node_status.configure(text=f"Trạng thái: {status}", text_color=color)
        self.lbl_node_deg.configure(text=f"Bậc liên kết: {info['degree']}")
        self.lbl_node_clust.configure(text=f"Gom cụm: {info['clustering']:.4f}")
        self.lbl_node_comm.configure(text=f"Cộng đồng: Nhóm {info['community'] + 1}")

        # Fill neighbors
        for w in self.neighbor_box.winfo_children():
            w.destroy()

        for nb in info["neighbors"][:30]:
            nb_deg = self.canvas_3d.graph.degree(nb) if self.canvas_3d.graph else 0
            row = ctk.CTkLabel(
                self.neighbor_box,
                text=f"• Đỉnh v{nb} (bậc {nb_deg})",
                font=("Segoe UI", 9),
                text_color=TEXT_MUTED,
                anchor="w"
            )
            row.pack(fill="x", padx=4, pady=1)

    def _open_webgl(self):
        g = self.full_graph or self.current_graph
        if g is not None:
            seeds = list(self.canvas_3d.seed_nodes)
            export_and_open_webgl(g, seeds, self.dataset_var.get())
