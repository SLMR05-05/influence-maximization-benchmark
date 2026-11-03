"""Theme constants, color palette, and fonts for IM-Benchmark-Lab GUI."""
from pathlib import Path
import sys
import customtkinter as ctk
from im_research.core.theme_config import get_theme, set_theme

# ── Appearance & Theme ────────────────────────────────────────────────────────
INITIAL_THEME = get_theme()
ctk.set_appearance_mode(INITIAL_THEME)
ctk.set_default_color_theme("blue")

# ── Color Palette (Adaptive Light & Dark Tuples) ──────────────────────────────
BG_APP         = ("#f8f9fa", "#0b0f19")
SIDEBAR_BG     = ("#ffffff", "#0f172a")
ACTIVE_BG      = "#1a73e8"
INACTIVE_HOVER = ("#f1f3f4", "#1e293b")
BORDER_COLOR   = ("#e8eaed", "#1e293b")
CARD_BG        = ("#ffffff", "#131c31")
HEADER_FG      = ("#202124", "#f8fafc")
SUBTEXT_FG     = ("#5f6368", "#94a3b8")
STATUS_BG      = ("#e8f0fe", "#0a101d")
STATUS_FG      = ("#174ea6", "#38bdf8")
DIVIDER        = ("#e8eaed", "#1e293b")
BLUE           = "#1a73e8"
GREEN          = "#1e8e3e"
ORANGE         = "#f9ab00"
RED            = "#d93025"
PURPLE         = "#9334e6"
TEAL           = "#007b83"

FONT_MAIN   = ("Segoe UI", 11)
FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_CARD   = ("Segoe UI", 26, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)

NAV_ITEMS = [
    ("dashboard",   "Tổng quan (Dashboard)",           "home"),
    ("results",     "Kết quả lan truyền (Results)",    "line_chart"),
    ("comparison",  "So sánh thuật toán (Comparison)", "bar_chart"),
    ("datasets",    "Bộ dữ liệu (Datasets)",           "network"),
    ("experiments", "Thí nghiệm (Experiments)",       "flask"),
    ("reports",     "Báo cáo & Luận văn (Reports)",    "document"),
]

PROJECT_ROOT = Path(__file__).resolve().parents[4]
PYPROJECT_ROOT = PROJECT_ROOT
PYPROJECT_SRC = PROJECT_ROOT / "src"

if str(PYPROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PYPROJECT_SRC))
