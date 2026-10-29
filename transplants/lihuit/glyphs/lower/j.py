"""j — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("j", group="lc.mixed")
def j(system: System):
    return ref_drawing("j", system)
