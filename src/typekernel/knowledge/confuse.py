"""Common glyph confusion pairs (S2).

Pairs are Unicode codepoints. Letter names appear only as documentation /
derived labels via :mod:`typekernel.knowledge.priors`.
"""

from __future__ import annotations

from typekernel.knowledge.priors import prior_for

__all__ = ["CONFUSE_PAIRS", "confuse_partners"]

# (a, b) means a is often misread as b (and we also check the reverse).
CONFUSE_PAIRS: tuple[tuple[int, int], ...] = (
    (0x7A, 0x32),  # z / 2
    (0x65, 0x03B5),  # e / ε
    (0x75, 0x6E),  # u / n
    (0x61, 0x64),  # a / d
    (0x6E, 0x68),  # n / h
    (0x7A, 0x65),  # z / e  (cold-trial failure mode)
    (0x6F, 0x61),  # o / a
)


def confuse_partners(codepoint: int) -> tuple[int, ...]:
    """Codepoints commonly confused with ``codepoint``."""
    cp = int(codepoint)
    out: list[int] = []
    for a, b in CONFUSE_PAIRS:
        if a == cp:
            out.append(b)
        elif b == cp:
            out.append(a)
    # Drop partners we have no prior for.
    return tuple(p for p in out if prior_for(p) is not None)
