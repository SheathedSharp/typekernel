"""w — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("w", group="lc.straight")
def w(system: System):
    return ref_drawing("w", system)
