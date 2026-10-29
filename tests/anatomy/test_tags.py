"""Tag grammar parser tests (ARCHITECTURE.md 标签语法 / P3-1)."""

from __future__ import annotations

import pytest

from typekernel.anatomy import tags as T
from typekernel.anatomy.tags import (
    PARTS,
    ParsedTag,
    TagGrammarError,
    is_valid_tag,
    parse_tag,
)


def _side(name: str) -> str:
    assert name in T.SIDES
    return name


def _face(name: str) -> str:
    assert name in T.FACES
    return name


def _end(name: str) -> str:
    assert name in T.ENDPOINTS
    return name


@pytest.mark.parametrize(
    "tag,part,sides,positions,faces,endpoints,indices",
    [
        ("stem.l.foot.o", "stem", ("l",), ("foot",), ("o",), (), ()),
        ("arch.crown.o", "arch", (), ("crown",), ("o",), (), ()),
        ("join.crotch.r", "join", ("r",), ("crotch",), (), (), ()),
        ("aperture.0.a", "aperture", (), (), (), ("a",), ("0",)),
        ("aperture.0.b", "aperture", (), (), (), ("b",), ("0",)),
        ("bar.l.top", "bar", ("l",), ("top",), (), (), ()),
        ("diag.vertex", "diag", (), ("vertex",), (), (), ()),
        ("hook.exit", "hook", (), ("exit",), (), (), ()),
        ("spur", "spur", (), (), (), (), ()),
        ("cross", "cross", (), (), (), (), ()),
        ("stem", "stem", (), (), (), (), ()),
        ("stem.b.foot", "stem", ("b",), ("foot",), (), (), ()),
    ],
)
def test_parse_valid(
    tag: str,
    part: str,
    sides: tuple[str, ...],
    positions: tuple[str, ...],
    faces: tuple[str, ...],
    endpoints: tuple[str, ...],
    indices: tuple[str, ...],
) -> None:
    # Validate expected qualifier letters against the grammar sets (not glyph tables).
    for s in sides:
        _side(s)
    for f in faces:
        _face(f)
    for e in endpoints:
        _end(e)
    parsed = parse_tag(tag)
    assert isinstance(parsed, ParsedTag)
    assert parsed.part == part
    assert parsed.sides == sides
    assert parsed.positions == positions
    assert parsed.faces == faces
    assert parsed.endpoints == endpoints
    assert parsed.indices == indices
    assert is_valid_tag(tag)


@pytest.mark.parametrize(
    "tag",
    [
        "",
        "arm.l.top",
        "stem.l.bot",
        "bar.bl",
        "cup.l.outer",
        "paren.top.o",
        "stem..foot",
        ".stem",
        "stem.",
        "unknown.l",
        "stem.l.foot.outer",
        "J.hook.stem.l",
    ],
)
def test_parse_invalid(tag: str) -> None:
    assert not is_valid_tag(tag)
    with pytest.raises(TagGrammarError):
        parse_tag(tag)


def test_parts_cover_architecture_list() -> None:
    required = {
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
        "dot",
        "drop",
        "aperture",
        "serif",
        "mark",
    }
    assert required <= PARTS
