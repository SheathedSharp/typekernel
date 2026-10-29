"""Anatomy — letter-free structural parts (target-architecture §4).

Parts return a single structural ``Drawing`` (stem, arch, bowl, …), never a
whole letter. Projects assemble glyphs in ``elements.py`` / ``glyphs/``.

Pen / skeleton construction for italic starters lives in
:mod:`typekernel.anatomy.pen` (P5-1) — cubic skeletons only on ``stroke``.
"""

from __future__ import annotations

from typekernel.anatomy.curves import BarSpec, arch, bowl, bowl_join, open_bowl, spine
from typekernel.anatomy.diagonal import crossing, diagonal_pair
from typekernel.anatomy.straight import crossbar, dot, drop, stem
from typekernel.anatomy.tags import (
    ENDPOINTS,
    FACES,
    PARTS,
    POSITIONS,
    SIDES,
    ParsedTag,
    TagGrammarError,
    is_valid_tag,
    parse_tag,
)
from typekernel.anatomy.terminals import ear, hook, spur, tail

__all__ = [
    "ENDPOINTS",
    "FACES",
    "PARTS",
    "POSITIONS",
    "SIDES",
    "BarSpec",
    "ParsedTag",
    "TagGrammarError",
    "arch",
    "bowl",
    "bowl_join",
    "crossbar",
    "crossing",
    "diagonal_pair",
    "dot",
    "drop",
    "ear",
    "hook",
    "is_valid_tag",
    "open_bowl",
    "parse_tag",
    "spine",
    "spur",
    "stem",
    "tail",
]
