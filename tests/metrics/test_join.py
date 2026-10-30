"""S3 join advance + rhythm CV."""

from __future__ import annotations

from typekernel.font.glyph import Anchor, Glyph
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.metrics.join import (
    Join,
    gap_cv,
    join_advance,
    measure_join_pair,
    measure_text_joins,
)


def _box_glyph(name: str, *, advance: float, entry=None, exit=None) -> Glyph:
    # Minimal closed square outline so Glyph is valid.
    c = Contour(
        segments=(
            LineSegment(Point(0, 0), Point(100, 0)),
            LineSegment(Point(100, 0), Point(100, 100)),
            LineSegment(Point(100, 100), Point(0, 100)),
            LineSegment(Point(0, 100), Point(0, 0)),
        ),
        closed=True,
    )
    anchors = []
    if entry is not None:
        anchors.append(Anchor("entry", *entry[:2], angle=entry[2] if len(entry) > 2 else 0.0, width=entry[3] if len(entry) > 3 else 40.0))
    if exit is not None:
        anchors.append(Anchor("exit", *exit[:2], angle=exit[2] if len(exit) > 2 else 0.0, width=exit[3] if len(exit) > 3 else 40.0))
    return Glyph(
        name=name,
        outline=Outline(contours=(c,)),
        advance=advance,
        unicodes=(ord(name),) if len(name) == 1 else (),
        anchors=tuple(anchors),
    )


def test_join_advance_aligns_exit_to_entry() -> None:
    left = _box_glyph("a", advance=500, exit=(400, 200, 0, 40))
    right = _box_glyph("b", advance=500, entry=(50, 200, 0, 40))
    ex = left.anchors[0]
    en = right.anchors[0]
    adv = join_advance(ex, en)
    assert adv == 350.0
    m = measure_join_pair(left, right, advance=adv)
    assert m.has_join
    assert m.dy == 0.0
    assert abs(m.gap) < 1e-9


def test_forever_young_dy_under_20_on_joined_fixture() -> None:
    # Shared join height → Δy = 0 for every adjacent pair.
    y = 220.0
    glyphs = {}
    for ch in "forever young":
        if ch == " ":
            continue
        glyphs[ch] = _box_glyph(
            ch,
            advance=400,
            entry=(20, y, 0, 40),
            exit=(380, y, 0, 40),
        )
    measures, cv = measure_text_joins(glyphs, "forever young", use_join_advance=True)
    assert measures
    assert all(m.has_join and m.dy < 20 for m in measures)
    assert cv <= Join().max_gap_cv


def test_gap_cv_fails_on_gappy_fixture() -> None:
    gaps_good = [0.0, 0.0, 0.0, 0.0, 0.0]
    gaps_bad = [2.0, 80.0, 5.0, 90.0, 3.0, 100.0]
    assert gap_cv(gaps_good) <= Join().max_gap_cv
    assert gap_cv(gaps_bad) > Join().max_gap_cv


def test_metrics_join_field_defaults_none() -> None:
    from typekernel.metrics import Metrics

    assert Metrics().join is None
    assert Metrics(join=Join(max_dy=15)).join.max_dy == 15
