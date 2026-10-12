"""Human approval gate helpers — never auto-approve."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.qa.gates import ApprovalError, load_approval, require_approval, write_approval


def test_write_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "sample-gate.json"
    write_approval(
        path,
        gate="sample-gate",
        approved=True,
        approver="zayju",
        date="2026-10-12",
        notes="looks fine",
        scope="unit-test",
    )
    data = load_approval(path)
    assert data["gate"] == "sample-gate"
    assert data["approved"] is True
    assert data["approver"] == "zayju"
    assert data["date"] == "2026-10-12"
    assert data["notes"] == "looks fine"
    assert data["scope"] == "unit-test"


def test_require_approval_passes_when_true(tmp_path: Path) -> None:
    path = tmp_path / "ok.json"
    write_approval(
        path,
        gate="ok",
        approved=True,
        approver="zayju",
        date="2026-10-12",
        notes="",
    )
    assert require_approval(path)["approved"] is True


def test_require_approval_raises_when_false(tmp_path: Path) -> None:
    path = tmp_path / "no.json"
    write_approval(
        path,
        gate="no",
        approved=False,
        approver="zayju",
        date="2026-10-12",
        notes="not yet",
    )
    with pytest.raises(ApprovalError, match="not approved"):
        require_approval(path)


def test_require_approval_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(ApprovalError, match="not found"):
        require_approval(tmp_path / "missing.json")


def test_load_rejects_missing_field(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"gate": "x", "approved": true}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="missing required field"):
        load_approval(path)


def test_write_approval_does_not_force_true(tmp_path: Path) -> None:
    """Recording approved=False must stay False — no auto-approve."""
    path = tmp_path / "pending.json"
    write_approval(
        path,
        gate="pending",
        approved=False,
        approver="",
        date="2026-10-12",
        notes="awaiting human",
    )
    assert load_approval(path)["approved"] is False
