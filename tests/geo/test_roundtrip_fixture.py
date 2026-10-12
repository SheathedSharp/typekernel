"""Round-trip tests: fixture cubics ↔ Outline ↔ PathBuilder.

The serialiser lives here rather than in ``fixtures`` on purpose: keep the
loader API small; round-trip coverage belongs in tests, not as a new public
export.
"""

import json
from pathlib import Path

from typekernel.geo.contour import Contour
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"
TOLERANCE = 1e-6


def _serialise(outline: Outline) -> dict[str, object]:
    """Write an all-cubic outline back into the fixture document schema."""
    contours = []
    for contour in outline.contours:
        cubics = []
        for segment in contour.segments:
            assert isinstance(segment, CubicSegment), "fixture round-trip is cubic-only"
            cubics.append([value for point in segment.points for value in point.as_tuple()])
        contours.append({"closed": contour.closed, "cubics": cubics})
    return {"glyph": "O", "unitsPerEm": 1000, "contours": contours}


def _build_with_path_builder(outline: Outline) -> Outline:
    """Re-create the same geometry through the pen-like builder."""
    builder = PathBuilder()
    for contour in outline.contours:
        first = contour.segments[0]
        builder.moveTo(first.p0.x, first.p0.y)
        for segment in contour.segments:
            assert isinstance(segment, CubicSegment)
            builder.curveTo(
                segment.p1.x,
                segment.p1.y,
                segment.p2.x,
                segment.p2.y,
                segment.p3.x,
                segment.p3.y,
            )
        if contour.closed:
            builder.closePath()
    return builder.build()


def _assert_same_geometry(left: Outline, right: Outline) -> None:
    assert left.contour_count == right.contour_count
    for left_contour, right_contour in zip(left.contours, right.contours, strict=True):
        assert left_contour.closed == right_contour.closed
        assert len(left_contour.segments) == len(right_contour.segments)
        for left_segment, right_segment in zip(
            left_contour.segments, right_contour.segments, strict=True
        ):
            assert left_segment.kind == right_segment.kind == "cubic"
            for left_point, right_point in zip(
                left_segment.points, right_segment.points, strict=True
            ):
                assert abs(left_point.x - right_point.x) <= TOLERANCE
                assert abs(left_point.y - right_point.y) <= TOLERANCE


def test_serialised_geometry_matches_the_source_document() -> None:
    outline = load_synthetic_outline(FIXTURE)
    serialised = _serialise(outline)
    original = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert serialised["glyph"] == original["glyph"]
    assert serialised["unitsPerEm"] == original["unitsPerEm"]
    assert len(serialised["contours"]) == len(original["contours"])
    for written, source in zip(
        serialised["contours"], original["contours"], strict=True
    ):
        assert written["closed"] == source["closed"]
        assert written["cubics"] == source["cubics"]


def test_outline_survives_serialise_and_reload(tmp_path: Path) -> None:
    outline = load_synthetic_outline(FIXTURE)
    round_trip_path = tmp_path / "round_trip_O.json"
    round_trip_path.write_text(json.dumps(_serialise(outline)), encoding="utf-8")
    _assert_same_geometry(outline, load_synthetic_outline(round_trip_path))


def test_path_builder_reproduces_the_fixture_cubics() -> None:
    outline = load_synthetic_outline(FIXTURE)
    _assert_same_geometry(outline, _build_with_path_builder(outline))


def test_path_builder_output_survives_a_full_round_trip(tmp_path: Path) -> None:
    outline = load_synthetic_outline(FIXTURE)
    rebuilt = _build_with_path_builder(outline)
    round_trip_path = tmp_path / "rebuilt_O.json"
    round_trip_path.write_text(json.dumps(_serialise(rebuilt)), encoding="utf-8")
    _assert_same_geometry(outline, load_synthetic_outline(round_trip_path))


def test_closure_invariant_holds_after_every_hop(tmp_path: Path) -> None:
    outline = load_synthetic_outline(FIXTURE)
    rebuilt = _build_with_path_builder(outline)
    round_trip_path = tmp_path / "closed_O.json"
    round_trip_path.write_text(json.dumps(_serialise(rebuilt)), encoding="utf-8")
    for contour in load_synthetic_outline(round_trip_path).contours:
        contour.assert_closed_consistent()


def test_handles_are_not_rounded_away_by_the_round_trip() -> None:
    """A coordinate with many digits must come back bit-for-bit, not rounded."""
    awkward = Outline(
        (
            Contour(
                (
                    CubicSegment(
                        Point(0.123456789, 0.0),
                        Point(0.987654321, 1.234567891),
                        Point(2.345678912, 3.456789123),
                        Point(4.567891234, 0.0),
                    ),
                ),
                closed=False,
            ),
        )
    )
    assert _serialise(awkward)["contours"][0]["cubics"][0] == [
        0.123456789,
        0.0,
        0.987654321,
        1.234567891,
        2.345678912,
        3.456789123,
        4.567891234,
        0.0,
    ]
