"""Compose optical operators in a documented order."""

from __future__ import annotations

from typekernel.geo.outline import Outline
from typekernel.optics.context import OpticalContext
from typekernel.optics.joins import JoinPolicy, cleanup_joins
from typekernel.optics.overshoot import apply_overshoot


def apply(
    outline: Outline,
    ctx: OpticalContext,
    *,
    overshoot: bool = False,
    joins_policy: JoinPolicy = "noop",
) -> Outline:
    """Apply selected optical operators and return a new (or same) outline.

    Order (fixed, documented):

    1. **Overshoot** — if ``overshoot`` is true, run
       :func:`~typekernel.optics.overshoot.apply_overshoot` with
       ``kind='round'`` (sharp selection is left to a direct call for now).
    2. **Join cleanup** — always run
       :func:`~typekernel.optics.joins.cleanup_joins` with ``joins_policy``
       (default ``noop``, which is identity).

    Stem measure, contrast validation, and sidebearing suggestion are
    query/validation helpers and are intentionally not part of this mutating
    pipeline. Weight / stroke expand is never applied here.
    """
    result = outline
    if overshoot:
        result = apply_overshoot(result, ctx, kind="round")
    result = cleanup_joins(result, policy=joins_policy)
    return result
