from elements import stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("l", group="lc")
def l(system: System):
    top = float(system.zones.x) + (float(system.zones.asc) - float(system.zones.x)) * 0.85
    return stem(system, 120.0, y1=top)
