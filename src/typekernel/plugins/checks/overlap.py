"""Opt-in ink∩ink even-odd cavity check plugin.

Intentional overlap construction (stem + shoulder, no counters) is the
recommended VF pattern and must not flood warnings. This check only reports
when an ink∩ink cancel region sits next to a declared counter (字腔) — the
case where even-odd preview opens a notch into the cavity.
"""

from __future__ import annotations

import math

from typekernel.draw import Drawing
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.plugins.checks.protocol import CheckContext, Finding

__all__ = ["check"]


def check(ctx: CheckContext) -> None:
    """Report-only: ink∩ink cancels that adjoin a counter under even-odd."""
    _audit_overlap_cavity(ctx.name, ctx.final, ctx.system, ctx.findings)


def _stem_scale(system) -> float:
    stem = getattr(system, "stem", None) or {}
    try:
        return float(stem.get("lc", stem.get("uc", 70.0)))
    except Exception:
        return 70.0


def _box_gap(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    """Axis-aligned gap between boxes; 0 if they touch or overlap."""
    dx = max(0.0, max(a[0] - b[2], b[0] - a[2]))
    dy = max(0.0, max(a[1] - b[3], b[1] - a[3]))
    return math.hypot(dx, dy)


def _audit_overlap_cavity(
    name: str,
    drawing: Drawing,
    system,
    findings: list[Finding],
) -> None:
    ink_idxs = [i for i, role in enumerate(drawing.roles) if role == "ink"]
    counter_idxs = [i for i, role in enumerate(drawing.roles) if role == "counter"]
    if len(ink_idxs) < 2:
        return

    # Pure multi-ink overlap with no counters: intentional VF construction.
    # Even-odd notches stay inside solid ink; do not warn (avoids training
    # agents to ignore --overlap). Use proof --glyph under nonzero if unsure.
    if not counter_idxs:
        return

    boxes: list[tuple[int, tuple[float, float, float, float]]] = []
    for i in ink_idxs:
        contour = drawing.contours[i]
        if not contour.segments:
            continue
        try:
            from typekernel.geo.outline import Outline

            boxes.append((i, bounds(Outline((contour,)))))
        except ValueError:
            continue

    pairs: list[tuple[int, int]] = []
    for a in range(len(boxes)):
        ia, ba = boxes[a]
        for b in range(a + 1, len(boxes)):
            ib, bb = boxes[b]
            if ba[2] < bb[0] or bb[2] < ba[0] or ba[3] < bb[1] or bb[3] < ba[1]:
                continue
            pairs.append((ia, ib))
    if not pairs:
        return

    counter_boxes: list[tuple[int, tuple[float, float, float, float]]] = []
    for ic in counter_idxs:
        try:
            from typekernel.geo.outline import Outline

            counter_boxes.append((ic, bounds(Outline((drawing.contours[ic],)))))
        except ValueError:
            continue
    if not counter_boxes:
        return

    proximity = max(1.0, 0.35 * _stem_scale(system))

    try:
        from typekernel.geo.boolean import boolean_op
        from typekernel.geo.outline import Outline
    except Exception:
        findings.append(
            Finding(
                "overlap",
                "info",
                name,
                f"{len(pairs)} ink contour pair(s) have overlapping bounds near "
                f"counters (install typekernel[boolean] for cavity confirmation)",
            )
        )
        return

    for ia, ib in pairs:
        try:
            inter = boolean_op(
                Outline((drawing.contours[ia],)),
                Outline((drawing.contours[ib],)),
                "intersection",
            )
        except Exception:
            continue
        if not inter.contours:
            continue
        area = sum(abs(signed_area(c)) for c in inter.contours)
        if area < 1.0:
            continue
        try:
            ibox = bounds(inter)
        except ValueError:
            continue
        nearest = min(_box_gap(ibox, cb) for _, cb in counter_boxes)
        if nearest > proximity:
            # Cancel island sits in solid ink, away from 字腔 — intentional
            # overlap under nonzero/VF; skip.
            continue
        findings.append(
            Finding(
                "overlap",
                "warn",
                name,
                f"ink[{ia}]∩ink[{ib}] area≈{area:.0f}u² cancels under even-odd "
                f"within {nearest:.0f}u of a counter (cavity notch risk). "
                f"Inspect: `tk proof --glyph {name}`. "
                "Fix design: reshape so overlap stays in solid ink away from "
                "the counter, not a heal/seal pass. Static ship only: "
                "`tk build --resolve-overlaps` (forbidden with --variable)",
            )
        )
