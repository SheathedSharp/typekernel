"""Every derived glyph keeps its topology from hairline to black — masters interpolate."""

from __future__ import annotations

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.font import Glyph
from typekernel.parts import Controls, DesignContext

PRESETS = (
    "geometric_sans",
    "humanist_sans",
    "mono",
    "display",
    "paper_ink",
    "code_clear",
    "open_print",
)


@pytest.mark.parametrize("preset", PRESETS)
def test_controls_family_interpolates_across_stems(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    families = [
        Controls.from_context(base.tuned(stem=s)).build_all() for s in (30.0, base.stem, 220.0)
    ]
    problems: dict[str, list[str]] = {}
    for ch in families[0]:
        outlines = [Glyph.from_composed(ch, f[ch]).outline for f in families]
        issues = check_interpolatable(outlines)
        if issues:
            problems[ch] = issues
    assert problems == {}


def test_tuned_counter_keeps_topology() -> None:
    ctx = DesignContext.code_clear()
    narrow = Controls.from_context(ctx).tuned_n(counter=200.0).tuned_o(rx=230.0).build_all()
    wide = Controls.from_context(ctx).tuned_n(counter=360.0).tuned_o(rx=330.0).build_all()
    for ch in narrow:
        a = Glyph.from_composed(ch, narrow[ch]).outline
        b = Glyph.from_composed(ch, wide[ch]).outline
        assert check_interpolatable([a, b]) == [], ch
