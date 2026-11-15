import sys
sys.path.insert(0, "src")

from im_research.gui.core.icon_factory import IconSet
icons = IconSet()
print("Testing icon set aliases & fallbacks:")
for name in ["chart", "results", "comparison", "add", "trash", "refresh", "play", "settings", "nonexistent_test"]:
    img = icons.get(name)
    assert img is not None
    print(f"  {name} -> {img}")

from im_research.core.theme_config import get_font_scale, set_font_scale, FONT_SCALE_MAP
print("Testing font scaling:")
for k in FONT_SCALE_MAP:
    set_font_scale(k)
    assert get_font_scale() == k
print("  All font scales tested successfully!")

set_font_scale("100% (Mặc định)")
print("Settings and icons verification complete!")
