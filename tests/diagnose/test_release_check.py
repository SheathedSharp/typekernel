"""P4-7: H-class release checks and tk check --release."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufo2ft")

from typekernel.cli.build import build_project
from typekernel.cli.check_cmd import check_release_project
from typekernel.diagnose.release import check_release_binary


def test_latin_sans_h_class_clean(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    _font, built = build_project(root, out_dir=tmp_path, formats=("ttf",))
    binary = built.binaries["ttf"]
    findings = check_release_binary(binary)
    errors = [f for f in findings if f.level == "error"]
    assert errors == [], "; ".join(f.message for f in errors)


def test_tk_check_release_writes_manifest(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    code, manifest = check_release_project(
        root, out_dir=tmp_path, fontbakery=False, build_if_missing=True
    )
    assert manifest is not None and manifest.is_file()
    # H-class alone should pass; FontBakery skipped.
    assert code == 0


def test_fontbakery_opentype_zero_fail(tmp_path: Path) -> None:
    import importlib.util

    if importlib.util.find_spec("fontbakery") is None:
        pytest.skip("fontbakery not installed")
    from typekernel.diagnose.release import check_release

    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    _font, built = build_project(root, out_dir=tmp_path, formats=("ttf",))
    report = check_release(built.binaries["ttf"], fontbakery=True)
    assert report.fontbakery is not None
    assert report.fontbakery_fail_count == 0, report.fontbakery
