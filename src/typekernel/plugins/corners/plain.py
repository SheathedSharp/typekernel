"""Plain (sharp) corner filler — geometry no-op (槽位与填充协议)."""

from __future__ import annotations

from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.plugins.corners.geom import noop_corner_fill
from typekernel.system import System


def plain() -> CornerFiller:
    """Return a filler that keeps the corner sharp without changing segments.

    Unmatched slots already leave geometry as-is (plain-equivalent). This filler
    is for explicit ``corners={...: plain()}`` / ``fill="plain"`` wiring: it
    returns the shared noop fill so ``apply_slots`` skips apply and keeps the
    corner slot (槽位与填充协议 ≡ unmatched).
    """

    def fill(site: CornerSite, system: System) -> CornerFill:
        del system  # plain ignores System; signature matches CornerFiller
        return noop_corner_fill(site)

    return fill
