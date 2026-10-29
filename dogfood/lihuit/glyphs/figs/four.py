"""four — LihuiT Regular/Bold transplant (P6-3)."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("four", group="figs")
def four(system: System):
    return ref_drawing("four", system)
