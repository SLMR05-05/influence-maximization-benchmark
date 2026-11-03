#!/usr/bin/env python3
"""
IM-Benchmark-Lab — Influence Maximization Research Platform
Main Desktop Application using CustomTkinter
Entry point: imports all page modules from separate files.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.sidebar import Sidebar
from im_research.gui.core.ui_helpers import section_header, metric_card
from im_research.gui.core.status_bar import StatusBar

from im_research.gui.pages.dashboard import PageDashboard
from im_research.gui.pages.results import PageResults
from im_research.gui.pages.comparison import PageComparison
from im_research.gui.pages.datasets import PageDatasets
from im_research.gui.pages.experiments import PageExperiments
from im_research.gui.pages.reports import PageReports
from im_research.gui.pages.settings import PageSettings

from im_research.gui.core.icon_factory import IconSet
from im_research.gui.visualization.graph_explorer_view import GraphExplorerView


class IMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("IM-Benchmark-Lab — Influence Maximization Research Platform")
        self.geometry("1360x860")
        self.minsize(980, 680)

        self.icon_set = IconSet(target_size=24)

        self.pages = {
            "dashboard":   lambda m: PageDashboard(m, on_switch_tab=self.navigate),
            "results":     PageResults,
            "comparison":  PageComparison,
            "datasets":    PageDatasets,
            "experiments": PageExperiments,
            "reports":     PageReports,
            "settings":    PageSettings,
        }

        self._current_page_key = None
        self._page_widget = None

        self._build_layout()

    def on_theme_changed(self, mode: str):
        if hasattr(self, "status_bar"):
            self.status_bar.update_theme_display(mode)
        if hasattr(self, "sidebar"):
            self.sidebar.update_theme_icon(mode)

    def _build_layout(self):
        self.sidebar = Sidebar(self, icon_set=self.icon_set, on_navigate=self.navigate)
        self.sidebar.pack(side="left", fill="y")

        right_panel = ctk.CTkFrame(self, fg_color=BG_APP, corner_radius=0)
        right_panel.pack(side="right", fill="both", expand=True)

        self.content_container = ctk.CTkFrame(right_panel, fg_color=BG_APP, corner_radius=0)
        self.content_container.pack(side="top", fill="both", expand=True, padx=24, pady=18)

        self.status_bar = StatusBar(right_panel)
        self.status_bar.pack(side="bottom", fill="x")

        self.sidebar.activate("dashboard")

    def navigate(self, key: str):
        if key not in self.pages:
            return
        if self._page_widget:
            self._page_widget.destroy()
        factory = self.pages[key]
        self._page_widget = factory(self.content_container)
        self._page_widget.pack(fill="both", expand=True)
        self._current_page_key = key


if __name__ == "__main__":
    app = IMApp()
    app.mainloop()
