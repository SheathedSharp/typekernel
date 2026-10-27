"""Drawing — multi-contour result of Writer (ARCHITECTURE.md §9.4)."""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from typekernel.draw.fragment import Node
from typekernel.draw.geomutil import map_segment, segment_end, segment_start
from typekernel.geo.contour import Contour, reverse_contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point

ContourRole = Literal["ink", "counter"]


def _freeze_meta(meta: Mapping[str, float]) -> Mapping[str, float]:
    return MappingProxyType({str(k): float(v) for k, v in meta.items()})


@dataclass(frozen=True, slots=True)
class Slot:
    """A corner or end site awaiting a plugin fill."""

    kind: Literal["corner", "end"]
    tag: str
    contour: int
    node: int
    meta: Mapping[str, float] = field(default_factory=dict)
    fill: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))


@dataclass(frozen=True, slots=True)
class Drawing:
    """Closed contours with named nodes and slots."""

    contours: tuple[Contour, ...]
    roles: tuple[ContourRole, ...]
    nodes: tuple[tuple[Node, ...], ...]
    slots: tuple[Slot, ...] = ()

    def __post_init__(self) -> None:
        if len(self.contours) != len(self.roles) or len(self.contours) != len(self.nodes):
            raise ValueError("contours, roles, and nodes must have the same length")

    def point(self, tag: str) -> Point:
        for contour_nodes, contour in zip(self.nodes, self.contours, strict=True):
            for node in contour_nodes:
                if node.tag == tag:
                    return on_curve_at(contour, node.index)
        raise KeyError(tag)

    def find(self, pattern: str) -> list[Node]:
        found: list[Node] = []
        for contour_nodes in self.nodes:
            for node in contour_nodes:
                if fnmatch.fnmatchcase(node.tag, pattern):
                    found.append(node)
        return found

    def outline(self) -> Outline:
        return Outline(self.contours)

    def translated(self, dx: float, dy: float = 0.0) -> Drawing:
        def move(p: Point) -> Point:
            return Point(p.x + dx, p.y + dy)

        contours = tuple(
            Contour(tuple(map_segment(s, move) for s in c.segments), closed=c.closed)
            for c in self.contours
        )
        return Drawing(contours, self.roles, self.nodes, self.slots)

    def mirrored_x(self, axis_x: float) -> Drawing:
        def mirror(p: Point) -> Point:
            return Point(2.0 * axis_x - p.x, p.y)

        new_contours: list[Contour] = []
        new_nodes: list[tuple[Node, ...]] = []
        for contour, cnodes in zip(self.contours, self.nodes, strict=True):
            mirrored = Contour(
                tuple(map_segment(s, mirror) for s in contour.segments),
                closed=contour.closed,
            )
            reversed_c = reverse_contour(mirrored)
            n = len(reversed_c.segments)
            remap = {i: (n - i) % n for i in range(n)} if n else {}
            remapped_nodes = tuple(
                Node(index=remap[node.index], tag=node.tag, meta=node.meta)
                for node in cnodes
            )
            new_contours.append(reversed_c)
            new_nodes.append(remapped_nodes)
        rebuilt: list[Slot] = []
        for slot in self.slots:
            n = len(new_contours[slot.contour].segments)
            remap_i = (n - slot.node) % n if n else 0
            rebuilt.append(
                Slot(
                    kind=slot.kind,
                    tag=slot.tag,
                    contour=slot.contour,
                    node=remap_i,
                    meta=slot.meta,
                    fill=slot.fill,
                )
            )
        return Drawing(tuple(new_contours), self.roles, tuple(new_nodes), tuple(rebuilt))


def on_curve_at(contour: Contour, index: int) -> Point:
    if not contour.segments:
        raise IndexError(index)
    n = len(contour.segments)
    if contour.closed:
        if not 0 <= index < n:
            raise IndexError(index)
        return segment_start(contour.segments[index])
    if not 0 <= index <= n:
        raise IndexError(index)
    if index == n:
        return segment_end(contour.segments[-1])
    return segment_start(contour.segments[index])
