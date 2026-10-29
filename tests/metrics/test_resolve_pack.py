"""Metrics resolve / pack (P1-4)."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.font.font import Font
from typekernel.font.glyph import Glyph
from typekernel.geo.outline import bounds
from typekernel.metrics import (
    Abs,
    Metrics,
    Mirror,
    Ref,
    Stem,
    apply_metrics,
    pack,
    resolve,
)
from typekernel.system import Overshoot, System, Zones


def _system(**tokens: float) -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 100, "uc": 120},
        tokens=dict(tokens),
    )


def _rect_glyph(name: str, x0: float, x1: float, y0: float = 0.0, y1: float = 500.0) -> Glyph:
    drawing = (
        Writer()
        .start((x0, y0))
        .line((x1, y0))
        .line((x1, y1))
        .line((x0, y1))
        .close()
        .build()
    )
    return Glyph(name=name, outline=drawing.outline(), advance=x1 - x0)


def test_resolve_stem_ref_mirror() -> None:
    metrics = Metrics(
        keys={
            "n": (Stem("lc", 0.9), Stem("lc", 0.9)),
            "h": (Ref("n", "lsb"), Mirror()),
            "r": (Ref("n", "lsb"), Abs(40)),
        }
    )
    got = resolve(metrics, _system())
    assert got["n"] == (90.0, 90.0)
    assert got["h"] == (90.0, 90.0)
    assert got["r"] == (90.0, 40.0)


def test_resolve_cycle_raises() -> None:
    metrics = Metrics(
        keys={
            "a": (Ref("b", "lsb"), Abs(1)),
            "b": (Ref("a", "lsb"), Abs(1)),
        }
    )
    try:
        resolve(metrics, _system())
    except ValueError as exc:
        assert "unresolved" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_pack_bbox_sets_lsb_and_advance() -> None:
    g = _rect_glyph("n", 10, 110)
    packed = pack(g, 40, 50, _system(), policy="bbox")
    min_x, _, _max_x, _ = bounds(packed.outline)
    assert min_x == 40.0
    assert packed.advance == 40 + 100 + 50


def test_apply_metrics_writes_space_and_sidebearings() -> None:
    system = _system(space_advance=250.0)
    font = Font.from_system(system, "T", "Regular")
    font.add_glyph(_rect_glyph("n", 0, 100), replace=True)
    metrics = Metrics(keys={"n": (Stem("lc", 0.5), Stem("lc", 0.5))})
    apply_metrics(font, metrics, system)
    min_x, _, _max_x, _ = bounds(font["n"].outline)
    assert min_x == 50.0
    assert font["n"].advance == 50 + 100 + 50
    assert font["space"].advance == 250.0
