"""Diagonal optical compensation pass / helper."""

from __future__ import annotations

import math

from typekernel.draw.drawing import Drawing
from typekernel.draw.geomutil import segment_end, segment_start
from typekernel.geo.contour import Contour
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.system import System

Segment = LineSegment | CubicSegment


def compensated_weight(
    stem: float,
    angle_from_vertical_deg: float,
    *,
    contrast: float = 1.0,
    floor: float = 0.55,
) -> float:
    """Perpendicular thickness so a diagonal matches a vertical stem optically.

    Same formula as ``optics.stem.diagonal_compensation``, reimplemented so
    this plugin stays free of optics imports.
    """
    if stem <= 0:
        raise ValueError(f"stem must be positive, got {stem!r}")
    if contrast <= 0:
        raise ValueError(f"contrast must be positive, got {contrast!r}")
    if floor <= 0 or floor > 1.0:
        raise ValueError(f"floor must be in (0, 1], got {floor!r}")
    phi = math.radians(angle_from_vertical_deg)
    w = stem * max(floor, abs(math.cos(phi)))
    w *= 1.0 - (1.0 - contrast) * abs(math.sin(phi))
    return w


def diagonal_comp(
    d: Drawing,
    system: System,
    *,
    at: str,
    angle_from_vertical_deg: float,
    contrast: float = 1.0,
    floor: float = 0.55,
) -> Drawing:
    """Pull a tagged join toward its chord by the diagonal compensation ratio.

    Motion magnitude is ``(1 - compensated/stem)`` scaled into the stem, along
    the vector from the tagged point to the midpoint of its neighbour ends.
    Upright (0°) is a no-op; steeper diagonals thin more. Nodes/slots kept.
    """
    stem = float(system.stem.get("lc") or next(iter(system.stem.values()), 80.0))
    target = compensated_weight(
        stem, angle_from_vertical_deg, contrast=contrast, floor=floor
    )
    ratio = target / stem if stem else 1.0
    pull = max(0.0, 1.0 - ratio)

    found: tuple[int, int] | None = None
    for ci, cnodes in enumerate(d.nodes):
        for node in cnodes:
            if node.tag == at:
                found = (ci, node.index)
                break
        if found is not None:
            break
    if found is None:
        raise KeyError(f"node tag {at!r} not found in drawing")
    ci, idx = found
    contour = d.contours[ci]
    n = len(contour.segments)
    prev = contour.segments[(idx - 1) % n]
    nxt = contour.segments[idx % n]
    pt = segment_start(nxt)
    p_prev = segment_start(prev)
    p_next = segment_end(nxt)
    mid = Point(0.5 * (p_prev.x + p_next.x), 0.5 * (p_prev.y + p_next.y))
    inward = Point(mid.x - pt.x, mid.y - pt.y)
    dist = math.hypot(inward.x, inward.y)
    if dist < 1e-12 or pull <= 1e-12:
        return d
    mag = pull * min(stem * 0.25, dist * 0.45)
    delta = Point(inward.x / dist * mag, inward.y / dist * mag)
    new_pt = Point(pt.x + delta.x, pt.y + delta.y)

    new_segs: list[Segment] = []
    for i, seg in enumerate(contour.segments):
        start = i == (idx % n)
        end = i == ((idx - 1) % n)
        if not (start or end):
            new_segs.append(seg)
            continue
        if isinstance(seg, LineSegment):
            p0 = new_pt if start else seg.p0
            p1 = new_pt if end else seg.p1
            new_segs.append(LineSegment(p0, p1))
        else:
            p0 = new_pt if start else seg.p0
            p3 = new_pt if end else seg.p3
            p1 = Point(
                seg.p1.x + (delta.x if start else 0.0),
                seg.p1.y + (delta.y if start else 0.0),
            )
            p2 = Point(
                seg.p2.x + (delta.x if end else 0.0),
                seg.p2.y + (delta.y if end else 0.0),
            )
            new_segs.append(CubicSegment(p0, p1, p2, p3))

    new_contours = list(d.contours)
    new_contours[ci] = Contour(tuple(new_segs), closed=contour.closed)
    return Drawing(
        contours=tuple(new_contours),
        roles=d.roles,
        nodes=d.nodes,
        slots=d.slots,
    )
