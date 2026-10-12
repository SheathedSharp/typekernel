"""Sidebearing / rhythm helpers (reserved).

Sidebearing suggestions should eventually follow counter space and gray value,
not a single hard-coded constant such as ``sb=60``.
"""

from __future__ import annotations

from typekernel.geo.outline import Outline
from typekernel.optics.context import OpticalContext


def suggest_sidebearings(
    outline: Outline,
    ctx: OpticalContext,
) -> tuple[float, float]:
    """Suggest left and right sidebearings for ``outline``.

    Reserved API. A future implementation may use counter/gray heuristics from
    ``ctx`` and the outline. It must not reduce to a fixed magic constant as
    the only public path.
    """
    del outline, ctx
    raise NotImplementedError(
        "suggest_sidebearings is reserved; sidebearings should follow "
        "counter/gray value later, not a fixed constant"
    )
