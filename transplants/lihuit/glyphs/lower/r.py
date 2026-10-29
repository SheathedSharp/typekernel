"""r — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("r", group="lc.straight")
def r(system: System):
    return ref_drawing("r", system)
