"""Merge Abs sidebearing suggestions into a Metrics table (pure; no I/O)."""

from __future__ import annotations

from collections.abc import Mapping

from typekernel.metrics import Abs, Metrics, Side

__all__ = ["with_abs_sidebearings"]


def with_abs_sidebearings(
    metrics: Metrics,
    updates: Mapping[str, tuple[float, float]],
) -> Metrics:
    """Return a new Metrics with ``Abs`` LSB/RSB for each name in ``updates``.

    Does not mutate ``metrics``. Contours are untouched — packing happens later
    via ``apply_metrics`` / build.
    """
    keys: dict[str, tuple[Side, Side]] = dict(metrics.keys)
    for name, (lsb, rsb) in updates.items():
        keys[str(name)] = (Abs(float(lsb)), Abs(float(rsb)))
    return Metrics(
        keys=keys,
        space=metrics.space,
        pack=metrics.pack,
        italic_pack_ys=metrics.italic_pack_ys,
        join=metrics.join,
    )
