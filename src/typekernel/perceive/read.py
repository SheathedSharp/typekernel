"""Lightweight glyph identity reader (S2/C3) — topology + continuous shape.

No heavy ML: score knowledge priors against measured counters/islands/extent
plus aspect / top-mass / right-mass / diagonal-mass / mid-band. Confuse-pair
mismatches become hard warns. Grid occupancy remains a soft tie-break.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from typekernel.geo.outline import Outline
from typekernel.knowledge import TopologyPrior, confuse_partners, prior_for
from typekernel.knowledge.priors import LATIN_BASIC, LATIN_EXT
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
    """(ascender, descender, has_dot) heuristics from bbox vs zones."""
    _x0, y0, _x1, y1 = _bbox(outline)
    xh = float(system.zones.x)
    base = float(system.zones.base)
    cap = float(system.zones.cap)
    asc = float(system.zones.asc)
    desc = float(system.zones.desc)
    ov = float(getattr(system.overshoot, "round", 12.0) or 12.0)
    asc_gate = xh + max(ov * 2.0, (cap - xh) * 0.45, (asc - xh) * 0.35 if asc > xh else 0.0)
    ascender = y1 > asc_gate
    desc_gate = base - max(ov * 1.5, abs(desc - base) * 0.35 if desc < base else ov * 1.5)
    descender = y0 < desc_gate
    return ascender, descender, False


def _mass_cues(
    grid: Sequence[float], *, grid_n: int = 4
) -> tuple[float, float, float, float, float, float]:
    """Derive shape masses in ``[0, 1]``.

    Returns
    ``(top_mass, right_mass, diag_mass, mid_band, edge_mass, mid_right)``.
    """
    if len(grid) != grid_n * grid_n:
        return (0.5, 0.5, 0.0, 0.0, 0.5, 0.0)
    cols = [sum(grid[r * grid_n + c] for r in range(grid_n)) for c in range(grid_n)]
    rows = [sum(grid[r * grid_n + c] for c in range(grid_n)) for r in range(grid_n)]
    left = sum(cols[: grid_n // 2]) + 1e-6
    right = sum(cols[grid_n // 2 :]) + 1e-6
    bot = sum(rows[: grid_n // 2]) + 1e-6
    top = sum(rows[grid_n // 2 :]) + 1e-6
    top_mass = top / (top + bot)
    right_mass = right / (left + right)
    main = sum(grid[i * grid_n + i] for i in range(grid_n))
    anti = sum(grid[i * grid_n + (grid_n - 1 - i)] for i in range(grid_n))
    diag_mass = (main + anti) / (sum(grid) + 1e-6)
    mid = grid_n // 2
    mid_row = rows[mid] if mid < len(rows) else 0.0
    mid_band = mid_row / (sum(rows) + 1e-6)
    total = sum(grid) + 1e-6
    # Outer columns: dual stems (N/H) vs open/bowl forms.
    edge_mass = (cols[0] + cols[grid_n - 1]) / total
    # Mid-band on the right half: spur / open-right bar (G vs C).
    mid_rows = range(max(0, mid - 1), min(grid_n, mid + 1))
    mid_right = sum(
        grid[r * grid_n + c] for r in mid_rows for c in range(grid_n // 2, grid_n)
    )
    return (top_mass, right_mass, diag_mass, mid_band, edge_mass, mid_right)


def _feature_vector(
    outline: Outline,
    system: System,
    *,
    stem: float,
) -> tuple[float, ...]:
    topo = measure_topology(outline, stem=stem)
    asc, desc, _dot = _extent_flags(outline, system)
    has_dot = bool(topo.islands >= 2 and asc)
    grid = _grid_features(outline)
    x0, y0, x1, y1 = _bbox(outline)
    aspect = (y1 - y0) / max(x1 - x0, 1e-6)
    masses = _mass_cues(grid)
    return (
        float(topo.counters),
        float(topo.islands),
        1.0 if asc else 0.0,
        1.0 if desc else 0.0,
        1.0 if has_dot else 0.0,
        float(aspect),
        *masses,
        *grid,
    )


# Feature layout indices
_I_COUNTERS, _I_ISLANDS, _I_ASC, _I_DESC, _I_DOT = 0, 1, 2, 3, 4
_I_ASPECT = 5
_I_TOP, _I_RIGHT, _I_DIAG, _I_MID = 6, 7, 8, 9
_I_EDGE, _I_MID_RIGHT = 10, 11
_I_GRID0 = 12


def _distance_to_prior(feats: Sequence[float], prior: TopologyPrior) -> float:
    """Weighted distance; optional mass targets skipped when prior field is None."""
    acc = 0.0

    def add(d: float, w: float) -> None:
        nonlocal acc
        acc += (d * w) * (d * w)

    # Prefer primary counters; allow counters_alt (storey variants) without penalty.
    meas_c = float(feats[_I_COUNTERS])
    c_opts = (float(prior.counters), *(float(c) for c in prior.counters_alt))
    add(min(abs(meas_c - c) for c in c_opts), 3.0)
    add(float(feats[_I_ISLANDS]) - float(prior.islands), 2.0)
    add(float(feats[_I_ASC]) - (1.0 if prior.ascender else 0.0), 2.0)
    add(float(feats[_I_DESC]) - (1.0 if prior.descender else 0.0), 2.0)
    add(float(feats[_I_DOT]) - (1.0 if prior.has_dot else 0.0), 1.5)
    # Log-aspect: scale-invariant width/height discrimination (m vs n vs i).
    meas_a = max(float(feats[_I_ASPECT]), 1e-3)
    prior_a = max(float(prior.aspect), 1e-3)
    add(math.log(meas_a / prior_a), 1.4)
    if prior.top_mass is not None:
        add(float(feats[_I_TOP]) - float(prior.top_mass), 2.2)
    if prior.right_mass is not None:
        add(float(feats[_I_RIGHT]) - float(prior.right_mass), 1.4)
    if prior.diag_mass is not None:
        add(float(feats[_I_DIAG]) - float(prior.diag_mass), 2.0)
    if prior.mid_band is not None:
        add(float(feats[_I_MID]) - float(prior.mid_band), 1.6)
    if prior.edge_mass is not None:
        add(float(feats[_I_EDGE]) - float(prior.edge_mass), 2.0)
    if prior.mid_right is not None:
        add(float(feats[_I_MID_RIGHT]) - float(prior.mid_right), 2.4)
    # Soft grid residual (measurement-only; no prior grid).
    for i in range(16):
        add(float(feats[_I_GRID0 + i]), 0.05)
    return math.sqrt(acc)


def _latin_rank_pool(*, case: str | None = None) -> dict[int, TopologyPrior]:
    """Basic Latin + Ext digraph priors; optional lower/upper case filter."""
    out: dict[int, TopologyPrior] = {}
    for cp, pr in LATIN_BASIC.items():
        if 0x30 <= cp <= 0x39:
            out[cp] = pr
            continue
        if not ((0x41 <= cp <= 0x5A) or (0x61 <= cp <= 0x7A)):
            continue
        if case == "lower" and not (0x61 <= cp <= 0x7A):
            continue
        if case == "upper" and not (0x41 <= cp <= 0x5A):
            continue
        out[cp] = pr
    for cp, pr in LATIN_EXT.items():
        ch = chr(cp)
        if case == "lower" and not ch.islower():
            continue
        if case == "upper" and not ch.isupper():
            continue
        out[cp] = pr
    return out


def read_outline(
    outline: Outline,
    system: System,
    *,
    stem: float | None = None,
    candidates: Mapping[int, TopologyPrior] | None = None,
    top_k: int = 3,
    case: str | None = None,
) -> tuple[tuple[ReadHit, ...], tuple[float, ...]]:
    """Score ``outline`` against knowledge priors; return top-k + features.

    ``case`` is ``"lower"`` / ``"upper"`` to keep ranking within the intended
    alphabet case (digits always included). Non-Latin lookalikes stay available
    via ``prior_for`` / confuse-pair checks, not default top-k.
    """
    st = float(stem if stem is not None else next(iter(system.stem.values()), 80.0))
    feats = _feature_vector(outline, system, stem=st)
    pool: Mapping[int, TopologyPrior]
    if candidates is not None:
        pool = candidates
    else:
        pool = _latin_rank_pool(case=case)
    hits: list[ReadHit] = []
    for cp, prior in pool.items():
        score = _distance_to_prior(feats, prior)
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
    case = None
    if intended_cp is not None:
        ch = chr(int(intended_cp))
        if ch.islower():
            case = "lower"
        elif ch.isupper():
            case = "upper"
    top, feats = read_outline(
        draft.drawing.outline(), system, stem=stem, top_k=top_k, case=case
    )
    warnings: list[ReadWarning] = []
    if intended_cp is not None:
        intended = prior_for(intended_cp)
        intended_name = intended.name if intended else f"U+{intended_cp:04X}"
        best = top[0] if top else None
        if intended is not None:
            intended_score = _distance_to_prior(feats, intended)
        else:
            intended_score = float("inf")
        # Hard-warn only when intended topology mismatches the measurement
        # (or confuse-pair below). Shape-only rank fights stay info so styles
        # that share topology but not mass centroids (script, italic, …)
        # do not flood false identity fails.
        margin = 0.12
        topo_ok = False
        if intended is not None:
            c_opts = (float(intended.counters), *(float(c) for c in intended.counters_alt))
            meas_c = float(feats[_I_COUNTERS])
            counters_ok = min(abs(meas_c - c) for c in c_opts) < 0.15
            topo_ok = (
                counters_ok
                and abs(float(feats[_I_ISLANDS]) - float(intended.islands)) < 0.15
                and abs(float(feats[_I_ASC]) - (1.0 if intended.ascender else 0.0)) < 0.15
                and abs(float(feats[_I_DESC]) - (1.0 if intended.descender else 0.0)) < 0.15
            )
        if best is not None and best.codepoint != int(intended_cp):
            clear_misread = best.score + margin < intended_score
            if clear_misread and not topo_ok:
                warnings.append(
                    ReadWarning(
                        level="warn",
                        glyph=name,
                        intended=intended_name,
                        message=(
                            f"intended {intended_name} but top read is {best.name} "
                            f"(score={best.score:.3f})"
                        ),
                        hint="check counters/islands/shape cues vs knowledge prior",
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
        if intended is not None and best is not None:
            for partner_cp in confuse_partners(intended_cp):
                partner = prior_for(partner_cp)
                if partner is None:
                    continue
                meas_c = float(feats[_I_COUNTERS])
                intended_c_dist = min(
                    abs(meas_c - float(intended.counters)),
                    *(abs(meas_c - float(c)) for c in intended.counters_alt),
                ) if intended.counters_alt else abs(meas_c - float(intended.counters))
                if abs(meas_c - float(partner.counters)) + 0.1 < intended_c_dist:
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
