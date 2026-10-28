"""Intent / Brief → System mapping and contradiction checks."""

from __future__ import annotations

import pytest

from typekernel.system import (
    Brief,
    Intent,
    Overshoot,
    System,
    Zones,
    apply_intent,
    check_intent,
    system_from_intent,
)
from typekernel.system.intent import (
    CONTRAST_TO_PEN,
    SLANT_TO_VALUE,
    WEIGHT_TO_LC,
    coerce_intent,
)


def test_system_from_intent_uses_published_tables() -> None:
    intent = Intent(
        contrast="high",
        slant="steep",
        openness="open",
        weight="light",
        pen_angle_deg=40.0,
    )
    s = system_from_intent(intent)
    assert s.slant == SLANT_TO_VALUE["steep"]
    assert s.stem["lc"] == WEIGHT_TO_LC["light"]
    assert s.tokens["pen_contrast"] == CONTRAST_TO_PEN["high"]
    assert s.tokens["pen_angle_deg"] == 40.0
    assert check_intent(s, intent) == []


def test_apply_intent_preserves_unrelated_tokens() -> None:
    base = System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80, "lc_h": 70, "uc": 90},
        tokens={"custom_flag": 1.0, "n_width": 400.0},
        slant=0.0,
    )
    out = apply_intent(base, Intent(contrast="medium", slant="italic", openness="normal", weight="regular"))
    assert out.tokens["custom_flag"] == 1.0
    assert out.slant == pytest.approx(0.18)
    assert out.tokens["pen_contrast"] == CONTRAST_TO_PEN["medium"]
    assert "n_width" in out.tokens


def test_check_intent_flags_contradiction() -> None:
    intent = Intent(contrast="high", slant="italic", openness="normal", weight="regular")
    # high contrast expects pen_contrast in [0.12, 0.40]; 0.82 is low-contrast
    bad = system_from_intent(Intent(contrast="low", slant="italic", openness="normal", weight="regular"))
    mismatches = check_intent(bad, intent)
    fields = {m.field for m in mismatches}
    assert "contrast" in fields


def test_check_intent_upright_rejects_lean() -> None:
    intent = Intent(slant="upright")
    s = system_from_intent(Intent(slant="italic"))
    mismatches = check_intent(s, intent)
    assert any(m.field == "slant" for m in mismatches)


def test_coerce_intent_accepts_brief_and_mapping() -> None:
    brief = Brief(prose="demo face", intent=Intent(contrast="low"))
    assert coerce_intent(brief) == brief.intent
    assert coerce_intent({"contrast": "high", "slant": "steep"}).contrast == "high"
    assert coerce_intent(None) is None


def test_intent_is_not_an_aesthetics_score_api() -> None:
    """Guard: no style_consistency / originality knobs on Intent."""
    assert not hasattr(Intent, "style_consistency")
    assert not hasattr(Intent, "originality")
    assert not hasattr(Brief, "score")
