import sys
sys.path.insert(0, "src")

from im_research.core.theme_config import set_theme, get_theme, is_dark_mode

print("Testing 'system' mode...")
set_theme("system")
assert get_theme() == "system"
print("Effective is_dark:", is_dark_mode())

print("Testing 'light' mode...")
set_theme("light")
assert get_theme() == "light"
assert is_dark_mode() is False

print("Testing 'dark' mode...")
set_theme("dark")
assert get_theme() == "dark"
assert is_dark_mode() is True

print("All theme mode tests passed successfully!")
