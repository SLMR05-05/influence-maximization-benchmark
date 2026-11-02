#!/usr/bin/env python3
"""
IM-Benchmark-Lab — Influence Maximization Research Platform
Entrypoint: Desktop Application
Redirects to modern CustomTkinter IMApp with research icon taskbar.
"""

import sys
from pathlib import Path

# Ensure src is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from im_research.gui.app import IMApp

def main():
    app = IMApp()
    app.mainloop()

if __name__ == "__main__":
    main()
