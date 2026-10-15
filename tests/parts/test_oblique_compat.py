"""TK-402: bowl oblique pre-splits with VF parity."""

from __future__ import annotations

from typekernel.font import Font, Master, check_masters
from typekernel.geo.extrema import cubic_has_off_node_axis_extrema
from typekernel.geo.segment import CubicSegment
from typekernel.parts import Controls, DesignContext
from typekernel.parts.italic import italic_design, vf_upright_controls
from typekernel.parts.oblique_compat import OBLIQUE_COMPAT_EXCLUDE, oblique_compat_charset
from typekernel.qa.lint import lint_controls


def test_oblique_compat_excludes_branching_arch_glyphs() -> None:
    supported = Controls.from_context(DesignContext.code_clear()).supported
    compat = oblique_compat_charset(supported)
    assert OBLIQUE_COMPAT_EXCLUDE <= set(supported) - compat


def test_italic_o_clears_r4_with_oblique_compat_pipeline() -> None:
    ital = italic_design(Controls.from_context(DesignContext.code_clear()))
    o = ital.build("o")
    for solid in o.solids:
        for seg in solid.iter_segments():
            if isinstance(seg, CubicSegment):
                assert not cubic_has_off_node_axis_extrema(seg)


def test_wght_ital_vf_masters_interpolate_with_oblique_compat() -> None:
    base = DesignContext.code_clear()
    reg = vf_upright_controls(Controls.from_context(base))
    ital = italic_design(reg)
    bold = vf_upright_controls(
        Controls.from_context(base.tuned(stem=120.0)).with_stem_relief()
    )

    def _font(controls: Controls, style: str, *, stem: float | None = None) -> Font:
        from dataclasses import replace

        ctx = controls.context
        if stem is not None:
            ctx = ctx.tuned(stem=stem)
        sheet = replace(controls, context=ctx)
        if stem is not None and stem >= 100:
            sheet = sheet.with_stem_relief()
        font = Font.from_context(ctx, "Oblique VF", style)
        font.add_chars(sheet.build_all())
        return font

    masters = [
        Master({"wght": 400, "ital": 0}, _font(reg, "Regular")),
        Master({"wght": 400, "ital": 1}, _font(ital, "Italic")),
        Master({"wght": 700, "ital": 0}, _font(bold, "Bold", stem=120.0)),
    ]
    assert check_masters(masters) == []


def test_italic_r4_warn_count_drops_on_compat_charset() -> None:
    reg = Controls.from_context(DesignContext.code_clear())
    ital = italic_design(reg)
    compat = oblique_compat_charset(reg.supported)
    report = lint_controls(ital)
    r4 = {i.glyph for i in report.issues if i.rule == "R4_extrema"}
    assert r4 <= set(reg.supported) - compat


def test_italic_r4_warns_only_on_oblique_compat_exclude() -> None:
    """Arch / relief-sensitive glyphs stay on plain slant until TK-402 follow-up."""
    ital = italic_design(Controls.from_context(DesignContext.code_clear()))
    r4 = {i.glyph for i in lint_controls(ital).issues if i.rule == "R4_extrema"}
    assert r4 <= OBLIQUE_COMPAT_EXCLUDE
    assert r4 == frozenset("ehmnu")
