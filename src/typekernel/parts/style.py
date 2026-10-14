"""Discrete style DNA for family-wide glyph topology choices (TK-305)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal

AForm = Literal["single", "double"]
GForm = Literal["single", "double"]
LTail = Literal["none", "tailed"]
YTail = Literal["straight", "curved"]
IDot = Literal["round", "square", "diamond"]
TCut = Literal["flat", "slanted"]

__all__ = [
    "DEFAULT_STYLE",
    "AForm",
    "GForm",
    "IDot",
    "LTail",
    "Style",
    "TCut",
    "YTail",
]


@dataclass(frozen=True, slots=True)
class Style:
    """High-leverage discrete switches; defaults match pre-TK-305 behaviour."""

    a_form: AForm = "single"
    g_form: GForm = "single"
    l_tail: LTail = "none"
    y_tail: YTail = "straight"
    i_dot: IDot = "round"
    t_cut: TCut = "flat"

    def tuned(self, **kwargs: Any) -> Style:
        return replace(self, **kwargs)


DEFAULT_STYLE = Style()
