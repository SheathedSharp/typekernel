"""Glyph-pair kern exceptions beyond class representatives."""

from __future__ import annotations

from typekernel.compile import FamilyBuildOptions, compose_font_from_controls
from typekernel.optics.space import pair_gap_optical, space_font
from typekernel.parts import (
    Controls,
    DesignContext,
    auto_class_kern,
    auto_side_kern_classes,
    fit_glyph_pair_kerns,
    rhythm_from_control_glyphs,
)


def test_fit_glyph_pair_kerns_hits_rhythm_target() -> None:
    ctx = DesignContext.humanist_sans()
    drawn = Controls.from_context(ctx).build_all()
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    table = fit_glyph_pair_kerns(spaced, (("o", "w"), ("T", "o")), target=rhythm)
    assert table.lookup("o", "w") != 0.0 or abs(
        pair_gap_optical(spaced["o"], spaced["w"], kern=0.0) - rhythm.target_gap
    ) < 1.0
    gap = pair_gap_optical(
        spaced["o"], spaced["w"], kern=table.lookup("o", "w")
    )
    assert abs(gap - rhythm.target_gap) < 1.5


def test_compose_font_merges_pair_kern_exceptions() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    font = compose_font_from_controls(
        controls,
        "KernEx",
        options=FamilyBuildOptions(pair_kern_exceptions=(("o", "w"), ("a", "v"))),
    )
    # Glyph-pair keys (not class groups) after resolve
    assert ("o", "w") in font.kerning or any(
        k == ("o", "w") for k in font.kerning
    )


def test_compose_font_applies_default_pair_kern_exceptions() -> None:
    from typekernel.compile import DEFAULT_PAIR_KERN_EXCEPTIONS

    controls = Controls.from_context(DesignContext.humanist_sans())
    font = compose_font_from_controls(controls, "KernDefault")
    assert ("o", "w") in DEFAULT_PAIR_KERN_EXCEPTIONS
    assert ("o", "w") in font.kerning or any(k == ("o", "w") for k in font.kerning)
