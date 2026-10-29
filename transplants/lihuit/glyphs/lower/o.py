"""o — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("o", group="lc.round")
def o(system: System):
    return ref_drawing("o", system)
