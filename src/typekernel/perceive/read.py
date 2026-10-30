"""Lightweight glyph identity reader (S2) — topology + coarse bitmap cues.

No heavy ML: score knowledge priors against measured counters/islands/extent
and a tiny occupancy grid. Confuse-pair mismatches become hard warns.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from typekernel.geo.outline import Outline
from typekernel.knowledge import TopologyPrior, confuse_partners, prior_for
from typekernel.knowledge.priors import LATIN_BASIC
from typekernel.perceive.topology import measure_topology
from typekernel.project.session import ProjectSession
from typekernel.system import System

__all__ = [
    "ReadHit",
    "ReadReport",
    "ReadWarning",
    "format_read_report",
    "read_glyph",
    "read_outline",
    "read_text",
]


@dataclass(frozen=True, slots=True)
class ReadHit:
    """One candidate identity."""

    codepoint: int
    name: str
    score: float
    """Lower is better (distance to prior + features)."""


@dataclass(frozen=True, slots=True)
class ReadWarning:
    level: str  # "warn" | "info"
    glyph: str
    intended: str | None
    message: str
    hint: str = ""


@dataclass(frozen=True, slots=True)
class ReadReport:
    glyph: str
    intended_cp: int | None
    top: tuple[ReadHit, ...]
    warnings: tuple[ReadWarning, ...]
    features: tuple[float, ...]


def _bbox(outline: Outline) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for contour in outline.contours:
        for seg in contour.segments:
            for pt in seg.points:
                xs.append(float(pt.x))
                ys.append(float(pt.y))
    if not xs:
        return 0.0, 0.0, 0.0, 0.0
    return min(xs), min(ys), max(xs), max(ys)


def _grid_features(outline: Outline, *, grid: int = 4) -> tuple[float, ...]:
    """Occupancy fractions on a ``grid``×``grid`` bbox lattice (0..1)."""
    x0, y0, x1, y1 = _bbox(outline)
    w = max(x1 - x0, 1e-6)
    h = max(y1 - y0, 1e-6)
    cells = [0] * (grid * grid)
    samples = 0
    for contour in outline.contours:
        for seg in contour.segments:
            pts = list(seg.points)
            # Sample chord midpoints + ends.
            for i in range(len(pts) - 1):
                for t in (0.0, 0.5, 1.0):
                    x = pts[i].x * (1 - t) + pts[i + 1].x * t
                    y = pts[i].y * (1 - t) + pts[i + 1].y * t
                    cx = min(grid - 1, max(0, int((x - x0) / w * grid)))
                    cy = min(grid - 1, max(0, int((y - y0) / h * grid)))
                    cells[cy * grid + cx] += 1
                    samples += 1
    if samples <= 0:
        return tuple(0.0 for _ in cells)
    return tuple(c / samples for c in cells)


def _extent_flags(outline: Outline, system: System) -> tuple[bool, bool, bool]:
    """(ascender, descender, has_dot) heuristics from bbox vs zones.

    Overshoot on x-height / baseline must **not** flip these — only clear
    past-cap / past-descender extents count.
    """
    _x0, y0, _x1, y1 = _bbox(outline)
    xh = float(system.zones.x)
    base = float(system.zones.base)
    cap = float(system.zones.cap)
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    ov = float(getattr(system.overshoot, "round", 12.0) or 12.0)
    # Midway between x-height and cap (or asc zone) — past ordinary overshoot.
    asc_gate = xh + max(ov * 2.0, (cap - xh) * 0.45, (asc - xh) * 0.35 if asc > xh else 0.0)
    ascender = y1 > asc_gate
    # Below baseline by more than round overshoot, or into descender band.
    desc_gate = base - max(ov * 1.5, abs(desc - base) * 0.35 if desc < base else ov * 1.5)
    descender = y0 < desc_gate
    has_dot = False
    return ascender, descender, has_dot


def _feature_vector(
    outline: Outline,
    system: System,
    *,
    stem: float,
) -> tuple[float, ...]:
    topo = measure_topology(outline, stem=stem)
    asc, desc, _dot = _extent_flags(outline, system)
    # Refine has_dot from island count + tall bbox.
    has_dot = bool(topo.islands >= 2 and asc)
    grid = _grid_features(outline)
    x0, y0, x1, y1 = _bbox(outline)
    aspect = (y1 - y0) / max(x1 - x0, 1e-6)
    return (
        float(topo.counters),
        float(topo.islands),
        1.0 if asc else 0.0,
        1.0 if desc else 0.0,
        1.0 if has_dot else 0.0,
        float(aspect),
        *grid,
    )


def _prior_vector(prior: TopologyPrior, *, aspect: float = 1.0) -> tuple[float, ...]:
    # Grid left as zeros — topology/extent dominate identity.
    # Aspect copied from measurement so the placeholder does not distort ties.
    return (
        float(prior.counters),
        float(prior.islands),
        1.0 if prior.ascender else 0.0,
        1.0 if prior.descender else 0.0,
        1.0 if prior.has_dot else 0.0,
        float(aspect),
        *(0.0 for _ in range(16)),
    )


def _distance(a: Sequence[float], b: Sequence[float], *, weights: Sequence[float]) -> float:
    n = min(len(a), len(b), len(weights))
    acc = 0.0
    for i in range(n):
        d = (float(a[i]) - float(b[i])) * float(weights[i])
        acc += d * d
    return math.sqrt(acc)


_WEIGHTS: tuple[float, ...] = (
    3.0,  # counters — hard identity
    2.0,  # islands
    2.0,  # asc
    2.0,  # desc
    1.5,  # dot
    0.0,  # aspect (copied from measurement; reserved for future)
    *(0.12 for _ in range(16)),
)


def read_outline(
    outline: Outline,
    system: System,
    *,
    stem: float | None = None,
    candidates: Mapping[int, TopologyPrior] | None = None,
    top_k: int = 3,
) -> tuple[tuple[ReadHit, ...], tuple[float, ...]]:
    """Score ``outline`` against knowledge priors; return top-k + features."""
    st = float(stem if stem is not None else next(iter(system.stem.values()), 80.0))
    feats = _feature_vector(outline, system, stem=st)
    pool: Mapping[int, TopologyPrior] = candidates if candidates is not None else LATIN_BASIC
    hits: list[ReadHit] = []
    for cp, prior in pool.items():
        score = _distance(feats, _prior_vector(prior, aspect=feats[5]), weights=_WEIGHTS)
        hits.append(ReadHit(codepoint=int(cp), name=prior.name, score=score))
    hits.sort(
        key=lambda h: (
            h.score,
            0 if len(h.name) == 1 and h.name.islower() else 1,
            h.codepoint,
        )
    )
    return tuple(hits[: max(1, int(top_k))]), feats


def read_glyph(
    session: ProjectSession,
    name: str,
    *,
    intended_cp: int | None = None,
    master: str | None = None,
    top_k: int = 3,
) -> ReadReport:
    """Read one project glyph; optionally compare to an intended codepoint."""
    draft = session.evaluate(name, master=master)
    system = session.project.system
    if master is not None:
        by = {m.name: m for m in session.project.masters}
        if master in by:
            system = by[master].system
    stem = float(next(iter(system.stem.values()), 80.0))
    top, feats = read_outline(draft.drawing.outline(), system, stem=stem, top_k=top_k)
    warnings: list[ReadWarning] = []
    if intended_cp is not None:
        intended = prior_for(intended_cp)
        intended_name = intended.name if intended else f"U+{intended_cp:04X}"
        best = top[0] if top else None
        # Always score the intended prior (may sit outside top-k).
        if intended is not None:
            intended_score = _distance(
                feats, _prior_vector(intended, aspect=feats[5]), weights=_WEIGHTS
            )
        else:
            intended_score = float("inf")
        margin = 0.08  # grid noise band — ties inside this are not hard misreads
        if best is not None and best.codepoint != int(intended_cp):
            # Hard warn only when top clearly beats intended.
            clear_misread = best.score + margin < intended_score
            if clear_misread:
                warnings.append(
                    ReadWarning(
                        level="warn",
                        glyph=name,
                        intended=intended_name,
                        message=(
                            f"intended {intended_name} but top read is {best.name} "
                            f"(score={best.score:.3f})"
                        ),
                        hint="check counters/islands vs knowledge prior; see confuse pairs",
                    )
                )
            else:
                warnings.append(
                    ReadWarning(
                        level="info",
                        glyph=name,
                        intended=intended_name,
                        message=(
                            f"near-tie: top={best.name}:{best.score:.3f} vs "
                            f"intended {intended_name}:{intended_score:.3f}"
                        ),
                    )
                )
        # Confuse-pair hard warn when measured topology matches partner better.
        if intended is not None and best is not None:
            for partner_cp in confuse_partners(intended_cp):
                partner = prior_for(partner_cp)
                if partner is None:
                    continue
                meas_c = feats[0]
                if abs(meas_c - partner.counters) + 0.1 < abs(meas_c - intended.counters):
                    warnings.append(
                        ReadWarning(
                            level="warn",
                            glyph=name,
                            intended=intended.name,
                            message=(
                                f"confuse-pair: looks like {partner.name} "
                                f"(counters={meas_c:.0f}; {intended.name} expects "
                                f"{intended.counters})"
                            ),
                            hint="cold-trial failure mode — reshape or retune topology",
                        )
                    )
                    break
    return ReadReport(
        glyph=name,
        intended_cp=intended_cp,
        top=top,
        warnings=tuple(warnings),
        features=feats,
    )


def read_text(
    session: ProjectSession,
    text: str,
    *,
    master: str | None = None,
    top_k: int = 3,
) -> list[ReadReport]:
    """Read each non-space character in ``text`` against matching project glyphs."""
    from typekernel.font.glyph import glyph_name_for_char

    reports: list[ReadReport] = []
    specs = session.specs()
    for ch in text:
        if ch.isspace():
            continue
        cp = ord(ch)
        name = glyph_name_for_char(ch)
        if name not in specs:
            # Still emit an empty-top report so callers see coverage gaps.
            reports.append(
                ReadReport(
                    glyph=name,
                    intended_cp=cp,
                    top=(),
                    warnings=(
                        ReadWarning(
                            level="info",
                            glyph=name,
                            intended=ch,
                            message=f"glyph {name!r} not in project",
                        ),
                    ),
                    features=(),
                )
            )
            continue
        reports.append(
            read_glyph(session, name, intended_cp=cp, master=master, top_k=top_k)
        )
    return reports


def format_read_report(reports: Sequence[ReadReport], *, as_json: bool = False) -> str:
    """Human or JSON formatter for ``tk read``."""
    if as_json:
        import json

        payload = []
        for r in reports:
            payload.append(
                {
                    "glyph": r.glyph,
                    "intended_cp": r.intended_cp,
                    "top": [
                        {"cp": h.codepoint, "name": h.name, "score": round(h.score, 4)}
                        for h in r.top
                    ],
                    "warnings": [
                        {
                            "level": w.level,
                            "message": w.message,
                            "intended": w.intended,
                        }
                        for w in r.warnings
                    ],
                }
            )
        return json.dumps(payload, indent=2) + "\n"
    lines: list[str] = []
    for r in reports:
        top_s = ", ".join(f"{h.name}:{h.score:.2f}" for h in r.top) or "(none)"
        lines.append(f"{r.glyph}: top=[{top_s}]")
        for w in r.warnings:
            lines.append(f"  {w.level.upper()}: {w.message}")
    return "\n".join(lines) + ("\n" if lines else "")
