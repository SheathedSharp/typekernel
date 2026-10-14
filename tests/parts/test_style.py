"""TK-305 Style DNA (scaffold + i_dot)."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style
from typekernel.qa.originality import nearest_voice_distance, topology_signature
from typekernel.qa.outline_hash import composed_glyph_hash


def test_default_style_preserves_preset_i_hash() -> None:
    for preset in ("humanist_sans", "geometric_sans", "code_clear"):
        ctx = getattr(DesignContext, preset)()
        base = Controls.from_context(ctx).build_all("i")["i"]
        again = Controls.from_context(ctx, style=Style()).build_all("i")["i"]
        assert composed_glyph_hash(base) == composed_glyph_hash(again)


def test_i_dot_square_changes_topology() -> None:
    ctx = DesignContext.geometric_sans()
    round_i = Controls.from_context(ctx).build_all("i")["i"]
    square_i = Controls.from_context(ctx, style=Style(i_dot="square")).build_all("i")["i"]
    assert topology_signature(round_i) != topology_signature(square_i)


def test_with_style_helper() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans()).with_style(i_dot="diamond")
    assert controls.style.i_dot == "diamond"
    assert controls.context.style.i_dot == "diamond"


def test_non_default_style_raises_voice_distance() -> None:
    base = Controls.from_context(DesignContext.humanist_sans())
    styled = base.with_style(i_dot="diamond")
    assert nearest_voice_distance(styled) > nearest_voice_distance(base)
