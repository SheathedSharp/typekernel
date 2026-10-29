"""``tk explain`` — structured GlyphReport (target §6.3)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from typekernel.draw.drawing import Drawing, Measure
from typekernel.geo.outline import bounds
from typekernel.perceive.topology import Topology, measure_topology
from typekernel.project.session import ProjectSession
from typekernel.qa.outline_hash import outline_hash

__all__ = ["GlyphReport", "explain", "measure_value"]


@dataclass(frozen=True, slots=True)
class NodeRow:
    tag: str
    x: float
    y: float
    contour: int
    index: int
    smooth: bool = False


@dataclass(frozen=True, slots=True)
class MeasureRow:
    kind: str
    a: str
    b: str | None
    expected: float | None
    measured: float | None
    direction_deg: float | None = None


@dataclass(frozen=True, slots=True)
class GlyphReport:
    glyph: str
    master: str | None
    outline_hash: str
    bbox: tuple[float, float, float, float]
    advance: float
    lsb: float | None
    rsb: float | None
    nodes: tuple[NodeRow, ...]
    measures: tuple[MeasureRow, ...]
    counters: int
    islands: int
    slit_counters: int
    counter_areas: tuple[float, ...]
    island_areas: tuple[float, ...]
    ink_density: float
    note: str = ""
    traits: tuple[str, ...] = ()
    slots: tuple[dict[str, Any], ...] = ()
    zone_fit: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def measure_value(drawing: Drawing, measure: Measure) -> float | None:
    """Distance between tagged nodes (or None if a tag is missing)."""
    import math

    try:
        pa = drawing.point(measure.a)
    except KeyError:
        return None
    if measure.b is None:
        return None
    try:
        pb = drawing.point(measure.b)
    except KeyError:
        return None
    if measure.direction_deg is not None:
        rad = math.radians(measure.direction_deg)
        ux, uy = math.cos(rad), math.sin(rad)
        return abs((pb.x - pa.x) * ux + (pb.y - pa.y) * uy)
    return math.hypot(pb.x - pa.x, pb.y - pa.y)


def _nodes(drawing: Drawing) -> tuple[NodeRow, ...]:
    rows: list[NodeRow] = []
    for ci, (contour, cnodes) in enumerate(
        zip(drawing.contours, drawing.nodes, strict=True)
    ):
        for node in cnodes:
            from typekernel.draw.drawing import on_curve_at

            pt = on_curve_at(contour, node.index)
            smooth = bool(node.meta.get("smooth", 0.0)) if node.meta else False
            rows.append(
                NodeRow(
                    tag=node.tag,
                    x=pt.x,
                    y=pt.y,
                    contour=ci,
                    index=node.index,
                    smooth=smooth,
                )
            )
    return tuple(rows)


def _ink_density(topo: Topology, advance: float, zones_span: float) -> float:
    ink = sum(topo.island_areas) - sum(topo.counter_areas)
    denom = max(1.0, float(advance) * max(1.0, zones_span))
    return max(0.0, ink) / denom


def explain(
    session: ProjectSession,
    glyph: str,
    *,
    master: str | None = None,
) -> GlyphReport:
    """Build a :class:`GlyphReport` for ``glyph`` (no compile)."""
    draft = session.evaluate(glyph, master=master, slots=True)
    g = session.glyph(glyph, master=master)
    drawing = draft.drawing
    system = session.project.system
    if master is not None:
        by = {m.name: m for m in session.project.masters}
        if master in by:
            system = by[master].system
    stem = float(next(iter(system.stem.values()), 80.0))
    topo = measure_topology(g.outline, stem=stem)
    lsb: float | None
    rsb: float | None
    try:
        bx0, by0, bx1, by1 = bounds(g.outline)
        bbox = (bx0, by0, bx1, by1)
        lsb = float(bx0)
        rsb = float(g.advance) - float(bx1)
    except ValueError:
        bbox = (0.0, 0.0, 0.0, 0.0)
        lsb = None
        rsb = None
    measures = tuple(
        MeasureRow(
            kind=m.kind,
            a=m.a,
            b=m.b,
            expected=m.expected,
            measured=measure_value(drawing, m),
            direction_deg=m.direction_deg,
        )
        for m in drawing.measures
    )
    slots = tuple(
        {
            "kind": s.kind,
            "tag": s.tag,
            "contour": s.contour,
            "node": s.node,
            "fill": s.fill,
        }
        for s in drawing.slots
    )
    spec = session.specs().get(glyph)
    traits = spec.traits if spec is not None else ()
    zones = system.zones
    zone_fit = {
        "base": bbox[1],
        "x": bbox[3],
        "cap": zones.cap,
        "asc": zones.asc,
        "desc": zones.desc,
    }
    span = float(zones.asc - zones.desc)
    return GlyphReport(
        glyph=glyph,
        master=master,
        outline_hash=outline_hash(g.outline),
        bbox=bbox,
        advance=float(g.advance),
        lsb=lsb,
        rsb=rsb,
        nodes=_nodes(drawing),
        measures=measures,
        counters=topo.counters,
        islands=topo.islands,
        slit_counters=topo.slit_counters,
        counter_areas=topo.counter_areas,
        island_areas=topo.island_areas,
        ink_density=_ink_density(topo, float(g.advance), span),
        note=draft.note,
        traits=traits,
        slots=slots,
        zone_fit=zone_fit,
    )
