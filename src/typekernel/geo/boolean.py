"""Optional boolean operations, delegated to skia-pathops.

Boolean geometry is **not** implemented here, and never with Shapely. Shapely
operates on polygons, so using it would mean turning cubic outlines into
polygons first — exactly the lossy flattening this kernel forbids as a design
truth. ``skia-pathops`` works on real curves, so it is the only acceptable
backend, and it stays behind an optional extra rather than becoming a hard
dependency.

v0 is a stub on purpose. It fixes the signature and the failure modes so the
rest of the kernel can be written against it, while making no claim to do
booleans yet. In particular the curve round-trip — turning pathops' output back
into cubic ``Outline`` data without losing curvature — is unresolved, and is
tracked as a follow-up rather than half-implemented here.
"""

from __future__ import annotations

from typing import Literal

from typekernel.geo.outline import Outline

BooleanOp = Literal["union", "intersection", "difference"]
"""The boolean operations this module will eventually support."""

BOOLEAN_OPS: frozenset[str] = frozenset({"union", "intersection", "difference"})

INSTALL_HINT = (
    "boolean operations require the optional extra: "
    'pip install "typekernel[boolean]"'
)

ROUND_TRIP_NOTE = (
    "boolean_op is a stub: the curve round-trip from pathops back to cubic "
    "Outline data is not implemented yet"
)


def boolean_op(a: Outline, b: Outline, op: BooleanOp) -> Outline:
    """Combine two outlines with a boolean operation.

    Not implemented yet. The call exists so callers can be written against it,
    and so the failure is explicit rather than silent.

    Raises:
        ValueError: if ``op`` is not a known operation.
        RuntimeError: if ``skia-pathops`` is not installed, with the install
            hint for the ``boolean`` extra.
        NotImplementedError: if pathops is available but the curve round-trip
            has not been implemented yet.
    """
    if op not in BOOLEAN_OPS:
        raise ValueError(f"unknown boolean op {op!r}; expected one of {sorted(BOOLEAN_OPS)}")

    try:
        import pathops  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(INSTALL_HINT) from exc

    raise NotImplementedError(ROUND_TRIP_NOTE)
