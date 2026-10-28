"""Stem / optical thickness check plugin."""

from __future__ import annotations

import math
from collections.abc import Sequence

from typekernel.geo.outline import bounds
from typekernel.optics.stem import (
    list_vertical_stems,
    measure_oriented_stem,
    vertical_equiv_from_diagonal,
)
from typekernel.plugins.checks.protocol import CheckContext, Finding

__all__ = ["check"]


def _stem_from_nodes(drawing, prefix: str) -> float | None:
    try:
        a = drawing.point(f"{prefix}.foot.o")
        b = drawing.point(f"{prefix}.foot.i")
    except KeyError:
        return None
    return abs(float(b.x) - float(a.x))


def _oriented_from_nodes(drawing, prefix: str) -> float | None:
    try:
        a = drawing.point(f"{prefix}.foot.o")
        b = drawing.point(f"{prefix}.foot.i")
    except KeyError:
        return None
    return math.hypot(float(b.x) - float(a.x), float(b.y) - float(a.y))


def check(ctx: CheckContext, *, tol_ratio: float = 0.08) -> None:
    """Compare tagged / optical stem widths to System targets."""
    name = ctx.name
    drawing = ctx.raw
    system = ctx.system
    kinds: Sequence[str] = ctx.stem_kinds.get(name, ())
    # When caller put kinds on context via audit, stem_kinds is the full map;
    # kinds_for already resolved — audit passes per-glyph via a side channel.
    # Prefer ctx attribute set by audit: we store resolved kinds under the map
    # key "" or use stem_kinds[name]. Audit will set stem_kinds as {name: kinds}
    # for the active glyph only OR full map. Use name key.
    if name in ctx.stem_kinds:
        kinds = tuple(ctx.stem_kinds[name])
    expected_lc = float(system.stem.get("lc", 0.0))
    expected_uc = float(system.stem.get("uc", expected_lc))
    is_uc = len(name) == 1 and name.isupper()
    stem_target = expected_uc if is_uc else expected_lc
    measured: list[tuple[str, float, float]] = []
    for prefix, expected in (
        ("stem.l", stem_target),
        ("stem.r", stem_target),
        ("stem", stem_target),
        ("stem.L", expected_uc),
        ("stem.R", expected_uc),
        ("stem.diag", stem_target),
        ("stem.diag.a", stem_target),
        ("stem.diag.b", stem_target),
    ):
        w = _oriented_from_nodes(drawing, prefix)
        if w is None:
            w = _stem_from_nodes(drawing, prefix)
        if w is not None:
            measured.append((prefix, w, expected))

    if not measured and (len(name) == 1 or name in {"zero", "one", "four", "seven"}):
        outline = drawing.outline()
        zone = float(system.zones.cap if is_uc else system.zones.x)
        if "vertical" in kinds:
            # Italic: constructed "verticals" lean — probe along System.stem_direction.
            if system.is_italic:
                try:
                    min_x, min_y, max_x, max_y = bounds(outline)
                except ValueError:
                    min_x = min_y = max_x = max_y = 0.0
                origin = ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5)
                deg = float(system.stem_direction_deg())
                try:
                    w = measure_oriented_stem(outline, origin, deg)
                except Exception:
                    w = None
                if w is not None and w > 0:
                    if abs(w - stem_target) / stem_target <= 0.25:
                        measured.append(("optical.slanted_vertical", w, stem_target))
            best: list = []
            best_score = float("inf")
            agreeing_bands = 0
            for frac in (0.32, 0.5, 0.68):
                try:
                    spans = list_vertical_stems(outline, y=zone * frac)
                except Exception:
                    continue
                near = []
                for span in spans:
                    if span.width <= 0:
                        continue
                    if abs(span.width - stem_target) / stem_target > 0.25:
                        continue
                    near.append(span)
                if not near:
                    continue
                agreeing_bands += 1
                score = sum(abs(s.width - stem_target) for s in near) / len(near)
                if score < best_score:
                    best_score = score
                    best = near
            if agreeing_bands >= 2:
                for span in best:
                    measured.append(("optical.vertical", span.width, stem_target))
        if "diagonal" in kinds:
            try:
                min_x, min_y, max_x, max_y = bounds(outline)
            except ValueError:
                min_x = min_y = max_x = max_y = 0.0
            origin = ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5)
            for deg in (45.0, 135.0, -45.0):
                try:
                    w = measure_oriented_stem(outline, origin, deg)
                except Exception:
                    w = None
                if w is None or w <= 0:
                    continue
                angle_from_vertical = abs(90.0 - (abs(deg) % 180.0))
                if angle_from_vertical > 90.0:
                    angle_from_vertical = 180.0 - angle_from_vertical
                try:
                    equiv = vertical_equiv_from_diagonal(
                        w, angle_from_vertical_deg=angle_from_vertical
                    )
                except ValueError:
                    continue
                if abs(equiv - stem_target) / stem_target > 0.35:
                    continue
                measured.append((f"optical.diag@{deg:.0f}", equiv, stem_target))
                break

    for label, got, expected in measured:
        if expected <= 0:
            continue
        err = abs(got - expected) / expected
        if err > tol_ratio:
            ctx.findings.append(
                Finding(
                    "stem",
                    "warn",
                    name,
                    f"{label} width {got:.1f} vs System {expected:.1f} ({err:.0%})",
                )
            )
