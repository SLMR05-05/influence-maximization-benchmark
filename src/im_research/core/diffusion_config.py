"""SQLite persistence for the Independent Cascade (IC) diffusion configuration.

The diffusion settings are shared by every experiment launched from the GUI:
edge probability, Monte Carlo budgets and evaluator seeds.  Only the
Independent Cascade model is supported; Linear Threshold is intentionally
rejected so an unsupported configuration can never be saved.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "config.db"

DEFAULT_IC_CONFIG: Dict[str, Any] = {
    "model": "IC",
    "probability_mode": "uniform",
    "edge_probability": 0.1,
    "mc_search": 200,
    "mc_validation": 1000,
    "seed_search": 42,
    "seed_validation": 12345,
}

_MAX_MC = 100_000
_MAX_SEED = 2**32 - 1


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS diffusion_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    return conn


def _coerce_int(value: Any, label: str, minimum: int, maximum: int) -> int:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label} phải là số nguyên.") from None
    if not minimum <= number <= maximum:
        raise ValueError(
            f"{label} phải nằm trong khoảng {minimum:,} – {maximum:,}."
        )
    return number


def validate_ic_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize a raw IC configuration dictionary.

    Raises:
        ValueError: with a Vietnamese message suitable for the GUI.
    """
    model = str(raw.get("model", "IC")).strip().upper()
    if model != "IC":
        raise ValueError("Chỉ hỗ trợ mô hình Independent Cascade (IC).")

    mode = str(raw.get("probability_mode", "uniform")).strip().lower()
    if mode != "uniform":
        raise ValueError("Cơ chế gán xác suất hiện chỉ hỗ trợ Uniform (hằng số).")

    p_raw = str(raw.get("edge_probability", DEFAULT_IC_CONFIG["edge_probability"]))
    p_raw = p_raw.replace(",", ".").strip()
    try:
        probability = float(p_raw)
    except (TypeError, ValueError):
        raise ValueError("Xác suất cạnh p phải là số thực.") from None
    if not 0.0 < probability <= 1.0:
        raise ValueError("Xác suất cạnh p phải nằm trong khoảng (0, 1].")

    mc_search = _coerce_int(
        raw.get("mc_search", DEFAULT_IC_CONFIG["mc_search"]),
        "Số lần mô phỏng MC (tìm kiếm)",
        1,
        _MAX_MC,
    )
    mc_validation = _coerce_int(
        raw.get("mc_validation", DEFAULT_IC_CONFIG["mc_validation"]),
        "Số lần mô phỏng MC (kiểm định)",
        1,
        _MAX_MC,
    )
    seed_search = _coerce_int(
        raw.get("seed_search", DEFAULT_IC_CONFIG["seed_search"]),
        "Seed evaluator (tìm kiếm)",
        0,
        _MAX_SEED,
    )
    seed_validation = _coerce_int(
        raw.get("seed_validation", DEFAULT_IC_CONFIG["seed_validation"]),
        "Seed evaluator (kiểm định)",
        0,
        _MAX_SEED,
    )

    return {
        "model": "IC",
        "probability_mode": "uniform",
        "edge_probability": round(probability, 6),
        "mc_search": mc_search,
        "mc_validation": mc_validation,
        "seed_search": seed_search,
        "seed_validation": seed_validation,
    }


def get_ic_config() -> Dict[str, Any]:
    """Load the stored IC configuration, falling back to safe defaults."""
    config = dict(DEFAULT_IC_CONFIG)
    try:
        with closing(_connect()) as conn:
            rows = conn.execute("SELECT key, value FROM diffusion_config").fetchall()
        for key, value in rows:
            if key not in config:
                continue
            try:
                config[key] = json.loads(value)
            except (TypeError, ValueError):
                continue
        return validate_ic_config(config)
    except (sqlite3.Error, ValueError):
        return dict(DEFAULT_IC_CONFIG)


def save_ic_config(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Validate, persist and return the normalized IC configuration."""
    config = validate_ic_config(raw)
    with closing(_connect()) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO diffusion_config (key, value) VALUES (?, ?)",
            [(key, json.dumps(value)) for key, value in config.items()],
        )
        conn.commit()
    return config


def reset_ic_config() -> Dict[str, Any]:
    """Delete the stored IC settings and return the factory defaults."""
    with closing(_connect()) as conn:
        conn.execute("DELETE FROM diffusion_config")
        conn.commit()
    return dict(DEFAULT_IC_CONFIG)
