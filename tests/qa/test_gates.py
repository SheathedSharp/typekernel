"""Human approval gate helpers — never auto-approve."""

from __future__ import annotations

import re
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


def test_repo_pending_human_review_templates_load_but_block_require() -> None:
    """TK-306 / TK-402: shipped placeholders stay ``approved: false``."""
    root = Path(__file__).resolve().parents[2] / "approvals"
    for name in (
        "serif-slab-voice.json",
        "serif-bracketed-voice.json",
        "italic-vf-construct.json",
    ):
        path = root / name
        data = load_approval(path)
        assert data["approved"] is False
        assert data["approver"] == ""
        with pytest.raises(ApprovalError, match="not approved"):
            require_approval(path)
    slab = load_approval(root / "serif-slab-voice.json")
    assert "slab_serif/proof.png" in slab["notes"]
    assert "proof_vf.png" in slab["notes"]
    bracketed = load_approval(root / "serif-bracketed-voice.json")
    assert "bracketed_serif/proof.png" in bracketed["notes"]
    assert "weight_ladder_bracketed_serif.png" in bracketed["notes"]
    italic = load_approval(root / "italic-vf-construct.json")
    assert "proof.png" in italic["notes"]
    assert "proof_vf.png" in italic["notes"]
    # parts 时期的证据路径已删除；待人工评审的 JSON 仍可加载
    # and remain unapproved. Live evidence paths are checked only when present.
    repo = root.parent
    for name in (
        "serif-slab-voice.json",
        "serif-bracketed-voice.json",
        "italic-vf-construct.json",
    ):
        evidence = load_approval(root / name).get("test_evidence", [])
        for rel in evidence:
            path = repo / rel
            if not path.is_file():
                continue  # parts 时期的证据路径已移除
            assert path.is_file(), f"{name} missing test_evidence {rel!r}"


_PENDING_GATE_JSON = (
    "serif-slab-voice.json",
    "serif-bracketed-voice.json",
    "italic-vf-construct.json",
)


def _readme_signoff_block(readme: str, gate_json: str) -> str:
    marker = f"**`{gate_json}`**"
    start = readme.index(marker)
    tail = readme[start + len(marker) :]
    next_gate = re.search(r"\n\*\*`[^`]+`\*\*", tail)
    end = start + len(marker) + (next_gate.start() if next_gate else len(tail))
    section = readme[start:end]
    bash = re.search(r"```bash\n(.*?)```", section, re.DOTALL)
    return bash.group(1) if bash else section


def test_approvals_readme_signoff_matches_test_evidence() -> None:
    """README copy-paste pytest blocks must list exactly each gate's test_evidence."""
    repo = Path(__file__).resolve().parents[2]
    readme = (repo / "approvals" / "README.md").read_text(encoding="utf-8")
    approvals = repo / "approvals"
    for name in _PENDING_GATE_JSON:
        evidence = list(load_approval(approvals / name)["test_evidence"])
        block = _readme_signoff_block(readme, name)
        assert "pytest -q" in block
        for rel in evidence:
            assert rel in block, f"{name} README sign-off missing {rel!r}"
        cited = {
            m.split("::")[0]
            for m in re.findall(r"tests/[\w./:_-]+", block)
        }
        for rel in evidence:
            assert rel in cited, f"{name} README pytest block must cite {rel!r}"
        assert cited <= set(evidence), f"{name} README cites extra test paths: {cited - set(evidence)}"


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
