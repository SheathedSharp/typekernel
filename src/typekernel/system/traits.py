"""Closed trait vocabulary (target-architecture §5.4). Letter-agnostic."""

from __future__ import annotations

from collections.abc import Iterable

__all__ = ["TRAITS", "UnknownTraitError", "validate_traits"]

TRAITS: frozenset[str] = frozenset(
    {
        "x-height",
        "cap",
        "ascender",
        "descender",
        "smcp",
        "round-top",
        "round-bottom",
        "flat-top",
        "flat-bottom",
        "pointed-top",
        "pointed-bottom",
        "diagonal",
        "mark",
        "spacing-mark",
        "figure",
        "tabular",
        "punct",
        "symbol",
        "no-stem",
    }
)


class UnknownTraitError(ValueError):
    """Raised when ``@glyph(..., traits=...)`` names a trait outside TRAITS."""


def validate_traits(traits: Iterable[str]) -> tuple[str, ...]:
    """Return a sorted unique trait tuple; raise on unknown names."""
    out = tuple(sorted(set(traits)))
    unknown = [t for t in out if t not in TRAITS]
    if unknown:
        raise UnknownTraitError(
            f"unknown trait(s) {unknown!r}; known: {sorted(TRAITS)}"
        )
    return out
