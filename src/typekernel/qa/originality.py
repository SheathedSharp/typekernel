"""Voice originality metrics (TK-307): topology + normalized shape distance."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from typekernel.geo.contour import Contour
from typekernel.geo.rounding import DEFAULT_NDIGITS, quantize
from typekernel.geo.segment import LineSegment
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.family import Controls
from typekernel.qa.family_gate import collect_family_gate_failures
from typekernel.qa.lint import lint_controls

L3_VOICE_DISTANCE_THRESHOLD = 0.35
# L3 must diverge in letter topology, not only normalized shape (TK-307 anti-cheat).
L3_MIN_TOPOLOGY_FRACTION = 0.05

BUILTIN_PRESET_FACTORIES: dict[str, Callable[[], DesignContext]] = {
    "code_clear": DesignContext.code_clear,
    "display": DesignContext.display,
    "geometric_sans": DesignContext.geometric_sans,
    "humanist_sans": DesignContext.humanist_sans,
    "mono": DesignContext.mono,
    "open_print": DesignContext.open_print,
    "paper_ink": DesignContext.paper_ink,
}

__all__ = [
    "BUILTIN_PRESET_FACTORIES",
    "L3_MIN_TOPOLOGY_FRACTION",
    "L3_VOICE_DISTANCE_THRESHOLD",
    "OriginalityReport",
    "TopologySignature",
    "nearest_voice_distance",
    "normalized_shape_signature",
    "originality_report",
    "topology_fraction_vs_nearest_presets",
    "topology_signature",
    "voice_distance",
]


@dataclass(frozen=True, slots=True)
class TopologySignature:
    """Per-contour segment-type codes plus hole count on the composed glyph."""

    contour_codes: tuple[str, ...]
    hole_count: int


@dataclass(frozen=True, slots=True)
class VoiceDistance:
    """Divergence between two control sheets on a shared charset."""

    topology_fraction: float
    shape_fraction: float
    combined: float

    def __float__(self) -> float:
        return self.combined


@dataclass(frozen=True, slots=True)
class OriginalityReport:
    """Distance from ``controls`` to the nearest built-in preset default."""

    nearest_preset: str
    nearest_distance: float
    by_preset: Mapping[str, VoiceDistance]


def _contour_codes(contour: Contour) -> str:
    parts: list[str] = []
    for segment in contour.segments:
        parts.append("L" if isinstance(segment, LineSegment) else "C")
    closed = "1" if contour.closed else "0"
    return f"{closed}:" + "".join(parts)


def topology_signature(glyph: ComposedGlyph) -> TopologySignature:
    """Segment-type sequence for every solid/hole contour and the hole count."""
    codes: list[str] = []
    for outline in (*glyph.solids, *glyph.holes):
        for contour in outline.contours:
            codes.append(_contour_codes(contour))
    return TopologySignature(tuple(codes), len(glyph.holes))


def normalized_shape_signature(glyph: ComposedGlyph, *, ndigits: int = DEFAULT_NDIGITS) -> str:
    """Hash of coordinates scaled by ``x_height`` (shape, not topology)."""
    xh = glyph.context.x_height
    if xh <= 0.0:
        raise ValueError("x_height must be positive for shape signatures")
    lines: list[str] = []
    for outline in (*glyph.solids, *glyph.holes):
        for contour in outline.contours:
            for segment in contour.segments:
                for point in segment.points:
                    x = quantize(point.x / xh, ndigits)
                    y = quantize(point.y / xh, ndigits)
                    lines.append(f"{x:.{ndigits}f},{y:.{ndigits}f}")
    payload = "\n".join(lines) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _shared_charset(a: Controls, b: Controls, charset: str | None) -> str:
    if charset is not None:
        return charset
    if a.supported == b.supported:
        return a.supported
    shared = "".join(ch for ch in a.supported if ch in b.supported)
    return shared or a.supported


def voice_distance(
    a: Controls,
    b: Controls,
    charset: str | None = None,
) -> VoiceDistance:
    """Share of glyphs that differ in topology or normalized shape."""
    wanted = _shared_charset(a, b, charset)
    if not wanted:
        return VoiceDistance(0.0, 0.0, 0.0)
    ga = a.build_all(wanted)
    gb = b.build_all(wanted)
    topo_diffs = 0
    shape_diffs = 0
    for ch in wanted:
        g1, g2 = ga[ch], gb[ch]
        t1, t2 = topology_signature(g1), topology_signature(g2)
        if t1 != t2:
            topo_diffs += 1
            continue
        if normalized_shape_signature(g1) != normalized_shape_signature(g2):
            shape_diffs += 1
    n = len(wanted)
    topo_f = topo_diffs / n
    shape_f = shape_diffs / n
    return VoiceDistance(topo_f, shape_f, (topo_diffs + shape_diffs) / n)


def originality_report(controls: Controls, charset: str | None = None) -> OriginalityReport:
    """Compare ``controls`` against every built-in preset; return the nearest."""
    by_preset: dict[str, VoiceDistance] = {}
    nearest_name = ""
    nearest = float("inf")
    for name, factory in BUILTIN_PRESET_FACTORIES.items():
        ref = Controls.from_context(factory())
        dist = voice_distance(controls, ref, charset)
        by_preset[name] = dist
        if dist.combined < nearest:
            nearest = dist.combined
            nearest_name = name
    return OriginalityReport(nearest_name, nearest, by_preset)


def topology_fraction_vs_nearest_presets(
    controls: Controls,
    charset: str | None = None,
) -> float:
    """Topology divergence from the closest built-in preset (or max if tied)."""
    report = originality_report(controls, charset)
    if not report.by_preset:
        return 0.0
    if report.nearest_preset:
        return report.by_preset[report.nearest_preset].topology_fraction
    return max(vd.topology_fraction for vd in report.by_preset.values())


def nearest_voice_distance(controls: Controls, charset: str | None = None) -> float:
    """Combined distance to the closest preset (used by agent trials / L3)."""
    return originality_report(controls, charset).nearest_distance


def l3_voice_criteria_met(controls: Controls) -> bool:
    """L3 voice distance plus lint/identity gate (human review still required)."""
    if nearest_voice_distance(controls) < L3_VOICE_DISTANCE_THRESHOLD:
        return False
    if topology_fraction_vs_nearest_presets(controls) < L3_MIN_TOPOLOGY_FRACTION:
        return False
    if collect_family_gate_failures(controls):
        return False
    return len(lint_controls(controls).errors) == 0
