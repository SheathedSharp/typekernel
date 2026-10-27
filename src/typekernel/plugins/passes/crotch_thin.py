"""Crotch thinning pass — explicit readable optical cut at a tagged join."""

from __future__ import annotations

import math

from typekernel.draw.drawing import Drawing
from typekernel.draw.geomutil import segment_end, segment_start
from typekernel.geo.contour import Contour
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

Segment = LineSegment | CubicSegment


def crotch_thin(d: Drawing, *, at: str, amount: float = 0.82) -> Drawing:
    """Thin the ink at a tagged crotch/join by pulling the corner inward.

    ``amount`` is the fraction of the join to **keep** (ARCHITECTURE.md example
    ``crotch_thin(d, at=..., amount=0.82)``). The tagged on-curve point moves
    toward the midpoint of its two neighbour ends by ``(1 - amount)`` of that
    vector, so ``1.0`` is a no-op and smaller values cut deeper. Nodes/slots
    are preserved.
    """
    if amount <= 0.0:
        raise ValueError(f"amount must be positive, got {amount!r}")
    pull = max(0.0, 1.0 - float(amount))

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
    if pull <= 1e-12:
        return d

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
    if dist < 1e-12:
        return d
    delta = Point(inward.x * pull, inward.y * pull)
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
