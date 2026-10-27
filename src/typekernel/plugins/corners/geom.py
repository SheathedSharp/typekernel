"""Shared geometry helpers for corner fillers (public; no cross-plugin imports)."""

from __future__ import annotations

import math

from typekernel.draw.slots import CornerFill, CornerSite
from typekernel.geo.point import Point
from typekernel.system import System


def unit(v: Point) -> Point:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        return Point(0.0, 0.0)
    return Point(v.x / length, v.y / length)


def stem_ref(site: CornerSite, system: System) -> float:
    """Stem width: ``meta['stem']``, else a ``System.stem`` value, else edge min."""
    if "stem" in site.meta:
        return float(site.meta["stem"])
    for key in ("lc", "uc", "fig"):
        if key in system.stem:
            return float(system.stem[key])
    if system.stem:
        return float(next(iter(system.stem.values())))
    return min(site.in_len, site.out_len)


def turn_cross(site: CornerSite) -> float:
    """``in_dir × out_dir`` — positive means a left (CCW) turn."""
    return site.in_dir.x * site.out_dir.y - site.in_dir.y * site.out_dir.x


def exterior_unit(site: CornerSite) -> Point:
    """Unit normal pointing to the exterior at the corner (right of travel if CCW)."""
    if turn_cross(site) >= 0.0:
        return Point(site.in_dir.y, -site.in_dir.x)
    return Point(-site.in_dir.y, site.in_dir.x)


def interior_unit(site: CornerSite) -> Point:
    return Point(-exterior_unit(site).x, -exterior_unit(site).y)


def clamp_trim(distance: float, limit: float) -> float:
    if distance < 0.0:
        return 0.0
    return min(distance, max(0.0, limit - 1e-9))


def noop_corner_fill(site: CornerSite) -> CornerFill:
    """Canonical §9.5 geometry no-op (plain / radius·size → 0).

    Zero trim and ``path=None`` so ``apply_slots`` skips ``_apply_corner``,
    leaves contour segments unchanged, and keeps the corner slot — same as
    an unmatched pattern. Fillers must call this instead of inventing
    zero-length segments.
    """
    del site  # site identity unused; signature documents the call site
    return CornerFill(trim_in=0.0, trim_out=0.0, path=None)
