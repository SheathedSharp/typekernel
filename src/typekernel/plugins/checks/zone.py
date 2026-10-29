"""Zone / overshoot extent check plugin."""

from __future__ import annotations

from typekernel.geo.outline import bounds
from typekernel.plugins.checks.protocol import CheckContext, Finding

__all__ = ["check"]


def check(ctx: CheckContext, *, tol: float = 24.0) -> None:
    """Warn when glyph bounds fall far outside System zones."""
    outline = ctx.final.outline()
    if not outline.contours or not any(c.segments for c in outline.contours):
        return
    try:
        _minx, min_y, _maxx, max_y = bounds(outline)
    except ValueError:
        return
    system = ctx.system
    name = ctx.name
    ov = float(system.overshoot.round)
    if min_y < float(system.zones.desc) - tol:
        ctx.findings.append(
            Finding(
                "zone",
                "warn",
                name,
                f"ymin {min_y:.1f} below desc {system.zones.desc} (tol {tol})",
            )
        )
    ceiling = max(float(system.zones.asc), float(system.zones.cap)) + ov + tol
    if max_y > ceiling:
        ctx.findings.append(
            Finding(
                "zone",
                "warn",
                name,
                f"ymax {max_y:.1f} above zones+overshoot ({ceiling:.1f})",
            )
        )
