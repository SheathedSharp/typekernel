"""TK-302: stress axis rotates the thin point on round strokes."""

from __future__ import annotations

import math

import pytest

from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts import Controls, DesignContext
from typekernel.parts.control import o_metrics
from typekernel.qa.thickness import measurement_outline


def _thinnest_ring_angle_deg(glyph, m: object) -> float:
    outline = measurement_outline(glyph)
    cx, cy = m.rx, m.x_height / 2.0
    best_angle = 0.0
    best_w = float("inf")
    for deg in range(0, 360, 2):
        rad = math.radians(deg)
        px = cx + m.rx * 0.82 * math.cos(rad)
        py = cy + m.ry * 0.82 * math.sin(rad)
        tang = deg + 90.0
        w = measure_oriented_stem(outline, (px, py), tang)
        if w is not None and w < best_w:
            best_w = w
            best_angle = float(deg)
    return best_angle


def _near(angle: float, target: float, tol: float = 22.0) -> bool:
    return min(abs(angle - target), abs(angle - target + 360.0), abs(angle - target - 360.0)) <= tol


def test_stress_zero_preserves_preset_outline_hashes() -> None:
    """Default stress must not move golden presets."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    for preset in ("humanist_sans", "geometric_sans", "code_clear"):
        ctx = getattr(DesignContext, preset)()
        assert ctx.stress == 0.0
        controls = Controls.from_context(ctx)
        hashes = {ch: composed_glyph_hash(controls.build_all(ch)[ch]) for ch in "oce"}
        controls2 = Controls.from_context(ctx.tuned(stress=0.0))
        hashes2 = {ch: composed_glyph_hash(controls2.build_all(ch)[ch]) for ch in "oce"}
        assert hashes == hashes2


def test_stress_zero_preserves_lowercase_s_hashes() -> None:
    """Default stress must not move golden ``s`` on main presets."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    for preset in ("humanist_sans", "geometric_sans", "code_clear"):
        ctx = getattr(DesignContext, preset)()
        assert ctx.stress == 0.0
        controls = Controls.from_context(ctx)
        h0 = composed_glyph_hash(controls.build("s"))
        h1 = composed_glyph_hash(Controls.from_context(ctx.tuned(stress=0.0)).build("s"))
        assert h0 == h1


@pytest.mark.parametrize("ch", ("2", "3", "5", "6", "8", "9"))
def test_stress_zero_preserves_lining_figure_hashes(ch: str) -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    for preset in ("humanist_sans", "geometric_sans", "code_clear"):
        ctx = getattr(DesignContext, preset)()
        h0 = composed_glyph_hash(Controls.from_context(ctx).build(ch))
        h1 = composed_glyph_hash(Controls.from_context(ctx.tuned(stress=0.0)).build(ch))
        assert h0 == h1


@pytest.mark.parametrize("ch", ("2", "3", "5", "6", "8", "9"))
def test_stress_moves_lining_figure_outline(ch: str) -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    ctx = DesignContext.geometric_sans().tuned(contrast=0.55, stem=90.0)
    g0 = Controls.from_context(ctx).build(ch)
    g35 = Controls.from_context(ctx.tuned(stress=35.0)).build(ch)
    assert composed_glyph_hash(g0) != composed_glyph_hash(g35)


def test_stress_moves_lowercase_s_outline() -> None:
    ctx = DesignContext.geometric_sans().tuned(contrast=0.55, stem=90.0)
    from typekernel.qa.outline_hash import composed_glyph_hash

    g0 = Controls.from_context(ctx).build("s")
    g35 = Controls.from_context(ctx.tuned(stress=35.0)).build("s")
    assert composed_glyph_hash(g0) != composed_glyph_hash(g35)


def test_stress_moves_thinnest_point_on_o() -> None:
    ctx0 = DesignContext.geometric_sans().tuned(contrast=0.55, stem=90.0, stress=0.0)
    ctx45 = ctx0.tuned(stress=45.0)
    g0 = Controls.from_context(ctx0).build_all("o")["o"]
    g45 = Controls.from_context(ctx45).build_all("o")["o"]
    m0 = o_metrics(ctx0)
    m45 = o_metrics(ctx45)
    a0 = _thinnest_ring_angle_deg(g0, m0)
    a45 = _thinnest_ring_angle_deg(g45, m45)
    assert _near(a0, 90.0) or _near(a0, 270.0)
    thin_rot = (a0 + 45.0) % 360.0
    assert _near(a45, thin_rot, tol=32.0) or _near(a45, (thin_rot + 180.0) % 360.0, tol=32.0)


@pytest.mark.parametrize("preset", ("humanist_sans", "geometric_sans", "code_clear"))
def test_supported_charset_builds_under_moderate_stress(preset: str) -> None:
    """TK-302: opening ``o`` derivatives must build when inner rings are rotated."""
    ctx = getattr(DesignContext, preset)()
    if preset == "geometric_sans":
        ctx = ctx.tuned(contrast=0.55, stem=90.0)
    controls = Controls.from_context(ctx.tuned(stress=35.0))
    for ch in controls.supported:
        controls.build(ch)
