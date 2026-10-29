"""explain topology on latin-sans e / three."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from typekernel.cli.explain_cmd import explain_project, format_report
from typekernel.cli.new import create_project
from typekernel.perceive.topology import measure_topology


def _starter(tmp: Path) -> Path:
    return create_project("explain_trial", parent=tmp, starter="latin-sans")


def test_latin_sans_e_has_two_counters() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = _starter(td)
        report = explain_project(root, "e")
        assert report.counters == 2, report
        assert report.islands == 1, report
    finally:
        shutil.rmtree(td)


def test_latin_sans_three_has_at_least_two_counters() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = _starter(td)
        report = explain_project(root, "three")
        assert report.counters >= 2, report
    finally:
        shutil.rmtree(td)


def test_explain_json_roundtrip() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = _starter(td)
        report = explain_project(root, "o")
        payload = json.loads(format_report(report, as_json=True))
        assert payload["glyph"] == "o"
        assert payload["counters"] == 1
        assert payload["islands"] == 1
        assert "nodes" in payload
    finally:
        shutil.rmtree(td)


def test_measure_topology_synthetic_ring() -> None:
    from typekernel.geo.contour import Contour
    from typekernel.geo.outline import Outline
    from typekernel.geo.point import Point
    from typekernel.geo.segment import LineSegment

    def rect(x0, y0, x1, y1, *, ccw: bool) -> Contour:
        if ccw:
            segs = (
                LineSegment(Point(x0, y0), Point(x1, y0)),
                LineSegment(Point(x1, y0), Point(x1, y1)),
                LineSegment(Point(x1, y1), Point(x0, y1)),
                LineSegment(Point(x0, y1), Point(x0, y0)),
            )
        else:
            segs = (
                LineSegment(Point(x0, y0), Point(x0, y1)),
                LineSegment(Point(x0, y1), Point(x1, y1)),
                LineSegment(Point(x1, y1), Point(x1, y0)),
                LineSegment(Point(x1, y0), Point(x0, y0)),
            )
        return Contour(segs, closed=True)

    ring = Outline((rect(0, 0, 100, 100, ccw=True), rect(25, 25, 75, 75, ccw=False)))
    topo = measure_topology(ring, stem=10)
    assert topo.islands == 1
    assert topo.counters == 1
