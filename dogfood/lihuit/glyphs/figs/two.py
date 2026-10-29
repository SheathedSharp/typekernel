"""two — LihuiT Regular/Bold transplant (P6-3)."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("two", group="figs")
def two(system: System):
    return ref_drawing("two", system)
