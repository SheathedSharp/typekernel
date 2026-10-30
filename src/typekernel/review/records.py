"""Review records bound to outline hashes (target §8.1).

S0 evidence gate: ``verdict=pass`` requires proof-image hashes. Agent
self-passes are stored but surface as ``agent-pass (unverified)`` in
``tk status`` and do not satisfy the release exit gate.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

from typekernel.project.session import ProjectSession
from typekernel.qa.outline_hash import outline_hash

__all__ = [
    "EvidenceRequired",
    "ReviewRecord",
    "is_agent_reviewer",
    "is_stale",
    "latest_pass",
    "open_review",
    "proof_file_hash",
    "record_review",
]

Verdict = Literal["pending", "pass", "fail"]


class EvidenceRequired(ValueError):
    """Raised when ``verdict=pass`` is missing required evidence."""


def is_agent_reviewer(reviewer: str) -> bool:
    """True when the reviewer string is an agent (not ``human:…``)."""
    return not str(reviewer).startswith("human:")


def proof_file_hash(path: str | Path) -> str:
    """SHA-256 hex digest of a proof image (or any evidence file)."""
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


@dataclass
class ReviewRecord:
    group: str
    round: int
    reviewer: str
    verdict: Verdict
    masters: list[str] = field(default_factory=list)
    glyphs: dict[str, str] = field(default_factory=dict)
    proofs: list[str] = field(default_factory=list)
    reads_as: dict[str, str] = field(default_factory=dict)
    expect_changes: list[str] = field(default_factory=list)
    notes: str = ""
    date: str = field(default_factory=lambda: date.today().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewRecord:
        raw_verdict = str(data.get("verdict", "pending"))
        verdict: Verdict
        if raw_verdict == "pass":
            verdict = "pass"
        elif raw_verdict == "fail":
            verdict = "fail"
        else:
            verdict = "pending"
        reads = data.get("reads_as") or {}
        return cls(
            group=str(data["group"]),
            round=int(data.get("round", 1)),
            reviewer=str(data.get("reviewer", "")),
            verdict=verdict,
            masters=list(data.get("masters", [])),
            glyphs=dict(data.get("glyphs", {})),
            proofs=list(data.get("proofs", [])),
            reads_as={str(k): str(v) for k, v in dict(reads).items()},
            expect_changes=list(data.get("expect_changes", [])),
            notes=str(data.get("notes", "")),
            date=str(data.get("date", date.today().isoformat())),
        )

    @property
    def has_proof_evidence(self) -> bool:
        return any(str(p).strip() for p in self.proofs)


def _reviews_dir(session: ProjectSession) -> Path:
    path = Path(session.root) / "reviews"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _group_glyphs(session: ProjectSession, group: str) -> list[str]:
    policy = session.project.review
    if group in policy.groups:
        return list(policy.groups[group])
    names = [n for n, spec in session.specs().items() if spec.group == group]
    if names:
        return sorted(names)
    if group in session.specs():
        return [group]
    raise KeyError(f"unknown review group {group!r}")


def _current_hashes(session: ProjectSession, names: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in names:
        g = session.glyph(name)
        out[name] = outline_hash(g.outline)
    for name in session.specs():
        draft = session.evaluate(name)
        for comp in draft.components:
            if comp.base in names:
                out[name] = outline_hash(session.glyph(name).outline)
    return out


def _next_round(reviews_dir: Path, group: str) -> int:
    existing = list(reviews_dir.glob(f"{group}-r*.json"))
    rounds = []
    for path in existing:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rounds.append(int(data.get("round", 0)))
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return (max(rounds) if rounds else 0) + 1


def _require_pass_evidence(
    *,
    proofs: Sequence[str],
    reads_as: Mapping[str, str] | None,
    require_reads_as: bool,
) -> None:
    if not any(str(p).strip() for p in proofs):
        raise EvidenceRequired(
            "verdict=pass requires evidence: at least one proof image hash "
            "(pass --proof PATH or --proof-hash HEX). Empty proofs: [] is refused."
        )
    if require_reads_as and not reads_as:
        raise EvidenceRequired(
            "verdict=pass requires per-glyph reads_as evidence when --require-reads-as "
            "is set (or when reads_as is expected). Provide --reads-as JSON."
        )


def open_review(
    session: ProjectSession,
    group: str,
    *,
    reviewer: str = "agent:unknown",
) -> ReviewRecord:
    """Write a pending review template for ``group``; return the record."""
    if reviewer.startswith("human:") is False and "approved" in reviewer:
        raise ValueError("reviewer must not write human approvals")
    names = _group_glyphs(session, group)
    reviews_dir = _reviews_dir(session)
    rnd = _next_round(reviews_dir, group)
    record = ReviewRecord(
        group=group,
        round=rnd,
        reviewer=reviewer,
        verdict="pending",
        masters=[m.name for m in session.project.masters],
        glyphs=_current_hashes(session, names),
        notes="",
    )
    path = reviews_dir / f"{group}-r{rnd}.json"
    path.write_text(
        json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def record_review(
    session: ProjectSession,
    group: str,
    *,
    verdict: Verdict,
    note: str = "",
    reviewer: str = "agent:unknown",
    proofs: Sequence[str] | None = None,
    proof_paths: Sequence[str | Path] | None = None,
    reads_as: Mapping[str, str] | None = None,
    require_reads_as: bool = False,
) -> ReviewRecord:
    """Write a pass/fail review with current outline hashes.

    ``verdict=pass`` requires non-empty proof hashes (file SHA-256 or hex).
    Per-glyph ``reads_as`` is optional unless ``require_reads_as=True`` (S2+).
    """
    if verdict not in ("pass", "fail", "pending"):
        raise ValueError(f"invalid verdict {verdict!r}")
    if "approved" in note.lower() and "true" in note.lower():
        raise ValueError("refusing to write approved:true via review record")
    if reviewer.startswith("human:") and verdict == "pass":
        raise ValueError(
            "refusing human: reviewer via tk review; write approvals/ manually"
        )

    proof_hashes: list[str] = [str(p).strip() for p in (proofs or ()) if str(p).strip()]
    for raw in proof_paths or ():
        proof_hashes.append(proof_file_hash(raw))

    if verdict == "pass":
        _require_pass_evidence(
            proofs=proof_hashes,
            reads_as=reads_as,
            require_reads_as=require_reads_as,
        )

    names = _group_glyphs(session, group)
    reviews_dir = _reviews_dir(session)
    rnd = _next_round(reviews_dir, group)
    record = ReviewRecord(
        group=group,
        round=rnd,
        reviewer=reviewer,
        verdict=verdict,
        masters=[m.name for m in session.project.masters],
        glyphs=_current_hashes(session, names),
        proofs=proof_hashes,
        reads_as={str(k): str(v) for k, v in dict(reads_as or {}).items()},
        notes=note,
    )
    path = reviews_dir / f"{group}-r{rnd}.json"
    path.write_text(
        json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def latest_pass(session: ProjectSession, group: str) -> ReviewRecord | None:
    reviews_dir = Path(session.root) / "reviews"
    if not reviews_dir.is_dir():
        return None
    best: ReviewRecord | None = None
    for path in reviews_dir.glob(f"{group}-r*.json"):
        try:
            rec = ReviewRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        if rec.verdict != "pass":
            continue
        if best is None or rec.round > best.round:
            best = rec
    return best


def is_stale(session: ProjectSession, group: str) -> tuple[bool, list[str]]:
    """Return (stale?, changed glyph names) vs latest pass hashes."""
    passed = latest_pass(session, group)
    if passed is None:
        return True, _group_glyphs(session, group)
    names = list(passed.glyphs.keys())
    names = sorted(set(names) | set(_group_glyphs(session, group)))
    live = _current_hashes(session, names)
    changed = [n for n, h in live.items() if passed.glyphs.get(n) != h]
    for n in names:
        if n not in passed.glyphs:
            changed.append(n)
    return (len(changed) > 0, sorted(set(changed)))
