"""æ ø Æ Ø outlines."""

from __future__ import annotations

from typekernel.parts import DesignContext, FormSources


def test_extended_latin_opt_in() -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    assert "æ" not in controls.supported
    assert "æ" in controls.derive("æøÆØ")


def test_build_ae_oslash() -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    g = controls.derive("æøÆØ")
    base = controls.derive("ae")
    assert g["æ"].advance > base["a"].advance + base["e"].advance * 0.5
    assert len(g["ø"].solids) >= 2
