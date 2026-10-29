"""humanist-italic e/four no longer closed-θ / broken-4."""

from __future__ import annotations

from pathlib import Path

from typekernel.project import open_project

STARTER = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_humanist_italic"


def test_e_has_aperture_not_closed_theta() -> None:
    with open_project(STARTER) as session:
        g = session.glyph("e")
        # open_bowl + bar → at least two contours (not a single annulus θ).
        assert len(g.outline.contours) >= 2


def test_four_has_open_spine_and_bar() -> None:
    with open_project(STARTER) as session:
        g = session.glyph("four")
        # Spine (diag+stem) + gapped crossbar — two contours after expand.
        assert len(g.outline.contours) >= 2
