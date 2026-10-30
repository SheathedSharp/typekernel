"""Topology priors keyed by Unicode codepoint (S2 knowledge packet)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

__all__ = [
    "LATIN_BASIC",
    "TopologyPrior",
    "prior_for",
    "priors_for_text",
]


@dataclass(frozen=True, slots=True)
class TopologyPrior:
    """Expected structural identity for one encoded character.

    Fields are design priors an agent can check after ``measure_topology`` /
    bbox vs zones — not construction recipes.
    """

    codepoint: int
    """Unicode scalar value."""

    name: str
    """AGL / common glyph name (allowed here only — knowledge exception)."""

    counters: int
    islands: int
    ascender: bool = False
    descender: bool = False
    has_dot: bool = False


def _p(
    cp: int,
    name: str,
    *,
    counters: int,
    islands: int,
    ascender: bool = False,
    descender: bool = False,
    has_dot: bool = False,
) -> TopologyPrior:
    return TopologyPrior(
        codepoint=cp,
        name=name,
        counters=counters,
        islands=islands,
        ascender=ascender,
        descender=descender,
        has_dot=has_dot,
    )


# Basic Latin letters used by cold-trial strings and confuse pairs.
# Names are intentional data (S2 exception); constructors must not import these
# as builder entry points.
LATIN_BASIC: Mapping[int, TopologyPrior] = {
    # lowercase
    0x61: _p(0x61, "a", counters=1, islands=1),
    0x62: _p(0x62, "b", counters=1, islands=1, ascender=True),
    0x63: _p(0x63, "c", counters=0, islands=1),
    0x64: _p(0x64, "d", counters=1, islands=1, ascender=True),
    0x65: _p(0x65, "e", counters=1, islands=1),
    0x66: _p(0x66, "f", counters=0, islands=1, ascender=True),
    0x67: _p(0x67, "g", counters=1, islands=1, descender=True),  # binocular ~1+ lower
    0x68: _p(0x68, "h", counters=0, islands=1, ascender=True),
    0x69: _p(0x69, "i", counters=0, islands=2, ascender=True, has_dot=True),
    0x6A: _p(0x6A, "j", counters=0, islands=2, descender=True, has_dot=True),
    0x6B: _p(0x6B, "k", counters=0, islands=1, ascender=True),
    0x6C: _p(0x6C, "l", counters=0, islands=1, ascender=True),
    0x6D: _p(0x6D, "m", counters=0, islands=1),
    0x6E: _p(0x6E, "n", counters=0, islands=1),
    0x6F: _p(0x6F, "o", counters=1, islands=1),
    0x70: _p(0x70, "p", counters=1, islands=1, descender=True),
    0x71: _p(0x71, "q", counters=1, islands=1, descender=True),
    0x72: _p(0x72, "r", counters=0, islands=1),
    0x73: _p(0x73, "s", counters=0, islands=1),
    0x74: _p(0x74, "t", counters=0, islands=1, ascender=True),
    0x75: _p(0x75, "u", counters=0, islands=1),
    0x76: _p(0x76, "v", counters=0, islands=1),
    0x77: _p(0x77, "w", counters=0, islands=1),
    0x78: _p(0x78, "x", counters=0, islands=1),
    0x79: _p(0x79, "y", counters=0, islands=1, descender=True),
    0x7A: _p(0x7A, "z", counters=0, islands=1),
    # uppercase (subset)
    0x41: _p(0x41, "A", counters=1, islands=1, ascender=True),
    0x45: _p(0x45, "E", counters=0, islands=1, ascender=True),
    0x48: _p(0x48, "H", counters=0, islands=1, ascender=True),
    0x4F: _p(0x4F, "O", counters=1, islands=1, ascender=True),
    0x5A: _p(0x5A, "Z", counters=0, islands=1, ascender=True),
    # digits / lookalikes
    0x32: _p(0x32, "two", counters=0, islands=1),
    0x03B5: _p(0x03B5, "epsilon", counters=1, islands=1),  # Greek small epsilon
}


def prior_for(codepoint: int) -> TopologyPrior | None:
    """Return the prior for ``codepoint``, or ``None`` if unknown."""
    return LATIN_BASIC.get(int(codepoint))


def priors_for_text(text: str) -> list[TopologyPrior]:
    """Priors for each character in ``text`` (skips unknowns / whitespace)."""
    out: list[TopologyPrior] = []
    for ch in text:
        if ch.isspace():
            continue
        prior = prior_for(ord(ch))
        if prior is not None:
            out.append(prior)
    return out
