"""Fragment — a reusable open chain of segments with optional named nodes."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from typekernel.draw.errors import ContinuityError
from typekernel.draw.geomutil import (
    Segment,
    map_segment,
    points_close,
    reverse_segment,
    segment_end,
    segment_start,
)
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment
from typekernel.geo.smoothness import (
    g1_join_error,
    incoming_tangent,
    outgoing_tangent,
)

_G1_TOL = 1e-6


def _unit(v: Point) -> Point:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        return Point(0.0, 0.0)
    return Point(v.x / length, v.y / length)


def _freeze_meta(meta: Mapping[str, float]) -> Mapping[str, float]:
    return MappingProxyType({str(k): float(v) for k, v in meta.items()})


def _node_at(nodes: tuple[Node, ...], index: int) -> Node | None:
    for node in nodes:
        if node.index == index:
            return node
    return None


def _is_curve(seg: Segment) -> bool:
    return isinstance(seg, CubicSegment)


@dataclass(frozen=True, slots=True)
class Node:
    """A named on-curve point on a fragment or contour."""

    index: int
    tag: str
    meta: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))


@dataclass(frozen=True, slots=True)
class Fragment:
    """An open, non-empty chain of segments with optional named nodes."""

    segments: tuple[Segment, ...]
    nodes: tuple[Node, ...] = ()

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("Fragment.segments must be non-empty")
        frozen_nodes = tuple(
            n if type(n.meta) is MappingProxyType else Node(n.index, n.tag, n.meta)
            for n in self.nodes
        )
        object.__setattr__(self, "nodes", frozen_nodes)

        for i in range(len(self.segments) - 1):
            prev, nxt = self.segments[i], self.segments[i + 1]
            end, start = segment_end(prev), segment_start(nxt)
            if not points_close(end, start):
                raise ValueError(
                    f"Fragment segments do not chain at join {i + 1}: "
                    f"end {end.as_tuple()} != start {start.as_tuple()}"
                )
            if not (_is_curve(prev) or _is_curve(nxt)):
                continue
            join_index = i + 1
            node = _node_at(self.nodes, join_index)
            if node is not None and float(node.meta.get("cusp", 0.0)) == 1.0:
                continue
            err = g1_join_error(prev, nxt)
            if err > _G1_TOL:
                tag = node.tag if node is not None else None
                where = f"tag={tag!r}" if tag else f"point={end.as_tuple()}"
                raise ContinuityError(
                    f"Fragment join {join_index} is not G1 ({where}): "
                    f"error {err} > tol {_G1_TOL}"
                )

    @property
    def start(self) -> Point:
        return segment_start(self.segments[0])

    @property
    def end(self) -> Point:
        return segment_end(self.segments[-1])

    def start_tangent(self) -> Point:
        return _unit(outgoing_tangent(self.segments[0]))

    def end_tangent(self) -> Point:
        return _unit(incoming_tangent(self.segments[-1]))

    def reversed(self) -> Fragment:
        n_seg = len(self.segments)
        new_segs = tuple(reverse_segment(s) for s in reversed(self.segments))
        new_nodes = tuple(
            Node(index=n_seg - n.index, tag=n.tag, meta=n.meta) for n in self.nodes
        )
        return Fragment(new_segs, new_nodes)

    def translated(self, dx: float, dy: float = 0.0) -> Fragment:
        def move(p: Point) -> Point:
            return Point(p.x + dx, p.y + dy)

        return Fragment(tuple(map_segment(s, move) for s in self.segments), self.nodes)

    def mirrored_x(self, axis_x: float) -> Fragment:
        def mirror(p: Point) -> Point:
            return Point(2.0 * axis_x - p.x, p.y)

        mirrored = Fragment(
            tuple(map_segment(s, mirror) for s in self.segments), self.nodes
        )
        return mirrored.reversed()

    def mirrored_y(self, axis_y: float) -> Fragment:
        def mirror(p: Point) -> Point:
            return Point(p.x, 2.0 * axis_y - p.y)

        mirrored = Fragment(
            tuple(map_segment(s, mirror) for s in self.segments), self.nodes
        )
        return mirrored.reversed()

    def tagged(self, prefix: str) -> Fragment:
        if not prefix:
            return self
        new_nodes = tuple(
            Node(index=n.index, tag=f"{prefix}.{n.tag}", meta=n.meta) for n in self.nodes
        )
        return Fragment(self.segments, new_nodes)
