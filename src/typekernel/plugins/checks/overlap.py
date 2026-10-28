"""Opt-in ink∩ink even-odd cavity check plugin."""

from __future__ import annotations

from typekernel.draw import Drawing
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.plugins.checks.protocol import CheckContext, Finding

__all__ = ["check"]


def check(ctx: CheckContext) -> None:
    """Report-only: overlapping ink contours that cancel under even-odd fill."""
    _audit_overlap_cavity(ctx.name, ctx.final, ctx.findings)


def _audit_overlap_cavity(name: str, drawing: Drawing, findings: list[Finding]) -> None:
    ink_idxs = [i for i, role in enumerate(drawing.roles) if role == "ink"]
    if len(ink_idxs) < 2:
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
    try:
        from typekernel.geo.boolean import boolean_op
        from typekernel.geo.outline import Outline
    except Exception:
        findings.append(
            Finding(
                "overlap",
                "info",
                name,
                f"{len(pairs)} ink contour pair(s) have overlapping bounds "
                "(install typekernel[boolean] for cavity confirmation)",
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
        findings.append(
            Finding(
                "overlap",
                "warn",
                name,
                f"ink[{ia}]∩ink[{ib}] area≈{area:.0f}u² cancels under even-odd "
                f"(cavity / white hole risk). Inspect: `tk proof --glyph {name}`. "
                "Fix design: reshape fragments so overlap stays in solid ink "
                "(outside counters), not a heal/seal pass. Static OTF/TTF ship "
                "only: `tk build --resolve-overlaps` (forbidden with --variable; "
                "VF keeps intentional overlaps)",
            )
        )
