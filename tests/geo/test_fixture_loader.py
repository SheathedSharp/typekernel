"""Unit tests for the synthetic fixture loader."""

import json
from pathlib import Path

import pytest

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.point import Point

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def test_fixture_loads_into_an_outline() -> None:
    outline = load_synthetic_outline(FIXTURE)
    assert outline.contour_count == 2
    assert not any(contour.is_empty for contour in outline.contours)


def test_loaded_contours_are_closed_and_consistent() -> None:
    for contour in load_synthetic_outline(FIXTURE).contours:
        assert contour.closed is True
        contour.assert_closed_consistent()
        contour.assert_segments_continuous()


def test_every_segment_is_cubic() -> None:
    outline = load_synthetic_outline(FIXTURE)
    assert [segment.kind for segment in outline.iter_segments()] == ["cubic"] * 8


def test_outer_contour_geometry_matches_the_document() -> None:
    outline = load_synthetic_outline(FIXTURE)
    outer = outline.contours[0]
    assert len(outer.segments) == 4
    assert outer.segments[0].p0 == Point(850.0, 350.0)
    assert outer.segments[0].p3 == Point(500.0, 700.0)
    assert outer.segments[-1].p3 == Point(850.0, 350.0)


def test_loading_is_deterministic() -> None:
    assert load_synthetic_outline(FIXTURE) == load_synthetic_outline(FIXTURE)


def test_rejects_a_cubic_with_the_wrong_number_of_values(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps({"contours": [{"closed": False, "cubics": [[0, 0, 1, 1, 2, 2]]}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="8 numbers"):
        load_synthetic_outline(bad)


def test_rejects_a_closed_contour_that_does_not_close(tmp_path: Path) -> None:
    bad = tmp_path / "gapped.json"
    bad.write_text(
        json.dumps(
            {
                "contours": [
                    {"closed": True, "cubics": [[0, 0, 0, 1, 1, 1, 1, 0]]}
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="does not close"):
        load_synthetic_outline(bad)


def test_rejects_cubics_that_do_not_meet_end_to_start(tmp_path: Path) -> None:
    """Adjacent cubics with a gap must fail the continuity check."""
    bad = tmp_path / "discontinuous.json"
    bad.write_text(
        json.dumps(
            {
                "contours": [
                    {
                        "closed": False,
                        "cubics": [
                            [0, 0, 0, 1, 1, 1, 1, 0],
                            [2, 0, 2, 1, 3, 1, 3, 0],  # starts at (2,0), not (1,0)
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="gap between segments"):
        load_synthetic_outline(bad)

