"""Vertical overshoot pass for Drawing + System."""

from __future__ import annotations

from typing import Literal

from typekernel.draw.drawing import Drawing
from typekernel.geo.contour import Contour
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.system import System

Kind = Literal["round", "pointed"]
Segment = LineSegment | CubicSegment


def overshoot(
    d: Drawing,
    system: System,
    *,
    kind: Kind = "round",
    at: str | None = None,
    band: float | None = None,
) -> Drawing:
    """Shift vertical extrema past alignment zones by ``system.overshoot``.

    When ``at`` is set, only the on-curve point at that node tag is shifted
    (up if near ``zones.x`` / ``cap`` / ``asc``, down if near ``base`` /
    ``desc``). Otherwise every on-curve point within ``band`` of a zone line
    is shifted.

    ``kind`` selects ``overshoot.round`` vs ``overshoot.pointed``. Nodes and
    slots are preserved unchanged.
    """
    amount = float(system.overshoot.round if kind == "round" else system.overshoot.pointed)
    if amount == 0.0:
        return d
    half = float(band) if band is not None else max(abs(amount), 2.0)
    zones = system.zones
    top_zones = (zones.x, zones.cap, zones.asc)
    bottom_zones = (zones.base, zones.desc)

    tag_at: dict[tuple[int, int], str] = {}
    for ci, cnodes in enumerate(d.nodes):
        for node in cnodes:
            tag_at[(ci, node.index)] = node.tag

    def shift_for_y(y: float) -> float:
        if any(abs(y - z) <= half for z in top_zones):
            return amount
        if any(abs(y - z) <= half for z in bottom_zones):
            return -amount
        return 0.0

    def should_touch(ci: int, node_index: int, y: float) -> bool:
        if at is None:
            return shift_for_y(y) != 0.0
        return tag_at.get((ci, node_index)) == at

    new_contours: list[Contour] = []
    for ci, contour in enumerate(d.contours):
        n = len(contour.segments)
        new_segs: list[Segment] = []
        for i, seg in enumerate(contour.segments):
            if isinstance(seg, LineSegment):
                p0, p1 = seg.p0, seg.p1
                if should_touch(ci, i, p0.y):
                    p0 = Point(p0.x, p0.y + shift_for_y(p0.y))
                ni1 = (i + 1) % n
                if should_touch(ci, ni1, p1.y):
                    p1 = Point(p1.x, p1.y + shift_for_y(p1.y))
                new_segs.append(LineSegment(p0, p1))
            else:
                p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
                if should_touch(ci, i, p0.y):
                    dy = shift_for_y(p0.y)
                    p0 = Point(p0.x, p0.y + dy)
                    p1 = Point(p1.x, p1.y + dy)
                ni1 = (i + 1) % n
                if should_touch(ci, ni1, p3.y):
                    dy = shift_for_y(p3.y)
                    p3 = Point(p3.x, p3.y + dy)
                    p2 = Point(p2.x, p2.y + dy)
                new_segs.append(CubicSegment(p0, p1, p2, p3))
        new_contours.append(Contour(tuple(new_segs), closed=contour.closed))

    return Drawing(
        contours=tuple(new_contours),
        roles=d.roles,
        nodes=d.nodes,
        slots=d.slots,
    )
