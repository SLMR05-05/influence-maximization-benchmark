"""SQLite Theme Configuration — Lưu trữ cài đặt theme (Dark/Light/System)"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "config.db")

VALID_MODES = ("dark", "light", "system")

FONT_SCALE_MAP = {
    "90% (Nhỏ)": 0.90,
    "100% (Mặc định)": 1.00,
    "110% (Trung bình)": 1.10,
    "120% (Lớn)": 1.20,
    "130% (Rất lớn)": 1.30,
}

def init_db():
    """Initialize the SQLite database with theme and appearance settings."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    # Default theme if not exists
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('theme_mode', 'dark')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('font_scale', '100% (Mặc định)')")
    conn.commit()
    conn.close()

def get_theme():
    """Get the current theme mode from SQLite ('dark', 'light', or 'system')."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'theme_mode'")
    result = c.fetchone()
    conn.close()
    if result and result[0].lower().strip() in VALID_MODES:
        return result[0].lower().strip()
    return "dark"

def set_theme(mode):
    """Save theme mode to SQLite. mode = 'dark', 'light', or 'system'."""
    mode_clean = str(mode).lower().strip()
    if mode_clean not in VALID_MODES:
        raise ValueError(f"Theme mode must be 'dark', 'light', or 'system', got '{mode}'")
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('theme_mode', ?)", (mode_clean,))
    conn.commit()
    conn.close()

def is_dark_mode() -> bool:
    """Returns True if the current effective appearance mode is dark."""
    curr = get_theme()
    if curr == "system":
        try:
            import customtkinter as ctk
            return ctk.get_appearance_mode().lower() == "dark"
        except Exception:
            return True
    return curr == "dark"


def get_font_scale() -> str:
    """Get saved font scale label from SQLite, defaulting to '100% (Mặc định)'."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'font_scale'")
    result = c.fetchone()
    conn.close()
    if result and result[0] in FONT_SCALE_MAP:
        return result[0]
    return "100% (Mặc định)"


def set_font_scale(scale_key: str) -> float:
    """Saves font scale to SQLite and applies scaling to CustomTkinter."""
    if scale_key not in FONT_SCALE_MAP:
        scale_key = "100% (Mặc định)"
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('font_scale', ?)", (scale_key,))
    conn.commit()
    conn.close()

    factor = FONT_SCALE_MAP[scale_key]
    try:
        import customtkinter as ctk
        ctk.set_widget_scaling(factor)
    except Exception:
        pass
    return factor


def get_font_scaling_factor() -> float:
    """Returns the numeric float scaling factor corresponding to current font scale."""
    return FONT_SCALE_MAP.get(get_font_scale(), 1.00)


