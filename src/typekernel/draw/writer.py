"""Writer — build a Drawing by walking contours (ARCHITECTURE.md §9.3)."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypeAlias

from typekernel.draw.drawing import ContourRole, Drawing, Slot
from typekernel.draw.errors import ContinuityError
from typekernel.draw.fragment import Fragment, Node
from typekernel.draw.geomutil import Segment, points_close, segment_end
from typekernel.geo.contour import Contour, reverse_contour, signed_area
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.smoothness import g1_join_error

PointLike: TypeAlias = Point | tuple[float, float]

_G1_TOL = 1e-6


def _as_point(p: PointLike) -> Point:
    if isinstance(p, Point):
        return p
    x, y = p
    return Point(float(x), float(y))


def _angle_deg(prev: Segment, nxt: Segment) -> float:
    from typekernel.geo.smoothness import incoming_tangent, outgoing_tangent

    a = incoming_tangent(prev)
    b = outgoing_tangent(nxt)
    la = math.hypot(a.x, a.y)
    lb = math.hypot(b.x, b.y)
    if la < 1e-12 or lb < 1e-12:
        return float("nan")
    a = Point(a.x / la, a.y / la)
    b = Point(b.x / lb, b.y / lb)
    dot = max(-1.0, min(1.0, a.x * b.x + a.y * b.y))
    return math.degrees(math.acos(dot))


class Writer:
    """Imperative contour builder with write-time G1 checks."""

    def __init__(self) -> None:
        self._done_contours: list[Contour] = []
        self._done_roles: list[ContourRole] = []
        self._done_nodes: list[tuple[Node, ...]] = []
        self._slots: list[Slot] = []
        self._segs: list[Segment] = []
        self._nodes: list[Node] = []
        self._corner_at: dict[int, tuple[str, Mapping[str, float]]] = {}
        self._cusp_at: set[int] = set()
        self._pending_end: tuple[str, Mapping[str, float]] | None = None
        self._start: Point | None = None
        self._current: Point | None = None
        self._built = False

    def start(self, p: PointLike) -> Writer:
        self._ensure_open()
        if self._segs:
            raise ValueError("call close() before start() for a new contour")
        pt = _as_point(p)
        self._start = pt
        self._current = pt
        self._nodes = []
        self._corner_at = {}
        self._cusp_at = set()
        self._pending_end = None
        return self

    def line(self, p: PointLike) -> Writer:
        self._ensure_pen_down()
        assert self._current is not None
        dest = _as_point(p)
        seg: Segment = LineSegment(self._current, dest)
        self._append_segment(seg)
        return self

    def curve(self, c1: PointLike, c2: PointLike, p: PointLike) -> Writer:
        self._ensure_pen_down()
        assert self._current is not None
        seg = CubicSegment(self._current, _as_point(c1), _as_point(c2), _as_point(p))
        self._append_segment(seg)
        return self

    def fragment(self, f: Fragment, *, prefix: str = "") -> Writer:
        self._ensure_pen_down()
        assert self._current is not None
        if not points_close(f.start, self._current):
            raise ValueError(
                f"fragment.start {f.start.as_tuple()} != current {self._current.as_tuple()}"
            )
        base = len(self._segs)
        if self._segs:
            self._check_join(self._segs[-1], f.segments[0], join_index=base)
        if self._pending_end is not None:
            tag, meta = self._pending_end
            self._slots.append(
                Slot(
                    kind="end",
                    tag=tag,
                    contour=len(self._done_contours),
                    node=base,
                    meta=meta,
                )
            )
            self._pending_end = None
        self._segs.extend(f.segments)
        tagged = f.tagged(prefix) if prefix else f
        for node in tagged.nodes:
            self._nodes.append(
                Node(index=base + node.index, tag=node.tag, meta=node.meta)
            )
            if float(node.meta.get("cusp", 0.0)) == 1.0:
                self._cusp_at.add(base + node.index)
        self._current = f.end
        return self

    def node(self, tag: str, **meta: float) -> Writer:
        self._ensure_pen_down()
        idx = len(self._segs)
        self._nodes.append(Node(index=idx, tag=tag, meta=meta))
        return self

    def corner(self, tag: str, **meta: float) -> Writer:
        self._ensure_pen_down()
        idx = len(self._segs)
        self._corner_at[idx] = (tag, meta)
        self._nodes.append(Node(index=idx, tag=tag, meta=meta))
        return self

    def cusp(self) -> Writer:
        self._ensure_pen_down()
        self._cusp_at.add(len(self._segs))
        return self

    def end(self, tag: str, **meta: float) -> Writer:
        self._ensure_pen_down()
        self._pending_end = (tag, meta)
        return self

    def close(self, role: ContourRole = "ink") -> Writer:
        self._ensure_pen_down()
        assert self._start is not None and self._current is not None
        if not self._segs:
            raise ValueError("cannot close an empty contour")
        if not points_close(self._current, self._start):
            closing: Segment = LineSegment(self._current, self._start)
            self._append_segment(closing, closing_to_start=True)
        # Closing join between last and first at index 0.
        self._check_join(self._segs[-1], self._segs[0], join_index=0)
        contour = Contour(tuple(self._segs), closed=True)
        nodes = list(self._nodes)
        slots_for_contour = [
            s for s in self._slots if s.contour == len(self._done_contours)
        ]
        # Normalize winding: ink CCW (area>0), counter CW (area<0).
        area = signed_area(contour)
        if (role == "ink" and area < 0) or (role == "counter" and area > 0):
            contour, nodes, new_local_slots = self._reverse_closed(
                contour, nodes, slots_for_contour
            )
            self._replace_contour_slots(len(self._done_contours), new_local_slots)

        # Corner slots (after possible reverse remapping already applied to nodes).
        ci = len(self._done_contours)
        existing_corner_tags = {s.tag for s in self._slots if s.contour == ci and s.kind == "corner"}
        for idx, (tag, meta) in list(self._corner_at.items()):
            # Find remapped index via nodes with same tag if reversed
            node_idx = next((n.index for n in nodes if n.tag == tag), idx)
            if tag not in existing_corner_tags:
                self._slots.append(
                    Slot(kind="corner", tag=tag, contour=ci, node=node_idx, meta=meta)
                )

        self._done_contours.append(contour)
        self._done_roles.append(role)
        self._done_nodes.append(tuple(nodes))
        self._segs = []
        self._nodes = []
        self._corner_at = {}
        self._cusp_at = set()
        self._pending_end = None
        self._start = None
        self._current = None
        return self

    def build(self) -> Drawing:
        if self._segs:
            raise ValueError("close() the open contour before build()")
        if self._built:
            raise ValueError("Writer.build() already called")
        # Unique tags across drawing
        seen: set[str] = set()
        for group in self._done_nodes:
            for node in group:
                if node.tag in seen:
                    raise ValueError(f"duplicate tag {node.tag!r}")
                seen.add(node.tag)
        for slot in self._slots:
            if slot.tag in seen and not any(
                n.tag == slot.tag for group in self._done_nodes for n in group
            ):
                # end slots may not have a node tag duplicate of node; tags must be unique among nodes;
                # slot tags that match node tags are the corner case (corner creates both).
                pass
            if slot.kind == "end" and slot.tag in seen:
                raise ValueError(f"duplicate tag {slot.tag!r}")
            if slot.kind == "end":
                seen.add(slot.tag)
        self._built = True
        return Drawing(
            contours=tuple(self._done_contours),
            roles=tuple(self._done_roles),
            nodes=tuple(self._done_nodes),
            slots=tuple(self._slots),
        )

    # --- internals ---------------------------------------------------------

    def _ensure_open(self) -> None:
        if self._built:
            raise ValueError("Writer already built")

    def _ensure_pen_down(self) -> None:
        self._ensure_open()
        if self._current is None:
            raise ValueError("call start() before drawing")

    def _append_segment(self, seg: Segment, *, closing_to_start: bool = False) -> None:
        assert self._current is not None
        join_index = len(self._segs)
        if self._segs:
            self._check_join(self._segs[-1], seg, join_index=join_index)
        if self._pending_end is not None:
            tag, meta = self._pending_end
            self._slots.append(
                Slot(
                    kind="end",
                    tag=tag,
                    contour=len(self._done_contours),
                    node=join_index,
                    meta=meta,
                )
            )
            self._pending_end = None
        self._segs.append(seg)
        self._current = segment_end(seg)

    def _check_join(self, prev: Segment, nxt: Segment, *, join_index: int) -> None:
        if isinstance(prev, LineSegment) and isinstance(nxt, LineSegment):
            return
        if join_index in self._corner_at or join_index in self._cusp_at:
            return
        # Also allow cusp via node meta already recorded at this index
        for node in self._nodes:
            if node.index == join_index and float(node.meta.get("cusp", 0.0)) == 1.0:
                return
        err = g1_join_error(prev, nxt)
        if err > _G1_TOL:
            tag = None
            for node in self._nodes:
                if node.index == join_index:
                    tag = node.tag
                    break
            pt = segment_end(prev)
            where = f"tag={tag!r}" if tag else f"point={pt.as_tuple()}"
            angle = _angle_deg(prev, nxt)
            raise ContinuityError(
                f"join {join_index} is not G1 ({where}): error {err} > {_G1_TOL}, "
                f"angle_deg={angle}"
            )

    def _reverse_closed(
        self,
        contour: Contour,
        nodes: list[Node],
        slots: list[Slot],
    ) -> tuple[Contour, list[Node], list[Slot]]:
        reversed_c = reverse_contour(contour)
        n = len(reversed_c.segments)
        remap = {i: (n - i) % n for i in range(n)}
        new_nodes = [Node(index=remap[n.index], tag=n.tag, meta=n.meta) for n in nodes]
        new_slots = [
            Slot(
                kind=s.kind,
                tag=s.tag,
                contour=s.contour,
                node=remap[s.node],
                meta=s.meta,
                fill=s.fill,
            )
            for s in slots
        ]
        # Remap corner_at keys for subsequent corner slot emission
        self._corner_at = {
            remap[i]: data for i, data in self._corner_at.items() if i in remap
        }
        self._cusp_at = {remap[i] for i in self._cusp_at if i in remap}
        return reversed_c, new_nodes, new_slots

    def _replace_contour_slots(self, contour_index: int, new_slots: list[Slot]) -> None:
        kept = [s for s in self._slots if s.contour != contour_index]
        self._slots = kept + new_slots
