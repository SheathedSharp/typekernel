"""period — anatomy dot ."""

from __future__ import annotations

from typekernel.anatomy import dot
from typekernel.project import glyph
from typekernel.system import System


@glyph("period", group="punct")
def period(system: System):
    st = float(system.stem["lc"])
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    return dot((lsb + size / 2.0, size / 2.0), size, shape="square", name="dot")
