"""Hook-root thickness on the weight ladder (TK-205 / TK-207)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.weight_relief import STEM_RELIEF_ONSET
from typekernel.qa.thickness import hook_min_thin_floor, min_hook_thickness

_LADDER_STEMS = (30.0, 70.0, 110.0, 150.0, 180.0)
_HOOK_CHARS = ("f", "t", "g", "J", "j")


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans", "open_print"),
)
@pytest.mark.parametrize("stem", _LADDER_STEMS)
def test_hook_root_thickness_weight_ladder(preset: str, stem: float) -> None:
    ctx = getattr(DesignContext, preset)().tuned(stem=stem)
    controls = Controls.from_context(ctx)
    if stem >= STEM_RELIEF_ONSET:
        controls = controls.with_stem_relief()
    floor = hook_min_thin_floor(ctx)
    for char in _HOOK_CHARS:
        glyph = controls.build(char)
        if char == "j":
            glyph = ComposedGlyph((glyph.solids[0],), (), glyph.advance, ctx)
        assert min_hook_thickness(glyph, char, ctx) >= floor
