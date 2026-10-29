"""Space advance coefficients are project tokens, not library letter law."""

from __future__ import annotations

from typekernel.font.font import Font
from typekernel.metrics import Metrics, Token, apply_metrics
from typekernel.system import Overshoot, System, Zones


def test_sans_and_humanist_declare_space_tokens() -> None:
    from typekernel.starters.latin_humanist_italic.system import system as hum
    from typekernel.starters.latin_sans.system import system as sans

    for s in (sans, hum):
        assert "space_stem_mul" in s.tokens
        assert "space_lsb_mul" in s.tokens


def test_space_advance_absolute_token_override() -> None:
    system = System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80, "uc": 90},
        tokens={"space_advance": 333.0, "lsb_lc": 40},
    )
    font = Font.from_system(system, "Tok", "Regular")
    apply_metrics(font, Metrics(keys={}, space=Token("space_advance")), system)
    assert font["space"].advance == 333.0
