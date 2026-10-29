"""nbsp and soft hyphen ."""
from __future__ import annotations

from typekernel.anatomy import crossbar
from typekernel.draw import Writer
from typekernel.project import GlyphDraft, glyph
from typekernel.system import System


@glyph("nbspace", unicodes=(0x00A0,), group="space", traits=("no-stem",))
def nbspace(system: System):
    return GlyphDraft(drawing=Writer().build(), note="nbsp")

@glyph("softhyphen", unicodes=(0x00AD,), group="punct", traits=("punct", "no-stem"))
def softhyphen(system: System):
    # Visible when needed; same geometry as hyphen
    st = float(system.stem["lc"]); xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    return crossbar(lsb, lsb + 220, xh * 0.48, thick=st * 0.85, name="bar", ends="none")
