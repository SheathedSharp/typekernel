"""Topology + coarse shape priors keyed by Unicode codepoint (S2 knowledge)."""

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

    Topology fields match ``measure_topology`` / bbox-vs-zones. Continuous
    shape targets are **coarse letter-class bins** (high / mid / low), not
    face-specific centroids — so ``tk read`` ranks by relative mass across
    styles. ``None`` means the cue is unused for that letter.
    """

    codepoint: int
    name: str
    counters: int
    islands: int
    ascender: bool = False
    descender: bool = False
    has_dot: bool = False
    # --- continuous shape targets (C3; coarse bins) ---
    aspect: float = 1.0
    """Expected height/width (bbox); approximate class, not a face measure."""

    top_mass: float | None = None
    """Ink in upper half: ~0.75 high (n/m/r), ~0.50 mid, ~0.25 low (u/g)."""

    right_mass: float | None = None
    """Ink in right half: ~0.35 left-heavy (k/f), ~0.50 mid, ~0.65 right-heavy."""

    diag_mass: float | None = None
    """Diagonal occupancy: ~0.85 (x/z), ~0.55 mid, ~0.35 low (o/e/c)."""

    mid_band: float | None = None
    """Mid-row density: ~0.30 crossbar-ish, ~0.05 sparse waist."""


def _p(
    cp: int,
    name: str,
    *,
    counters: int,
    islands: int,
    ascender: bool = False,
    descender: bool = False,
    has_dot: bool = False,
    aspect: float = 1.0,
    top_mass: float | None = None,
    right_mass: float | None = None,
    diag_mass: float | None = None,
    mid_band: float | None = None,
) -> TopologyPrior:
    return TopologyPrior(
        codepoint=cp,
        name=name,
        counters=counters,
        islands=islands,
        ascender=ascender,
        descender=descender,
        has_dot=has_dot,
        aspect=float(aspect),
        top_mass=top_mass,
        right_mass=right_mass,
        diag_mass=diag_mass,
        mid_band=mid_band,
    )


# Coarse letter-class bins — transferable across Latin faces; not calibrated
# to one starter's measured floats (that overfits and breaks script/italic).
LATIN_BASIC: Mapping[int, TopologyPrior] = {
    # lowercase
    0x61: _p(0x61, "a", counters=1, islands=1, aspect=1.2, top_mass=0.50, diag_mass=0.45, mid_band=0.15),
    0x62: _p(0x62, "b", counters=1, islands=1, ascender=True, aspect=1.6, top_mass=0.45, right_mass=0.50, mid_band=0.25),
    0x63: _p(0x63, "c", counters=0, islands=1, aspect=1.2, top_mass=0.50, diag_mass=0.35, mid_band=0.15),
    0x64: _p(0x64, "d", counters=1, islands=1, ascender=True, aspect=1.6, top_mass=0.45, right_mass=0.60, mid_band=0.25),
    0x65: _p(0x65, "e", counters=1, islands=1, aspect=1.25, top_mass=0.48, right_mass=0.58, diag_mass=0.32, mid_band=0.18),
    0x66: _p(0x66, "f", counters=0, islands=1, ascender=True, aspect=2.5, top_mass=0.75, right_mass=0.35, mid_band=0.15),
    0x67: _p(0x67, "g", counters=1, islands=1, descender=True, aspect=1.55, top_mass=0.35, mid_band=0.20),
    0x68: _p(0x68, "h", counters=0, islands=1, ascender=True, aspect=1.7, top_mass=0.75, mid_band=0.30),
    0x69: _p(0x69, "i", counters=0, islands=2, ascender=True, has_dot=True, aspect=5.0, top_mass=0.75, mid_band=0.05),
    0x6A: _p(0x6A, "j", counters=0, islands=2, descender=True, has_dot=True, aspect=3.5, top_mass=0.50, right_mass=0.65, mid_band=0.05),
    0x6B: _p(0x6B, "k", counters=0, islands=1, ascender=True, aspect=1.4, top_mass=0.50, right_mass=0.35, diag_mass=0.60, mid_band=0.20),
    0x6C: _p(0x6C, "l", counters=0, islands=1, ascender=True, aspect=6.0, mid_band=0.08),
    0x6D: _p(0x6D, "m", counters=0, islands=1, aspect=0.75, top_mass=0.75, mid_band=0.05),
    0x6E: _p(0x6E, "n", counters=0, islands=1, aspect=1.15, top_mass=0.75, mid_band=0.05),
    0x6F: _p(0x6F, "o", counters=1, islands=1, aspect=1.15, top_mass=0.55, right_mass=0.55, diag_mass=0.35, mid_band=0.20),
    0x70: _p(0x70, "p", counters=1, islands=1, descender=True, aspect=1.55, top_mass=0.55, right_mass=0.50, mid_band=0.25),
    0x71: _p(0x71, "q", counters=1, islands=1, descender=True, aspect=1.55, top_mass=0.55, right_mass=0.60, mid_band=0.25),
    0x72: _p(0x72, "r", counters=0, islands=1, aspect=1.5, top_mass=0.75, mid_band=0.05),
    0x73: _p(0x73, "s", counters=0, islands=1, aspect=1.4, top_mass=0.50, mid_band=0.25),
    0x74: _p(0x74, "t", counters=0, islands=1, ascender=True, aspect=2.0, top_mass=0.75, mid_band=0.08),
    0x75: _p(0x75, "u", counters=0, islands=1, aspect=1.15, top_mass=0.25, mid_band=0.05),
    0x76: _p(0x76, "v", counters=0, islands=1, aspect=1.15, top_mass=0.50, diag_mass=0.55, mid_band=0.08),
    0x77: _p(0x77, "w", counters=0, islands=1, aspect=0.80, top_mass=0.50, diag_mass=0.50, mid_band=0.08),
    0x78: _p(0x78, "x", counters=0, islands=1, aspect=1.15, top_mass=0.50, right_mass=0.50, diag_mass=0.98, mid_band=0.08),
    0x79: _p(0x79, "y", counters=0, islands=1, descender=True, aspect=1.5, top_mass=0.70, diag_mass=0.75, mid_band=0.20),
    0x7A: _p(0x7A, "z", counters=0, islands=1, aspect=1.1, top_mass=0.50, right_mass=0.55, diag_mass=0.88, mid_band=0.05),
    # uppercase — coarse letter-class bins (not face centroids)
    0x41: _p(0x41, "A", counters=1, islands=1, ascender=True, aspect=1.05, top_mass=0.35, diag_mass=0.55, mid_band=0.15),
    0x42: _p(0x42, "B", counters=2, islands=1, ascender=True, aspect=1.15, top_mass=0.50, mid_band=0.25),
    0x43: _p(0x43, "C", counters=0, islands=1, ascender=True, aspect=1.10, top_mass=0.50, diag_mass=0.45, mid_band=0.15),
    0x44: _p(0x44, "D", counters=1, islands=1, ascender=True, aspect=1.05, top_mass=0.55, diag_mass=0.35, mid_band=0.20),
    0x45: _p(0x45, "E", counters=0, islands=1, ascender=True, aspect=1.30, right_mass=0.40, mid_band=0.25),
    0x46: _p(0x46, "F", counters=0, islands=1, ascender=True, aspect=1.35, top_mass=0.70, right_mass=0.35, mid_band=0.25),
    0x47: _p(0x47, "G", counters=0, islands=1, ascender=True, aspect=1.05, top_mass=0.50, right_mass=0.60, mid_band=0.15),
    0x48: _p(0x48, "H", counters=0, islands=1, ascender=True, aspect=1.15, mid_band=0.25),
    0x49: _p(0x49, "I", counters=0, islands=1, ascender=True, aspect=6.0, mid_band=0.15),
    0x4A: _p(0x4A, "J", counters=0, islands=1, ascender=True, aspect=1.40, top_mass=0.25, right_mass=0.60, mid_band=0.05),
    0x4B: _p(0x4B, "K", counters=0, islands=1, ascender=True, aspect=1.20, right_mass=0.35, diag_mass=0.60, mid_band=0.20),
    0x4C: _p(0x4C, "L", counters=0, islands=1, ascender=True, aspect=1.30, top_mass=0.30, right_mass=0.35, mid_band=0.08),
    0x4D: _p(0x4D, "M", counters=0, islands=1, ascender=True, aspect=0.90, top_mass=0.55, diag_mass=0.65, mid_band=0.12),
    0x4E: _p(0x4E, "N", counters=0, islands=1, ascender=True, aspect=1.10, diag_mass=0.80, mid_band=0.05),
    0x4F: _p(0x4F, "O", counters=1, islands=1, ascender=True, aspect=1.05, top_mass=0.55, diag_mass=0.35, mid_band=0.20),
    0x50: _p(0x50, "P", counters=1, islands=1, ascender=True, aspect=1.20, top_mass=0.70, mid_band=0.25),
    0x51: _p(0x51, "Q", counters=1, islands=1, ascender=True, aspect=1.05, top_mass=0.50, diag_mass=0.45, mid_band=0.20),
    0x52: _p(0x52, "R", counters=1, islands=1, ascender=True, aspect=1.15, top_mass=0.70, mid_band=0.30),
    0x53: _p(0x53, "S", counters=0, islands=1, ascender=True, aspect=1.35, top_mass=0.50, mid_band=0.25),
    0x54: _p(0x54, "T", counters=0, islands=1, ascender=True, aspect=1.15, top_mass=0.75, mid_band=0.08),
    0x55: _p(0x55, "U", counters=0, islands=1, ascender=True, aspect=1.10, top_mass=0.25, mid_band=0.08),
    0x56: _p(0x56, "V", counters=0, islands=1, ascender=True, aspect=1.05, top_mass=0.50, diag_mass=0.55, mid_band=0.08),
    0x57: _p(0x57, "W", counters=0, islands=1, ascender=True, aspect=0.75, top_mass=0.50, diag_mass=0.50, mid_band=0.08),
    0x58: _p(0x58, "X", counters=0, islands=1, ascender=True, aspect=1.10, diag_mass=0.95, mid_band=0.08),
    0x59: _p(0x59, "Y", counters=0, islands=1, ascender=True, aspect=1.05, top_mass=0.40, diag_mass=0.75, mid_band=0.12),
    0x5A: _p(0x5A, "Z", counters=0, islands=1, ascender=True, aspect=1.15, diag_mass=0.85, mid_band=0.05),
    # digits / lookalikes
    0x32: _p(0x32, "two", counters=0, islands=1, aspect=1.5, top_mass=0.55, diag_mass=0.50, mid_band=0.15),
    0x03B5: _p(0x03B5, "epsilon", counters=1, islands=1, aspect=1.2, top_mass=0.50, diag_mass=0.35, mid_band=0.25),
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
