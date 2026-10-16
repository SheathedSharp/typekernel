"""Cubic stroke spike program acceptance (not the default glyph pipeline)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from typekernel.geo.stroke import CubicBezier, CubicCenterline, Pen, expand_cubic
from typekernel.parts import DesignContext, Skeleton, Stroke, trace_letter
from typekernel.qa.lint import lint_glyph

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_stroke_spike_meets_program_acceptance() -> None:
    """D3 spike: honest expand report, lint-clean cubic trace, no family wiring."""
    seg = CubicBezier.line((0.0, 0.0), (240.0, 0.0))
    centerline = CubicCenterline((seg,))
    chord_budget = 0.35
    outline, report = expand_cubic(
        centerline,
        Pen(thickness=60.0),
        chord_budget=chord_budget,
        offset_fit_budget=0.75,
    )
    assert outline.contours
    assert report.max_chord_error <= chord_budget + 1e-6
    assert report.max_offset_fit_error <= 0.75 + 1e-6

    family_src = Path(__file__).resolve().parents[2] / "src/typekernel/parts/family.py"
    text = family_src.read_text(encoding="utf-8")
    assert "trace_letter" not in text
    assert "Skeleton" not in text

    if not HAS_PATHOPS:
        pytest.skip("pathops required for closed cubic ring subtract")
    ctx = DesignContext.geometric_sans().tuned(stem=40.0)
    ring = (
        CubicBezier.line((30.0, 30.0), (90.0, 30.0)),
        CubicBezier.line((90.0, 30.0), (90.0, 90.0)),
        CubicBezier.line((90.0, 90.0), (30.0, 90.0)),
        CubicBezier.line((30.0, 90.0), (30.0, 30.0)),
    )
    skel = Skeleton.of(Stroke.from_beziers("ring", ring, thickness=20.0, closed=True))
    glyph = trace_letter(skel, ctx, union=True, blend=False, ease=False, join="miter")
    issues = [i for i in lint_glyph(glyph, ctx, glyph_name="ring") if i.severity == "error"]
    assert not issues
