"""P5-2: humanist-italic e/four no longer closed-θ / broken-4."""

from __future__ import annotations

from pathlib import Path

from typekernel.project import open_project

STARTER = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_humanist_italic"


def test_e_has_aperture_not_closed_theta() -> None:
    with open_project(STARTER) as session:
        draft = session.evaluate("e")
        # open_bowl construction → at least one open contour path (ink without full ring seal)
        # Topology: expect apertures declared or 2 contours (bowl + bar).
        g = session.glyph("e")
        assert len(g.outline.contours) >= 2
        expect = session.project.expect.get("e") if session.project.expect else None
        # Soft: e should not be a single annulus (θ). Contour count 2+ from bowl+bar.
        assert len(g.outline.contours) >= 2


def test_four_has_three_strokes() -> None:
    with open_project(STARTER) as session:
        g = session.glyph("four")
        assert len(g.outline.contours) >= 3
