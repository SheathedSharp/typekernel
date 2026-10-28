"""``tk audit`` — stem / zone / direction / master-compat diagnostics (ARCH 验收方式).

Reports are diagnostic by default. Structural errors (wrong contour direction,
master signature mismatch) raise the process exit code. Stem / zone deviations
are warnings for the designer to fix in glyph code.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typekernel.cli.load import load_project
from typekernel.draw import Drawing
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.stem import (
    list_vertical_stems,
    measure_oriented_stem,
    vertical_equiv_from_diagonal,
)
from typekernel.project import Project
from typekernel.system import System

__all__ = ["AuditReport", "Finding", "audit_project", "format_report", "load_audit_stems"]

# Glyphs that rarely carry upright stems; optical vertical probes on these are
# usually measuring diagonals or bowls. Projects may override via AUDIT_STEMS.
_DEFAULT_NON_VERTICAL = frozenset(
    {
        "v",
        "w",
        "x",
        "y",
        "z",
        "V",
        "W",
        "X",
        "Y",
        "Z",
        "s",
        "S",
        "e",
        "c",
        "o",
        "O",
        "a",
        "A",
        "k",
        "K",
        "Q",
        "R",
        "G",
        "C",
    }
)


@dataclass
class Finding:
    kind: str  # stem | zone | direction | compat | overlap
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


def load_audit_stems(root: Path) -> Mapping[str, Sequence[str]]:
    """Load optional ``AUDIT_STEMS`` from the project's ``system.py``.

    Values are stroke-kind tokens per glyph::

        AUDIT_STEMS = {
            "n": ("vertical",),
            "v": ("diagonal",),
            "w": (),            # named nodes only; no optical fallback
            "x": "none",        # alias for ()
        }

    Allowed kinds: ``vertical``, ``diagonal``. Unknown keys fall back to the
    built-in auto policy in :func:`_kinds_for`.
    """
    system_py = root / "system.py"
    if not system_py.is_file():
        return {}
    root_s = str(root.resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    mod_name = f"_typekernel_user_system_audit_{abs(hash(root_s)) & 0xFFFFFFFF:x}"
    spec = importlib.util.spec_from_file_location(mod_name, system_py)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    # Do not register permanently — avoid clobbering project ``system`` imports.
    try:
        spec.loader.exec_module(module)
    except Exception:
        return {}
    raw = getattr(module, "AUDIT_STEMS", None)
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, tuple[str, ...]] = {}
    for key, value in raw.items():
        out[str(key)] = _normalize_kinds(value)
    return out


def _normalize_kinds(value: Any) -> tuple[str, ...]:
    if value is None or value == "none" or value == ():
        return ()
    if isinstance(value, str):
        if value in {"vertical", "diagonal"}:
            return (value,)
        if value == "auto":
            return ("auto",)
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        kinds = []
        for item in value:
            s = str(item)
            if s in {"vertical", "diagonal"}:
                kinds.append(s)
        return tuple(kinds)
    return ()


def _kinds_for(name: str, declared: Mapping[str, Sequence[str]]) -> tuple[str, ...]:
    if name in declared:
        kinds = tuple(declared[name])
        if kinds == ("auto",):
            return _auto_kinds(name)
        return kinds
    return _auto_kinds(name)


def _auto_kinds(name: str) -> tuple[str, ...]:
    """Default optical policy when the project does not declare AUDIT_STEMS.

    Letters without upright stems skip optical vertical probes (the historical
    false-noise source). Oriented / diagonal optical probes run only when the
    project opts in via ``AUDIT_STEMS`` — guessing 45° on every ``v``/``w`` is
    another noise generator.
    """
    if name in _DEFAULT_NON_VERTICAL:
        return ()
    return ("vertical",)


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


def _oriented_from_nodes(drawing: Drawing, prefix: str) -> float | None:
    """Perpendicular stem width from a tagged outer/inner pair (any orientation)."""
    try:
        a = drawing.point(f"{prefix}.foot.o")
        b = drawing.point(f"{prefix}.foot.i")
    except KeyError:
        return None
    return math.hypot(float(b.x) - float(a.x), float(b.y) - float(a.y))


def _audit_stem(
    name: str,
    drawing: Drawing,
    system: System,
    findings: list[Finding],
    *,
    kinds: Sequence[str],
    tol_ratio: float = 0.08,
) -> None:
    expected_lc = float(system.stem.get("lc", 0.0))
    expected_uc = float(system.stem.get("uc", expected_lc))
    is_uc = len(name) == 1 and name.isupper()
    stem_target = expected_uc if is_uc else expected_lc
    measured: list[tuple[str, float, float]] = []
    for prefix, expected in (
        ("stem.l", stem_target),
        ("stem.r", stem_target),
        ("stem", stem_target),
        ("stem.L", expected_uc),
        ("stem.R", expected_uc),
        ("stem.diag", stem_target),
        ("stem.diag.a", stem_target),
        ("stem.diag.b", stem_target),
    ):
        # Prefer Euclidean foot distance so diagonal tagged pairs work.
        w = _oriented_from_nodes(drawing, prefix)
        if w is None:
            w = _stem_from_nodes(drawing, prefix)
        if w is not None:
            measured.append((prefix, w, expected))

    if not measured and (len(name) == 1 or name in {"zero", "one", "four", "seven"}):
        outline = drawing.outline()
        zone = float(system.zones.cap if is_uc else system.zones.x)
        if "vertical" in kinds:
            best: list = []
            best_score = float("inf")
            agreeing_bands = 0
            for frac in (0.32, 0.5, 0.68):
                try:
                    spans = list_vertical_stems(outline, y=zone * frac)
                except Exception:
                    continue
                near = []
                for span in spans:
                    if span.width <= 0:
                        continue
                    if abs(span.width - stem_target) / stem_target > 0.25:
                        continue
                    near.append(span)
                if not near:
                    continue
                agreeing_bands += 1
                score = sum(abs(s.width - stem_target) for s in near) / len(near)
                if score < best_score:
                    best_score = score
                    best = near
            # Require ≥2 y-bands to agree before optical vertical warns —
            # single-band hits on diagonals/curves are usually noise.
            if agreeing_bands >= 2:
                for span in best:
                    measured.append(("optical.vertical", span.width, stem_target))
        if "diagonal" in kinds:
            try:
                min_x, min_y, max_x, max_y = bounds(outline)
            except ValueError:
                min_x = min_y = max_x = max_y = 0.0
            origin = ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5)
            for deg in (45.0, 135.0, -45.0):
                try:
                    w = measure_oriented_stem(outline, origin, deg)
                except Exception:
                    w = None
                if w is None or w <= 0:
                    continue
                # Stroke bearing ``deg`` (0=+x): angle-from-vertical for invert.
                # 90° stroke → 0° from vertical; 0° stroke → 90° from vertical.
                angle_from_vertical = abs(90.0 - (abs(deg) % 180.0))
                if angle_from_vertical > 90.0:
                    angle_from_vertical = 180.0 - angle_from_vertical
                try:
                    equiv = vertical_equiv_from_diagonal(
                        w, angle_from_vertical_deg=angle_from_vertical
                    )
                except ValueError:
                    continue
                if abs(equiv - stem_target) / stem_target > 0.35:
                    continue
                measured.append(
                    (f"optical.diag@{deg:.0f}", equiv, stem_target)
                )
                break  # one confirming oriented probe is enough

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
    if min_y < float(system.zones.desc) - tol:
        findings.append(
            Finding(
                "zone",
                "warn",
                name,
                f"ymin {min_y:.1f} below desc {system.zones.desc} (tol {tol})",
            )
        )
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
    if name in {"o", "O", "c", "e", "a"} and abs(
        max_y - float(system.zones.x if name.islower() else system.zones.cap)
    ) < 1.0:
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


def _audit_overlap_cavity(
    name: str,
    drawing: Drawing,
    findings: list[Finding],
) -> None:
    """Report-only: overlapping ink contours that cancel under even-odd fill.

    Does **not** rewrite outlines (no heal/blend/seal). Agents should change
    fragments or leave overlaps intentional for VF; see anti-patterns.
    """
    ink_idxs = [i for i, role in enumerate(drawing.roles) if role == "ink"]
    if len(ink_idxs) < 2:
        return
    # Bounding-box overlap is a cheap necessary condition; pathops confirms.
    boxes: list[tuple[int, tuple[float, float, float, float]]] = []
    for i in ink_idxs:
        contour = drawing.contours[i]
        if not contour.segments:
            continue
        try:
            from typekernel.geo.outline import Outline

            boxes.append((i, bounds(Outline((contour,)))))
        except ValueError:
            continue
    pairs: list[tuple[int, int]] = []
    for a in range(len(boxes)):
        ia, ba = boxes[a]
        for b in range(a + 1, len(boxes)):
            ib, bb = boxes[b]
            if ba[2] < bb[0] or bb[2] < ba[0] or ba[3] < bb[1] or bb[3] < ba[1]:
                continue
            pairs.append((ia, ib))
    if not pairs:
        return
    try:
        from typekernel.geo.boolean import boolean_op
        from typekernel.geo.outline import Outline
    except Exception:
        # Without boolean extra, bbox overlap alone is only info-level.
        findings.append(
            Finding(
                "overlap",
                "info",
                name,
                f"{len(pairs)} ink contour pair(s) have overlapping bounds "
                "(install typekernel[boolean] for cavity confirmation)",
            )
        )
        return
    for ia, ib in pairs:
        try:
            inter = boolean_op(
                Outline((drawing.contours[ia],)),
                Outline((drawing.contours[ib],)),
                "intersection",
            )
        except Exception:
            continue
        if not inter.contours:
            continue
        area = sum(abs(signed_area(c)) for c in inter.contours)
        if area < 1.0:
            continue
        findings.append(
            Finding(
                "overlap",
                "warn",
                name,
                f"ink contours [{ia}]∩[{ib}] area≈{area:.0f} — under even-odd "
                "preview this overlap cancels (cavity risk); change fragments "
                "or resolve overlaps only at static export (not a design-time seal)",
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
    check_overlap: bool = False,
) -> AuditReport:
    """Run named-node / outline audits on a project; return a structured report.

    ``check_overlap`` is opt-in: overlap construction is the recommended VF
    pattern, so pairwise ink∩ink is noisy as a default. Pass True (CLI
    ``--overlap``) when hunting even-odd cavity defects.
    """
    root_path = Path(root).resolve()
    project = load_project(root_path)
    project.discover()
    names = glyphs if glyphs is not None else sorted(project.specs())
    report = AuditReport(glyphs=len(names))
    stem_kinds = load_audit_stems(root_path)

    for name in names:
        raw = _raw_drawing(project, name)
        final = project.evaluate(name)
        if check_direction:
            _audit_direction(name, final, report.findings)
        if check_stem:
            _audit_stem(
                name,
                raw,
                project.system,
                report.findings,
                kinds=_kinds_for(name, stem_kinds),
            )
        if check_zone:
            _audit_zone(name, final, project.system, report.findings)
        if check_overlap:
            _audit_overlap_cavity(name, final, report.findings)
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
