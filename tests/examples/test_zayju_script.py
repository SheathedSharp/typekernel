"""zayju_script skeleton face smoke (trace_letter, not FormSources pipeline)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "zayju_script"

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def _load_design():
    spec = importlib.util.spec_from_file_location("zayju_script_design", EXAMPLE / "design.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_zayju_script_charset_builds_and_lints_clean() -> None:
    """Sequential compose + style report builds the script charset without lint errors."""
    design = _load_design()
    ctx = design.script_context()
    charset, report = design.build_charset_sequential(ctx)
    assert report.passed, list(report.failures)
    assert set(charset) == set(design.CHARSET)
    from typekernel.qa.lint import lint_glyph

    for ch in design.CHARSET:
        issues = [
            i for i in lint_glyph(charset[ch], ctx, glyph_name=ch) if i.severity == "error"
        ]
        assert not issues, f"{ch}: {issues}"


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required for trace_letter union")
def test_zayju_script_build_script() -> None:
    pytest.importorskip("ufoLib2")
    proc = subprocess.run(
        [sys.executable, "build.py"],
        cwd=EXAMPLE,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "sentence_brief.png" in proc.stdout
    assert (EXAMPLE / "out" / "sentence_brief.png").is_file()


def test_zayju_script_sequential_style_gate_passes() -> None:
    """Charset must pass designer-order style consistency report."""
    from examples.zayju_script import design

    _drawn, report = design.build_charset_sequential()
    assert report.passed, [
        (r.reference_name, r.candidate_name, [c.name for c in r.failures])
        for r in report.failures
    ]
    assert "".join(report.unlocked) == "".join(design.DESIGN_ORDER)
