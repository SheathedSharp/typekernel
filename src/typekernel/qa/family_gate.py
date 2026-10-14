"""Charset-wide quality gate (lint + identity) for shipped glyph sets."""

from __future__ import annotations

from typekernel.parts.family import Controls
from typekernel.qa.identity import check_identity_controls
from typekernel.qa.lint import lint_controls

FAMILY_GATE_VERSION = "1"

__all__ = [
    "FAMILY_GATE_VERSION",
    "check_family_gate",
    "collect_family_gate_failures",
]


def collect_family_gate_failures(
    controls: Controls,
    charset: str | None = None,
) -> list[str]:
    """Return human-readable failures for lint/identity errors on ``charset``."""
    wanted = charset if charset is not None else controls.supported
    if not wanted:
        return ["empty charset"]
    failures: list[str] = []
    lint_report = lint_controls(controls, wanted)
    for issue in lint_report.errors:
        failures.append(f"{issue.glyph}: lint {issue.rule} — {issue.detail}")
    identity_report = check_identity_controls(controls, wanted)
    for id_issue in identity_report.errors:
        failures.append(f"{id_issue.glyph}: identity {id_issue.rule} — {id_issue.detail}")
    return failures


def check_family_gate(
    controls: Controls,
    charset: str | None = None,
    *,
    baseline: Controls | None = None,
    masters: tuple[Controls, ...] | None = None,
) -> list[str]:
    """Lint + identity on the declared charset (and optional extra masters).

    ``baseline`` is reserved for future regression compares; unused today.
    """
    _ = baseline
    failures: list[str] = []
    sheets = masters if masters is not None else (controls,)
    for sheet in sheets:
        label = f"stem={sheet.context.stem:.0f}"
        for msg in collect_family_gate_failures(sheet, charset):
            failures.append(f"[{label}] {msg}")
    return failures
