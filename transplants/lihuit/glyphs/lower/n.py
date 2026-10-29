"""n — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("n", group="lc.straight")
def n(system: System):
    return ref_drawing("n", system)
