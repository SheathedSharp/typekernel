"""d — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("d", group="lc.round")
def d(system: System):
    return ref_drawing("d", system)
