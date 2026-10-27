"""Shared helpers for end fillers."""

from __future__ import annotations

import math

from typekernel.draw.slots import EndFill, EndSite
from typekernel.geo.point import Point
from typekernel.system import System


def unit(v: Point) -> Point:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        return Point(0.0, 0.0)
    return Point(v.x / length, v.y / length)


def cut_vec(site: EndSite) -> Point:
    return Point(site.b.x - site.a.x, site.b.y - site.a.y)


def cut_len(site: EndSite) -> float:
    v = cut_vec(site)
    return math.hypot(v.x, v.y)


def tip_outs(site: EndSite) -> tuple[Point, Point]:
    """Unit directions past the tip along each stroke edge."""
    return unit(site.a_dir), unit(Point(-site.b_dir.x, -site.b_dir.y))


def stem_ref(site: EndSite, system: System) -> float:
    if "stem" in site.meta:
        return float(site.meta["stem"])
    for key in ("lc", "uc", "fig"):
        if key in system.stem:
            return float(system.stem[key])
    if system.stem:
        return float(next(iter(system.stem.values())))
    return max(cut_len(site), 1.0)


def noop_end_fill(site: EndSite) -> EndFill:
    """Canonical §9.5 geometry no-op for ends (inset/radius/amount → 0).

    Zero trim and ``path=None`` so ``apply_slots`` skips ``_apply_end``,
    leaves the cut unchanged, and keeps the end slot — same as unmatched.
    """
    del site
    return EndFill(trim_a=0.0, trim_b=0.0, path=None)
