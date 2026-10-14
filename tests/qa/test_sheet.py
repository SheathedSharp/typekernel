"""Contact sheet helpers."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.qa.sheet import contact_sheet, review_index

pytest.importorskip("PIL")


def test_contact_sheet_writes(tmp_path) -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    path = contact_sheet(controls, tmp_path / "contact.png", chars="noa")
    assert path.is_file()
    assert path.stat().st_size > 500


def test_review_index(tmp_path) -> None:
    p = tmp_path / "a.png"
    p.write_bytes(b"x")
    index = review_index(tmp_path, {"sample": p})
    assert index.is_file()
    assert "sample" in index.read_text()
