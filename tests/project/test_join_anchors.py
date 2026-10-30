"""GlyphDraft entry/exit anchors carry angle and width."""

from __future__ import annotations

from typekernel.geo.point import Point
from typekernel.project.evaluate import anchors_from_draft


def test_draft_join_anchor_tuple() -> None:
    anchors = anchors_from_draft(
        {
            "entry": (10.0, 200.0, 5.0, 42.0),
            "exit": (400.0, 200.0, 5.0, 42.0),
            "top": Point(200, 700),
        }
    )
    by = {a.name: a for a in anchors}
    assert by["entry"].angle == 5.0
    assert by["entry"].width == 42.0
    assert by["exit"].x == 400.0
    assert by["top"].angle is None
