#!/usr/bin/env python3
"""Main Application Window for IM-Benchmark-Lab.

Unified Desktop Platform for Influence Maximization Research:
- Pure CustomTkinter UI (no native Tkinter widget flicker)
- Dark / Light / System modern theme
- Left sidebar navigation
- Top breadcrumb and system health indicators
- Real-time logging & C++ OpenMP Batch Evaluator
"""

from __future__ import annotations
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk

from im_research.gui.core.theme import *
from im_research.gui.core.sidebar import Sidebar
from im_research.gui.core.top_header import TopHeader
from im_research.gui.core.status_bar import StatusBar
from im_research.gui.core.icon_factory import IconSet

from im_research.gui.pages.dashboard import PageDashboard
from im_research.gui.pages.results import PageResults
from im_research.gui.pages.comparison import PageComparison
from im_research.gui.pages.datasets import PageDatasets
from im_research.gui.pages.statistics import PageStatistics
from im_research.gui.pages.experiments import PageExperiments
from im_research.gui.pages.reports import PageReports
from im_research.gui.pages.system_runtime import PageSystemRuntime
from im_research.gui.pages.settings import PageSettings


class IMApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("IM-Benchmark-Lab — Nền tảng Thí nghiệm Tối đa hóa Lan truyền")
        self.geometry("1400x880")
        self.minsize(1100, 700)
        self.configure(fg_color=BG_APP)

        self.icon_set = IconSet()

        # Page registry
        self.pages = {
            "dashboard":   lambda m: PageDashboard(m, on_switch_tab=self.navigate),
            "datasets":    PageDatasets,
            "statistics":  lambda m: PageStatistics(m, on_switch_tab=self.navigate),
            "results":     lambda m: PageResults(m, on_switch_tab=self.navigate),
            "comparison":  lambda m: PageComparison(m, on_switch_tab=self.navigate),
            "experiments": PageExperiments,
            "reports":     lambda m: PageReports(m, on_switch_tab=self.navigate),
            "runtime":     PageSystemRuntime,
            "settings":    PageSettings,
        }

        self._current_page_key = None
        self._page_widget = None
        self._page_cache = {}

        self._build_layout()

    def on_theme_changed(self, mode: str):
        """Propagate theme changes across all application chrome components and cached pages."""
        if hasattr(self, "status_bar"):
            self.status_bar.update_theme_display(mode)
        if hasattr(self, "sidebar"):
            self.sidebar.update_theme_icon(mode)
        if hasattr(self, "top_header"):
            self.top_header.update_theme_display(mode)
        for p in self._page_cache.values():
            if hasattr(p, "on_theme_changed"):
                try:
                    p.on_theme_changed(mode)
                except Exception:
                    pass

    def _build_layout(self):
        # ── Left Navigation Sidebar (236px width) ─────────────────────────────
        self.sidebar = Sidebar(
            self,
            icon_set=self.icon_set,
            on_navigate=self.navigate,
            on_toggle_theme=self.on_theme_changed
        )
        self.sidebar.pack(side="left", fill="y")

        # ── Right Panel: Top Header + Content View + Status Bar ───────────────
        right_panel = ctk.CTkFrame(self, fg_color=BG_APP, corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)

        # Top Application Breadcrumb & Status Header
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

        # Hide currently visible page (instantaneous pack_forget, NO destruction)
        if self._page_widget:
            self._page_widget.pack_forget()

        # Retrieve from cache or lazy-load once
        if key in self._page_cache:
            page = self._page_cache[key]
        else:
            factory = self.pages[key]
            page = factory(self.content_container)
            self._page_cache[key] = page

        # Call on_show callback if page has one (e.g. PageResults, PageComparison)
        if hasattr(page, "on_show"):
            try:
                page.on_show()
            except Exception:
                pass

        # Show page instantaneously
        page.pack(fill="both", expand=True)
        self._page_widget = page
        self._current_page_key = key

        if hasattr(self, "top_header"):
            self.top_header.set_page(key)

        if hasattr(self, "sidebar") and self.sidebar._active_key != key:
            self.sidebar.activate(key)


if __name__ == "__main__":
    app = IMApp()
    app.mainloop()
