"""Slot sites, fill protocol, and apply_slots (ARCHITECTURE.md §9.5)."""

from __future__ import annotations

import fnmatch
import itertools
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

T = TypeVar("T")


class SlotFillError(ValueError):
    """Raised when a fill trims past an edge or path endpoints miss trim points."""


def _freeze_meta(meta: Mapping[str, float]) -> Mapping[str, float]:
    return MappingProxyType({str(k): float(v) for k, v in meta.items()})


def _unit(v: Point) -> Point:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        return Point(0.0, 0.0)
    return Point(v.x / length, v.y / length)


def _seg_length(seg: Segment) -> float:
    if isinstance(seg, LineSegment):
        return math.hypot(seg.p1.x - seg.p0.x, seg.p1.y - seg.p0.y)
    return math.hypot(seg.p3.x - seg.p0.x, seg.p3.y - seg.p0.y)


def _point_along(seg: Segment, *, from_start: bool, distance: float) -> Point:
    length = _seg_length(seg)
    if length < 1e-12:
        return segment_start(seg) if from_start else segment_end(seg)
    t = max(0.0, min(1.0, distance / length))
    if isinstance(seg, LineSegment):
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

    u = t if from_start else 1.0 - t
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

    u = max(0.0, min(1.0, 1.0 - distance / length))
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

    u = max(0.0, min(1.0, distance / length))
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))


@dataclass(frozen=True, slots=True)
class CornerFill:
    trim_in: float
    trim_out: float
    path: Fragment


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze_meta(self.meta))


@dataclass(frozen=True, slots=True)
class EndFill:
    trim_a: float
    trim_b: float
    path: Fragment


class EndFiller(Protocol):
    def __call__(self, site: EndSite, system: System) -> EndFill: ...


def _match_filler(
    tag: str,
    patterns: Mapping[str, T],
    named: Mapping[str, object],
    fill_name: str | None,
) -> T | None:
    if fill_name is not None:
        if fill_name not in named:
            raise SlotFillError(f"Slot.fill={fill_name!r} not in named fillers")
        return named[fill_name]  # type: ignore[return-value]
    for pattern, filler in patterns.items():
        if fnmatch.fnmatchcase(tag, pattern):
            return filler
    return None


def _assert_path_endpoints(path: Fragment, start: Point, end: Point) -> None:
    if not points_close(path.start, start, _POINT_TOL):
        raise SlotFillError(
            f"fill path start {path.start.as_tuple()} != trim point {start.as_tuple()}"
        )
    if not points_close(path.end, end, _POINT_TOL):
        raise SlotFillError(
            f"fill path end {path.end.as_tuple()} != trim point {end.as_tuple()}"
        )


def _is_degenerate_line(seg: Segment) -> bool:
    """True for near-zero line segments (ignored by continuity checks)."""
    return isinstance(seg, LineSegment) and _seg_length(seg) < 1e-9


def _is_noop_corner_fill(fill: CornerFill) -> bool:
    """§9.5: plain ≡ unmatched — zero trim + only degenerate path segs is a no-op.

    Explicit ``corners.plain`` (and zero-radius rounded fallbacks) must not insert
    zero-length segments; geometry and the corner slot stay as in the unmatched case.
    """
    if fill.trim_in > 1e-12 or fill.trim_out > 1e-12:
        return False
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

    Sharp corners left unmatched or filled with ``plain`` (geometry no-op) remain
    discontinuous by design (§9.3 / §9.5) and must stay exempt.
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
        if isinstance(prev, LineSegment) and isinstance(nxt, LineSegment):
            continue
        # Defensive: ignore accidental zero-length inserts next to a curve.
        if _is_degenerate_line(prev) or _is_degenerate_line(nxt):
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
            f"trim_in={fill.trim_in}/{site.in_len}, trim_out={fill.trim_out}/{site.out_len}"
        )
    trim_start = _point_along(segs[prev_i], from_start=False, distance=fill.trim_in)
    trim_end = _point_along(segs[next_i], from_start=True, distance=fill.trim_out)
    _assert_path_endpoints(fill.path, trim_start, trim_end)

    new_prev = _trim_segment_end(segs[prev_i], fill.trim_in)
    new_next = _trim_segment_start(segs[next_i], fill.trim_out)

    out: list[Segment] = []
    i = (next_i + 1) % n
    while i != prev_i:
        out.append(segs[i])
        i = (i + 1) % n
    if new_prev is not None:
        out.append(new_prev)
    out.extend(fill.path.segments)
    if new_next is not None:
        out.append(new_next)
    if not out:
        raise SlotFillError(f"corner fill for {site.tag!r} removed entire contour")
    return out


def _apply_end(segs: list[Segment], node_index: int, fill: EndFill, site: EndSite) -> list[Segment]:
    n = len(segs)
    idx = node_index % n
    cut = segs[idx]
    cut_len = _seg_length(cut)
    if fill.trim_a < 0 or fill.trim_b < 0:
        raise SlotFillError(f"negative end trim for {site.tag!r}")
    if fill.trim_a + fill.trim_b > cut_len + 1e-9:
        raise SlotFillError(
            f"end trim exceeds cut length for {site.tag!r}: "
            f"{fill.trim_a}+{fill.trim_b} > {cut_len}"
        )
    pa = _point_along(cut, from_start=True, distance=fill.trim_a)
    pb = _point_along(cut, from_start=False, distance=fill.trim_b)
    _assert_path_endpoints(fill.path, pa, pb)
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
                        f"could not relocate corner {slot.tag!r} after prior fill"
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
            fill = corner_filler(site, system)
            if not isinstance(fill, CornerFill):
                raise SlotFillError(
                    f"corner filler for {slot.tag!r} returned {type(fill)}"
                )
            # plain / zero-radius: leave geometry + corner slot (§9.5 ≡ unmatched).
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
            )
            fill_e = end_filler(site_e, system)
            if not isinstance(fill_e, EndFill):
                raise SlotFillError(
                    f"end filler for {slot.tag!r} returned {type(fill_e)}"
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
    )
