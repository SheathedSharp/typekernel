"""TK-403: true italic branching vs construct oblique."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.italic import italic_design, slant_composed_glyph
from typekernel.qa.lint import lint_glyph


def test_italic_n_outline_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.humanist_sans())
    sheared = slant_composed_glyph(reg.build_all("n")["n"], 10.0)
    italic = italic_design(reg).build_all("n")["n"]
    assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_h_outline_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.code_clear())
    sheared = slant_composed_glyph(reg.build_all("h")["h"], 10.0)
    italic = italic_design(reg).build_all("h")["h"]
    assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_branching_n_lint_clean() -> None:
    controls = italic_design(Controls.from_context(DesignContext.geometric_sans()))
    for ch in "nhrum":
        issues = lint_glyph(controls.build_all(ch)[ch], controls.context, glyph_name=ch)
        assert not [i for i in issues if i.severity == "error"]


def test_italic_ru_topology_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.humanist_sans())
    for ch in "ru":
        sheared = slant_composed_glyph(reg.build_all(ch)[ch], 10.0)
        italic = italic_design(reg).build_all(ch)[ch]
        assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)
