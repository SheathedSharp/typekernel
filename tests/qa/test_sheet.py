"""Contact sheet helpers."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.qa.sheet import contact_sheet, review_index, weight_ladder_sheet

pytest.importorskip("PIL")


def test_contact_sheet_writes(tmp_path) -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    path = contact_sheet(controls, tmp_path / "contact.png", chars="noa")
    assert path.is_file()
    assert path.stat().st_size > 500


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
