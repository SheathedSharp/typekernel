"""one — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("one", group="figs")
def one(system: System):
    return ref_drawing("one", system)
