"""five — LihuiT Regular/Bold transplant."""

from __future__ import annotations

from ref_outlines import ref_drawing

from typekernel.project import glyph
from typekernel.system import System


@glyph("five", group="figs")
def five(system: System):
    return ref_drawing("five", system)
