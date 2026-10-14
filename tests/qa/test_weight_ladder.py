"""R8 counter pinch across the weight ladder (TK-207)."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.weight_relief import STEM_RELIEF_ONSET
from typekernel.qa.lint import lint_controls

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pathops") is None,
    reason="lint needs skia-pathops",
)

_LADDER_STEMS = (30.0, 70.0, 110.0, 150.0, 180.0, 200.0)


@pytest.mark.parametrize("stem", _LADDER_STEMS)
def test_counter_pinch_charset_passes_r8(stem: float) -> None:
    ctx = DesignContext.humanist_sans().tuned(stem=stem)
    controls = Controls.from_context(ctx)
    if stem >= STEM_RELIEF_ONSET:
        controls = controls.with_stem_relief()
    report = lint_controls(controls, counter_min=True)
    r8 = [i for i in report.issues if i.rule == "R8_counter_min"]
    assert not r8, r8
