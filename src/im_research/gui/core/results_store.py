"""Shared store for experiment run payloads.

Keeps the most recent experiment run in memory so that the Results and
Comparison pages can display the execution data of the run that was just
executed in the same session, even when the run could not be written to disk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
RUNS_DIR = PROJECT_ROOT / "runs"

_LATEST_RUN = None


def set_latest_run(payload: dict) -> None:
    """Remember the payload of the most recent experiment run."""
    global _LATEST_RUN
    _LATEST_RUN = payload


def get_latest_run() -> dict | None:
    """Return the payload of the most recent experiment run (memory or disk)."""
    global _LATEST_RUN
    if _LATEST_RUN is not None:
        return _LATEST_RUN

    latest_path = RUNS_DIR / "latest_results.json"
    if latest_path.exists():
        try:
            with open(latest_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                _LATEST_RUN = payload
                return _LATEST_RUN
        except Exception:
            return None
    return None


def load_runs() -> list:
    """Load every stored run, newest first."""
    runs = []
    history_path = RUNS_DIR / "results_history.json"
    latest_path = RUNS_DIR / "latest_results.json"

    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, list):
                runs = [run for run in data if isinstance(run, dict)]
        except Exception:
            runs = []

    if latest_path.exists():
        try:
            with open(latest_path, "r", encoding="utf-8") as handle:
                latest = json.load(handle)
            if isinstance(latest, dict):
                timestamp = latest.get("timestamp")
                if not any(run.get("timestamp") == timestamp for run in runs):
                    runs.append(latest)
        except Exception:
            pass

    memory_run = get_latest_run()
    if memory_run is not None:
        timestamp = memory_run.get("timestamp")
        if not any(run.get("timestamp") == timestamp for run in runs):
            runs.append(memory_run)

    runs.sort(key=lambda run: str(run.get("timestamp", "")), reverse=True)
    return runs
