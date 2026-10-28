"""Master signature compatibility check plugin."""

from __future__ import annotations

from typekernel.plugins.checks.protocol import CheckContext, Finding, raw_drawing

__all__ = ["check"]


def check(ctx: CheckContext) -> None:
    """Error when a named master Drawing.signature differs from Regular."""
    project = ctx.project
    if not project.masters:
        return
    name = ctx.name
    base_sig = ctx.raw.signature()
    for master in project.masters:
        other_raw = raw_drawing(project, name, master=master.name)
        if other_raw.signature() != base_sig:
            ctx.findings.append(
                Finding(
                    "compat",
                    "error",
                    name,
                    f"signature mismatch vs master {master.name!r} "
                    f"(contours/segments/tags differ)",
                )
            )
