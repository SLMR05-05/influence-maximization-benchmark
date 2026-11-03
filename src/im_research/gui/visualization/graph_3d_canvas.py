"""
Interactive 3D Network Graph Canvas for IM-Benchmark-Lab.
Features:
- Real-time 3D rotation, pitch, yaw, zoom, and panning.
- Full multi-input zooming: mouse wheel, laptop touchpad pinch-to-zoom (Control-MouseWheel),
  two-finger swipe, double-click, keyboard shortcuts, and on-screen zoom controls.
- True 3D perspective projection with depth-faded edges and glowing halos.
- Influence Maximization Cascade Simulation:
  * Progressive animated traveling wave: edge color travels gradually from source node to target node.
  * Moving wavefront photon particles and expanding shockwave ripples upon node activation.
- Ultra-crisp rendering: compact node radii, screen-space fixed labels, adaptive light/dark palette.
"""

from __future__ import annotations
import math
import time
from typing import Dict, List, Tuple, Set, Optional, Callable
import tkinter as tk

import numpy as np
import networkx as nx
import customtkinter as ctk

# ── Color Palette ─────────────────────────────────────────────────────────────
COLOR_SEED          = "#ff3366"      # Ruby pink / seed node
COLOR_ACTIVATED     = "#f59e0b"      # Amber pulse / activated node
COLOR_COMMUNITIES   = [
    "#0284c7",  # Sky Blue
    "#8b5cf6",  # Violet
    "#10b981",  # Emerald
    "#ec4899",  # Pink
    "#f97316",  # Orange
    "#06b6d4",  # Cyan
]


class Graph3DCanvas(tk.Canvas):
    """
    High-performance 3D Force-Directed Network Graph Canvas.
    Renders 3D projected vertices and edges with depth-sorting,
    progressive cascade wave animations, and multi-device zoom support.
    """

    def __init__(
        self,
        master,
        on_node_selected: Optional[Callable[[int, dict], None]] = None,
        on_zoom_changed: Optional[Callable[[float], None]] = None,
        on_diffusion_status: Optional[Callable[[int, int, int, bool], None]] = None,
        **kw
    ):
        super().__init__(
            master,
            bg="#ffffff",
            highlightthickness=0,
            borderwidth=0,
            **kw
        )
        self.on_node_selected = on_node_selected
        self.on_zoom_changed = on_zoom_changed
        self.on_diffusion_status = on_diffusion_status

        # Graph Data
        self.graph: Optional[nx.Graph] = None
        self.node_positions_3d: np.ndarray = np.empty((0, 3))
        self.node_degrees: np.ndarray = np.empty(0, dtype=int)
        self.node_communities: List[int] = []
        self.edges: List[Tuple[int, int]] = []
        self.num_nodes: int = 0

        # Influence Maximization States & Progressive Wave Engine
        self.seed_nodes: Set[int] = set()
        self.activated_nodes: Set[int] = set()
        self.activated_edges: Set[Tuple[int, int]] = set()
        self.active_signals: List[dict] = []
        self.node_ripples: List[dict] = []
        self._newly_activated: Set[int] = set()
        self.pulse_step: int = 0
        self.pulse_active: bool = False

        # Camera & Transform
        self.yaw: float = 0.4        # Horizontal rotation (radians)
        self.pitch: float = -0.2     # Vertical tilt (radians)
        self.zoom: float = 1.0       # Zoom multiplier
        self.pan_x: float = 0.0      # Pan offset X
        self.pan_y: float = 0.0      # Pan offset Y
        self.focal_length: float = 550.0
        self.sphere_radius: float = 230.0

        # Animation & Physics
        self.auto_spin: bool = True
        self.spin_speed: float = 0.008
        self.show_labels: bool = True
        self.show_glow: bool = True

        # Mouse Drag State
        self._drag_start_x: int = 0
        self._drag_start_y: int = 0
        self._is_dragging: bool = False
        self._selected_node: Optional[int] = None
        self._hovered_node: Optional[int] = None

        # Projected 2D coordinates cache: node_id -> (screen_x, screen_y, depth_z, radius)
        self._projected_nodes: Dict[int, Tuple[float, float, float, float]] = {}

        self._bind_events()
        self._animation_loop()

    # ------------------------------------------------------------------ #
    #  Event Handlers (Mouse, Laptop Touchpad, Gestures)                 #
    # ------------------------------------------------------------------ #

    def _bind_events(self):
        # Drag to rotate
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

        # Mouse Wheel & Laptop Touchpad Scroll
        self.bind("<MouseWheel>", self._on_mouse_wheel)

        # Laptop Touchpad Pinch-to-zoom (Windows sends Control-MouseWheel)
        self.bind("<Control-MouseWheel>", self._on_ctrl_mouse_wheel)

        # Linux / X11 / external trackpad wheel buttons
        self.bind("<Button-4>", lambda e: self._apply_zoom_delta(120))
        self.bind("<Button-5>", lambda e: self._apply_zoom_delta(-120))
        self.bind("<Control-Button-4>", lambda e: self._apply_zoom_delta(160))
        self.bind("<Control-Button-5>", lambda e: self._apply_zoom_delta(-160))

        # Double click to quick zoom
        self.bind("<Double-Button-1>", lambda e: self._apply_zoom_delta(160))
        self.bind("<Shift-Double-Button-1>", lambda e: self._apply_zoom_delta(-160))

        # Hover detection
        self.bind("<Motion>", self._on_mouse_move)

    def _apply_zoom_delta(self, delta: float):
        """
        Smooth, non-linear zoom handler supporting:
        - Traditional mouse wheel clicks (delta = +/- 120)
        - Laptop touchpad pinch-to-zoom and two-finger swipes (variable continuous deltas)
        """
        if delta == 0:
            return
        abs_d = abs(delta)
        # Scaled rate prevents jumps on high-resolution touchpads
        rate = min(0.35, max(0.04, abs_d / 500.0))
        if delta > 0:
            factor = 1.0 + rate
        else:
            factor = 1.0 / (1.0 + rate)

        new_zoom = max(0.25, min(5.0, self.zoom * factor))
        if abs(new_zoom - self.zoom) > 1e-4:
            self.zoom = new_zoom
            if self.on_zoom_changed:
                self.on_zoom_changed(self.zoom)
            self.redraw()

    def _on_mouse_wheel(self, event):
        self._apply_zoom_delta(event.delta)

    def _on_ctrl_mouse_wheel(self, event):
        # Laptop Touchpad Pinch-to-zoom
        self._apply_zoom_delta(event.delta * 1.4)

    def zoom_in(self):
        """Programmatic zoom in."""
        self._apply_zoom_delta(160)

    def zoom_out(self):
        """Programmatic zoom out."""
        self._apply_zoom_delta(-160)

    def _on_mouse_down(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._is_dragging = True

        clicked = self._find_node_at_screen(event.x, event.y)
        if clicked is not None:
            self._selected_node = clicked
            if self.on_node_selected and self.graph:
                info = self._get_node_info(clicked)
                self.on_node_selected(clicked, info)
            self.redraw()

    def _on_mouse_drag(self, event):
        if not self._is_dragging:
            return
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y

        self.yaw += dx * 0.007
        self.pitch += dy * 0.007
        self.pitch = max(-1.45, min(1.45, self.pitch))

        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.redraw()

    def _on_mouse_up(self, event):
        self._is_dragging = False

    def _on_mouse_move(self, event):
        hovered = self._find_node_at_screen(event.x, event.y)
        if hovered != self._hovered_node:
            self._hovered_node = hovered
            self.redraw()

    def _find_node_at_screen(self, x: float, y: float, hit_radius: float = 12.0) -> Optional[int]:
        closest_node = None
        min_depth = float("inf")

        for u, (sx, sy, sz, rad) in self._projected_nodes.items():
            dist = math.hypot(x - sx, y - sy)
            if dist <= max(rad + 2, hit_radius):
                if sz < min_depth:
                    min_depth = sz
                    closest_node = u
        return closest_node

    # ------------------------------------------------------------------ #
    #  Graph Loading & 3D Layout Initialization                          #
    # ------------------------------------------------------------------ #

    def set_graph(self, nx_graph: nx.Graph, seed_nodes: Optional[List[int]] = None):
        """Loads a NetworkX graph and computes its 3D force-directed layout."""
        self.graph = nx_graph
        self.num_nodes = nx_graph.number_of_nodes()
        self.edges = list(nx_graph.edges())

        # 3D Spring Layout via NetworkX
        pos_dict = nx.spring_layout(nx_graph, dim=3, iterations=60, seed=42)
        pos_list = [pos_dict[u] for u in sorted(nx_graph.nodes())]
        self.node_positions_3d = np.array(pos_list, dtype=np.float64)

        # Center and normalize positions
        centroid = self.node_positions_3d.mean(axis=0)
        self.node_positions_3d -= centroid
        max_dist = np.linalg.norm(self.node_positions_3d, axis=1).max()
        if max_dist > 0:
            self.node_positions_3d /= max_dist

        # Compute degrees
        self.node_degrees = np.array([nx_graph.degree(u) for u in sorted(nx_graph.nodes())], dtype=int)

        # Louvain / Greedy Communities for coloring
        try:
            comms = list(nx.community.greedy_modularity_communities(nx_graph))
            self.node_communities = [0] * self.num_nodes
            for cid, cset in enumerate(comms):
                for u in cset:
                    if u < self.num_nodes:
                        self.node_communities[u] = cid
        except Exception:
            self.node_communities = [0] * self.num_nodes

        # Set seed nodes & reset states
        self.seed_nodes = set(seed_nodes or self._default_seeds())
        self.activated_nodes = set(self.seed_nodes)
        self.activated_edges.clear()
        self.active_signals.clear()
        self.node_ripples.clear()
        self._newly_activated.clear()
        self.pulse_active = False
        self.pulse_step = 0
        self._selected_node = next(iter(self.seed_nodes)) if self.seed_nodes else (0 if self.num_nodes > 0 else None)

        self.redraw()

    def _default_seeds(self) -> List[int]:
        if self.num_nodes == 0:
            return []
        deg_pairs = [(self.node_degrees[u], u) for u in range(self.num_nodes)]
        deg_pairs.sort(reverse=True)
        k = min(5, max(1, self.num_nodes // 8))
        return [u for _, u in deg_pairs[:k]]

    # ------------------------------------------------------------------ #
    #  Progressive Cascade Simulation Engine                             #
    # ------------------------------------------------------------------ #

    def trigger_diffusion_simulation(self):
        """
        Initiates an authentic step-by-step IC diffusion wave.
        Edge colors travel gradually from source to target, accompanied by
        moving photon particles and activation shockwaves!
        """
        if not self.graph or self.num_nodes == 0:
            return

        self.activated_nodes = set(self.seed_nodes)
        self.activated_edges.clear()
        self.active_signals.clear()
        self.node_ripples.clear()
        self.pulse_active = True
        self.pulse_step = 1
        self._newly_activated = set(self.seed_nodes)

        # Launch initial wave along incident edges of seeds
        self._launch_signals_from(self.seed_nodes)

        if self.on_diffusion_status:
            self.on_diffusion_status(
                self.pulse_step, len(self.activated_nodes), self.num_nodes, True
            )

        self.redraw()

    def _launch_signals_from(self, sources: Set[int]) -> bool:
        """Launches moving signal packets along edges toward unactivated neighbors."""
        launched = False
        p_activation = 0.40  # Independent Cascade propagation probability

        for u in sources:
            if not self.graph.has_node(u):
                continue
            for v in self.graph.neighbors(u):
                if v not in self.activated_nodes:
                    # Prevent duplicate signals to the same target in the same wave
                    if any(s["v"] == v for s in self.active_signals):
                        continue
                    success = (np.random.random() < p_activation)
                    self.active_signals.append({
                        "u": u,
                        "v": v,
                        "progress": 0.0,
                        "speed": 0.045,  # ~22 animation frames per hop (smooth speed)
                        "success": success,
                    })
                    launched = True
        return launched

    # ------------------------------------------------------------------ #
    #  3D Math & Rendering Engine                                        #
    # ------------------------------------------------------------------ #

    def _get_rotation_matrix(self) -> np.ndarray:
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        return np.array([
            [cy, 0.0, sy],
            [sp * sy, cp, -sp * cy],
            [-cp * sy, sp, cp * cy],
        ], dtype=np.float64)

    def redraw(self):
        """Renders all 3D edges, progressive signals, glowing halos, and vertices."""
        self.delete("all")

        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10 or self.num_nodes == 0:
            return

        # Adaptive Dark / Light mode colors
        mode = ctk.get_appearance_mode().lower()
        is_dark = (mode == "dark")
        target_bg = "#080b11" if is_dark else "#ffffff"
        if self.cget("bg") != target_bg:
            self.configure(bg=target_bg)

        color_edge_active = "#38bdf8" if is_dark else "#0284c7"

        cx = w / 2.0 + self.pan_x
        cy = h / 2.0 + self.pan_y
        R = self.sphere_radius * self.zoom

        # 1. Rotate 3D vertices
        R_mat = self._get_rotation_matrix()
        scaled_coords = self.node_positions_3d * R
        rotated = scaled_coords @ R_mat.T  # Shape: (N, 3)

        # 2. Perspective Project
        D_cam = self.focal_length
        z_vals = rotated[:, 2]
        factors = D_cam / (D_cam + z_vals)

        screen_x = cx + rotated[:, 0] * factors
        screen_y = cy + rotated[:, 1] * factors

        # Screen-space compact node radius (crisp, fine resolution, doesn't balloon)
        max_deg = max(1.0, float(self.node_degrees.max())) if len(self.node_degrees) > 0 else 1.0
        deg_ratio = self.node_degrees / max_deg
        screen_radii = 1.8 + deg_ratio * 1.2

        # Update cache
        self._projected_nodes.clear()
        for u in range(self.num_nodes):
            self._projected_nodes[u] = (
                float(screen_x[u]), float(screen_y[u]), float(z_vals[u]), float(screen_radii[u])
            )

        # 3. Background Orbit Rings
        self._draw_background_rings(cx, cy, R, is_dark)

        # 4A. Render Base Graph Edges (Depth Sorted)
        edge_data = []
        for u, v in self.edges:
            if u >= self.num_nodes or v >= self.num_nodes:
                continue
            z_mid = (z_vals[u] + z_vals[v]) / 2.0
            edge_data.append((z_mid, u, v))

        # Back to front
        edge_data.sort(key=lambda item: item[0], reverse=True)

        hovered = self._hovered_node
        selected = self._selected_node

        for z_mid, u, v in edge_data:
            is_active = (hovered in (u, v)) or (selected in (u, v))
            is_cascaded = ((u, v) in self.activated_edges) or ((v, u) in self.activated_edges)

            x1, y1 = screen_x[u], screen_y[u]
            x2, y2 = screen_x[v], screen_y[v]

            if is_active:
                color = color_edge_active
                width = 2.0
            elif is_cascaded:
                # Permanent energized cascade trail
                color = "#f59e0b" if not is_dark else "#fbbf24"
                width = 1.6
            else:
                norm_z = (z_mid + R) / (2.0 * R)
                norm_z = max(0.0, min(1.0, norm_z))
                if is_dark:
                    color = "#071c2e" if norm_z > 0.65 else ("#0c2d48" if norm_z > 0.35 else "#0369a1")
                else:
                    color = "#e2e8f0" if norm_z > 0.65 else ("#cbd5e1" if norm_z > 0.35 else "#94a3b8")
                width = 0.8 if norm_z > 0.65 else (1.0 if norm_z > 0.35 else 1.2)

            self.create_line(x1, y1, x2, y2, fill=color, width=width)

        # 4B. Render In-Flight Progressive Traveling Signals (Signal traveling along edge!)
        for s in self.active_signals:
            u, v = s["u"], s["v"]
            if u not in self._projected_nodes or v not in self._projected_nodes:
                continue
            x_u, y_u, _, _ = self._projected_nodes[u]
            x_v, y_v, _, _ = self._projected_nodes[v]
            p = min(1.0, max(0.0, s["progress"]))

            # Calculate leading wave head coordinate
            x_head = x_u + (x_v - x_u) * p
            y_head = y_u + (y_v - y_u) * p

            # 1. Progressive colored line: grows gradually from node u to x_head, y_head
            color_trail = "#f59e0b" if is_dark else "#d97706"
            self.create_line(x_u, y_u, x_head, y_head, fill=color_trail, width=2.4)

            # 2. Moving Wavefront Pulse Particle (Bright photon orb at x_head, y_head)
            glow_rad = 4.5
            core_rad = 2.2
            # Outer glow halo
            self.create_oval(
                x_head - glow_rad, y_head - glow_rad,
                x_head + glow_rad, y_head + glow_rad,
                fill="", outline="#fbbf24", width=1.4
            )
            # Inner bright spark
            self.create_oval(
                x_head - core_rad, y_head - core_rad,
                x_head + core_rad, y_head + core_rad,
                fill="#ffffff", outline="#f59e0b", width=1.0
            )

        # 4C. Render Node Shockwave Ripples (expanding activation ring)
        for r in self.node_ripples:
            u = r["u"]
            if u in self._projected_nodes:
                sx, sy, _, _ = self._projected_nodes[u]
                rad = r["radius"]
                self.create_oval(
                    sx - rad, sy - rad, sx + rad, sy + rad,
                    outline="#f59e0b", width=1.4, dash=(3, 3)
                )

        # 5. Render Nodes (Depth Sorted: back to front)
        node_order = list(range(self.num_nodes))
        node_order.sort(key=lambda u: z_vals[u], reverse=True)

        for u in node_order:
            sx, sy, sz, base_rad = self._projected_nodes[u]
            deg = self.node_degrees[u]
            is_seed = u in self.seed_nodes
            is_activated = u in self.activated_nodes
            is_hovered = (u == hovered)
            is_selected = (u == selected)

            comm_id = self.node_communities[u] % len(COLOR_COMMUNITIES)
            comm_color = COLOR_COMMUNITIES[comm_id]

            if is_seed:
                rad = base_rad + 0.8
                core_color = "#ffffff"
                halo_color = COLOR_SEED
            elif is_activated:
                rad = base_rad + 0.6
                core_color = "#ffffff"
                halo_color = COLOR_ACTIVATED
            elif deg >= 10 or is_hovered or is_selected:
                rad = base_rad + 0.4
                core_color = "#ffffff" if is_dark else "#0284c7"
                halo_color = "#00e5ff" if is_dark else "#0284c7"
            else:
                rad = base_rad
                core_color = comm_color
                halo_color = comm_color

            # A. Outer Halo Ring
            if self.show_glow and (is_seed or is_activated or is_hovered or is_selected or deg >= 12):
                halo_rad = rad + 2.0
                self.create_oval(
                    sx - halo_rad, sy - halo_rad, sx + halo_rad, sy + halo_rad,
                    fill="", outline=halo_color, width=1.0
                )

            # B. Inner Core Node Disc
            border_col = ("#ffffff" if is_dark else "#0f172a") if (is_hovered or is_selected) else halo_color
            border_width = 1.0 if (is_hovered or is_selected or is_seed or is_activated) else 0.7
            self.create_oval(
                sx - rad, sy - rad, sx + rad, sy + rad,
                fill=core_color, outline=border_col, width=border_width
            )

            # C. Fixed Screen-Space Node Labels for ALL nodes
            if self.show_labels:
                label_text = f"v{u}"
                if is_seed:
                    label_fg = "#ff3366" if is_dark else "#dc2626"
                    font_w = "bold"
                    font_sz = 7
                elif is_activated:
                    label_fg = "#f59e0b" if is_dark else "#d97706"
                    font_w = "bold"
                    font_sz = 7
                elif is_hovered or is_selected:
                    label_fg = "#00e5ff" if is_dark else "#0284c7"
                    font_w = "bold"
                    font_sz = 7
                else:
                    label_fg = "#94a3b8" if is_dark else "#334155"
                    font_w = "normal"
                    font_sz = 6

                self.create_text(
                    sx + rad + 2.5, sy - 1,
                    text=label_text,
                    fill=label_fg,
                    font=("Segoe UI", font_sz, font_w),
                    anchor="w"
                )

    def _draw_background_rings(self, cx: float, cy: float, R: float, is_dark: bool):
        ring_col = "#0c1824" if is_dark else "#f1f5f9"
        r_x = R * 1.15
        r_y = R * 0.35 * abs(math.cos(self.pitch))
        self.create_oval(
            cx - r_x, cy - r_y, cx + r_x, cy + r_y,
            outline=ring_col, width=1, dash=(4, 6)
        )

    # ------------------------------------------------------------------ #
    #  Animation Loop                                                    #
    # ------------------------------------------------------------------ #

    def _animation_loop(self):
        need_redraw = False

        # Continuous celestial auto-rotation
        if self.auto_spin and not self._is_dragging:
            self.yaw += self.spin_speed
            if self.yaw > 2.0 * math.pi:
                self.yaw -= 2.0 * math.pi
            need_redraw = True

        # Diffusion Wave Progression
        if self.pulse_active and self.graph:
            need_redraw = True
            new_activations_this_frame = set()

            # Advance all traveling signals
            for s in self.active_signals:
                s["progress"] += s["speed"]
                if s["progress"] >= 1.0:
                    u, v = s["u"], s["v"]
                    if s["success"] and v not in self.activated_nodes:
                        self.activated_nodes.add(v)
                        self.activated_edges.add((u, v))
                        self.activated_edges.add((v, u))
                        new_activations_this_frame.add(v)
                        # Add expanding shockwave ripple around newly activated node v
                        self.node_ripples.append({
                            "u": v,
                            "radius": 4.0,
                            "max_radius": 22.0,
                        })

            # Retain in-flight signals
            self.active_signals = [s for s in self.active_signals if s["progress"] < 1.0]

            # Update ripples
            for r in self.node_ripples:
                r["radius"] += 1.2
            self.node_ripples = [r for r in self.node_ripples if r["radius"] < r["max_radius"]]

            # Track newly activated nodes for the next wave
            if new_activations_this_frame:
                self._newly_activated.update(new_activations_this_frame)
                if self.on_diffusion_status:
                    self.on_diffusion_status(
                        self.pulse_step, len(self.activated_nodes), self.num_nodes, True
                    )

            # If all signals in current hop finished:
            if len(self.active_signals) == 0:
                if self._newly_activated:
                    frontier = set(self._newly_activated)
                    self._newly_activated.clear()
                    self.pulse_step += 1
                    has_more = self._launch_signals_from(frontier)
                    if not has_more and len(self.active_signals) == 0:
                        self.pulse_active = False
                        if self.on_diffusion_status:
                            self.on_diffusion_status(
                                self.pulse_step, len(self.activated_nodes), self.num_nodes, False
                            )
                else:
                    self.pulse_active = False
                    if self.on_diffusion_status:
                        self.on_diffusion_status(
                            self.pulse_step, len(self.activated_nodes), self.num_nodes, False
                        )

        if need_redraw:
            self.redraw()

        self.after(30, self._animation_loop)

    def reset_camera(self):
        self.yaw = 0.4
        self.pitch = -0.2
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        if self.on_zoom_changed:
            self.on_zoom_changed(self.zoom)
        self.redraw()

    def _get_node_info(self, u: int) -> dict:
        deg = int(self.node_degrees[u])
        neighbors = list(self.graph.neighbors(u)) if self.graph else []
        clustering = round(float(nx.clustering(self.graph, u)), 4) if self.graph else 0.0
        return {
            "id": u,
            "degree": deg,
            "clustering": clustering,
            "neighbors": sorted(neighbors),
            "is_seed": u in self.seed_nodes,
            "is_activated": u in self.activated_nodes,
            "community": self.node_communities[u] if u < len(self.node_communities) else 0,
        }
