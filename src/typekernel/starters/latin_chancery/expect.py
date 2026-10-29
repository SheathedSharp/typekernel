"""Topology expectations (diagnose §7.3). Correct intent so B-class defects fire."""

from __future__ import annotations

from typekernel.project import Expect

__all__ = ["EXPECT", "STARTER_EXPECT"]

EXPECT: dict[str, Expect] = {
    "e": Expect(counters=1, islands=1, apertures=1),
    "o": Expect(counters=1, islands=1),
    "three": Expect(counters=0, islands=1),
    "g": Expect(counters=2, islands=1),
    "B": Expect(counters=2, islands=1),
    "i": Expect(counters=0, islands=2),
    "colon": Expect(counters=0, islands=2),
}
STARTER_EXPECT = EXPECT
