"""period — baseline square/dot."""

from __future__ import annotations

from elements import stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("period", group="punct")
def period(system: System):
    st = float(system.stem["lc"])
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    # advance token period_advance preferred
    return stem_rect(lsb, lsb + size, 0.0, size, prefix="dot")
