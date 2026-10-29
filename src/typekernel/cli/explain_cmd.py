"""``tk explain`` — GlyphReport as text or JSON."""

from __future__ import annotations

import json
from pathlib import Path

from typekernel.perceive.explain import GlyphReport, explain
from typekernel.project import open_project

__all__ = ["explain_project", "format_report"]


def explain_project(
    path: str | Path,
    glyph: str,
    *,
    master: str | None = None,
) -> GlyphReport:
    with open_project(path) as session:
        return explain(session, glyph, master=master)


def format_report(report: GlyphReport, *, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)
    lines = [
        f"glyph: {report.glyph}"
        + (f"  master={report.master}" if report.master else ""),
        f"hash: {report.outline_hash}",
        f"bbox: {report.bbox}",
        f"advance: {report.advance}  lsb={report.lsb}  rsb={report.rsb}",
        (
            f"topology: counters={report.counters} islands={report.islands} "
            f"slits={report.slit_counters}"
        ),
        f"ink_density: {report.ink_density:.4f}",
        f"nodes: {len(report.nodes)}  measures: {len(report.measures)}",
    ]
    if report.traits:
        lines.append(f"traits: {', '.join(report.traits)}")
    if report.note:
        lines.append(f"note: {report.note}")
    for m in report.measures:
        lines.append(
            f"  measure {m.kind} {m.a}"
            + (f"–{m.b}" if m.b else "")
            + f" measured={m.measured} expected={m.expected}"
        )
    return "\n".join(lines)
