"""Drawing.signature and overlay tests (测试清单)."""

from __future__ import annotations

import pytest

from typekernel.draw import Writer


def _unit_square(*, tag_prefix: str = "sq"):
    return (
        Writer()
        .start((0, 0))
        .node(f"{tag_prefix}.origin")
        .line((10, 0))
        .line((10, 10))
        .line((0, 10))
        .close()
        .build()
    )


def test_signature_equal_for_same_structure_different_size() -> None:
    a = (
        Writer()
        .start((0, 0))
        .node("origin")
        .line((10, 0))
        .line((10, 10))
        .line((0, 10))
        .close()
        .build()
    )
    b = (
        Writer()
        .start((0, 0))
        .node("origin")
        .line((20, 0))
        .line((20, 20))
        .line((0, 20))
        .close()
        .build()
    )
    assert a.signature() == b.signature()


def test_signature_differs_when_extra_segment() -> None:
    a = (
        Writer()
        .start((0, 0))
        .line((10, 0))
        .line((10, 10))
        .line((0, 10))
        .close()
        .build()
    )
    b = (
        Writer()
        .start((0, 0))
        .line((5, 0))
        .line((10, 0))
        .line((10, 10))
        .line((0, 10))
        .close()
        .build()
    )
    assert a.signature() != b.signature()


def test_overlay_stacks_contours() -> None:
    left = _unit_square(tag_prefix="left")
    right = (
        Writer()
        .start((20, 0))
        .node("right.origin")
        .line((30, 0))
        .line((30, 10))
        .line((20, 10))
        .close()
        .build()
    )
    both = left + right
    assert len(both.contours) == 2
    assert both.point("left.origin").x == 0
    assert both.point("right.origin").x == 20


def test_overlay_tag_conflict_raises() -> None:
    a = _unit_square(tag_prefix="same")
    b = _unit_square(tag_prefix="same")
    with pytest.raises(ValueError, match="tag conflict"):
        _ = a + b
