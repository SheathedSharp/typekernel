"""Join polish in compose_font."""

from __future__ import annotations

from typekernel.compile import FamilyBuildOptions, compose_font
from typekernel.parts import DesignContext, FormSources


def test_joins_policy_noop_skips_polish() -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    raw = controls.derive_one("f")
    font = compose_font(
        controls.derive("fno"),
        controls.context,
        "Polish Test",
        options=FamilyBuildOptions(joins_policy="noop"),
    )
    # noop: segment count unchanged vs raw draw (no tangent_fix remapping)
    assert len(font["f"].outline.contours[0].segments) == len(
        raw.solids[0].contours[0].segments
    )
