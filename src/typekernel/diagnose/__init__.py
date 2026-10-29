"""Diagnose — check engine v2, baselines, topology/spacing/gray checks (target §7)."""

from __future__ import annotations

from typekernel.diagnose.baseline import Baseline, BaselineEntry, load_baseline, save_baseline
from typekernel.diagnose.engine import AuditReport, audit_project, format_report
from typekernel.diagnose.protocol import Check, CheckContext, Finding

__all__ = [
    "AuditReport",
    "Baseline",
    "BaselineEntry",
    "Check",
    "CheckContext",
    "Finding",
    "audit_project",
    "format_report",
    "load_baseline",
    "save_baseline",
]
