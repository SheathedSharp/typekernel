"""System per-glyph width/advance token lint."""

from __future__ import annotations

from typekernel.system import (
    CONTROL_WIDTH_TOKENS,
    Overshoot,
    System,
    Zones,
    lint_per_glyph_metric_tokens,
)


def _system(**tokens: float) -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80},
        tokens=dict(tokens),
    )


def test_control_widths_allowed() -> None:
    tokens = {name: 400.0 for name in CONTROL_WIDTH_TOKENS}
    assert lint_per_glyph_metric_tokens(_system(**tokens)) == []


def test_per_glyph_width_and_advance_warn() -> None:
    got = lint_per_glyph_metric_tokens(
        _system(n_width=430, a_width=400, fig_advance=500, shoulder_tension=0.5)
    )
    assert got == ["a_width", "fig_advance"]


def test_latin_sans_system_lint_clean() -> None:
    from typekernel.starters.latin_sans.system import system

    assert lint_per_glyph_metric_tokens(system) == []
