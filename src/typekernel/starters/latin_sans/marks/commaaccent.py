"""commaaccent combining mark (P4-2 Ext-A comma accents)."""

from __future__ import annotations

from typekernel.anatomy import drop
from typekernel.project import GlyphDraft, glyph
from typekernel.system import System


@glyph("commaaccentcomb", unicodes=(0x0326,), group="marks", traits=("mark",))
def commaaccentcomb(system: System):
    st = float(system.stem["lc"]) * 0.5
    body = drop((0.0, -st * 0.05), (st * 0.15, -st * 2.2), width=st * 0.95, name="drop")
    return GlyphDraft(drawing=body, anchors={"_bottom": (0.0, 0.0)})


@glyph("commaaccentcomb.case", unicodes=(), group="marks.case", traits=("mark",))
def commaaccentcomb_case(system: System):
    st = float(system.stem.get("uc", system.stem["lc"])) * 0.5
    body = drop((0.0, -st * 0.05), (st * 0.2, -st * 2.4), width=st * 1.05, name="drop")
    return GlyphDraft(drawing=body, anchors={"_bottom": (0.0, 0.0)})
