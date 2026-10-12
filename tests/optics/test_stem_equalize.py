"""Equalize vertical stems — designed-delta infrastructure."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.geo.boolean import boolean_op
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.context import OpticalContext
from typekernel.optics.contrast import ContrastParams, apply_designed_contrast
from typekernel.optics.stem import (
    equalize_horizontal_stems,
    equalize_vertical_stems,
    horizontal_vs_vertical_report,
    list_vertical_stems,
)

H = Path(__file__).parent.parent / "fixtures" / "synthetic_H.json"


def _rect(x0: float, y0: float, x1: float, y1: float):
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


def test_list_vertical_stems_on_synthetic_h() -> None:
    outline = load_synthetic_outline(H)
    spans = list_vertical_stems(outline)
    assert len(spans) == 2
    assert spans[0].width == pytest.approx(80.0)
    assert spans[1].width == pytest.approx(80.0)


def test_equalize_synthetic_h_to_target() -> None:
    outline = load_synthetic_outline(H)
    out = equalize_vertical_stems(outline, 100.0, OpticalContext())
    spans = list_vertical_stems(out)
    assert len(spans) == 2
    assert spans[0].width == pytest.approx(100.0, abs=0.05)
    assert spans[1].width == pytest.approx(100.0, abs=0.05)
    # centered growth: left stem was 100..180 → 90..190
    assert spans[0].left == pytest.approx(90.0, abs=0.05)
    assert spans[0].right == pytest.approx(190.0, abs=0.05)


def test_equalize_uneven_stems_both_hit_target() -> None:
    multi = boolean_op(_rect(0, 0, 60, 200), _rect(200, 0, 300, 200), "union")
    before = [s.width for s in list_vertical_stems(multi)]
    assert before == pytest.approx([60.0, 100.0])
    out = equalize_vertical_stems(multi, 80.0)
    after = list_vertical_stems(out)
    assert len(after) == 2
    assert after[0].width == pytest.approx(80.0, abs=0.05)
    assert after[1].width == pytest.approx(80.0, abs=0.05)


def test_equalize_side_left_keeps_right_edge() -> None:
    stem = _rect(100, 0, 160, 200)  # width 60
    out = equalize_vertical_stems(stem, 80.0, side="left")
    spans = list_vertical_stems(out)
    assert len(spans) == 1
    assert spans[0].width == pytest.approx(80.0, abs=0.05)
    assert spans[0].right == pytest.approx(160.0, abs=0.05)
    assert spans[0].left == pytest.approx(80.0, abs=0.05)


def test_equalize_noop_when_already_on_target() -> None:
    outline = load_synthetic_outline(H)
    out = equalize_vertical_stems(outline, 80.0)
    assert out is outline


def test_equalize_rejects_non_positive_target() -> None:
    with pytest.raises(ValueError):
        equalize_vertical_stems(_rect(0, 0, 10, 10), 0.0)


def test_connected_h_uses_probe_y_below_crossbar() -> None:
    glyph = boolean_op(
        boolean_op(_rect(0, 0, 80, 200), _rect(220, 0, 300, 200), "union"),
        _rect(80, 90, 220, 130),
        "union",
    )
    # Mid probe merges stems through the bar
    assert len(list_vertical_stems(glyph)) == 1
    assert len(list_vertical_stems(glyph, y=40.0)) == 2
    out = equalize_vertical_stems(glyph, 70.0, y=40.0)
    spans = list_vertical_stems(out, y=40.0)
    assert all(s.width == pytest.approx(70.0, abs=0.1) for s in spans)


def test_apply_designed_contrast_vertical_and_horizontal() -> None:
    glyph = boolean_op(
        boolean_op(_rect(0, 0, 80, 200), _rect(220, 0, 300, 200), "union"),
        _rect(80, 90, 220, 140),  # thickness 50
        "union",
    )
    out = apply_designed_contrast(
        glyph, ContrastParams(thick=70.0, thin=30.0), y=40.0, x=150.0
    )
    rep = horizontal_vs_vertical_report(out, y=40.0, x=150.0)
    assert rep.vertical_median == pytest.approx(70.0, abs=0.15)
    assert rep.horizontal_median == pytest.approx(30.0, abs=0.15)
    assert rep.contrast_ratio == pytest.approx(30.0 / 70.0, abs=0.01)


def test_equalize_horizontal_stems() -> None:
    bar = _rect(0, 100, 200, 160)  # thickness 60
    out = equalize_horizontal_stems(bar, 40.0)
    rep = horizontal_vs_vertical_report(out, x=100.0)
    assert rep.horizontal_median == pytest.approx(40.0, abs=0.1)
