"""Plain (sharp) corner filler — trim zero, degenerate join path."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.geo.segment import LineSegment
from typekernel.system import System


def plain() -> CornerFiller:
    """Return a filler that keeps the corner sharp.

    Unmatched slots are already left as-is by ``apply_slots`` (plain-equivalent).
    This filler is for explicit ``corners={...: plain()}`` / ``fill="plain"``
    wiring: it trims nothing and inserts a zero-length segment at the corner
    point so path endpoints still land on the trim points.
    """

    def fill(site: CornerSite, system: System) -> CornerFill:
        del system  # plain ignores System; signature matches CornerFiller
        p = site.point
        return CornerFill(
            trim_in=0.0,
            trim_out=0.0,
            path=Fragment((LineSegment(p, p),)),
        )

    return fill
