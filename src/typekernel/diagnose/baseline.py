"""Audit baseline: accepted warns with reasons; hash change invalidates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typekernel.diagnose.protocol import Finding

__all__ = ["Baseline", "BaselineEntry", "load_baseline", "save_baseline"]


@dataclass(frozen=True, slots=True)
class BaselineEntry:
    check: str
    glyph: str | None
    message: str
    reason: str
    outline_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "glyph": self.glyph,
            "message": self.message,
            "reason": self.reason,
            "outline_hash": self.outline_hash,
        }


@dataclass
class Baseline:
    entries: list[BaselineEntry] = field(default_factory=list)

    def filter(
        self,
        findings: list[Finding],
        *,
        hashes: dict[str, str] | None = None,
    ) -> list[Finding]:
        """Drop warn findings that match a still-valid baseline entry.

        Errors are never baselined. An entry whose ``outline_hash`` no longer
        matches the live glyph hash is ignored (stale).
        """
        hashes = hashes or {}
        active: list[BaselineEntry] = []
        for entry in self.entries:
            if not entry.reason.strip():
                continue  # reason required
            if entry.outline_hash and entry.glyph:
                live = hashes.get(entry.glyph)
                if live is not None and live != entry.outline_hash:
                    continue  # invalidated
            active.append(entry)

        kept: list[Finding] = []
        for f in findings:
            if f.level == "error":
                kept.append(f)
                continue
            if f.level != "warn":
                kept.append(f)
                continue
            matched = False
            for entry in active:
                if entry.check != f.check:
                    continue
                if entry.glyph != f.glyph:
                    continue
                if entry.message != f.message:
                    continue
                matched = True
                break
            if not matched:
                kept.append(f)
        return kept


def load_baseline(path: Path | str) -> Baseline:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    entries_raw = raw.get("entries", raw if isinstance(raw, list) else [])
    entries: list[BaselineEntry] = []
    for item in entries_raw:
        reason = str(item.get("reason", "")).strip()
        if not reason:
            raise ValueError("baseline entry missing required 'reason'")
        entries.append(
            BaselineEntry(
                check=str(item["check"]),
                glyph=item.get("glyph"),
                message=str(item["message"]),
                reason=reason,
                outline_hash=item.get("outline_hash"),
            )
        )
    return Baseline(entries=entries)


def save_baseline(path: Path | str, baseline: Baseline) -> Path:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {"entries": [e.to_dict() for e in baseline.entries]}
    dest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dest
