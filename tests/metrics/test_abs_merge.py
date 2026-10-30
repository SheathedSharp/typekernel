"""with_abs_sidebearings merges Abs without mutating the source Metrics."""

from __future__ import annotations

from typekernel.metrics import Abs, Metrics, Stem, with_abs_sidebearings


def test_with_abs_sidebearings_pure_merge() -> None:
    base = Metrics(keys={"n": (Stem("lc", 0.9), Stem("lc", 0.9))})
    out = with_abs_sidebearings(base, {"n": (40.0, 42.0), "o": (30.0, 31.0)})
    assert "n" in base.keys
    assert isinstance(base.keys["n"][0], Stem)
    assert isinstance(out.keys["n"][0], Abs)
    assert out.keys["n"][0].value == 40.0
    assert out.keys["n"][1].value == 42.0
    assert out.keys["o"] == (Abs(30.0), Abs(31.0))
