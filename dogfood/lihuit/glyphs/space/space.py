"""space — advance-only glyph (P4-2 charset)."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.project import GlyphDraft, glyph
from typekernel.system import System


@glyph("space", unicodes=(0x0020,), group="space", traits=("no-stem",))
def space(system: System):
    # Empty outline; metrics.apply sets advance from Metrics.space / tokens.
    d = Writer().build()
    return GlyphDraft(drawing=d, note="space")
