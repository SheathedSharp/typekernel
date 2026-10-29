"""i — LihuiT Regular/Bold transplant (P6-3)."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="lc.mixed")
def i(system: System):
    return ref_drawing("i", system)
