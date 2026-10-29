"""Topology expectations for latin-sans italic control glyphs."""

from __future__ import annotations

from typekernel.project import Expect

__all__ = ["EXPECT"]

EXPECT = {
    "n": Expect(counters=1, islands=1, reach=("base", "x")),
    "o": Expect(counters=1, islands=1, reach=("base", "x")),
    "e": Expect(counters=1, islands=1, apertures=1, reach=("base", "x")),
    "i": Expect(counters=0, islands=2, reach=("base", "x")),
    "H": Expect(counters=0, islands=1, reach=("base", "cap")),
    "O": Expect(counters=1, islands=1, reach=("base", "cap")),
}
