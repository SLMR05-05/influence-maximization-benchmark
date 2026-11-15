import sys
from pathlib import Path
sys.path.insert(0, "src")
from im_research.gui.core.icon_factory import *

out_dir = Path("scratch/icons")
out_dir.mkdir(parents=True, exist_ok=True)

icons = [
    ("atom", draw_atom),
    ("home", draw_home),
    ("line_chart", draw_line_chart),
    ("bar_chart", draw_bar_chart),
    ("network", draw_network),
    ("flask", draw_flask),
    ("document", draw_document),
    ("settings", draw_settings),
    ("sun", draw_sun),
    ("moon", draw_moon),
    ("chip", draw_chip),
]

for name, fn in icons:
    try:
        im_light = fn(size=128, color=GRAY_LIGHT)
        im_dark = fn(size=128, color=SILVER_DARK)
        im_active = fn(size=128, color=WHITE)
        im_light.save(out_dir / f"{name}_light.png")
        im_dark.save(out_dir / f"{name}_dark.png")
        im_active.save(out_dir / f"{name}_active.png")
        print(f"Icon {name}: OK (size={im_light.size})")
    except Exception as e:
        print(f"Icon {name}: FAILED - {e}")
