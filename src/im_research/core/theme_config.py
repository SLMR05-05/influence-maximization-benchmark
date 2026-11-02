"""SQLite Theme Configuration — Lưu trữ cài đặt theme (Dark/Light)"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "config.db")

def init_db():
    """Initialize the SQLite database with theme settings."""
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
    conn.commit()
    conn.close()

def get_theme():
    """Get the current theme mode from SQLite."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'theme_mode'")
    result = c.fetchone()
    conn.close()
    return result[0] if result else "dark"

def set_theme(mode):
    """Save theme mode to SQLite. mode = 'dark' or 'light'."""
    if mode not in ("dark", "light"):
        raise ValueError("Theme mode must be 'dark' or 'light'")
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('theme_mode', ?)", (mode,))
    conn.commit()
    conn.close()
