"""Contrast targets for designed weight deltas.

``ContrastParams`` records thick/thin *targets* for later designed-delta work.
They are not pen radii, stroke widths, or arguments to a buffer / expand step.
"""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.geo.outline import Outline
from typekernel.optics.context import OpticalContext


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


def apply_designed_contrast(
    outline: Outline,
    params: ContrastParams,
    ctx: OpticalContext | None = None,
    *,
    y: float | None = None,
    x: float | None = None,
) -> Outline:
    """Hit ``params.thick`` on vertical stems and ``params.thin`` on horizontals.

    Designed point deltas only (stem-band remaps). Never stroke expand / buffer.
    """
    from typekernel.optics.stem import equalize_horizontal_stems, equalize_vertical_stems

    validate_contrast_params(params)
    out = equalize_vertical_stems(outline, params.thick, ctx, y=y)
    return equalize_horizontal_stems(out, params.thin, ctx, x=x)
