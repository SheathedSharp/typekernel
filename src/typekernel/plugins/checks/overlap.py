"""Opt-in ink∩ink even-odd cavity check plugin.

Intentional overlap construction (stem + shoulder, no counters) is the
recommended VF pattern and must not flood warnings. This check only reports
when an ink∩ink cancel region **actually overlaps a declared counter** (字腔)
— the case where even-odd preview opens a notch into the cavity.

Bounding-box proximity is not enough: a stem overlapping a bowl's outer ring
is adjacent to the counter bbox but the cancel island sits in solid ink. Those
normal bowl+stem shapes must stay quiet.
"""

from __future__ import annotations

from typekernel.draw import Drawing
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import Outline
from typekernel.plugins.checks.protocol import CheckContext, Finding

__all__ = ["check"]

# Minimum area (design units²) for a cancel island to count as a cavity defect.
_MIN_AREA = 1.0


def check(ctx: CheckContext) -> None:
    """Report-only: ink∩ink cancels that overlap a counter under even-odd."""
    _audit_overlap_cavity(ctx.name, ctx.final, ctx.findings)


def _audit_overlap_cavity(
    name: str,
    drawing: Drawing,
    findings: list[Finding],
) -> None:
    ink_idxs = [i for i, role in enumerate(drawing.roles) if role == "ink"]
    counter_idxs = [i for i, role in enumerate(drawing.roles) if role == "counter"]
    if len(ink_idxs) < 2 or not counter_idxs:
        return

    inks = [
        (i, Outline((drawing.contours[i],)))
        for i in ink_idxs
        if drawing.contours[i].segments
    ]
    counters = [
        Outline((drawing.contours[i],))
        for i in counter_idxs
        if drawing.contours[i].segments
    ]
    if len(inks) < 2 or not counters:
        return

    try:
        from typekernel.geo.boolean import boolean_op
    except Exception:  # noqa: BLE001 - optional boolean extra
        findings.append(
            Finding(
                "overlap",
                "info",
                name,
                "overlapping ink contours present (install typekernel[boolean] "
                "for counter-intersection confirmation)",
            )
        )
        return

    for a in range(len(inks)):
        ia, outline_a = inks[a]
        for b in range(a + 1, len(inks)):
            ib, outline_b = inks[b]
            try:
                inter = boolean_op(outline_a, outline_b, "intersection")
            except Exception:  # noqa: BLE001, S112 - optional boolean engine
                continue
            if not inter.contours:
                continue
            cancel_area = sum(abs(signed_area(c)) for c in inter.contours)
            if cancel_area < _MIN_AREA:
                continue

            cavity_area = 0.0
            for counter in counters:
                try:
                    hit = boolean_op(inter, counter, "intersection")
                except Exception:  # noqa: BLE001, S112 - optional boolean engine
                    continue
                cavity_area += sum(abs(signed_area(c)) for c in hit.contours)
            if cavity_area < _MIN_AREA:
                # Cancel island sits in solid ink, away from 字腔 — intentional
                # overlap under nonzero/VF; skip.
                continue

            findings.append(
                Finding(
                    "overlap",
                    "warn",
                    name,
                    f"ink[{ia}]∩ink[{ib}] cancels over {cavity_area:.0f}u² of a "
                    f"counter (cavity notch risk). "
                    f"Inspect: `tk proof --glyph {name}`. "
                    "Fix design: reshape so overlap stays in solid ink away from "
                    "the counter, not a heal/seal pass. Static ship only: "
                    "`tk build --resolve-overlaps` (forbidden with --variable)",
                )
            )
