"""Slot sites, fill protocol, and apply_slots (ARCHITECTURE.md 槽位与填充协议)."""

from __future__ import annotations

import fnmatch
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol, TypeVar

from typekernel.draw.drawing import ContourRole, Drawing, Slot
from typekernel.draw.errors import ContinuityError
from typekernel.draw.fragment import Fragment, Node
from typekernel.draw.geomutil import (
    Segment,
    points_close,
    segment_end,
    segment_start,
)
from typekernel.geo.contour import Contour
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.smoothness import (
    g1_join_error,
    incoming_tangent,
    outgoing_tangent,
)
from typekernel.system import System

_G1_TOL = 1e-6
_POINT_TOL = 1e-6

FillerT = TypeVar("FillerT")


class SlotFillError(ValueError):
    """Raised when a fill trims past an edge or path endpoints miss trim points.

    ``slot_tag`` is set when the failing slot is known so ``Project.evaluate``
    can format ``glyph 'X' slot 'tag': reason``.
    """

    def __init__(self, message: str, *, slot_tag: str | None = None) -> None:
        super().__init__(message)
        self.slot_tag = slot_tag


def _freeze_meta(meta: Mapping[str, float]) -> Mapping[str, float]:
    return MappingProxyType({str(k): float(v) for k, v in meta.items()})


def _unit(v: Point) -> Point:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        return Point(0.0, 0.0)
    return Point(v.x / length, v.y / length)


def _seg_length(seg: Segment) -> float:
    """Edge length: Euclidean for lines, arc length for cubics."""
    if isinstance(seg, LineSegment):
        return math.hypot(seg.p1.x - seg.p0.x, seg.p1.y - seg.p0.y)
    from fontTools.misc.bezierTools import calcCubicArcLength

    return float(
        calcCubicArcLength(
            seg.p0.as_tuple(),
            seg.p1.as_tuple(),
            seg.p2.as_tuple(),
            seg.p3.as_tuple(),
        )
    )


def _cubic_arc_length_to_t(seg: CubicSegment, t: float) -> float:
    """Arc length of ``seg`` from parameter 0 to ``t`` (clamped)."""
    from fontTools.misc.bezierTools import calcCubicArcLength, splitCubicAtT

    t = max(0.0, min(1.0, t))
    if t <= 1e-12:
        return 0.0
    if t >= 1.0 - 1e-12:
        return _seg_length(seg)
    left, _right = splitCubicAtT(
        seg.p0.as_tuple(),
        seg.p1.as_tuple(),
        seg.p2.as_tuple(),
        seg.p3.as_tuple(),
        t,
    )
    return float(calcCubicArcLength(left[0], left[1], left[2], left[3]))


def _t_at_arc_distance(seg: CubicSegment, distance: float) -> float:
    """Parameter ``t`` where arc length from the start equals ``distance``."""
    length = _seg_length(seg)
    if length < 1e-12 or distance <= 0.0:
        return 0.0
    if distance >= length:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if _cubic_arc_length_to_t(seg, mid) < distance:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _point_along(seg: Segment, *, from_start: bool, distance: float) -> Point:
    """Point at arc-length ``distance`` from an endpoint along ``seg``."""
    length = _seg_length(seg)
    if length < 1e-12:
        return segment_start(seg) if from_start else segment_end(seg)
    dist = max(0.0, min(length, distance))
    if isinstance(seg, LineSegment):
        t = dist / length
        if from_start:
            return Point(
                seg.p0.x + (seg.p1.x - seg.p0.x) * t,
                seg.p0.y + (seg.p1.y - seg.p0.y) * t,
            )
        return Point(
            seg.p1.x + (seg.p0.x - seg.p1.x) * t,
            seg.p1.y + (seg.p0.y - seg.p1.y) * t,
        )
    from fontTools.misc.bezierTools import splitCubicAtT

    target = dist if from_start else length - dist
    u = _t_at_arc_distance(seg, target)
    left, _right = splitCubicAtT(
        seg.p0.as_tuple(),
        seg.p1.as_tuple(),
        seg.p2.as_tuple(),
        seg.p3.as_tuple(),
        u,
    )
    return Point(*left[3])


def _trim_segment_end(seg: Segment, distance: float) -> Segment | None:
    length = _seg_length(seg)
    if distance <= 1e-12:
        return seg
    if distance >= length - 1e-12:
        return None
    if isinstance(seg, LineSegment):
        return LineSegment(
            seg.p0, _point_along(seg, from_start=True, distance=length - distance)
        )
    from fontTools.misc.bezierTools import splitCubicAtT

    u = _t_at_arc_distance(seg, length - distance)
    left, _right = splitCubicAtT(
        seg.p0.as_tuple(),
        seg.p1.as_tuple(),
        seg.p2.as_tuple(),
        seg.p3.as_tuple(),
        u,
    )
    pts = [Point(*xy) for xy in left]
    return CubicSegment(pts[0], pts[1], pts[2], pts[3])


def _trim_segment_start(seg: Segment, distance: float) -> Segment | None:
    length = _seg_length(seg)
    if distance <= 1e-12:
        return seg
    if distance >= length - 1e-12:
        return None
    if isinstance(seg, LineSegment):
        return LineSegment(_point_along(seg, from_start=True, distance=distance), seg.p1)
    from fontTools.misc.bezierTools import splitCubicAtT

    u = _t_at_arc_distance(seg, distance)
    _left, right = splitCubicAtT(
        seg.p0.as_tuple(),
        seg.p1.as_tuple(),
        seg.p2.as_tuple(),
        seg.p3.as_tuple(),
        u,
    )
    pts = [Point(*xy) for xy in right]
    return CubicSegment(pts[0], pts[1], pts[2], pts[3])


@dataclass(frozen=True, slots=True)
class CornerSite:
    tag: str
    point: Point
    in_dir: Point
    out_dir: Point
    in_len: float
    out_len: float
    role: ContourRole
    meta: Mapping[str, float] = field(default_factory=dict)
    # Real adjacent edges (set by apply_slots). Optional so synthetic sites in
    # tests can still construct a CornerSite with directions only.
    in_edge: Segment | None = None
    out_edge: Segment | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))

    def point_in(self, trim: float) -> Point:
        """Point trim units back along the real incoming edge (arc length)."""
        if self.in_edge is not None:
            return _point_along(self.in_edge, from_start=False, distance=float(trim))
        return Point(
            self.point.x - self.in_dir.x * float(trim),
            self.point.y - self.in_dir.y * float(trim),
        )

    def point_out(self, trim: float) -> Point:
        """Point trim units forward along the real outgoing edge (arc length)."""
        if self.out_edge is not None:
            return _point_along(self.out_edge, from_start=True, distance=float(trim))
        return Point(
            self.point.x + self.out_dir.x * float(trim),
            self.point.y + self.out_dir.y * float(trim),
        )


@dataclass(frozen=True, slots=True)
class CornerFill:
    trim_in: float
    trim_out: float
    path: Fragment | None = None  # None + zero trim → geometry no-op (槽位与填充协议)


class CornerFiller(Protocol):
    def __call__(self, site: CornerSite, system: System) -> CornerFill: ...


@dataclass(frozen=True, slots=True)
class EndSite:
    tag: str
    a: Point
    b: Point
    a_dir: Point
    b_dir: Point
    role: ContourRole
    meta: Mapping[str, float] = field(default_factory=dict)
    cut_edge: Segment | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))

    def point_a(self, trim: float) -> Point:
        """Point trim units from ``a`` toward ``b`` along the real cut edge."""
        if self.cut_edge is not None:
            return _point_along(self.cut_edge, from_start=True, distance=float(trim))
        length = math.hypot(self.b.x - self.a.x, self.b.y - self.a.y)
        if length < 1e-12:
            return self.a
        t = max(0.0, min(1.0, float(trim) / length))
        return Point(
            self.a.x + (self.b.x - self.a.x) * t,
            self.a.y + (self.b.y - self.a.y) * t,
        )

    def point_b(self, trim: float) -> Point:
        """Point trim units from ``b`` toward ``a`` along the real cut edge."""
        if self.cut_edge is not None:
            return _point_along(self.cut_edge, from_start=False, distance=float(trim))
        length = math.hypot(self.b.x - self.a.x, self.b.y - self.a.y)
        if length < 1e-12:
            return self.b
        t = max(0.0, min(1.0, float(trim) / length))
        return Point(
            self.b.x + (self.a.x - self.b.x) * t,
            self.b.y + (self.a.y - self.b.y) * t,
        )


@dataclass(frozen=True, slots=True)
class EndFill:
    trim_a: float
    trim_b: float
    path: Fragment | None = None  # None + zero trim → geometry no-op (槽位与填充协议)


class EndFiller(Protocol):
    def __call__(self, site: EndSite, system: System) -> EndFill: ...


def _match_filler(
    tag: str,
    patterns: Mapping[str, FillerT],
    named: Mapping[str, object],
    fill_name: str | None,
) -> FillerT | None:
    if fill_name is not None:
        if fill_name not in named:
            raise SlotFillError(f"Slot.fill={fill_name!r} not in named fillers")
        return named[fill_name]  # type: ignore[return-value]
    for pattern, filler in patterns.items():
        if fnmatch.fnmatchcase(tag, pattern):
            return filler
    return None


def _assert_path_endpoints(
    path: Fragment, start: Point, end: Point, *, slot_tag: str | None = None
) -> None:
    if not points_close(path.start, start, _POINT_TOL):
        raise SlotFillError(
            f"fill path start {path.start.as_tuple()} != trim point {start.as_tuple()}",
            slot_tag=slot_tag,
        )
    if not points_close(path.end, end, _POINT_TOL):
        raise SlotFillError(
            f"fill path end {path.end.as_tuple()} != trim point {end.as_tuple()}",
            slot_tag=slot_tag,
        )


def _is_degenerate_line(seg: Segment) -> bool:
    """True for near-zero line segments (ignored by continuity checks)."""
    return isinstance(seg, LineSegment) and _seg_length(seg) < 1e-9


def _is_noop_corner_fill(fill: CornerFill) -> bool:
    """槽位与填充协议: plain ≡ unmatched — zero trim and no real path is a no-op.

    Preferred signal: ``path is None`` (see ``plugins.corners.geom.noop_corner_fill``).
    Legacy zero-length-only paths are still treated as no-op so old fillers do not
    insert segments; new code must not emit those segments.
    """
    if fill.trim_in > 1e-12 or fill.trim_out > 1e-12:
        return False
    if fill.path is None:
        return True
    segs = fill.path.segments
    if not segs:
        return True
    return all(_is_degenerate_line(s) for s in segs)


def _is_noop_end_fill(fill: EndFill) -> bool:
    """槽位与填充协议: degenerate end params ≡ unmatched — zero trim and no real path.

    Preferred signal: ``path is None`` (see ``plugins.ends.geom.noop_end_fill``).
    """
    if fill.trim_a > 1e-12 or fill.trim_b > 1e-12:
        return False
    if fill.path is None:
        return True
    segs = fill.path.segments
    if not segs:
        return True
    return all(_is_degenerate_line(s) for s in segs)


def _check_contour_g1(
    segments: tuple[Segment, ...],
    *,
    exempt_nodes: set[int] | None = None,
) -> None:
    """Post-fill G1 check; ``exempt_nodes`` are on-curve indices still marked corner.

    Intentional skips (ARCHITECTURE.md Writer / 槽位与填充协议):
    - ``exempt_nodes``: sharp corners left unmatched or filled with plain/noop.
    - line–line joins: G1 is not required (sharp corners between straights).

    Zero-length segments are **not** skipped: fillers must return ``path=None``
    instead of inserting degenerates. Finding one is a ContinuityError.
    """
    if len(segments) < 2:
        return
    n = len(segments)
    exempt = exempt_nodes or set()
    for i in range(n):
        if i in exempt:
            continue
        prev = segments[(i - 1) % n]
        nxt = segments[i]
        if _is_degenerate_line(prev) or _is_degenerate_line(nxt):
            pt = segment_end(prev)
            raise ContinuityError(
                f"post-fill zero-length segment at {pt.as_tuple()}; "
                "fillers must noop (path=None) instead of inserting degenerates"
            )
        if isinstance(prev, LineSegment) and isinstance(nxt, LineSegment):
            continue
        err = g1_join_error(prev, nxt)
        if err > _G1_TOL:
            pt = segment_end(prev)
            raise ContinuityError(
                f"post-fill join not G1 at {pt.as_tuple()}: error {err} > {_G1_TOL}"
            )


def _corner_site_from_segs(
    segs: list[Segment],
    node_index: int,
    *,
    tag: str,
    role: ContourRole,
    meta: Mapping[str, float],
) -> CornerSite:
    n = len(segs)
    idx = node_index % n
    prev = segs[(idx - 1) % n]
    nxt = segs[idx]
    point = segment_start(nxt)
    return CornerSite(
        tag=tag,
        point=point,
        in_dir=_unit(incoming_tangent(prev)),
        out_dir=_unit(outgoing_tangent(nxt)),
        in_len=_seg_length(prev),
        out_len=_seg_length(nxt),
        role=role,
        meta=meta,
        in_edge=prev,
        out_edge=nxt,
    )


def _apply_corner(
    segs: list[Segment], node_index: int, fill: CornerFill, site: CornerSite
) -> list[Segment]:
    n = len(segs)
    prev_i = (node_index - 1) % n
    next_i = node_index % n
    if fill.trim_in > site.in_len + 1e-9 or fill.trim_out > site.out_len + 1e-9:
        raise SlotFillError(
            f"trim exceeds edge length for {site.tag!r}: "
            f"trim_in={fill.trim_in}/{site.in_len}, trim_out={fill.trim_out}/{site.out_len}",
            slot_tag=site.tag,
        )
    trim_start = _point_along(segs[prev_i], from_start=False, distance=fill.trim_in)
    trim_end = _point_along(segs[next_i], from_start=True, distance=fill.trim_out)
    if fill.path is not None:
        _assert_path_endpoints(fill.path, trim_start, trim_end, slot_tag=site.tag)

    new_prev = _trim_segment_end(segs[prev_i], fill.trim_in)
    new_next = _trim_segment_start(segs[next_i], fill.trim_out)

    out: list[Segment] = []
    i = (next_i + 1) % n
    while i != prev_i:
        out.append(segs[i])
        i = (i + 1) % n
    if new_prev is not None:
        out.append(new_prev)
    if fill.path is not None:
        out.extend(fill.path.segments)
    if new_next is not None:
        out.append(new_next)
    if not out:
        raise SlotFillError(
            f"corner fill for {site.tag!r} removed entire contour",
            slot_tag=site.tag,
        )
    return out


def _apply_end(segs: list[Segment], node_index: int, fill: EndFill, site: EndSite) -> list[Segment]:
    n = len(segs)
    idx = node_index % n
    cut = segs[idx]
    cut_len = _seg_length(cut)
    if fill.trim_a < 0 or fill.trim_b < 0:
        raise SlotFillError(f"negative end trim for {site.tag!r}", slot_tag=site.tag)
    if fill.trim_a + fill.trim_b > cut_len + 1e-9:
        raise SlotFillError(
            f"end trim exceeds cut length for {site.tag!r}: "
            f"{fill.trim_a}+{fill.trim_b} > {cut_len}",
            slot_tag=site.tag,
        )
    if fill.path is None:
        raise SlotFillError(
            f"end fill for {site.tag!r} has path=None (use noop skip)",
            slot_tag=site.tag,
        )
    pa = _point_along(cut, from_start=True, distance=fill.trim_a)
    pb = _point_along(cut, from_start=False, distance=fill.trim_b)
    _assert_path_endpoints(fill.path, pa, pb, slot_tag=site.tag)
    replacement: list[Segment] = []
    if fill.trim_a > 1e-12:
        replacement.append(LineSegment(segment_start(cut), pa))
    replacement.extend(fill.path.segments)
    if fill.trim_b > 1e-12:
        replacement.append(LineSegment(pb, segment_end(cut)))
    return segs[:idx] + replacement + segs[idx + 1 :]


def apply_slots(
    d: Drawing,
    system: System,
    corners: Mapping[str, CornerFiller],
    ends: Mapping[str, EndFiller],
    named: Mapping[str, CornerFiller | EndFiller] | None = None,
) -> Drawing:
    """Apply corner/end fillers; unmatched and ``plain`` leave geometry unchanged."""
    named_map: dict[str, CornerFiller | EndFiller] = dict(named or {})
    new_contours: list[Contour] = []
    new_nodes: list[tuple[Node, ...]] = []
    remaining_slots: list[Slot] = []

    slots_by_c: dict[int, list[Slot]] = {i: [] for i in range(len(d.contours))}
    for slot in d.slots:
        slots_by_c[slot.contour].append(slot)

    for ci, (contour, role, cnodes) in enumerate(
        zip(d.contours, d.roles, d.nodes, strict=True)
    ):
        applied: set[str] = set()
        original = list(contour.segments)
        working = list(original)

        corner_slots = [s for s in slots_by_c[ci] if s.kind == "corner"]
        end_slots = [s for s in slots_by_c[ci] if s.kind == "end"]

        planned: list[tuple[Slot, int]] = []
        for slot in corner_slots:
            filler = _match_filler(slot.tag, corners, named_map, slot.fill)
            if filler is None:
                remaining_slots.append(slot)
                continue
            planned.append((slot, slot.node))

        for slot, node_index in sorted(planned, key=lambda t: t[1], reverse=True):
            corner_filler = _match_filler(slot.tag, corners, named_map, slot.fill)
            assert corner_filler is not None
            n = len(working)
            if len(planned) == 1 or working == original:
                idx = node_index % n
            else:
                orig_site = _corner_site_from_segs(
                    original, node_index, tag=slot.tag, role=role, meta=slot.meta
                )
                candidates = [
                    j
                    for j in range(n)
                    if points_close(segment_start(working[j]), orig_site.point, 1e-4)
                ]
                if not candidates:
                    raise SlotFillError(
                        f"could not relocate corner {slot.tag!r} after prior fill",
                        slot_tag=slot.tag,
                    )
                if len(candidates) == 1:
                    idx = candidates[0]
                else:
                    # Same coordinates can appear twice (e.g. n shoulder meet).
                    # Prefer the candidate whose in/out directions match the
                    # original site so we do not fill a G1 join by mistake.
                    best_j = candidates[0]
                    best_score = float("inf")
                    for j in candidates:
                        site_j = _corner_site_from_segs(
                            working, j, tag=slot.tag, role=role, meta=slot.meta
                        )
                        score = (
                            (site_j.in_dir.x - orig_site.in_dir.x) ** 2
                            + (site_j.in_dir.y - orig_site.in_dir.y) ** 2
                            + (site_j.out_dir.x - orig_site.out_dir.x) ** 2
                            + (site_j.out_dir.y - orig_site.out_dir.y) ** 2
                        )
                        if score < best_score:
                            best_score = score
                            best_j = j
                    idx = best_j
            site = _corner_site_from_segs(
                working, idx, tag=slot.tag, role=role, meta=slot.meta
            )
            requires = getattr(corner_filler, "requires", None) or ()
            if "line-line" in requires and not (
                isinstance(site.in_edge, LineSegment)
                and isinstance(site.out_edge, LineSegment)
            ):
                # Filler needs straight neighbors; leave geometry + slot (info skip).
                remaining_slots.append(slot)
                continue
            fill = corner_filler(site, system)
            if not isinstance(fill, CornerFill):
                raise SlotFillError(
                    f"corner filler for {slot.tag!r} returned {type(fill)}",
                    slot_tag=slot.tag,
                )
            # plain / zero-radius: leave geometry + corner slot (槽位与填充协议 ≡ unmatched).
            if _is_noop_corner_fill(fill):
                remaining_slots.append(slot)
                continue
            working = _apply_corner(working, idx, fill, site)
            applied.add(slot.tag)

        for slot in end_slots:
            end_filler = _match_filler(slot.tag, ends, named_map, slot.fill)
            if end_filler is None:
                remaining_slots.append(slot)
                continue
            n = len(working)
            idx = slot.node % n
            cut = working[idx]
            site_e = EndSite(
                tag=slot.tag,
                a=segment_start(cut),
                b=segment_end(cut),
                a_dir=_unit(incoming_tangent(working[(idx - 1) % n])),
                b_dir=_unit(outgoing_tangent(working[(idx + 1) % n])),
                role=role,
                meta=slot.meta,
                cut_edge=cut,
            )
            fill_e = end_filler(site_e, system)
            if not isinstance(fill_e, EndFill):
                raise SlotFillError(
                    f"end filler for {slot.tag!r} returned {type(fill_e)}",
                    slot_tag=slot.tag,
                )
            # Degenerate end params: leave geometry + end slot (槽位与填充协议 ≡ unmatched).
            if _is_noop_end_fill(fill_e):
                remaining_slots.append(slot)
                continue
            if fill_e.path is None:
                raise SlotFillError(
                    f"end filler for {slot.tag!r} returned path=None with non-zero trim",
                    slot_tag=slot.tag,
                )
            working = _apply_end(working, idx, fill_e, site_e)
            applied.add(slot.tag)

        new_contour = Contour(tuple(working), closed=True)
        exempt = {
            s.node
            for s in remaining_slots
            if s.contour == ci and s.kind == "corner"
        }
        _check_contour_g1(new_contour.segments, exempt_nodes=exempt)
        new_contours.append(new_contour)
        new_nodes.append(tuple(node for node in cnodes if node.tag not in applied))

    return Drawing(
        contours=tuple(new_contours),
        roles=d.roles,
        nodes=tuple(new_nodes),
        slots=tuple(remaining_slots),
        measures=d.measures,
    )
