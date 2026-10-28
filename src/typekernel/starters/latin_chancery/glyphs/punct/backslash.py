"""backslash — opposite diagonal (skeleton+pen)."""
from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("backslash", group="punct")
def backslash(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    desc = float(system.zones.desc) * 0.4
    width = float(system.tokens.get("slash_width", 280.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    return stroke(system, [(lsb, asc), (lsb + width, desc)], thickness=st * 0.9)
