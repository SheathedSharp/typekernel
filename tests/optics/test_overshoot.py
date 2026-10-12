"""Tests for minimal vertical overshoot."""

from pathlib import Path

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import bounds
from typekernel.optics.context import OpticalContext
from typekernel.optics.overshoot import apply_overshoot

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def test_round_overshoot_raises_synthetic_o_ymax() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=12.0)
    before = bounds(outline)
    after_outline = apply_overshoot(outline, ctx, kind="round")
    after = bounds(after_outline)

    assert after[3] == before[3] + 12.0  # max_y
    assert after[1] == before[1] - 12.0  # min_y
    # Input not mutated.
    assert bounds(outline) == before


def test_zero_overshoot_is_identity_bounds() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=0.0)
    after = apply_overshoot(outline, ctx, kind="round")
    assert bounds(after) == bounds(outline)


def test_sharp_uses_overshoot_sharp() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=12.0, overshoot_sharp=4.0)
    before = bounds(outline)
    after = bounds(apply_overshoot(outline, ctx, kind="sharp"))
    assert after[3] == before[3] + 4.0
    assert after[1] == before[1] - 4.0


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
