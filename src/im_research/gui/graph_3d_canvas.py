"""
Interactive 3D Network Graph Canvas for IM-Benchmark-Lab.
Features:
- Real-time 3D rotation, pitch, yaw, zoom, and panning.
- True 3D perspective projection with depth-faded edges and glowing halos.
- Auto-spin animation loop (gentle celestial drift).
- Mouse interaction: drag to rotate, wheel to zoom, click to inspect.
- Influence Maximization visualization: seed nodes glow golden/ruby, diffusion pulse wave animation.
- Clean dark cosmic aesthetic matching modern knowledge graph explorers.
"""

from __future__ import annotations
import math
import time
from typing import Dict, List, Tuple, Set, Optional, Callable
import tkinter as tk

import numpy as np
import networkx as nx
import customtkinter as ctk

# ── Color Palette (Dark Cyber / Celestial Aesthetic) ──────────────────────────
COLOR_BG            = "#080b11"
COLOR_GRID          = "#0d1522"
COLOR_EDGE_BASE     = "#0c2d48"
COLOR_EDGE_GLOW     = "#00bcd4"
COLOR_EDGE_ACTIVE   = "#38bdf8"
COLOR_NODE_HUB      = "#ffffff"
COLOR_NODE_HALO     = "#00e5ff"
COLOR_SEED          = "#ff3366"      # Ruby pink / seed node
COLOR_ACTIVATED     = "#fbbf24"      # Amber pulse / activated node
COLOR_COMMUNITIES   = [
    "#00e5ff",  # Electric Cyan
    "#818cf8",  # Indigo
    "#a855f7",  # Purple
    "#34d399",  # Emerald Mint
    "#f472b6",  # Rose Pink
    "#38bdf8",  # Sky Blue
]


class Graph3DCanvas(tk.Canvas):
    """
    High-performance 3D Force-Directed Network Graph Canvas.
    Renders 3D projected vertices and edges with depth-sorting,
    halo glows, and smooth interactive camera manipulation.
    """

    def __init__(
        self,
        master,
        on_node_selected: Optional[Callable[[int, dict], None]] = None,
        **kw
    ):
        super().__init__(
            master,
            bg=COLOR_BG,
            highlightthickness=0,
            borderwidth=0,
            **kw
        )
        self.on_node_selected = on_node_selected

        # Graph Data
        self.graph: Optional[nx.Graph] = None
        self.node_positions_3d: np.ndarray = np.empty((0, 3))
        self.node_degrees: np.ndarray = np.empty(0, dtype=int)
        self.node_communities: List[int] = []
        self.edges: List[Tuple[int, int]] = []
        self.num_nodes: int = 0

        # Influence Maximization States
        self.seed_nodes: Set[int] = set()
        self.activated_nodes: Set[int] = set()
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
    #  Event Handlers                                                    #
    # ------------------------------------------------------------------ #

    def _bind_events(self):
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.bind("<MouseWheel>", self._on_mouse_wheel)
        self.bind("<Motion>", self._on_mouse_move)

    def _on_mouse_down(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._is_dragging = True

        # Check if a node was clicked
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
        # Clamp pitch to avoid gimbal flipping
        self.pitch = max(-1.45, min(1.45, self.pitch))

        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.redraw()

    def _on_mouse_up(self, event):
        self._is_dragging = False

    def _on_mouse_wheel(self, event):
        delta = event.delta / 120.0
        scale = 1.12 if delta > 0 else 0.89
        self.zoom = max(0.35, min(3.5, self.zoom * scale))
        self.redraw()

    def _on_mouse_move(self, event):
        hovered = self._find_node_at_screen(event.x, event.y)
        if hovered != self._hovered_node:
            self._hovered_node = hovered
            self.redraw()

    def _find_node_at_screen(self, x: float, y: float, hit_radius: float = 14.0) -> Optional[int]:
        """Finds closest node within hit_radius, prioritizing nearest in depth."""
        closest_node = None
        min_depth = float("inf")

        for u, (sx, sy, sz, rad) in self._projected_nodes.items():
            dist = math.hypot(x - sx, y - sy)
            if dist <= max(rad, hit_radius):
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

        # Compute 3D Spring Layout via NetworkX
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

        # Compute Louvain / Greedy Communities for coloring
        try:
            comms = list(nx.community.greedy_modularity_communities(nx_graph))
            self.node_communities = [0] * self.num_nodes
            for cid, cset in enumerate(comms):
                for u in cset:
                    if u < self.num_nodes:
                        self.node_communities[u] = cid
        except Exception:
            self.node_communities = [0] * self.num_nodes

        # Set seed nodes
        self.seed_nodes = set(seed_nodes or self._default_seeds())
        self.activated_nodes = set(self.seed_nodes)
        self._selected_node = next(iter(self.seed_nodes)) if self.seed_nodes else 0

        self.redraw()

    def _default_seeds(self) -> List[int]:
        """Chooses top 3-5 highest degree nodes as default seed set."""
        if self.num_nodes == 0:
            return []
        deg_pairs = [(self.node_degrees[u], u) for u in range(self.num_nodes)]
        deg_pairs.sort(reverse=True)
        k = min(5, max(1, self.num_nodes // 8))
        return [u for _, u in deg_pairs[:k]]

    # ------------------------------------------------------------------ #
    #  3D Math & Projection Engine                                       #
    # ------------------------------------------------------------------ #

    def _get_rotation_matrix(self) -> np.ndarray:
        """Returns 3D rotation matrix for current yaw and pitch."""
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)

        # R = R_pitch * R_yaw
        return np.array([
            [cy, 0.0, sy],
            [sp * sy, cp, -sp * cy],
            [-cp * sy, sp, cp * cy],
        ], dtype=np.float64)

    def redraw(self):
        """Renders all 3D edges, glowing halos, and vertices with depth sorting."""
        self.delete("all")

        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10 or self.num_nodes == 0:
            return

        # Adaptive Dark / Light mode colors
        mode = ctk.get_appearance_mode().lower()
        is_dark = (mode == "dark")
        target_bg = "#080b11" if is_dark else "#f8fafc"
        if self.cget("bg") != target_bg:
            self.configure(bg=target_bg)

        color_edge_active = "#38bdf8" if is_dark else "#0284c7"
        color_edge_glow = "#00bcd4" if is_dark else "#0369a1"

        cx = w / 2.0 + self.pan_x
        cy = h / 2.0 + self.pan_y
        R = self.sphere_radius * self.zoom

        # 1. Rotate 3D vertices
        R_mat = self._get_rotation_matrix()
        scaled_coords = self.node_positions_3d * R
        rotated = scaled_coords @ R_mat.T  # Shape: (N, 3)

        # 2. Perspective Project
        # z in camera frame: positive = away, negative = towards camera
        # D_cam + z is distance from camera
        D_cam = self.focal_length
        z_vals = rotated[:, 2]
        factors = D_cam / (D_cam + z_vals)

        screen_x = cx + rotated[:, 0] * factors
        screen_y = cy + rotated[:, 1] * factors

        # Compute node screen radius based on degree (compact & crisp, fixed scale on zoom)
        max_deg = max(1.0, float(self.node_degrees.max())) if len(self.node_degrees) > 0 else 1.0
        deg_ratio = self.node_degrees / max_deg
        screen_radii = 2.6 + deg_ratio * 1.2

        # Update cache
        self._projected_nodes.clear()
        for u in range(self.num_nodes):
            self._projected_nodes[u] = (
                screen_x[u], screen_y[u], z_vals[u], screen_radii[u]
            )

        # 3. Draw Background Cosmic Starfield / Grid Rings
        self._draw_background_rings(cx, cy, R)

        # 4. Render Edges (Depth Sorted)
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
            # Check if edge is incident to hovered or selected node
            is_active = (hovered in (u, v)) or (selected in (u, v))
            is_diffusion = (u in self.activated_nodes) and (v in self.activated_nodes)

            x1, y1 = screen_x[u], screen_y[u]
            x2, y2 = screen_y[u], screen_y[v]  # Correct coordinate unpacking
            x2 = screen_x[v]

            if is_active:
                color = color_edge_active
                width = 2.4
            elif is_diffusion:
                color = color_edge_glow
                width = 1.6
            else:
                # Depth fading: further edges are dimmer/darker
                norm_z = (z_mid + R) / (2.0 * R)  # 0 (front) to 1 (back)
                norm_z = max(0.0, min(1.0, norm_z))
                if is_dark:
                    color = "#071c2e" if norm_z > 0.65 else ("#0c2d48" if norm_z > 0.35 else "#0369a1")
                else:
                    color = "#e2e8f0" if norm_z > 0.65 else ("#cbd5e1" if norm_z > 0.35 else "#64748b")
                width = 0.9 if norm_z > 0.65 else (1.1 if norm_z > 0.35 else 1.4)

            self.create_line(x1, y1, x2, y2, fill=color, width=width)

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

            # Determine colors and compact radius
            comm_id = self.node_communities[u] % len(COLOR_COMMUNITIES)
            comm_color = COLOR_COMMUNITIES[comm_id]

            if is_seed:
                rad = base_rad + 1.2
                core_color = "#ffffff"
                halo_color = COLOR_SEED
            elif is_activated:
                rad = base_rad + 0.8
                core_color = "#ffffff"
                halo_color = COLOR_ACTIVATED
            elif deg >= 10 or is_hovered or is_selected:
                rad = base_rad + 0.5
                core_color = "#ffffff" if is_dark else "#0284c7"
                halo_color = "#00e5ff" if is_dark else "#0284c7"
            else:
                rad = base_rad
                core_color = comm_color
                halo_color = comm_color

            # A. Draw Tight Outer Halo Ring (only for seeds, active, hovered, or top hubs)
            if self.show_glow and (is_seed or is_hovered or is_selected or deg >= 12):
                halo_rad = rad + 2.5
                self.create_oval(
                    sx - halo_rad, sy - halo_rad, sx + halo_rad, sy + halo_rad,
                    fill="", outline=halo_color, width=1.2
                )

            # B. Draw Inner Core Node Disc
            border_col = ("#ffffff" if is_dark else "#0f172a") if (is_hovered or is_selected) else halo_color
            border_width = 1.2 if (is_hovered or is_selected or is_seed) else 0.8
            self.create_oval(
                sx - rad, sy - rad, sx + rad, sy + rad,
                fill=core_color, outline=border_col, width=border_width
            )

            # C. Draw Node Label for ALL nodes (crisp, fixed-size 7pt font, no distorting zoom)
            if self.show_labels:
                label_text = f"v{u}"
                if is_seed:
                    label_fg = "#ff3366" if is_dark else "#e11d48"
                    font_w = "bold"
                elif is_hovered or is_selected:
                    label_fg = "#00e5ff" if is_dark else "#0284c7"
                    font_w = "bold"
                else:
                    label_fg = "#94a3b8" if is_dark else "#475569"
                    font_w = "normal"

                self.create_text(
                    sx + rad + 3, sy - 1,
                    text=label_text,
                    fill=label_fg,
                    font=("Segoe UI", 7, font_w),
                    anchor="w"
                )

    def _draw_background_rings(self, cx: float, cy: float, R: float):
        """Draws subtle orbital perspective circles in the background."""
        is_dark = (ctk.get_appearance_mode().lower() == "dark")
        ring_col = "#0c1824" if is_dark else "#e2e8f0"
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
        if self.auto_spin and not self._is_dragging:
            self.yaw += self.spin_speed
            if self.yaw > 2.0 * math.pi:
                self.yaw -= 2.0 * math.pi
            self.redraw()

        # Diffusion Wave Pulse Animation
        if self.pulse_active and self.graph:
            self.pulse_step += 1
            if self.pulse_step % 12 == 0:
                self._expand_diffusion_step()

        self.after(35, self._animation_loop)

    def trigger_diffusion_simulation(self):
        """Initiates a visual step-by-step IC diffusion wave from seed nodes."""
        self.activated_nodes = set(self.seed_nodes)
        self.pulse_active = True
        self.pulse_step = 0
        self.redraw()

    def _expand_diffusion_step(self):
        """Expands activation wave to 1-hop neighbors probabilistically."""
        newly_active = set()
        for u in list(self.activated_nodes):
            for v in self.graph.neighbors(u):
                if v not in self.activated_nodes:
                    # 40% chance to activate for visually pleasing demo
                    if np.random.random() < 0.35:
                        newly_active.add(v)
        if newly_active:
            self.activated_nodes.update(newly_active)
            self.redraw()
        else:
            # Completed
            self.pulse_active = False

    def reset_camera(self):
        self.yaw = 0.4
        self.pitch = -0.2
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.redraw()

    def _get_node_info(self, u: int) -> dict:
        """Collects topological metadata for the clicked node."""
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

