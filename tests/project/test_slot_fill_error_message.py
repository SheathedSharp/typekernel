"""Project.evaluate wraps slot failures as GlyphBuildError."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.draw import CornerFill, Fragment
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.project import GlyphBuildError, Project
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80},
    )


def test_evaluate_wraps_slot_fill_error_with_glyph_and_tag(tmp_path: Path) -> None:
    glyphs = tmp_path / "glyphs"
    glyphs.mkdir()
    (glyphs / "syn_box.py").write_text(
        """
from typekernel.draw import Writer
from typekernel.project import glyph

@glyph("syn.box")
def syn_box(system):
    return (
        Writer()
        .start((0, 0))
        .line((20, 0))
        .corner("knee")
        .line((20, 20))
        .line((0, 20))
        .close()
        .build()
    )
""",
        encoding="utf-8",
    )

    def bad_fill(site, system):
        trim = 2.0
        a = Point(site.point.x - 100.0, site.point.y)
        b = site.point_out(trim)
        return CornerFill(
            trim_in=trim,
            trim_out=trim,
            path=Fragment((LineSegment(a, b),)),
        )

    project = Project(
        system=_system(),
        glyphs=glyphs,
        corners={"knee": bad_fill},
    )
    project.discover()
    with pytest.raises(GlyphBuildError, match=r"glyph 'syn\.box'.*slot 'knee'") as ei:
        project.evaluate("syn.box")
    assert ei.value.tag == "knee"
    assert ei.value.glyph == "syn.box"
