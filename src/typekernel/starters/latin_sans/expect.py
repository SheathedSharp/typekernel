"""Topology / reach expectations for latin-sans (diagnose §7.3).

These encode *correct* topology so defects on the current structural starter
surface as findings (for example, a θ-shaped e). Projects may diverge; ``tk audit``
lists diffs against this starter table.
"""

from __future__ import annotations

from typekernel.project import Expect

__all__ = ["EXPECT", "STARTER_EXPECT"]

EXPECT: dict[str, Expect] = {
    "a": Expect(counters=1, islands=1),
    "b": Expect(counters=1, islands=1),
    "d": Expect(counters=1, islands=1),
    "e": Expect(counters=1, islands=1, apertures=1),  # one counter, one aperture
    "g": Expect(counters=2, islands=1),  # double-storey: upper + lower bowls, sealed stem
    "o": Expect(counters=1, islands=1),
    "p": Expect(counters=1, islands=1),
    "q": Expect(counters=1, islands=1),
    "A": Expect(counters=1, islands=1),
    "B": Expect(counters=2, islands=1),  # letter-class B; bowls meet at waist
    "D": Expect(counters=1, islands=1),
    "O": Expect(counters=1, islands=1),
    "P": Expect(counters=1, islands=1),
    "Q": Expect(counters=1, islands=1),
    "R": Expect(counters=1, islands=1),
    "zero": Expect(counters=1, islands=1),
    "two": Expect(counters=0, islands=1),
    "three": Expect(counters=0, islands=1),  # open counters
    "four": Expect(counters=0, islands=1),
    "five": Expect(counters=0, islands=1),
    "six": Expect(counters=1, islands=1),
    "eight": Expect(counters=2, islands=1),
    "nine": Expect(counters=1, islands=1),
    "i": Expect(counters=0, islands=2),
    "j": Expect(counters=0, islands=2),
    "colon": Expect(counters=0, islands=2),
    "semicolon": Expect(counters=0, islands=2),
    "exclam": Expect(counters=0, islands=2),
    "question": Expect(counters=0, islands=3, reach=("base",)),  # body+dot+hook island; x-height bowl
    "J": Expect(reach=("cap",)),  # hook clears desc zone optically, not to desc line
    "AE": Expect(counters=1, islands=1),
    "ae": Expect(counters=2, islands=1),
    "OE": Expect(counters=2, islands=1),
    "oe": Expect(counters=2, islands=1),
    "parenleft": Expect(counters=0, islands=1),
    "parenright": Expect(counters=0, islands=1),
}


STARTER_EXPECT = EXPECT
