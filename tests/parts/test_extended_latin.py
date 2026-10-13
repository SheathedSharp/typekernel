"""æ ø Æ Ø outlines."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext


def test_extended_latin_opt_in() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    assert "æ" not in controls.supported
    assert "æ" in controls.build_all("æøÆØ")


def test_build_ae_oslash() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    g = controls.build_all("æøÆØ")
    base = controls.build_all("ae")
    assert g["æ"].advance > base["a"].advance + base["e"].advance * 0.5
    assert len(g["ø"].solids) >= 2
