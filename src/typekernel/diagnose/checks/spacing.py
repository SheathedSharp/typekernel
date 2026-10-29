"""E-class spacing: ink overflow, keyless glyphs, pair collisions, Ref consistency."""

from __future__ import annotations

import itertools
from collections.abc import Iterable

from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.geo.outline import bounds
from typekernel.metrics import Optical, Ref
from typekernel.optics.space import pair_gap_bbox

__all__ = ["SpacingCheck"]


class SpacingCheck:
    id = "spacing.overflow"
    scope: Scope = "glyph"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        out: list[Finding] = []
        if ctx.name is None or ctx.final is None:
            return out
        g = ctx.session.glyph(ctx.name, master=ctx.master)
        try:
            bx0, _by0, bx1, _by1 = bounds(g.outline)
        except ValueError:
            return out
        # Ink overflow past advance.
        if bx1 > g.advance + 0.5:
            out.append(
                Finding(
                    check="spacing.overflow",
                    level="warn",
                    glyph=ctx.name,
                    master=ctx.master,
                    where="rsb",
                    measured=bx1,
                    expected=g.advance,
                    message=(
                        f"ink extends past advance "
                        f"(right={bx1:.1f} > advance={g.advance:.1f})"
                    ),
                    hint="widen advance or pull in the right sidebearing",
                )
            )
        if bx0 < -0.5:
            out.append(
                Finding(
                    check="spacing.overflow",
                    level="warn",
                    glyph=ctx.name,
                    master=ctx.master,
                    where="lsb",
                    measured=bx0,
                    expected=0.0,
                    message=f"ink extends left of origin (left={bx0:.1f})",
                    hint="shift outline or set a negative LSB deliberately via metrics",
                )
            )

        # Keyless glyph: no metrics key and no advance override path.
        metrics = ctx.project.metrics
        if (
            metrics is not None
            and ctx.name not in metrics.keys
            and ctx.name != "space"
            and metrics.pack is None
        ):
                out.append(
                    Finding(
                        check="spacing.keyless",
                        level="info",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=None,
                        measured=None,
                        expected=None,
                        message="glyph has no metrics key and Metrics.pack is None",
                        hint="add a Metrics.keys entry or enable pack",
                    )
                )
        return out


class PairCollisionCheck:
    id = "spacing.collision"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        """Check kerning pairs + proof control string neighbours for collisions."""
        out: list[Finding] = []
        project = ctx.project
        session = ctx.session
        pairs: list[tuple[str, str, float]] = []
        if project.kerning is not None:
            for pair in project.kerning.pairs:
                # KernPair has left/right/value; ClassKernPair similar.
                left = getattr(pair, "left", None) or getattr(pair, "first", None)
                right = getattr(pair, "right", None) or getattr(pair, "second", None)
                value = float(getattr(pair, "value", 0.0))
                if isinstance(left, str) and isinstance(right, str):
                    pairs.append((left, right, value))
        # Specimen / control string adjacent pairs.
        control = project.proofs.control if project.proofs else ""
        if control:
            # Map chars to glyph names via session specs when possible.
            from typekernel.font.glyph import glyph_name_for_char

            names: list[str] = []
            for ch in control:
                if ch == " ":
                    continue
                try:
                    gn = glyph_name_for_char(ch)
                except ValueError:
                    continue
                if gn in session.specs():
                    names.append(gn)
            for a, b in itertools.pairwise(names):
                pairs.append((a, b, 0.0))

        seen: set[tuple[str, str]] = set()
        for left, right, kern in pairs:
            key = (left, right)
            if key in seen:
                continue
            seen.add(key)
            if left not in session.specs() or right not in session.specs():
                continue
            lg = session.glyph(left, master=ctx.master)
            rg = session.glyph(right, master=ctx.master)
            gap = pair_gap_bbox(lg, rg, kern=kern)
            if gap < 0:
                out.append(
                    Finding(
                        check="spacing.collision",
                        level="warn",
                        glyph=f"{left}/{right}",
                        master=ctx.master,
                        where=None,
                        measured=gap,
                        expected=0.0,
                        message=(
                            f"pair {left!r}+{right!r} collides "
                            f"(bbox gap={gap:.1f} after kern={kern:.1f})"
                        ),
                        hint="increase sidebearings or reduce negative kern",
                    )
                )
        return out


class RefConsistencyCheck:
    id = "spacing.ref"
    scope: Scope = "font"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        """Warn when Ref-linked sidebearings diverge optically (appendix A-12)."""
        from typekernel.optics.space import measure_side_whitespace

        metrics = ctx.project.metrics
        if metrics is None:
            return []
        out: list[Finding] = []
        session = ctx.session
        zones = ctx.system.zones
        y0, y1 = float(zones.base), float(zones.x)
        for name, (left, right) in metrics.keys.items():
            if name not in session.specs():
                continue
            g = session.glyph(name, master=ctx.master)
            for side_name, side in (("lsb", left), ("rsb", right)):
                if not isinstance(side, (Ref, Optical)):
                    continue
                ref_name = side.glyph if isinstance(side, Ref) else side.ref
                if ref_name not in session.specs():
                    continue
                ref_g = session.glyph(ref_name, master=ctx.master)
                # Compare optical whitespace on the referenced side.
                side_key = "left" if side_name == "lsb" else "right"
                try:
                    live = measure_side_whitespace(
                        g.outline, side_key, y0=y0, y1=y1
                    )
                    ref_w = measure_side_whitespace(
                        ref_g.outline, side_key, y0=y0, y1=y1
                    )
                except (KeyError, ValueError, TypeError, RuntimeError):
                    continue
                if live is None or ref_w is None:
                    continue
                delta = abs(live - ref_w)
                if delta > 40.0:  # design-unit tolerance for optical match
                    out.append(
                        Finding(
                            check="spacing.ref",
                            level="warn",
                            glyph=name,
                            master=ctx.master,
                            where=side_name,
                            measured=live,
                            expected=ref_w,
                            message=(
                                f"{side_name} optical whitespace {live:.1f} "
                                f"diverges from {ref_name!r} ({ref_w:.1f}) "
                                f"by {delta:.1f}"
                            ),
                            hint="use Optical sidebearings or retune Ref delta",
                        )
                    )
        return out
