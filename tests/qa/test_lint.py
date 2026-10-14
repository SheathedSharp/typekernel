"""Structural glyph lint."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.path_builder import PathBuilder
from typekernel.parts import Controls, DesignContext
from typekernel.parts.compose import ComposedGlyph
from typekernel.qa.lint import lint_controls, lint_glyph

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pathops") is None,
    reason="lint keyhole/self-intersect rules need skia-pathops",
)


def test_lint_humanist_charset_no_keyhole() -> None:
    report = lint_controls(Controls.from_context(DesignContext.humanist_sans()))
    keyholes = [i for i in report.issues if i.rule == "R2_keyhole"]
    assert not keyholes, keyholes


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
