"""Structural glyph lint."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment
from typekernel.parts import Controls, DesignContext
from typekernel.parts.compose import ComposedGlyph
from typekernel.qa.lint import lint_controls, lint_glyph

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pathops") is None,
    reason="lint keyhole/self-intersect rules need skia-pathops",
)


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans"),
)
def test_lint_preset_charset_no_keyhole(preset: str) -> None:
    report = lint_controls(Controls.from_context(getattr(DesignContext, preset)()))
    keyholes = [i for i in report.issues if i.rule == "R2_keyhole"]
    assert not keyholes, keyholes


def test_lint_quote_marks_fit_advance() -> None:
    ctx = DesignContext.humanist_sans()
    controls = Controls.from_context(ctx)
    for ch in ('"', "'", "\u2019", "\u201d"):
        issues = lint_glyph(controls.build(ch), ctx, glyph_name=ch)
        assert not any(i.rule == "R7_sidebearing" for i in issues), ch


def test_lint_humanist_charset_no_r1_winding_errors() -> None:
    report = lint_controls(Controls.from_context(DesignContext.humanist_sans()))
    r1 = [i for i in report.issues if i.rule == "R1_winding" and i.severity == "error"]
    assert not r1, r1


def test_lint_multi_contour_solids_not_r1_false_positive() -> None:
    """Counters inside one solid outline are clockwise (negative area) by design."""
    ctx = DesignContext.humanist_sans()
    controls = Controls.from_context(ctx)
    for ch in "aeobd":
        issues = lint_glyph(controls.build(ch), ctx, glyph_name=ch)
        assert not any(i.rule == "R1_winding" for i in issues), ch


def test_lint_r4_interior_axis_extremum() -> None:
    ctx = DesignContext.code_clear()
    seg = CubicSegment(
        Point(0.0, 0.0),
        Point(40.0, 120.0),
        Point(60.0, 120.0),
        Point(100.0, 0.0),
    )
    b = PathBuilder()
    b.moveTo(seg.p0.x, seg.p0.y)
    b.curveTo(seg.p1.x, seg.p1.y, seg.p2.x, seg.p2.y, seg.p3.x, seg.p3.y)
    b.lineTo(seg.p0.x, seg.p0.y)
    b.closePath()
    outline = b.build()
    glyph = ComposedGlyph((outline,), (), 120.0, ctx)
    issues = lint_glyph(glyph, ctx, glyph_name="x")
    assert any(i.rule == "R4_extrema" for i in issues)


def test_lint_control_n_ok() -> None:
    ctx = DesignContext.code_clear()
    glyph = Controls.from_context(ctx).build_all("n")["n"]
    issues = lint_glyph(glyph, ctx, glyph_name="n")
    assert not any(i.severity == "error" for i in issues)


def test_lint_r9_optional_thickness() -> None:
    ctx = DesignContext.humanist_sans()
    controls = Controls.from_context(ctx)
    report = lint_controls(controls, "o", thickness=True)
    assert not any(i.rule == "R9_thickness_outlier" for i in report.issues)


def test_lint_r8_counter_min() -> None:
    ctx = DesignContext.code_clear().tuned(stem=180.0)
    controls = Controls.from_context(ctx).with_stem_relief()
    report = lint_controls(controls, "m", counter_min=True)
    assert not any(i.rule == "R8_counter_min" for i in report.issues)


def test_lint_negative_sidebearing() -> None:
    ctx = DesignContext.code_clear()
    b = PathBuilder()
    b.moveTo(-20, 0)
    b.lineTo(-20, 100)
    b.lineTo(50, 100)
    b.lineTo(50, 0)
    b.closePath()
    outline = b.build()
    g = ComposedGlyph((outline,), (), 80.0, ctx)
    issues = lint_glyph(g, ctx, glyph_name="x")
    assert any(i.rule == "R7_sidebearing" for i in issues)
