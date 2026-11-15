import sys
sys.path.insert(0, "src")
from im_research.gui.core.icon_factory import IconSet
icons = IconSet(20)
for k, v in icons._cache.items():
    print(k, v["inactive"]._size, v["active"]._size)
