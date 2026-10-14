"""Italic control-sheet placeholder (metric tweak only — not a slanted master).

``italic_controls`` widens ``n``/``o`` counters slightly for interpolation
experiments. It does **not** slant stems or change italic topology. True italic
masters (readable slant, branching arches, etc.) are planned in
``docs/DEVELOPMENT_PLAN.md`` (M4). For mechanical oblique, use
:func:`~typekernel.compile.oblique.oblique_font` instead.
"""

from __future__ import annotations

from dataclasses import replace

from typekernel.parts.family import Controls

__all__ = ["italic_controls"]


def italic_controls(regular: Controls, *, lean: float = 1.035) -> Controls:
    """Return a **non-italic** metric variant of ``regular`` (VF placeholder).

    ``lean`` widens counters and o-bowls slightly and lowers contrast. Contour
    topology and stem angles stay the same as the regular master. Do not ship
    this as a designed italic style until M4 lands.
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
