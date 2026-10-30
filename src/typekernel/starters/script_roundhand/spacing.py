"""Metrics for script-roundhand — data only."""

from __future__ import annotations

from typekernel.metrics import Kerning, Metrics, Ref, Stem

__all__ = ["KERNING", "METRICS"]

METRICS = Metrics(
    keys={
        "n": (Stem("lc", 0.7), Stem("lc", 0.7)),
        "o": (Stem("lc", 0.45), Stem("lc", 0.45)),
        "u": (Ref("n", "lsb"), Ref("n", "rsb")),
        "a": (Stem("lc", 0.4), Ref("n", "rsb")),
        "e": (Ref("o", "lsb"), Ref("o", "rsb")),
        "c": (Ref("o", "lsb"), Stem("lc", 0.35)),
        "r": (Ref("n", "lsb"), Stem("lc", 0.35)),
        "i": (Stem("lc", 0.9), Stem("lc", 0.9)),
        "l": (Ref("i", "lsb"), Ref("i", "rsb")),
        "f": (Stem("lc", 0.25), Stem("lc", 0.3)),
        "v": (Stem("lc", 0.2), Stem("lc", 0.2)),
        "y": (Stem("lc", 0.2), Stem("lc", 0.2)),
        "z": (Stem("lc", 0.35), Stem("lc", 0.35)),
    },
    pack="bbox",
)
KERNING = Kerning()
