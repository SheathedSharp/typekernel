"""zero — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("zero", group="figs")
def zero(system: System):
    return ref_drawing("zero", system)
