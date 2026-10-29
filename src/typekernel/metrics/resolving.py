"""Resolve Metrics keys to (lsb, rsb) per glyph (target-architecture §5.3)."""

from __future__ import annotations

from collections.abc import Mapping

from typekernel.font.glyph import Glyph
from typekernel.metrics import Abs, Metrics, Mirror, Optical, Ref, Side, Stem, Token
from typekernel.system import System

__all__ = ["resolve", "resolve_side"]


def resolve_side(
    side: Side,
    system: System,
    resolved: Mapping[str, tuple[float, float]],
    *,
    self_lsb: float | None = None,
) -> float:
    """Evaluate one side expression against System / already-resolved keys."""
    if isinstance(side, Abs):
        return float(side.value)
    if isinstance(side, Stem):
        return float(system.stem[side.key]) * float(side.factor)
    if isinstance(side, Token):
        return float(system.tokens[side.key]) * float(side.factor)
    if isinstance(side, Ref):
        if side.glyph not in resolved:
            raise KeyError(f"metrics key ref {side.glyph!r} not resolved yet")
        lsb, rsb = resolved[side.glyph]
        base = lsb if side.side == "lsb" else rsb
        return float(base) + float(side.delta)
    if isinstance(side, Mirror):
        if self_lsb is None:
            raise ValueError("Mirror requires the sibling LSB to be resolved first")
        return float(self_lsb)
    if isinstance(side, Optical):
        raise NotImplementedError("Optical sidebearings land in P2-7")
    raise TypeError(f"unknown Side type: {type(side)!r}")


def resolve(
    metrics: Metrics,
    system: System,
    glyphs: Mapping[str, Glyph] | None = None,
) -> dict[str, tuple[float, float]]:
    """Resolve ``metrics.keys`` in dependency order; detect cycles.

    ``glyphs`` is accepted for API completeness (Optical will need it in P2-7).
    """
    del glyphs  # reserved for Optical
    resolved: dict[str, tuple[float, float]] = {}
    pending = dict(metrics.keys)
    for _ in range(len(pending) + 2):
        if not pending:
            break
        progressed = False
        for name, (lsb_side, rsb_side) in list(pending.items()):
            try:
                lsb = resolve_side(lsb_side, system, resolved)
                if isinstance(rsb_side, Mirror):
                    rsb = resolve_side(rsb_side, system, resolved, self_lsb=lsb)
                else:
                    rsb = resolve_side(rsb_side, system, resolved)
            except KeyError:
                continue
            resolved[name] = (lsb, rsb)
            del pending[name]
            progressed = True
        if not progressed:
            break
    if pending:
        raise ValueError(
            f"unresolved metrics keys (cycle or missing ref): {sorted(pending)}"
        )
    return resolved
