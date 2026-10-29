"""Gray checks: ink density robust z-score vs height-band cohort (target §7.2)."""

from __future__ import annotations

from collections.abc import Iterable
from statistics import median

from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.perceive.explain import explain

__all__ = ["GrayCheck"]


def _band(y0: float, y1: float, zones_x: float, zones_cap: float) -> str:
    span = y1 - y0
    mid = 0.5 * (y0 + y1)
    if y0 < -0.25 * zones_x:
        return "descender"
    if y1 >= 0.9 * zones_cap:
        return "cap"
    if span <= 1.15 * zones_x and mid <= 0.7 * zones_cap:
        return "x-height"
    return "other"


def _mad(values: list[float], med: float) -> float:
    return median([abs(v - med) for v in values])


class GrayCheck:
    id = "gray.density"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        session = ctx.session
        zones = ctx.system.zones
        cohorts: dict[str, list[tuple[str, float]]] = {}
        for name in session.specs():
            try:
                report = explain(session, name, master=ctx.master)
            except (KeyError, ValueError, TypeError, RuntimeError):
                continue
            by0, by1 = report.bbox[1], report.bbox[3]
            key = _band(by0, by1, float(zones.x), float(zones.cap))
            traits = set(session.specs()[name].traits)
            if "punct" in traits:
                key = "punct"
            elif "symbol" in traits:
                key = "symbol"
            elif "figure" in traits:
                key = "figure"
            cohorts.setdefault(key, []).append((name, report.ink_density))

        out: list[Finding] = []
        for key, members in cohorts.items():
            if len(members) < 4:
                continue
            values = [d for _, d in members]
            med = median(values)
            mad = _mad(values, med)
            # Consistent with normal: sigma ≈ 1.4826 * MAD; fall back if MAD=0.
            scale = 1.4826 * mad if mad > 1e-12 else max(med * 0.05, 1e-6)
            for name, density in members:
                z = (density - med) / scale
                if abs(z) > 2.0:
                    out.append(
                        Finding(
                            check="gray.density",
                            level="warn",
                            glyph=name,
                            master=ctx.master,
                            where=key,
                            measured=round(density, 6),
                            expected=round(med, 6),
                            message=(
                                f"ink density robust-z={z:.2f} vs {key} cohort "
                                f"(density={density:.4f}, median={med:.4f})"
                            ),
                            hint="reshape or retune stems; check symbol construction",
                        )
                    )
        return out
