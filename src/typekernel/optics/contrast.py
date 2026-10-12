"""Contrast targets for designed weight deltas.

``ContrastParams`` records thick/thin *targets* for later designed-delta work.
They are not pen radii, stroke widths, or arguments to a buffer / expand step.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContrastParams:
    """Contrast targets for designed stem deltas — not stroke expand.

    Attributes:
        thick: Target width for the thick stroke direction (design units).
        thin: Target width for the thin stroke direction (design units).

    These numbers describe intended contrast after designed redistribution.
    They must not be interpreted as a pen radius or as ``buffer(distance)``.
    """

    thick: float
    thin: float


def validate_contrast_params(params: ContrastParams) -> None:
    """Assert ``thick >= thin > 0``.

    Raises:
        ValueError: if the inequality does not hold.
    """
    if not (params.thick >= params.thin > 0):
        raise ValueError(
            "contrast requires thick >= thin > 0; "
            f"got thick={params.thick!r}, thin={params.thin!r}"
        )
