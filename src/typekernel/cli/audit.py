"""``tk audit`` — argparse-facing re-exports of :mod:`typekernel.diagnose`.

Engine logic lives in ``typekernel.diagnose``. This module keeps the historical
import path (``from typekernel.cli.audit import audit_project``) working.
"""

from __future__ import annotations

from typekernel.diagnose.engine import (
    AuditReport,
    _kinds_for,
    audit_project,
    format_report,
    load_audit_stems,
    load_extra_checks,
    load_intent,
)
from typekernel.diagnose.protocol import Finding

__all__ = [
    "AuditReport",
    "Finding",
    "_kinds_for",
    "audit_project",
    "format_report",
    "load_audit_stems",
    "load_extra_checks",
    "load_intent",
]
