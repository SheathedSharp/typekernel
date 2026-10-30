"""S3 diagnose.join + tk audit --text."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.diagnose.engine import audit_project
from typekernel.font.glyph import Anchor, Glyph
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.metrics.join import Join, measure_text_joins


def test_latin_sans_audit_without_text_stays_quiet_on_join(tmp_path: Path) -> None:
    root = create_project("join_quiet", parent=tmp_path, starter="latin-sans")
    report = audit_project(root)
    join_warns = [f for f in report.warnings if f.check.startswith("join.")]
    assert join_warns == []


def test_audit_text_forever_young_on_sans_emits_info_or_spacing(tmp_path: Path) -> None:
    root = create_project("join_text", parent=tmp_path, starter="latin-sans")
    report = audit_project(root, text="forever young")
    # No entry/exit on latin-sans → info missing anchors; must not crash.
    assert any(f.check == "join.missing" for f in report.findings)


def test_well_joined_vs_gappy_rhythm() -> None:
    def box(name: str, entry_x: float, exit_x: float, y: float = 200.0) -> Glyph:
        c = Contour(
            segments=(
                LineSegment(Point(0, 0), Point(100, 0)),
                LineSegment(Point(100, 0), Point(100, 100)),
                LineSegment(Point(100, 100), Point(0, 100)),
                LineSegment(Point(0, 100), Point(0, 0)),
            ),
            closed=True,
        )
        return Glyph(
            name=name,
            outline=Outline(contours=(c,)),
            advance=400,
            unicodes=(ord(name),),
            anchors=(
                Anchor("entry", entry_x, y, angle=0.0, width=40.0),
                Anchor("exit", exit_x, y, angle=0.0, width=40.0),
            ),
        )

    good = {ch: box(ch, 20, 380) for ch in "forever"}
    _m, cv_good = measure_text_joins(good, "forever", use_join_advance=True)
    assert cv_good <= Join().max_gap_cv

    # Gappy: leave advances unjoined (use stored advance) with mismatched exit/entry x
    # so residuals vary wildly when not using join advance.
    bad = {
        "f": box("f", 20, 100),
        "o": box("o", 20, 500),
        "r": box("r", 20, 150),
        "e": box("e", 20, 480),
        "v": box("v", 20, 120),
    }
    # Force non-join advances → large varying gaps
    from typekernel.metrics.join import measure_join_pair

    gaps = []
    names = list("forev")
    for i in range(len(names) - 1):
        m = measure_join_pair(bad[names[i]], bad[names[i + 1]], advance=bad[names[i]].advance)
        gaps.append(m.gap)
    from typekernel.metrics.join import gap_cv

    assert gap_cv(gaps) > Join().max_gap_cv
