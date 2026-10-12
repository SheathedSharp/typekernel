"""Human approval records for visual / API gates.

Helpers read and write JSON under ``approvals/``. Nothing here marks a gate as
approved automatically — ``write_approval`` only persists what a caller
(typically a human or an agent acting on explicit human say-so) already decided.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("gate", "approved", "approver", "date", "notes")


class ApprovalError(LookupError):
    """Raised when an approval record is missing or not approved."""


def write_approval(
    path: str | Path,
    *,
    gate: str,
    approved: bool,
    approver: str,
    date: str,
    notes: str = "",
    **extra: Any,
) -> Path:
    """Write an approval JSON file.

    Required fields are always written. Additional keyword arguments are merged
    into the document (for example ``scope`` or ``test_evidence``). The file is
    created or overwritten; parent directories are created as needed.

    This function does **not** decide approval — it only records the values
    passed in.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    document: dict[str, Any] = {
        "gate": gate,
        "approved": bool(approved),
        "approver": approver,
        "date": date,
        "notes": notes,
    }
    document.update(extra)
    destination.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination


def load_approval(path: str | Path) -> dict[str, Any]:
    """Load an approval JSON document.

    Raises:
        FileNotFoundError: if ``path`` does not exist.
        TypeError: if required fields have the wrong type.
        ValueError: if required fields are missing or empty where non-empty is required.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"approval document must be a JSON object: {path}")
    _validate_schema(data, path=path)
    return data


def require_approval(path: str | Path) -> dict[str, Any]:
    """Load ``path`` and require ``approved`` to be true.

    Raises:
        ApprovalError: if the file is missing or ``approved`` is not true.
        TypeError: if the document fails type checks.
        ValueError: if the document fails schema checks.
    """
    try:
        data = load_approval(path)
    except FileNotFoundError as exc:
        raise ApprovalError(f"approval record not found: {path}") from exc
    if data.get("approved") is not True:
        raise ApprovalError(f"gate not approved: {path}")
    return data


def _validate_schema(data: dict[str, Any], *, path: str | Path) -> None:
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(f"approval missing required field {field!r}: {path}")
    if not isinstance(data["gate"], str):
        raise TypeError(f"approval 'gate' must be a string: {path}")
    if not data["gate"]:
        raise ValueError(f"approval 'gate' must be a non-empty string: {path}")
    if not isinstance(data["approved"], bool):
        raise TypeError(f"approval 'approved' must be a boolean: {path}")
    if not isinstance(data["approver"], str):
        raise TypeError(f"approval 'approver' must be a string: {path}")
    if not isinstance(data["date"], str):
        raise TypeError(f"approval 'date' must be a string: {path}")
    if not data["date"]:
        raise ValueError(f"approval 'date' must be a non-empty string: {path}")
    if not isinstance(data["notes"], str):
        raise TypeError(f"approval 'notes' must be a string: {path}")
