"""Drawing — multi-contour result of Writer (ARCHITECTURE.md Drawing)."""

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
class Measure:
    """Declared stem / gap / height check between tagged nodes (target-architecture §4.4)."""

    kind: Literal["stem", "thin", "gap", "height", "crotch"]
    a: str
    b: str | None = None
    expected: float | None = None
    direction_deg: float | None = None

    def prefixed(self, prefix: str) -> Measure:
        """Prefix label refs (used by :meth:`Drawing.tagged`)."""
        if not prefix:
            return self
        return Measure(
            kind=self.kind,
            a=f"{prefix}.{self.a}",
            b=None if self.b is None else f"{prefix}.{self.b}",
            expected=self.expected,
            direction_deg=self.direction_deg,
        )


@dataclass(frozen=True, slots=True)
class Drawing:
    """Closed contours with named nodes and slots."""

    contours: tuple[Contour, ...]
    roles: tuple[ContourRole, ...]
    nodes: tuple[tuple[Node, ...], ...]
    slots: tuple[Slot, ...] = ()
    measures: tuple[Measure, ...] = ()

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


    def signature(self) -> tuple[tuple[ContourRole, tuple[str, ...], tuple[str, ...]], ...]:
        """Compatibility signature: per contour (role, segment kinds, tags).

        Measures are omitted. Equal signatures mean masters are structurally interpolatable (``signature`` 只做结构比较；插值检查由 ``axes.interpolatable`` 负责).
        """
        parts: list[tuple[ContourRole, tuple[str, ...], tuple[str, ...]]] = []
        for role, contour, cnodes in zip(self.roles, self.contours, self.nodes, strict=True):
            kinds = tuple(seg.kind for seg in contour.segments)
            tags = tuple(sorted(n.tag for n in cnodes))
            parts.append((role, kinds, tags))
        return tuple(parts)

    def __add__(self, other: Drawing) -> Drawing:
        """Overlay contours (overlap construction); conflicting tags raise."""
        if not isinstance(other, Drawing):
            return NotImplemented
        seen = {n.tag for group in self.nodes for n in group}
        for group in other.nodes:
            for node in group:
                if node.tag in seen:
                    raise ValueError(f"tag conflict on overlay: {node.tag!r}")
                seen.add(node.tag)
        offset = len(self.contours)
        shifted_slots = tuple(
            Slot(
                kind=s.kind,
                tag=s.tag,
                contour=s.contour + offset,
                node=s.node,
                meta=s.meta,
                fill=s.fill,
            )
            for s in other.slots
        )
        return Drawing(
            contours=self.contours + other.contours,
            roles=self.roles + other.roles,
            nodes=self.nodes + other.nodes,
            slots=self.slots + shifted_slots,
            measures=self.measures + other.measures,
        )


    def tagged(self, prefix: str) -> Drawing:
        """Prefix every node tag and Measure label with ``prefix.``."""
        if not prefix:
            return self
        new_nodes = tuple(
            tuple(
                Node(index=n.index, tag=f"{prefix}.{n.tag}", meta=n.meta) for n in group
            )
            for group in self.nodes
        )
        new_slots = tuple(
            Slot(
                kind=s.kind,
                tag=f"{prefix}.{s.tag}" if s.tag else s.tag,
                contour=s.contour,
                node=s.node,
                meta=s.meta,
                fill=s.fill,
            )
            for s in self.slots
        )
        new_measures = tuple(m.prefixed(prefix) for m in self.measures)
        return Drawing(
            self.contours,
            self.roles,
            new_nodes,
            new_slots,
            new_measures,
        )


    def translated(self, dx: float, dy: float = 0.0) -> Drawing:
        def move(p: Point) -> Point:
            return Point(p.x + dx, p.y + dy)

        contours = tuple(
            Contour(tuple(map_segment(s, move) for s in c.segments), closed=c.closed)
            for c in self.contours
        )
        return Drawing(contours, self.roles, self.nodes, self.slots, self.measures)

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
        return Drawing(
            tuple(new_contours),
            self.roles,
            tuple(new_nodes),
            tuple(rebuilt),
            self.measures,
        )


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
