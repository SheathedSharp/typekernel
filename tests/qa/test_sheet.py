"""Contact sheet helpers."""

from __future__ import annotations

import pytest

from typekernel.parts import DesignContext, FormSources
from typekernel.qa.sheet import contact_sheet, diff_overlay, review_index, weight_ladder_sheet

pytest.importorskip("PIL")


def test_contact_sheet_writes(tmp_path) -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    path = contact_sheet(controls, tmp_path / "contact.png", chars="noa")
    assert path.is_file()
    assert path.stat().st_size > 500


def test_contact_sheet_full_charset_width_at_most_1600(tmp_path) -> None:
    """TK-104: agent-preview sheets stay within the documented width cap."""
    from PIL import Image

    controls = FormSources.from_context(DesignContext.humanist_sans())
    path = contact_sheet(controls, tmp_path / "full.png")
    with Image.open(path) as image:
        assert image.width <= 1600


def test_diff_overlay_writes(tmp_path) -> None:
    trial = FormSources.from_context(DesignContext.slab_serif())
    baseline = FormSources.from_context(DesignContext.humanist_sans())
    path = diff_overlay(trial, baseline, tmp_path / "diff.png", chars="m")
    assert path.is_file()
    assert path.stat().st_size > 200


def test_weight_ladder_sheet_writes(tmp_path) -> None:
    pytest.importorskip("ufo2ft")
    path = weight_ladder_sheet(
        DesignContext.humanist_sans(),
        tmp_path / "ladder.png",
        chars="aemn",
        stems=(70.0, 110.0),
    )
    assert path.is_file()
    assert path.stat().st_size > 500
    assert not (tmp_path / "_ladder_tmp").exists()


def test_review_index(tmp_path) -> None:
    p = tmp_path / "a.png"
    p.write_bytes(b"x")
    index = review_index(tmp_path, {"sample": p})
    assert index.is_file()
    assert "sample" in index.read_text()
