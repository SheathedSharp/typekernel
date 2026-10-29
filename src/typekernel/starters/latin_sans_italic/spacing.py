"""Metrics for latin-sans italic — control + n-group / uc.straight expand."""

from __future__ import annotations

from typekernel.metrics import Kerning, Metrics, Ref, Stem

__all__ = ["KERNING", "METRICS"]

METRICS = Metrics(
    keys={
        "n": (Stem("lc", 0.9), Stem("lc", 0.9)),
        "m": (Stem("lc", 0.85), Stem("lc", 0.85)),
        "h": (Ref("n", "lsb"), Ref("n", "rsb")),
        "u": (Ref("n", "lsb"), Ref("n", "rsb")),
        "l": (Stem("lc", 1.0), Stem("lc", 1.0)),
        "r": (Stem("lc", 0.95), Stem("lc", 0.7)),
        "o": (Stem("lc", 0.55), Stem("lc", 0.55)),
        "e": (Ref("o", "lsb"), Ref("o", "rsb")),
        "i": (Stem("lc", 1.0), Stem("lc", 1.0)),
        "H": (Stem("uc", 0.85), Stem("uc", 0.85)),
        "I": (Stem("uc", 1.0), Stem("uc", 1.0)),
        "L": (Stem("uc", 0.85), Stem("uc", 0.55)),
        "T": (Stem("uc", 0.55), Stem("uc", 0.55)),
        "E": (Stem("uc", 0.85), Stem("uc", 0.55)),
        "F": (Stem("uc", 0.85), Stem("uc", 0.55)),
        "O": (Stem("uc", 0.5), Stem("uc", 0.5)),
        "a": (Stem("lc", 0.7), Stem("lc", 0.7)),
        "b": (Stem("lc", 0.9), Stem("lc", 0.55)),
        "c": (Stem("lc", 0.55), Stem("lc", 0.55)),
        "d": (Stem("lc", 0.55), Stem("lc", 0.9)),
        "p": (Stem("lc", 0.9), Stem("lc", 0.55)),
        "q": (Stem("lc", 0.55), Stem("lc", 0.9)),
        "s": (Stem("lc", 0.6), Stem("lc", 0.6)),
        "v": (Stem("lc", 0.7), Stem("lc", 0.7)),
        "w": (Stem("lc", 0.65), Stem("lc", 0.65)),
        "x": (Stem("lc", 0.7), Stem("lc", 0.7)),
        "y": (Stem("lc", 0.7), Stem("lc", 0.7)),
        "z": (Stem("lc", 0.7), Stem("lc", 0.7)),
        "k": (Stem("lc", 0.9), Stem("lc", 0.7)),
        "A": (Stem("uc", 0.55), Stem("uc", 0.55)),
        "V": (Stem("uc", 0.55), Stem("uc", 0.55)),
        "N": (Stem("uc", 0.85), Stem("uc", 0.85)),
        "M": (Stem("uc", 0.8), Stem("uc", 0.8)),
        "K": (Stem("uc", 0.85), Stem("uc", 0.55)),
    },
    space=Stem("lc", 2.8),
)

KERNING = Kerning()
