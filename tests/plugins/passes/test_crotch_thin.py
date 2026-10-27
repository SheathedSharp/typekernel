"""Contract tests for ``plugins.passes.crotch_thin``."""

from __future__ import annotations

import pytest

from typekernel.draw import Writer
from typekernel.plugins.passes import crotch_thin


def _vee():
    return (
        Writer()
        .start((0, 40))
        .line((20, 0))
        .node("crotch")
        .line((40, 40))
        .line((30, 40))
        .line((20, 15))
        .line((10, 40))
        .close()
        .build()
    )


def test_crotch_thin_moves_join() -> None:
    d = _vee()
    out = crotch_thin(d, at="crotch", amount=0.82)
    assert out.nodes == d.nodes
    assert out.slots == d.slots
    # Point at crotch should differ.
    from typekernel.draw.geomutil import segment_start

    idx = d.nodes[0][0].index
    before = segment_start(d.contours[0].segments[idx])
    after = segment_start(out.contours[0].segments[idx])
    assert before != after


def test_crotch_thin_amount_one_is_noop() -> None:
    d = _vee()
    out = crotch_thin(d, at="crotch", amount=1.0)
    idx = d.nodes[0][0].index
    from typekernel.draw.geomutil import segment_start

    assert segment_start(out.contours[0].segments[idx]) == segment_start(
        d.contours[0].segments[idx]
    )


def test_crotch_thin_missing_tag_raises() -> None:
    d = _vee()
    with pytest.raises(KeyError):
        crotch_thin(d, at="nope", amount=0.8)


def test_crotch_thin_deterministic() -> None:
    d = _vee()
    a = crotch_thin(d, at="crotch", amount=0.82)
    b = crotch_thin(d, at="crotch", amount=0.82)
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
