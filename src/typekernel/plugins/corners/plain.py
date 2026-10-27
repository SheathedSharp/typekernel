"""Plain (sharp) corner filler — geometry no-op (§9.5)."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.geo.segment import LineSegment
from typekernel.system import System


def plain() -> CornerFiller:
    """Return a filler that keeps the corner sharp without changing segments.

    Unmatched slots already leave geometry as-is (plain-equivalent). This filler
    is for explicit ``corners={...: plain()}`` / ``fill="plain"`` wiring: it
    reports zero trim and a degenerate path so ``apply_slots`` treats it as a
    no-op and keeps the corner slot (§9.5 ≡ unmatched).
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
