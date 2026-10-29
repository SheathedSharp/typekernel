"""c — LihuiT Regular/Bold transplant (P6-3)."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("c", group="lc.round")
def c(system: System):
    return ref_drawing("c", system)
