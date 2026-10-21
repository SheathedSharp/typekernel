"""Hook letters with inline crossbar contours (f/t weight interpolation)."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.parts import DesignContext, FormSources

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pathops") is None,
    reason="skia-pathops required for crossbar union",
)


def test_f_single_solid_contour() -> None:
    f = FormSources.from_context(DesignContext.code_clear()).derive_one("f")
    assert len(f.solids) == 1


def test_f_interpolates_across_weight() -> None:
    outlines = []
    for stem in (86.0, 140.0):
        ctx = DesignContext.code_clear().tuned(stem=stem)
        sheet = FormSources.from_context(ctx)
        if stem > 100:
            sheet = sheet.with_stem_relief()
        outlines.append(sheet.derive_one("f").solids[0])
    problems = check_interpolatable(outlines)
    assert problems == []
