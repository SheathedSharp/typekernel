"""C-class vertical metrics: zone reach, trait overshoot bands (target §7.2)."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.geo.outline import bounds
from typekernel.project.manifest import Expect

__all__ = ["VerticalCheck"]

_ZONE_ATTR = {
    "base": "base",
    "x": "x",
    "x-height": "x",
    "cap": "cap",
    "asc": "asc",
    "ascender": "asc",
    "desc": "desc",
    "descender": "desc",
}


def _expect_for(ctx: CheckContext) -> Expect | None:
    if ctx.name is None:
        return None
    spec = ctx.session.specs().get(ctx.name)
    if spec is not None and spec.expect is not None:
        return spec.expect
    return ctx.project.expect.get(ctx.name)


def _traits(ctx: CheckContext) -> frozenset[str]:
    if ctx.name is None:
        return frozenset()
    spec = ctx.session.specs().get(ctx.name)
    return frozenset(spec.traits) if spec is not None else frozenset()


class VerticalCheck:
    id = "vertical.reach"
    scope: Scope = "glyph"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        if ctx.name is None or ctx.final is None:
            return []
        try:
            _bx0, by0, _bx1, by1 = bounds(ctx.final.outline())
        except ValueError:
            return []
        zones = ctx.system.zones
        overshoot = ctx.system.overshoot
        out: list[Finding] = []
        expect = _expect_for(ctx)
        traits = _traits(ctx)

        if expect is not None and expect.reach:
            for zone_name in expect.reach:
                attr = _ZONE_ATTR.get(zone_name, zone_name)
                if not hasattr(zones, attr):
                    continue
                target = float(getattr(zones, attr))
                # Distance from bbox to zone line.
                dist = min(abs(by0 - target), abs(by1 - target))
                # Also treat "reaching past" as ok (desc below, asc above).
                if attr in {"desc", "base"}:
                    reached = by0 <= target + 1.0
                else:
                    reached = by1 >= target - 1.0
                if not reached:
                    out.append(
                        Finding(
                            check="vertical.reach",
                            level="warn",
                            glyph=ctx.name,
                            master=ctx.master,
                            where=zone_name,
                            measured=by0 if attr in {"desc", "base"} else by1,
                            expected=target,
                            message=(
                                f"does not reach zone {zone_name} "
                                f"(edge={by0 if attr in {'desc', 'base'} else by1:.1f}, "
                                f"zone={target:.1f}, gap={dist:.1f})"
                            ),
                            hint="scale or extend the outline to the expected zone",
                        )
                    )

        # Trait-driven overshoot bands for round / pointed extrema.
        for trait, band_lo, band_hi, edge, zone_attr in (
            ("round-top", 0.5, 1.5, by1, "x" if "x-height" in traits else "cap"),
            ("round-bottom", 0.5, 1.5, by0, "base"),
            ("pointed-top", 0.5, 1.5, by1, "x" if "x-height" in traits else "cap"),
            ("pointed-bottom", 0.5, 1.5, by0, "base"),
        ):
            if trait not in traits:
                continue
            zone_val = float(getattr(zones, zone_attr))
            if "top" in trait:
                over = edge - zone_val
                amount = float(overshoot.round if trait.startswith("round") else overshoot.pointed)
            else:
                over = zone_val - edge
                amount = float(overshoot.round if trait.startswith("round") else overshoot.pointed)
            lo, hi = band_lo * amount, band_hi * amount
            if over < lo - 1e-6 or over > hi + 1e-6:
                out.append(
                    Finding(
                        check="vertical.overshoot",
                        level="warn",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=trait,
                        measured=over,
                        expected=f"[{lo:.1f}, {hi:.1f}]",
                        message=(
                            f"{trait} overshoot={over:.1f} outside "
                            f"[{lo:.1f}, {hi:.1f}] (zone {zone_attr}={zone_val})"
                        ),
                        hint="adjust extrema relative to System.overshoot",
                    )
                )

        # flat-* should sit within 1 unit of the zone (no overshoot).
        for trait, edge, zone_attr in (
            ("flat-top", by1, "x" if "x-height" in traits else "cap"),
            ("flat-bottom", by0, "base"),
        ):
            if trait not in traits:
                continue
            zone_val = float(getattr(zones, zone_attr))
            gap = abs(edge - zone_val)
            if gap > 1.0:
                out.append(
                    Finding(
                        check="vertical.flat",
                        level="warn",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=trait,
                        measured=edge,
                        expected=zone_val,
                        message=(
                            f"{trait} edge={edge:.1f} should sit on "
                            f"{zone_attr}={zone_val:.1f} (gap={gap:.1f})"
                        ),
                        hint="align flat extrema to the zone line",
                    )
                )
        return out
