"""Anatomy — letter-free structural parts (target-architecture §4).

Parts return a single structural ``Drawing`` (stem, arch, bowl, …), never a
whole letter. Projects assemble glyphs in ``elements.py`` / ``glyphs/``.

Pen / skeleton construction for italic starters lives in
:mod:`typekernel.anatomy.pen`. S4 script DSL:
:mod:`typekernel.anatomy.stroke` (``Stroke.through``, entry/exit/loop).
"""

from __future__ import annotations

from typekernel.anatomy.curves import BarSpec, arch, bowl, bowl_join, open_bowl, spine
from typekernel.anatomy.diagonal import crossing, diagonal_pair
from typekernel.anatomy.straight import crossbar, dot, drop, stem
from typekernel.anatomy.stroke import (
    Stroke,
    entry,
    exit,
    expand_pointed,
    expand_stroke,
    loop,
    overstroke,
)
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
    "Stroke",
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
    "entry",
    "exit",
    "expand_pointed",
    "expand_stroke",
    "hook",
    "is_valid_tag",
    "loop",
    "open_bowl",
    "overstroke",
    "parse_tag",
    "spine",
    "spur",
    "stem",
    "tail",
]
