"""TK-402: bowl oblique pre-splits with VF parity."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.extrema import cubic_has_off_node_axis_extrema
from typekernel.geo.segment import CubicSegment
from typekernel.parts import Controls, DesignContext
from typekernel.parts.italic import ItalicStyle, italic_design, vf_italic_pair, vf_upright_controls
from typekernel.parts.oblique_compat import OBLIQUE_COMPAT_EXCLUDE, oblique_compat_charset
from typekernel.qa.lint import lint_controls

_BUILTIN_PRESETS = (
    "humanist_sans",
    "geometric_sans",
    "code_clear",
    "mono",
    "display",
    "paper_ink",
    "open_print",
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


def test_vf_italic_pair_custom_slant_interpolates() -> None:
    base = DesignContext.code_clear()
    upright, ital = vf_italic_pair(
        Controls.from_context(base), style=ItalicStyle(slant_deg=12.0)
    )
    bold = vf_upright_controls(
        Controls.from_context(base.tuned(stem=120.0)).with_stem_relief()
    )
    masters = [
        Master({"wght": 400, "ital": 0}, _font(upright, "Regular")),
        Master({"wght": 400, "ital": 1}, _font(ital, "Italic")),
        Master({"wght": 700, "ital": 0}, _font(bold, "Bold", stem=120.0)),
    ]
    assert check_masters(masters) == []


def test_wght_ital_vf_masters_interpolate_with_oblique_compat() -> None:
    base = DesignContext.code_clear()
    reg = vf_upright_controls(Controls.from_context(base))
    ital = italic_design(reg)
    bold = vf_upright_controls(
        Controls.from_context(base.tuned(stem=120.0)).with_stem_relief()
    )

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
    ital = italic_design(Controls.from_context(DesignContext.code_clear()))
    r4 = {i.glyph for i in lint_controls(ital).issues if i.rule == "R4_extrema"}
    assert r4 <= OBLIQUE_COMPAT_EXCLUDE
    assert not r4


@pytest.mark.parametrize("preset", _BUILTIN_PRESETS)
def test_italic_design_clears_r4_on_builtin_presets(preset: str) -> None:
    ctx = getattr(DesignContext, preset)()
    ital = italic_design(Controls.from_context(ctx))
    r4 = {i.glyph for i in lint_controls(ital).issues if i.rule == "R4_extrema"}
    assert not r4


@pytest.mark.parametrize("preset", _BUILTIN_PRESETS)
def test_vf_italic_pair_check_masters_on_builtin_presets(preset: str) -> None:
    """TK-404: full charset wght×ital masters interpolate on every built-in preset."""
    ctx = getattr(DesignContext, preset)()
    upright, ital = vf_italic_pair(Controls.from_context(ctx))
    bold = vf_italic_pair(
        Controls.from_context(ctx.tuned(stem=120.0)).with_stem_relief()
    )[0]
    masters = [
        Master({"wght": 400, "ital": 0}, _font(upright, "Regular")),
        Master({"wght": 400, "ital": 1}, _font(ital, "Italic")),
        Master({"wght": 700, "ital": 0}, _font(bold, "Bold", stem=120.0)),
    ]
    assert check_masters(masters) == []
