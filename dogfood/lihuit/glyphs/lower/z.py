"""z — LihuiT Regular/Bold transplant (P6-3)."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("z", group="lc.diag")
def z(system: System):
    return ref_drawing("z", system)
