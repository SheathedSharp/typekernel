"""S3 join diagnose — adjacent Δy / tangent / width / gap + text rhythm CV."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.font.glyph import Glyph, glyph_name_for_char
from typekernel.metrics.join import (
    ENTRY,
    EXIT,
    Join,
    JoinPairMeasure,
    anchor_by_name,
    measure_join_pair,
    measure_text_joins,
)
from typekernel.project.session import ProjectSession

__all__ = [
    "JoinCheck",
    "TextJoinAudit",
    "run_text_join_audit",
]


def _policy(ctx: CheckContext) -> Join:
    metrics = ctx.project.metrics
    if metrics is not None and metrics.join is not None:
        return metrics.join
    return Join()


def _glyphs_with_join(session: ProjectSession, master: str | None) -> dict[str, Glyph]:
    out: dict[str, Glyph] = {}
    for name in session.specs():
        try:
            g = session.glyph(name, master=master)
        except Exception:  # noqa: BLE001, S112
            continue
        if anchor_by_name(g, ENTRY) is not None or anchor_by_name(g, EXIT) is not None:
            out[name] = g
    return out


class JoinCheck:
    """Font-scope: every adjacent pair that *both* expose entry/exit anchors.

    Skips silently when the project has no join anchors (latin-sans stays quiet).
    """

    id = "join"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        policy = _policy(ctx)
        joined = _glyphs_with_join(ctx.session, ctx.master)
        if len(joined) < 2:
            return []
        # Only pairs among glyphs that have *both* entry and exit.
        complete = {
            n: g
            for n, g in joined.items()
            if anchor_by_name(g, ENTRY) is not None and anchor_by_name(g, EXIT) is not None
        }
        if len(complete) < 2:
            return []
        names = sorted(complete)
        findings: list[Finding] = []
        # Check consecutive name-order pairs is weak; prefer control/proof text
        # neighbours when available, else sample sorted adjacent names.
        pairs: list[tuple[str, str]] = []
        control = ctx.project.proofs.control if ctx.project.proofs else ""
        if control:
            seq: list[str] = []
            for ch in control:
                if ch.isspace():
                    continue
                try:
                    gn = glyph_name_for_char(ch)
                except ValueError:
                    continue
                if gn in complete:
                    seq.append(gn)
            for i in range(len(seq) - 1):
                pairs.append((seq[i], seq[i + 1]))
        if not pairs:
            for i in range(len(names) - 1):
                pairs.append((names[i], names[i + 1]))
        seen: set[tuple[str, str]] = set()
        for left_n, right_n in pairs:
            key = (left_n, right_n)
            if key in seen:
                continue
            seen.add(key)
            m = measure_join_pair(complete[left_n], complete[right_n])
            findings.extend(_findings_for_measure(m, policy, master=ctx.master))
        return findings


def _findings_for_measure(
    m: JoinPairMeasure,
    policy: Join,
    *,
    master: str | None,
) -> list[Finding]:
    if not m.has_join:
        return []
    out: list[Finding] = []
    pair = f"{m.left}/{m.right}"
    if m.dy > policy.max_dy:
        out.append(
            Finding(
                check="join.dy",
                level="warn",
                glyph=m.left,
                master=master,
                where=pair,
                measured=m.dy,
                expected=policy.max_dy,
                message=f"join Δy={m.dy:.1f} exceeds {policy.max_dy} for {pair}",
                hint="align exit.y with next entry.y",
            )
        )
    if m.angle_delta > policy.max_angle_delta:
        out.append(
            Finding(
                check="join.tangent",
                level="warn",
                glyph=m.left,
                master=master,
                where=pair,
                measured=m.angle_delta,
                expected=policy.max_angle_delta,
                message=(
                    f"join tangent Δ={m.angle_delta:.1f}° exceeds "
                    f"{policy.max_angle_delta} for {pair}"
                ),
                hint="match exit/entry stroke angles",
            )
        )
    if m.width_delta > policy.max_width_delta:
        out.append(
            Finding(
                check="join.width",
                level="warn",
                glyph=m.left,
                master=master,
                where=pair,
                measured=m.width_delta,
                expected=policy.max_width_delta,
                message=(
                    f"join width Δ={m.width_delta:.1f} exceeds "
                    f"{policy.max_width_delta} for {pair}"
                ),
                hint="match stroke width at entry/exit",
            )
        )
    if abs(m.gap) > policy.gap_outlier:
        out.append(
            Finding(
                check="join.gap",
                level="warn",
                glyph=m.left,
                master=master,
                where=pair,
                measured=m.gap,
                expected=0.0,
                message=f"join gap/overlap={m.gap:.1f} for {pair} (outlier)",
                hint="retune exit/entry x or join advance",
            )
        )
    return out


def run_text_join_audit(
    session: ProjectSession,
    text: str,
    *,
    master: str | None = None,
    policy: Join | None = None,
    use_join_advance: bool = True,
) -> list[Finding]:
    """String-level join + rhythm CV (``tk audit --text``)."""
    pol = policy if policy is not None else Join()
    glyphs: dict[str, Glyph] = {}
    for ch in text:
        if ch.isspace():
            continue
        try:
            gn = glyph_name_for_char(ch)
        except ValueError:
            continue
        if gn in glyphs or gn not in session.specs():
            continue
        try:
            glyphs[gn] = session.glyph(gn, master=master)
        except Exception:  # noqa: BLE001, S112
            continue
    measures, cv = measure_text_joins(
        glyphs, text, use_join_advance=use_join_advance
    )
    findings: list[Finding] = []
    for m in measures:
        findings.extend(_findings_for_measure(m, pol, master=master))
        if not m.has_join:
            findings.append(
                Finding(
                    check="join.missing",
                    level="info",
                    glyph=m.left,
                    master=master,
                    where=f"{m.left}/{m.right}",
                    measured=None,
                    expected=f"{EXIT}+{ENTRY}",
                    message=(
                        f"pair {m.left}/{m.right} has no entry/exit join anchors"
                    ),
                    hint="declare GlyphDraft anchors entry/exit for script joins",
                )
            )
    # Spacing outliers among measured gaps (absolute).
    joined_gaps = [m.gap for m in measures if m.has_join]
    if joined_gaps:
        if cv > pol.max_gap_cv:
            findings.append(
                Finding(
                    check="join.rhythm_cv",
                    level="warn",
                    glyph="*",
                    master=master,
                    where=text.strip()[:48] or "*",
                    measured=cv,
                    expected=pol.max_gap_cv,
                    message=(
                        f"inter-letter gap CV={cv:.3f} exceeds threshold "
                        f"{pol.max_gap_cv}"
                    ),
                    hint="even out join advances / entry-exit x across the word",
                )
            )
        else:
            findings.append(
                Finding(
                    check="join.rhythm_cv",
                    level="info",
                    glyph="*",
                    master=master,
                    where=text.strip()[:48] or "*",
                    measured=cv,
                    expected=pol.max_gap_cv,
                    message=f"inter-letter gap CV={cv:.3f} within {pol.max_gap_cv}",
                )
            )
    # Named letter-spacing outliers in latin text (e.g. f o r) when gaps huge
    # even without join anchors — use advance-based bbox gap via optics.
    findings.extend(_latin_spacing_outliers(session, text, master=master, policy=pol))
    return findings


def _latin_spacing_outliers(
    session: ProjectSession,
    text: str,
    *,
    master: str | None,
    policy: Join,
) -> list[Finding]:
    """Flag absolute bbox gaps for adjacent letters in ``text``."""
    from typekernel.optics.space import pair_gap_bbox

    names: list[str] = []
    for ch in text:
        if ch.isspace():
            continue
        try:
            gn = glyph_name_for_char(ch)
        except ValueError:
            continue
        if gn in session.specs():
            names.append(gn)
    out: list[Finding] = []
    for i in range(len(names) - 1):
        try:
            lg = session.glyph(names[i], master=master)
            rg = session.glyph(names[i + 1], master=master)
        except Exception:  # noqa: BLE001, S112
            continue
        # Skip pairs already covered by join anchors (join.gap handles them).
        if anchor_by_name(lg, EXIT) and anchor_by_name(rg, ENTRY):
            continue
        gap = pair_gap_bbox(lg, rg, kern=0.0)
        if gap > policy.gap_outlier:
            out.append(
                Finding(
                    check="join.spacing_outlier",
                    level="warn",
                    glyph=names[i],
                    master=master,
                    where=f"{names[i]}/{names[i + 1]}",
                    measured=gap,
                    expected=policy.gap_outlier,
                    message=(
                        f"spacing outlier gap={gap:.1f} for "
                        f"{names[i]}/{names[i + 1]}"
                    ),
                    hint="tighten sidebearings or add kern for this pair",
                )
            )
    return out


class TextJoinAudit:
    """Placeholder Check id for docs; text path uses :func:`run_text_join_audit`."""

    id = "join.text"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        return []
