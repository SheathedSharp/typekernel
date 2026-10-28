"""``tk audit`` — stem / zone / direction / master-compat diagnostics (ARCH §3.3).

Reports are diagnostic by default. Structural errors (wrong contour direction,
master signature mismatch) raise the process exit code. Stem / zone deviations
are warnings for the designer to fix in glyph code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from typekernel.cli.load import load_project
from typekernel.draw import Drawing
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.stem import list_vertical_stems
from typekernel.project import Project
from typekernel.system import System

__all__ = ["AuditReport", "audit_project", "format_report"]


@dataclass
class Finding:
    kind: str  # stem | zone | direction | compat
    level: str  # error | warn | info
    glyph: str
    message: str


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)
    glyphs: int = 0

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warn"]


def _raw_drawing(project: Project, name: str, *, master: str | None = None) -> Drawing:
    """Pre-slot drawing so named corner nodes remain measurable."""
    spec = project.specs()[name]
    system = project.system
    build = spec.build
    if master is not None:
        by = {m.name: m for m in project.masters}
        if master in by:
            system = by[master].system
        if master in spec.masters:
            build = spec.masters[master]
    return build(system)


def _audit_direction(name: str, drawing: Drawing, findings: list[Finding]) -> None:
    """Outer ink should be CCW (positive area); counters CW (negative)."""
    for i, (contour, role) in enumerate(zip(drawing.contours, drawing.roles, strict=True)):
        if not contour.segments:
            continue
        area = signed_area(contour)
        if role == "ink" and area < 0:
            findings.append(
                Finding(
                    "direction",
                    "error",
                    name,
                    f"contour[{i}] role=ink has CW winding (area={area:.1f})",
                )
            )
        elif role == "counter" and area > 0:
            findings.append(
                Finding(
                    "direction",
                    "error",
                    name,
                    f"contour[{i}] role=counter has CCW winding (area={area:.1f})",
                )
            )


def _stem_from_nodes(drawing: Drawing, prefix: str) -> float | None:
    """Width between ``{prefix}.foot.o`` and ``{prefix}.foot.i`` when both exist."""
    try:
        a = drawing.point(f"{prefix}.foot.o")
        b = drawing.point(f"{prefix}.foot.i")
    except KeyError:
        return None
    return abs(float(b.x) - float(a.x))


def _audit_stem(
    name: str,
    drawing: Drawing,
    system: System,
    findings: list[Finding],
    *,
    tol_ratio: float = 0.08,
) -> None:
    expected_lc = float(system.stem.get("lc", 0.0))
    expected_uc = float(system.stem.get("uc", expected_lc))
    is_uc = len(name) == 1 and name.isupper()
    stem_target = expected_uc if is_uc else expected_lc
    # Prefer named stem.l / stem.r / stem nodes from elements.
    measured: list[tuple[str, float, float]] = []
    for prefix, expected in (
        ("stem.l", stem_target),
        ("stem.r", stem_target),
        ("stem", stem_target),
        ("stem.L", expected_uc),
        ("stem.R", expected_uc),
    ):
        w = _stem_from_nodes(drawing, prefix)
        if w is not None:
            measured.append((prefix, w, expected))

    if not measured and (len(name) == 1 or name in {"zero", "one", "four", "seven"}):
        # Optical fallback only for simple letter/figure shapes; skip dashes etc.
        # Sample several y bands and keep the band whose near-stem spans sit
        # closest to System.stem — mid crossbars (E/F/H) + even-odd overlap
        # otherwise thin the reading at 0.5× zone.
        outline = drawing.outline()
        zone = float(system.zones.cap if is_uc else system.zones.x)
        best: list = []
        best_score = float("inf")
        for frac in (0.32, 0.5, 0.68):
            try:
                spans = list_vertical_stems(outline, y=zone * frac)
            except Exception:
                continue
            near = []
            for span in spans:
                if span.width <= 0:
                    continue
                # Ignore counter gaps, full-width bars, and contrast-thin cuts
                # from elliptical broad nibs (often ~0.5× stem).
                if abs(span.width - stem_target) / stem_target > 0.25:
                    continue
                near.append(span)
            if not near:
                continue
            score = sum(abs(s.width - stem_target) for s in near) / len(near)
            if score < best_score:
                best_score = score
                best = near
        for span in best:
            measured.append(("optical", span.width, stem_target))

    for label, got, expected in measured:
        if expected <= 0:
            continue
        err = abs(got - expected) / expected
        if err > tol_ratio:
            findings.append(
                Finding(
                    "stem",
                    "warn",
                    name,
                    f"{label} width {got:.1f} vs System {expected:.1f} ({err:.0%})",
                )
            )


def _audit_zone(
    name: str,
    drawing: Drawing,
    system: System,
    findings: list[Finding],
    *,
    tol: float = 24.0,
) -> None:
    outline = drawing.outline()
    if not outline.contours or not any(c.segments for c in outline.contours):
        return
    try:
        _minx, min_y, _maxx, max_y = bounds(outline)
    except ValueError:
        return
    ov = float(system.overshoot.round)
    # Baseline / descender floor
    if min_y < float(system.zones.desc) - tol:
        findings.append(
            Finding(
                "zone",
                "warn",
                name,
                f"ymin {min_y:.1f} below desc {system.zones.desc} (tol {tol})",
            )
        )
    # Ascender / cap ceiling (allow overshoot)
    ceiling = max(float(system.zones.asc), float(system.zones.cap)) + ov + tol
    if max_y > ceiling:
        findings.append(
            Finding(
                "zone",
                "warn",
                name,
                f"ymax {max_y:.1f} above zones+overshoot ({ceiling:.1f})",
            )
        )
    # Round letters should overshoot x-height / baseline a little when tagged.
    # Soft info only when ymax sits exactly on a flat zone with no overshoot room used.
    if name in {"o", "O", "c", "e", "a"} and abs(max_y - float(system.zones.x if name.islower() else system.zones.cap)) < 1.0:
        findings.append(
            Finding(
                "zone",
                "info",
                name,
                "round glyph max sits on flat zone — consider overshoot",
            )
        )


def _audit_compat(project: Project, name: str, findings: list[Finding]) -> None:
    if not project.masters:
        return
    base = _raw_drawing(project, name)
    base_sig = base.signature()
    for master in project.masters:
        other = _raw_drawing(project, name, master=master.name)
        if other.signature() != base_sig:
            findings.append(
                Finding(
                    "compat",
                    "error",
                    name,
                    f"signature mismatch vs master {master.name!r} "
                    f"(contours/segments/tags differ)",
                )
            )


def audit_project(
    root: str | Path,
    *,
    glyphs: list[str] | None = None,
    check_stem: bool = True,
    check_zone: bool = True,
    check_direction: bool = True,
    check_compat: bool = True,
) -> AuditReport:
    """Run named-node / outline audits on a project; return a structured report."""
    root_path = Path(root).resolve()
    project = load_project(root_path)
    project.discover()
    names = glyphs if glyphs is not None else sorted(project.specs())
    report = AuditReport(glyphs=len(names))

    for name in names:
        raw = _raw_drawing(project, name)
        # Final outline for direction (post-slot winding).
        final = project.evaluate(name)
        if check_direction:
            _audit_direction(name, final, report.findings)
        if check_stem:
            _audit_stem(name, raw, project.system, report.findings)
        if check_zone:
            _audit_zone(name, final, project.system, report.findings)
        if check_compat:
            _audit_compat(project, name, report.findings)

    return report


def format_report(report: AuditReport) -> str:
    lines = [
        f"tk audit: {report.glyphs} glyphs, "
        f"{len(report.errors)} errors, {len(report.warnings)} warnings"
    ]
    for f in report.findings:
        lines.append(f"  [{f.level}] {f.kind} {f.glyph}: {f.message}")
    if not report.findings:
        lines.append("  (no findings)")
    return "\n".join(lines)
