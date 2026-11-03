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
BG_APP         = ("#f8fafc", "#0a0f1d")
SIDEBAR_BG     = ("#ffffff", "#0d1322")
ACTIVE_BG      = "#2563eb"
ACTIVE_HOVER   = "#1d4ed8"
INACTIVE_HOVER = ("#f1f5f9", "#1e293b")
BORDER_COLOR   = ("#e2e8f0", "#1e293b")
CARD_BG        = ("#ffffff", "#111827")
HEADER_FG      = ("#0f172a", "#f8fafc")
SUBTEXT_FG     = ("#64748b", "#94a3b8")
STATUS_BG      = ("#ffffff", "#0b0f19")
STATUS_FG      = ("#475569", "#94a3b8")
DIVIDER        = ("#e2e8f0", "#1e293b")
PILL_BG        = ("#eff6ff", "#172554")
PILL_FG        = ("#1d4ed8", "#60a5fa")
GREEN_PILL_BG  = ("#ecfdf5", "#064e3b")
GREEN_PILL_FG  = ("#059669", "#34d399")
CYAN_PILL_BG   = ("#f0fdfa", "#134e4a")
CYAN_PILL_FG   = ("#0d9488", "#2dd4bf")
BLUE           = "#2563eb"
GREEN          = "#10b981"
ORANGE         = "#f59e0b"
RED            = "#ef4444"
PURPLE         = "#8b5cf6"
TEAL           = "#0d9488"

FONT_MAIN   = ("Segoe UI", 11)
FONT_BOLD   = ("Segoe UI", 11, "bold")
FONT_TITLE  = ("Segoe UI", 16, "bold")
FONT_CARD   = ("Segoe UI", 26, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)

NAV_ITEMS = [
    ("dashboard",   "Tổng quan",              "home"),
    ("datasets",    "Bộ dữ liệu & Đồ thị 3D", "network"),
    ("results",     "Kết quả lan truyền",     "line_chart"),
    ("comparison",  "So sánh thuật toán",     "bar_chart"),
    ("experiments", "Thí nghiệm",             "flask"),
    ("reports",     "Báo cáo & Luận văn",     "document"),
]

PROJECT_ROOT = Path(__file__).resolve().parents[4]
PYPROJECT_ROOT = PROJECT_ROOT
PYPROJECT_SRC = PROJECT_ROOT / "src"

if str(PYPROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PYPROJECT_SRC))
