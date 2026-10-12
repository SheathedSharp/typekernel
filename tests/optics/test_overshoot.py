"""Tests for minimal vertical overshoot."""

from pathlib import Path

from tests.optics._bounds_helpers import outline_ymax, outline_ymin
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.optics.context import OpticalContext
from typekernel.optics.overshoot import apply_overshoot

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def test_round_overshoot_raises_synthetic_o_ymax() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=12.0)
    before_max = outline_ymax(outline)
    before_min = outline_ymin(outline)
    after_outline = apply_overshoot(outline, ctx, kind="round")

    assert outline_ymax(after_outline) == before_max + 12.0
    assert outline_ymin(after_outline) == before_min - 12.0
    # Input not mutated.
    assert outline_ymax(outline) == before_max
    assert outline_ymin(outline) == before_min


def test_zero_overshoot_is_identity_bounds() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=0.0)
    after = apply_overshoot(outline, ctx, kind="round")
    assert outline_ymax(after) == outline_ymax(outline)
    assert outline_ymin(after) == outline_ymin(outline)


def test_sharp_uses_overshoot_sharp() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=12.0, overshoot_sharp=4.0)
    before_max = outline_ymax(outline)
    before_min = outline_ymin(outline)
    after = apply_overshoot(outline, ctx, kind="sharp")
    assert outline_ymax(after) == before_max + 4.0
    assert outline_ymin(after) == before_min - 4.0


def test_overshoot_module_has_no_buffer_or_shapely_imports() -> None:
    source = Path(__file__).parents[2] / "src" / "typekernel" / "optics" / "overshoot.py"
    text = source.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith(("import ", "from ")):
            lower = stripped.lower()
            assert "shapely" not in lower
            assert "buffer" not in lower


def test_zone_mode_skips_descender_only_ymin() -> None:
    """Round extrema on the baseline must not drag a separate descender foot."""
    from typekernel.geo.path_builder import PathBuilder

    b = PathBuilder()
    # Oval on baseline: y in [0, 160]
    b.addEllipse(100, 80, 80, 80)
    # Sharp descender rectangle far below
    b.moveTo(40, -200)
    b.lineTo(60, -200)
    b.lineTo(60, -180)
    b.lineTo(40, -180)
    b.closePath()
    outline = b.build()
    ctx = OpticalContext(x_height=160.0, cap_height=700.0, overshoot_round=12.0)
    after = apply_overshoot(outline, ctx, kind="round", align_to_zones=True)
    assert outline_ymin(after) == -200.0
    assert outline_ymax(after) == 172.0


def test_legacy_global_mode_still_available() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=12.0)
    after = apply_overshoot(outline, ctx, kind="round", align_to_zones=False)
    assert outline_ymax(after) == outline_ymax(outline) + 12.0
