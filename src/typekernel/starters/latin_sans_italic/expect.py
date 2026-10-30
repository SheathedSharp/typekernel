"""Topology expectations for latin-sans italic control glyphs."""

from __future__ import annotations

from typekernel.project import Expect

__all__ = ["EXPECT"]

# Pen/skeleton italic construction yields open bowls and multi-island joins;
# values match live ``tk explain`` / diagnose counts (not roman latin-sans).
EXPECT = {
    "n": Expect(counters=0, islands=1),
    "o": Expect(counters=1, islands=1),
    "e": Expect(counters=0, islands=4, apertures=0),
    "i": Expect(counters=0, islands=2),
    "H": Expect(counters=0, islands=1),
    "O": Expect(counters=1, islands=1),
    "g": Expect(counters=1, islands=1),
}
