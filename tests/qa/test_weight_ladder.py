"""R8 counter pinch across the weight ladder (TK-207)."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.parts import DesignContext, FormSources
from typekernel.parts.weight_relief import STEM_RELIEF_ONSET
from typekernel.qa.lint import lint_controls
from typekernel.qa.trial_protocol import WEIGHT_LADDER_STEMS

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pathops") is None,
    reason="lint needs skia-pathops",
)

_LADDER_STEMS = WEIGHT_LADDER_STEMS


@pytest.mark.parametrize(
    "preset",
    (
        "humanist_sans",
        "code_clear",
        "geometric_sans",
        "mono",
        "display",
        "paper_ink",
        "open_print",
        "slab_serif",
        "bracketed_serif",
    ),
)
@pytest.mark.parametrize("stem", _LADDER_STEMS)
def test_counter_pinch_charset_passes_r8(preset: str, stem: float) -> None:
    ctx = getattr(DesignContext, preset)().tuned(stem=stem)
    controls = FormSources.from_context(ctx)
    if stem >= STEM_RELIEF_ONSET:
        controls = controls.with_stem_relief()
    report = lint_controls(controls, counter_min=True)
    r8 = [i for i in report.issues if i.rule == "R8_counter_min"]
    assert not r8, r8


@pytest.mark.parametrize(
    "preset",
    (
        "humanist_sans",
        "code_clear",
        "geometric_sans",
        "mono",
        "display",
        "paper_ink",
        "open_print",
    ),
)
@pytest.mark.parametrize("stem", _LADDER_STEMS)
def test_angled_terminal_counter_pinch_charset_passes_r8(
    preset: str, stem: float
) -> None:
    """TK-304: ``terminal_style=angled`` must not re-open R8 pinches on the ladder."""
    ctx = getattr(DesignContext, preset)().tuned(stem=stem, terminal_style="angled")
    controls = FormSources.from_context(ctx)
    if stem >= STEM_RELIEF_ONSET:
        controls = controls.with_stem_relief()
    report = lint_controls(controls, counter_min=True)
    r8 = [i for i in report.issues if i.rule == "R8_counter_min"]
    assert not r8, r8


@pytest.mark.parametrize("terminal_style", ("ball", "flared"))
@pytest.mark.parametrize(
    "preset",
    (
        "humanist_sans",
        "code_clear",
        "geometric_sans",
        "mono",
        "display",
        "paper_ink",
        "open_print",
    ),
)
@pytest.mark.parametrize("stem", _LADDER_STEMS)
def test_alt_terminal_counter_pinch_charset_passes_r8(
    terminal_style: str, preset: str, stem: float
) -> None:
    """TK-304: ``ball`` / ``flared`` must not re-open R8 pinches on the ladder."""
    ctx = getattr(DesignContext, preset)().tuned(
        stem=stem, terminal_style=terminal_style
    )
    controls = FormSources.from_context(ctx)
    if stem >= STEM_RELIEF_ONSET:
        controls = controls.with_stem_relief()
    report = lint_controls(controls, counter_min=True)
    r8 = [i for i in report.issues if i.rule == "R8_counter_min"]
    assert not r8, r8
