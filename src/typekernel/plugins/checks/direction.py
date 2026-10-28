"""Direction / winding check plugin."""

from __future__ import annotations

from typekernel.geo.contour import signed_area
from typekernel.plugins.checks.protocol import CheckContext, Finding

__all__ = ["check"]


def check(ctx: CheckContext) -> None:
    """Outer ink CCW (positive area); counters CW (negative)."""
    drawing = ctx.final
    for i, (contour, role) in enumerate(zip(drawing.contours, drawing.roles, strict=True)):
        if not contour.segments:
            continue
        area = signed_area(contour)
        if role == "ink" and area < 0:
            ctx.findings.append(
                Finding(
                    "direction",
                    "error",
                    ctx.name,
                    f"contour[{i}] role=ink has CW winding (area={area:.1f})",
                )
            )
        elif role == "counter" and area > 0:
            ctx.findings.append(
                Finding(
                    "direction",
                    "error",
                    ctx.name,
                    f"contour[{i}] role=counter has CCW winding (area={area:.1f})",
                )
            )
