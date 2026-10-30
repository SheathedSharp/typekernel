"""Topology expectations (diagnose §7.3) — measured for pen italic."""

from __future__ import annotations

from typekernel.project import Expect

__all__ = ["EXPECT", "STARTER_EXPECT"]

EXPECT: dict[str, Expect] = {
    "e": Expect(counters=0, islands=4, apertures=0),
    "o": Expect(counters=1, islands=1),
    "three": Expect(counters=0, islands=4),
    "g": Expect(counters=1, islands=1),
    "B": Expect(counters=2, islands=3),
    "i": Expect(counters=0, islands=2),
    "colon": Expect(counters=2, islands=2),
}
STARTER_EXPECT = EXPECT
