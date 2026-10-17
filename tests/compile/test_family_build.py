"""Feature-safe family assembly."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")

from typekernel.compile import FamilyBuildOptions, build_font, compose_font_from_controls
from typekernel.parts import Controls, DesignContext


def test_compose_liga_only_builds(tmp_path: Path) -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    font = compose_font_from_controls(
        controls,
        "Gate Test",
        options=FamilyBuildOptions(liga=True),
    )
    assert "fi" in font
    assert "sub f i by fi" in font.features
    assert "zero.tf" not in font.features
    build_font(font, tmp_path, formats=("otf",))


def test_compose_requires_body_unlock_by_default() -> None:
    """Stock sheets pass the gate; a thinned body letter must refuse compose."""
    from typekernel.qa.design_sequence import DesignSequenceError

    good = Controls.from_context(DesignContext.geometric_sans())
    font = compose_font_from_controls(good, "Unlocked")
    assert "n" in font

    # Bypass stock derivation: inject a conspicuously thin ``h`` master.
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph("h", lambda _n, _o, _ctx: thin.build("h"))
    with pytest.raises(DesignSequenceError, match="DesignSequence unlock"):
        compose_font_from_controls(broken, "Blocked")


def test_compose_allow_skip_unlock_for_stock_compile() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    font = compose_font_from_controls(
        controls,
        "SkipGate",
        options=FamilyBuildOptions(liga=True),
        require_body_unlock=False,
    )
    assert "fi" in font


def test_reference_kern_classes_requires_body_unlock() -> None:
    from typekernel.compile import reference_kern_classes
    from typekernel.qa.design_sequence import DesignSequenceError

    good = Controls.from_context(DesignContext.geometric_sans())
    assert reference_kern_classes(good)

    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph("h", lambda _n, _o, _ctx: thin.build("h"))
    with pytest.raises(DesignSequenceError):
        reference_kern_classes(broken)

    # Documented stock opt-out
    assert reference_kern_classes(broken, require_body_unlock=False)


def test_compose_requires_caps_unlock_when_caps_in_charset() -> None:
    """Default compose ships A–Z; a broken capital must refuse (not only body)."""
    from typekernel.qa.design_sequence import DesignSequenceError

    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph("H", lambda _n, _o, _ctx: thin.build("H"))
    with pytest.raises(DesignSequenceError, match="DesignSequence unlock"):
        compose_font_from_controls(broken, "CapsBlocked")


def test_compose_body_only_charset_skips_caps_gate() -> None:
    """Lowercase-only charset must not require unlock_caps."""
    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    # Broken H would fail caps unlock, but charset has no capitals.
    broken = good.with_glyph("H", lambda _n, _o, _ctx: thin.build("H"))
    font = compose_font_from_controls(
        broken,
        "BodyOnly",
        options=FamilyBuildOptions(chars="nhou", liga=False),
    )
    assert "n" in font
    assert "H" not in font


def test_compose_requires_digits_unlock_when_figures_in_charset() -> None:
    from typekernel.qa.design_sequence import DesignSequenceError

    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    # Control ``1`` stays stock; thin ``4`` must refuse digit unlock.
    broken = good.with_glyph("4", lambda _n, _o, _ctx: thin.build("4"))
    with pytest.raises(DesignSequenceError, match="DesignSequence unlock"):
        compose_font_from_controls(
            broken,
            "DigitsBlocked",
            options=FamilyBuildOptions(chars="n14", liga=False),
        )


def test_charset_unlock_needs() -> None:
    from typekernel.qa.design_sequence import charset_unlock_needs

    assert charset_unlock_needs("nho") == (True, False, False, False)
    assert charset_unlock_needs("nH") == (True, True, False, False)
    assert charset_unlock_needs("1") == (False, False, True, False)
    assert charset_unlock_needs(".,!") == (False, False, False, True)
    assert charset_unlock_needs("n.") == (True, False, False, True)


def test_compose_requires_punct_unlock_when_punct_in_charset() -> None:
    """Broken ``)`` must refuse compose when punct is in the charset."""
    from typekernel.qa.design_sequence import DesignSequenceError

    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph(")", lambda _n, _o, _ctx: thin.build(")"))
    with pytest.raises(DesignSequenceError, match="DesignSequence unlock"):
        compose_font_from_controls(
            broken,
            "PunctBlocked",
            options=FamilyBuildOptions(chars="n()", liga=False),
        )


def test_compose_letter_only_charset_skips_punct_gate() -> None:
    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph(")", lambda _n, _o, _ctx: thin.build(")"))
    font = compose_font_from_controls(
        broken,
        "NoPunct",
        options=FamilyBuildOptions(chars="nhou", liga=False),
    )
    assert "n" in font
