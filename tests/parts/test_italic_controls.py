"""Italic control sheet keeps topology."""

from __future__ import annotations

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.parts import Controls, DesignContext
from typekernel.parts.italic import italic_controls


def test_italic_and_regular_interpolate() -> None:
    ctx = DesignContext.code_clear()
    reg = Controls.from_context(ctx).build_all("a")
    ital = italic_controls(Controls.from_context(ctx)).build_all("a")
    assert check_interpolatable([reg["a"].solids[0], ital["a"].solids[0]]) == []
