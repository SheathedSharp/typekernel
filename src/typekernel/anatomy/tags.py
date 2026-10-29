"""Tag grammar for anatomy / diagnosis (ARCHITECTURE.md 标签语法).

Grammar (normative)::

    tag      := part ( "." qualifier )*
    part     := stem | arch | bowl | join | bar | diag | spine | hook
              | tail | ear | spur | cross | dot | drop | aperture | serif | mark
    qualifier:= side | position | face | index
    side     := l | r | t | b
    position := foot | top | crown | apex | vertex | crotch | entry | exit | stress
    face     := o | i
    endpoint:= a | b          # aperture ends only
    index    := [0-9]+

``a`` / ``b`` mark aperture endpoints (see ``aperture.N.a`` / ``aperture.N.b``).
When ``b`` appears under part ``aperture`` (or after an index) it is an endpoint,
not the side ``b`` (bottom).
``spur`` and ``cross`` are part names for P3-4 / P3-5 components.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "ENDPOINTS",
    "FACES",
    "PARTS",
    "POSITIONS",
    "SIDES",
    "ParsedTag",
    "TagGrammarError",
    "is_valid_tag",
    "parse_tag",
]

PARTS: frozenset[str] = frozenset(
    {
        "stem",
        "arch",
        "bowl",
        "join",
        "bar",
        "diag",
        "spine",
        "hook",
        "tail",
        "ear",
        "spur",
        "cross",
        "dot",
        "drop",
        "aperture",
        "serif",
        "mark",
    }
)
SIDES: frozenset[str] = frozenset({"l", "r", "t", "b"})
POSITIONS: frozenset[str] = frozenset(
    {
        "foot",
        "top",
        "crown",
        "apex",
        "vertex",
        "crotch",
        "entry",
        "exit",
        "stress",
    }
)
# o/i = outer/inner.
FACES: frozenset[str] = frozenset({"o", "i"})
# a/b = aperture endpoints (disambiguated from side ``b``).
ENDPOINTS: frozenset[str] = frozenset({"a", "b"})

_INDEX = re.compile(r"^[0-9]+$")
_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$|^[0-9]+$")


class TagGrammarError(ValueError):
    """Raised when ``parse_tag`` is given a non-conforming tag."""


@dataclass(frozen=True, slots=True)
class ParsedTag:
    """Structured view of a conforming tag."""

    raw: str
    part: str
    sides: tuple[str, ...]
    positions: tuple[str, ...]
    faces: tuple[str, ...]
    endpoints: tuple[str, ...]
    indices: tuple[str, ...]


def _classify(token: str, *, part: str, saw_index: bool) -> str:
    # aperture.N.a / .b — endpoint wins over side ``b``.
    if token in ENDPOINTS and (part == "aperture" or saw_index or token == "a"):
        return "endpoint"
    if token in SIDES:
        return "side"
    if token in POSITIONS:
        return "position"
    if token in FACES:
        return "face"
    if _INDEX.match(token):
        return "index"
    return "unknown"


def is_valid_tag(tag: str) -> bool:
    """Return whether ``tag`` matches the normative grammar."""
    try:
        parse_tag(tag)
    except TagGrammarError:
        return False
    return True


def parse_tag(tag: str) -> ParsedTag:
    """Parse ``tag`` or raise :class:`TagGrammarError`."""
    if not tag or not isinstance(tag, str):
        raise TagGrammarError(f"empty or non-string tag: {tag!r}")
    if tag != tag.strip() or ".." in tag or tag.startswith(".") or tag.endswith("."):
        raise TagGrammarError(f"malformed tag: {tag!r}")
    parts = tag.split(".")
    head, *rest = parts
    if head not in PARTS:
        raise TagGrammarError(f"unknown part {head!r} in tag {tag!r}")
    sides: list[str] = []
    positions: list[str] = []
    faces: list[str] = []
    endpoints: list[str] = []
    indices: list[str] = []
    for token in rest:
        if not _TOKEN.match(token):
            raise TagGrammarError(f"illegal qualifier {token!r} in tag {tag!r}")
        kind = _classify(token, part=head, saw_index=bool(indices))
        if kind == "side":
            sides.append(token)
        elif kind == "position":
            positions.append(token)
        elif kind == "face":
            faces.append(token)
        elif kind == "endpoint":
            endpoints.append(token)
        elif kind == "index":
            indices.append(token)
        else:
            raise TagGrammarError(f"unknown qualifier {token!r} in tag {tag!r}")
    return ParsedTag(
        raw=tag,
        part=head,
        sides=tuple(sides),
        positions=tuple(positions),
        faces=tuple(faces),
        endpoints=tuple(endpoints),
        indices=tuple(indices),
    )
