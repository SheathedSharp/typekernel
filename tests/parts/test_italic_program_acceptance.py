"""TK-402/404 program acceptance for true italic (human review still required)."""

from __future__ import annotations

import math

from typekernel.font import Font, Master, check_masters
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import Controls, DesignContext
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.italic import italic_design, slant_composed_glyph, vf_italic_pair
from typekernel.qa.identity import check_identity_controls
from typekernel.qa.lint import lint_controls
from typekernel.qa.originality import topology_signature
from typekernel.qa.outline_hash import composed_glyph_hash

_OBLIQUE_VS_ITALIC_CHARS = "aefghkmnruvwy"
_MIN_OUTLINE_DIFFS = 8


def _stem_slant_degrees(glyph: ComposedGlyph, y_lo: float, y_hi: float) -> float:
    def left_edge(y: float) -> float:
        intervals = ink_intervals_at_y(list(glyph.solids), y)
        return intervals[0][0] if intervals else 0.0

    x_lo, x_hi = left_edge(y_lo), left_edge(y_hi)
    return math.degrees(math.atan2(x_hi - x_lo, y_hi - y_lo))


def _font(controls: Controls, style: str, *, stem: float | None = None) -> Font:
    from dataclasses import replace

    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    ctx = controls.context
    if stem is not None:
        ctx = ctx.tuned(stem=stem)
    sheet = replace(controls, context=ctx)
    if stem is not None and stem >= STEM_RELIEF_ONSET:
        sheet = sheet.with_stem_relief()
    font = Font.from_context(ctx, "ItalicAccept", style)
    font.add_chars(sheet.build_all())
    return font


def test_italic_vf_meets_tk402_program_acceptance_on_humanist() -> None:
    """Lint/identity, construct slant, oblique delta, wght×ital ``check_masters``."""
    reg = Controls.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    charset = ital.supported

    lint_report = lint_controls(ital)
    assert not lint_report.errors, lint_report.errors
    identity_report = check_identity_controls(ital, charset)
    assert not identity_report.errors, identity_report.errors

    ctx = ital.context
    target = ctx.italic_slant_deg
    y_lo, y_hi = ctx.x_height * 0.15, ctx.x_height * 0.85
    for ch in "iln":
        measured = _stem_slant_degrees(ital.build(ch), y_lo, y_hi)
        assert abs(measured - target) <= 0.5

    outline_diffs = 0
    topology_diffs = 0
    for ch in _OBLIQUE_VS_ITALIC_CHARS:
        oblique = slant_composed_glyph(reg.build(ch), target)
        drawn = ital.build(ch)
        if composed_glyph_hash(oblique) != composed_glyph_hash(drawn):
            outline_diffs += 1
        if topology_signature(oblique) != topology_signature(drawn):
            topology_diffs += 1
    assert outline_diffs >= _MIN_OUTLINE_DIFFS
    assert topology_diffs >= 4

    upright, italic_sheet = vf_italic_pair(reg)
    bold = vf_italic_pair(
        Controls.from_context(DesignContext.humanist_sans().tuned(stem=120.0)).with_stem_relief()
    )[0]
    masters = [
        Master({"wght": 400, "ital": 0}, _font(upright, "Regular")),
        Master({"wght": 400, "ital": 1}, _font(italic_sheet, "Italic")),
        Master({"wght": 700, "ital": 0}, _font(bold, "Bold", stem=120.0)),
    ]
    assert check_masters(masters) == []
