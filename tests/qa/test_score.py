"""Word specimen scoring (bbox vs optical, stems, joins)."""

from __future__ import annotations

from typekernel.parts import DesignContext, default_sans_kern, word_zayju
from typekernel.qa.score import word_report, zayju_report


def test_heuristic_zayju_optical_ratio_is_uneven() -> None:
    """Document the baseline problem: bbox even, optical not."""
    ctx = DesignContext.geometric_sans()
    report = word_report(
        word_zayju(ctx), list("zayju"), kerning=default_sans_kern()
    )
    assert report.bbox_gap_ratio <= 1.05
    assert report.optical_gap_ratio > 1.15


def test_optical_zayju_meets_spacing_and_stem_thresholds() -> None:
    ctx = DesignContext.geometric_sans()
    report, _glyphs, _kern = zayju_report(ctx, optical=True)
    assert report.optical_gap_ratio <= 1.15
    assert report.optical_gap_spread < report.bbox_gap_spread or report.optical_gap_ratio <= 1.05
    assert report.stem_cv <= 0.05
    assert report.g1_join_total > 0  # measured; count itself is diagnostic


def test_zayju_report_json_roundtrip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report, _, _ = zayju_report(DesignContext.geometric_sans(), optical=True)
    path = report.write_json(tmp_path / "zayju.json")
    text = path.read_text(encoding="utf-8")
    assert "optical_gap_ratio" in text
    assert "stem_cv" in text


def test_optical_zayju_has_no_kinks_or_unblended_corners() -> None:
    """Only flat stroke terminals may break G1 after join blending."""
    report, _, _ = zayju_report(DesignContext.geometric_sans(), optical=True)
    assert report.kink_count == 0
    assert report.corner_count == 0
    assert report.g1_join_error_count == report.terminal_count
    assert report.g1_join_error_count <= 22
