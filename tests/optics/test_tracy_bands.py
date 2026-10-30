"""Multi-band silhouette sidebearings (partial Tracy; not gray-value)."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.optics.context import OpticalContext
from typekernel.optics.space import (
    suggest_sidebearings_optical,
    suggest_sidebearings_tracy_bands,
)


def _box(*, width: float, height: float = 500.0):
    return (
        Writer()
        .start((0.0, 0.0))
        .line((width, 0.0))
        .line((width, height))
        .line((0.0, height))
        .close()
        .build()
        .outline()
    )


def _notched(*, width: float = 400.0, height: float = 500.0, notch: float = 80.0):
    """Rectangle with a mid-height left notch (extra whitespace on left mid-band)."""
    mid0, mid1 = height * 0.35, height * 0.70
    return (
        Writer()
        .start((0.0, 0.0))
        .line((width, 0.0))
        .line((width, height))
        .line((0.0, height))
        .line((0.0, mid1))
        .line((notch, mid1))
        .line((notch, mid0))
        .line((0.0, mid0))
        .close()
        .build()
        .outline()
    )


def test_tracy_bands_flush_box_equals_target_air() -> None:
    ctx = OpticalContext(units_per_em=1000.0, x_height=500.0, cap_height=700.0)
    lsb, rsb = suggest_sidebearings_tracy_bands(_box(width=200.0), ctx)
    assert lsb == rsb == 100.0  # ratio 0.2 * x_height; zero inset


def test_tracy_bands_notch_reduces_needed_lsb() -> None:
    ctx = OpticalContext(units_per_em=1000.0, x_height=500.0, cap_height=700.0)
    lsb, rsb = suggest_sidebearings_tracy_bands(_notched(), ctx)
    # Left mid-band already has whitespace → larger left inset → smaller LSB.
    assert lsb < rsb


def test_tracy_bands_finite_and_near_optical() -> None:
    ctx = OpticalContext(units_per_em=1000.0, x_height=500.0, cap_height=700.0)
    outline = _notched()
    lsb, rsb = suggest_sidebearings_tracy_bands(outline, ctx)
    assert lsb >= 0.0 and rsb >= 0.0
    o_lsb, o_rsb = suggest_sidebearings_optical(outline, ctx)
    assert abs(lsb - o_lsb) < 80.0
    assert abs(rsb - o_rsb) < 80.0
