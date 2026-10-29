"""Anatomy — letter-free structural parts (target-architecture §4).

Parts return a single structural ``Drawing`` (stem, arch, bowl, …), never a
whole letter. Projects assemble glyphs in ``elements.py`` / ``glyphs/``.
"""

from __future__ import annotations

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

__all__ = [
    "ENDPOINTS",
    "FACES",
    "PARTS",
    "POSITIONS",
    "SIDES",
    "ParsedTag",
    "TagGrammarError",
    "crossbar",
    "dot",
    "drop",
    "is_valid_tag",
    "parse_tag",
    "stem",
]
