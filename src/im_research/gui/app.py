#!/usr/bin/env python3
"""
IM-Benchmark-Lab — Influence Maximization Research Platform
Main Desktop Application using CustomTkinter
Modern UI Redesign with structured Brand Sidebar, Top Header Breadcrumb, and Status Bar.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.sidebar import Sidebar
from im_research.gui.core.top_header import TopHeader
from im_research.gui.core.status_bar import StatusBar
from im_research.gui.core.icon_factory import IconSet

from im_research.gui.pages.dashboard import PageDashboard
from im_research.gui.pages.results import PageResults
from im_research.gui.pages.comparison import PageComparison
from im_research.gui.pages.datasets import PageDatasets
from im_research.gui.pages.experiments import PageExperiments
from im_research.gui.pages.reports import PageReports
from im_research.gui.pages.settings import PageSettings


class IMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IM-Benchmark-Lab — Influence Maximization Research Platform")
        self.geometry("1420x880")
        self.minsize(1080, 720)

        # High-DPI icon generator
        self.icon_set = IconSet(target_size=20)

        self.pages = {
            "dashboard":   lambda m: PageDashboard(m, on_switch_tab=self.navigate),
            "datasets":    PageDatasets,
            "results":     lambda m: PageResults(m, on_switch_tab=self.navigate),
            "comparison":  lambda m: PageComparison(m, on_switch_tab=self.navigate),
            "experiments": PageExperiments,
            "reports":     lambda m: PageReports(m, on_switch_tab=self.navigate),
            "settings":    PageSettings,
        }

        self._current_page_key = None
        self._page_widget = None
        self._cached_pages = {}

        self._build_layout()

    def on_theme_changed(self, mode: str):
        """Propagate theme changes across all application chrome components."""
        if hasattr(self, "status_bar"):
            self.status_bar.update_theme_display(mode)
        if hasattr(self, "sidebar"):
            self.sidebar.update_theme_icon(mode)
        if hasattr(self, "top_header"):
            self.top_header.update_theme_display(mode)

    def _build_layout(self):
        # ── Left Navigation Sidebar (236px width) ─────────────────────────────
        self.sidebar = Sidebar(
            self,
            icon_set=self.icon_set,
            on_navigate=self.navigate,
            on_toggle_theme=self.on_theme_changed
        )
        self.sidebar.pack(side="left", fill="y")

        # ── Right Main Content Area ───────────────────────────────────────────
        right_panel = ctk.CTkFrame(self, fg_color=BG_APP, corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)

        # Top Application Header with Breadcrumb and Status Pills
        self.top_header = TopHeader(
            right_panel,
            icon_set=self.icon_set,
            on_toggle_theme=self.on_theme_changed
        )
        self.top_header.pack(side="top", fill="x")

        # Dynamic Page Content Container
        self.content_container = ctk.CTkFrame(right_panel, fg_color=BG_APP, corner_radius=0)
        self.content_container.pack(side="top", fill="both", expand=True, padx=20, pady=16)

        # Bottom System Status Bar
        self.status_bar = StatusBar(right_panel)
        self.status_bar.pack(side="bottom", fill="x")

        # Default initial page
        self.sidebar.activate("dashboard")

    def navigate(self, key: str):
        if key not in self.pages:
            return

        if self._page_widget:
            if self._current_page_key == "experiments":
                self._page_widget.pack_forget()
            else:
                self._page_widget.destroy()
            self._page_widget = None

        if key == "experiments" and key in self._cached_pages:
            self._page_widget = self._cached_pages[key]
            self._page_widget.pack(fill="both", expand=True)
            if hasattr(self._page_widget, "on_show"):
                self._page_widget.on_show()
        else:
            factory = self.pages[key]
            self._page_widget = factory(self.content_container)
            self._page_widget.pack(fill="both", expand=True)
            if key == "experiments":
                self._cached_pages[key] = self._page_widget

        self._current_page_key = key

        if hasattr(self, "top_header"):
            self.top_header.set_page(key)

        if hasattr(self, "sidebar") and self.sidebar._active_key != key:
            self.sidebar.activate(key)


if __name__ == "__main__":
    app = IMApp()
    app.mainloop()
