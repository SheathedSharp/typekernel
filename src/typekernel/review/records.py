"""Review records bound to outline hashes (target §8.1)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

from typekernel.project.session import ProjectSession
from typekernel.qa.outline_hash import outline_hash

__all__ = ["ReviewRecord", "is_stale", "latest_pass", "open_review", "record_review"]

Verdict = Literal["pending", "pass", "fail"]


@dataclass
class ReviewRecord:
    group: str
    round: int
    reviewer: str
    verdict: Verdict
    masters: list[str] = field(default_factory=list)
    glyphs: dict[str, str] = field(default_factory=dict)
    proofs: list[str] = field(default_factory=list)
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
        return cls(
            group=str(data["group"]),
            round=int(data.get("round", 1)),
            reviewer=str(data.get("reviewer", "")),
            verdict=verdict,
            masters=list(data.get("masters", [])),
            glyphs=dict(data.get("glyphs", {})),
            proofs=list(data.get("proofs", [])),
            expect_changes=list(data.get("expect_changes", [])),
            notes=str(data.get("notes", "")),
            date=str(data.get("date", date.today().isoformat())),
        )


def _reviews_dir(session: ProjectSession) -> Path:
    path = Path(session.root) / "reviews"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _group_glyphs(session: ProjectSession, group: str) -> list[str]:
    policy = session.project.review
    if group in policy.groups:
        return list(policy.groups[group])
    # Fall back: GlyphSpec.group == group, or the single glyph named group.
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
        # Include composites that reference this glyph.
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
    path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def record_review(
    session: ProjectSession,
    group: str,
    *,
    verdict: Verdict,
    note: str = "",
    reviewer: str = "agent:unknown",
) -> ReviewRecord:
    """Write a pass/fail review with current outline hashes."""
    if verdict not in ("pass", "fail", "pending"):
        raise ValueError(f"invalid verdict {verdict!r}")
    # Two-level gate: tools refuse writing approved:true (human approvals).
    if "approved" in note.lower() and "true" in note.lower():
        raise ValueError("refusing to write approved:true via review record")
    if reviewer.startswith("human:") and verdict == "pass":
        # Agent may not impersonate human approver for milestones.
        raise ValueError(
            "refusing human: reviewer via tk review; write approvals/ manually"
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
        notes=note,
    )
    path = reviews_dir / f"{group}-r{rnd}.json"
    path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    # Also recompute group membership + composites.
    names = sorted(set(names) | set(_group_glyphs(session, group)))
    live = _current_hashes(session, names)
    changed = [
        n for n, h in live.items() if passed.glyphs.get(n) != h
    ]
    # Glyphs that disappeared from pass record but are in group.
    for n in names:
        if n not in passed.glyphs:
            changed.append(n)
    return (len(changed) > 0, sorted(set(changed)))
