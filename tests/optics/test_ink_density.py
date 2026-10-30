"""Scanline side-column ink density (partial Tracy gray cue)."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.optics.context import OpticalContext
from typekernel.optics.space import (
    measure_side_ink_density,
    suggest_sidebearings_ink_density,
)


def _box(*, width: float, height: float = 500.0, x0: float = 0.0):
    return (
        Writer()
        .start((x0, 0.0))
        .line((x0 + width, 0.0))
        .line((x0 + width, height))
        .line((x0, height))
        .close()
        .build()
        .outline()
    )


def test_flush_box_side_density_high() -> None:
    outline = _box(width=200.0)
    d = measure_side_ink_density(
        outline, "left", y0=0.0, y1=500.0, column=40.0, samples=9
    )
    assert d > 0.9


def test_ink_density_suggests_more_air_for_dense_side() -> None:
    ctx = OpticalContext(units_per_em=1000.0, x_height=500.0, cap_height=700.0)
    # Solid box vs box with left notch (less left-column ink).
    solid = _box(width=300.0)
    notched = (
        Writer()
        .start((0.0, 0.0))
        .line((300.0, 0.0))
        .line((300.0, 500.0))
        .line((0.0, 500.0))
        .line((0.0, 350.0))
        .line((80.0, 350.0))
        .line((80.0, 150.0))
        .line((0.0, 150.0))
        .close()
        .build()
        .outline()
    )
    s_lsb, _ = suggest_sidebearings_ink_density(solid, ctx)
    n_lsb, _ = suggest_sidebearings_ink_density(notched, ctx)
    assert s_lsb >= n_lsb
