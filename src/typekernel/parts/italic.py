"""Designed italic control sheet (metric/structure tune, not post-hoc shear).

True italic here means a **redrawn master** with the same topology as the
regular control sheet so ``wght``/``ital`` axes interpolate. For mechanical
oblique, use :func:`~typekernel.compile.oblique.oblique_font` instead.
"""

from __future__ import annotations

from dataclasses import replace

from typekernel.parts.family import Controls

__all__ = ["italic_controls"]


def italic_controls(regular: Controls, *, lean: float = 1.035) -> Controls:
    """Return an italic control sheet derived from ``regular``.

    ``lean`` widens counters and o-bowls slightly and lowers contrast so the
    italic master reads lighter and forward-leaning without changing contour
    topology (same segment counts as the regular master).
    """
    ctx = regular.context
    n = regular.n.tuned(counter=regular.n.counter * lean)
    o = regular.o.tuned(
        rx=regular.o.rx * lean,
        ry=regular.o.ry * (lean * 0.98),
    )
    return replace(
        regular,
        n=n,
        o=o,
        context=ctx.tuned(contrast=max(0.88, ctx.contrast * 0.96)),
    )
