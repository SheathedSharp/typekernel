"""Minimal metrics for latin-sans italic control set."""

from __future__ import annotations

from typekernel.metrics import Kerning, Metrics, Ref, Stem

__all__ = ["KERNING", "METRICS"]

METRICS = Metrics(
    keys={
        "n": (Stem("lc", 0.9), Stem("lc", 0.9)),
        "o": (Stem("lc", 0.55), Stem("lc", 0.55)),
        "e": (Ref("o", "lsb"), Ref("o", "rsb")),
        "i": (Stem("lc", 1.0), Stem("lc", 1.0)),
        "H": (Stem("uc", 0.85), Stem("uc", 0.85)),
        "O": (Stem("uc", 0.5), Stem("uc", 0.5)),
    },
    space=Stem("lc", 2.8),
)

KERNING = Kerning()
