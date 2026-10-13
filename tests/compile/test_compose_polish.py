"""Join polish in compose_font_from_controls."""

from __future__ import annotations

from typekernel.compile import FamilyBuildOptions, compose_font_from_controls
from typekernel.parts import Controls, DesignContext


def test_joins_policy_noop_skips_polish() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    raw = controls.build("f")
    font = compose_font_from_controls(
        controls,
        "Polish Test",
        options=FamilyBuildOptions(chars="f", joins_policy="noop"),
    )
    # noop: segment count unchanged vs raw draw (no tangent_fix remapping)
    assert len(font["f"].outline.contours[0].segments) == len(
        raw.solids[0].contours[0].segments
    )
