"""No derived glyph self-intersects, backtracks or overlaps, hairline to black.

Topology checks only compare segment counts; a contour that doubles back on
itself passes them. pathops ``simplify`` resolves such geometry, so any glyph
whose area changes under it is not a clean outline.
"""

from __future__ import annotations

import pytest

pathops = pytest.importorskip("pathops")

from fontTools.pens.areaPen import AreaPen

from typekernel.font import Glyph
from typekernel.geo.pens import draw_outline
from typekernel.parts import Controls, DesignContext

PRESETS = (
    "geometric_sans",
    "humanist_sans",
    "mono",
    "display",
    "paper_ink",
    "code_clear",
    "open_print",
)


def _area_change(outline) -> float:
    raw = AreaPen()
    draw_outline(outline, raw)
    path = pathops.Path()
    draw_outline(outline, path.getPen())
    path.simplify(fix_winding=True)
    clean = AreaPen()
    path.draw(clean)
    return abs(abs(raw.value) - abs(clean.value)) / max(abs(raw.value), 1.0)


@pytest.mark.parametrize("preset", PRESETS)
def test_outlines_are_simple(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    bad: dict[str, float] = {}
    for stem in (30.0, base.stem, 220.0):
        for ch, g in Controls.from_context(base.tuned(stem=stem)).build_all().items():
            change = _area_change(Glyph.from_composed(ch, g).outline)
            if change > 1e-4:
                bad[f"{ch}@{stem:g}"] = round(change, 5)
    assert bad == {}
