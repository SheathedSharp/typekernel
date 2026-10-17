"""First-class designer-order session: control → one glyph → gate → unlock.

Coding agents must design like human type designers: pick control letter(s),
draw **one** glyph, style-check against control and the previous unlocked
letter, unlock only on pass, and treat a specimen phrase as a **late** proof.

Use :class:`DesignSequence` for new faces (Controls-derived or skeleton).
``Controls.build_all`` remains a stock derivation helper after controls are
locked — it is not a substitute for sequential design of new letters.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from typekernel.parts.compose import ComposedGlyph
from typekernel.qa.style_consistency import (
    SequenceStyleReport,
    StyleConsistencyReport,
    StyleConsistencyTolerances,
    check_design_sequence,
    compare_glyph_styles,
)

if TYPE_CHECKING:
    from typekernel.parts.family import Controls

__all__ = [
    "DEFAULT_BODY_DESIGN_ORDER",
    "DesignSequence",
    "DesignSequenceError",
    "controls_body_tolerances",
    "default_body_design_order",
    "latin_topology_skip_checks",
    "unlock_controls_body",
    "unlock_controls_body_ladder",
]

# Humanist / geometric body order: stem control, bowl control, then related.
DEFAULT_BODY_DESIGN_ORDER: tuple[str, ...] = (
    "n",
    "o",
    "h",
    "u",
    "m",
    "r",
    "a",
    "e",
    "c",
    "d",
    "b",
    "p",
    "q",
    "g",
    "i",
    "l",
    "f",
    "t",
    "j",
    "s",
    "v",
    "w",
    "y",
    "x",
    "z",
    "k",
)


def default_body_design_order() -> tuple[str, ...]:
    """Default lowercase designer order for Controls-derived Latin faces."""
    return DEFAULT_BODY_DESIGN_ORDER

# Topology roles where some style metrics are meaningless across letters.
_CLOSED_BOWLS: frozenset[str] = frozenset({"o", "O", "e", "c", "0", "Q", "C", "G"})
# Openings / crossbars make vertical stem probes hit hairlines or eye bars.
_OPEN_ROUNDS: frozenset[str] = frozenset({"c", "e", "C"})
_ASCENDERS: frozenset[str] = frozenset(
    {"b", "d", "f", "h", "k", "l", "t", "B", "D", "F", "H", "K", "L", "P", "R", "T"}
)
_DESCENDERS: frozenset[str] = frozenset({"g", "j", "p", "q", "y", "J", "Q"})
_DOTTED: frozenset[str] = frozenset({"i", "j"})
_DIAGONALS: frozenset[str] = frozenset({"v", "w", "x", "y", "z", "k"})
_MULTI_ARCH: frozenset[str] = frozenset({"m", "w", "M", "W"})
_CURVED_SPINE: frozenset[str] = frozenset({"s", "S"})
# Baseline hooks that dip below the x-height floor without being full descenders.
_BASELINE_HOOKS: frozenset[str] = frozenset({"t"})


def latin_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Default metric skips across Latin topology roles (Controls path).

    Entry/exit rails and exit slant are **script writing** proxies — upright
    Controls Latin has no shared rail language, so they are always omitted
    here (script faces pass their own ``skip_checks_for_pair``). Stem,
    contrast, bowl centre, and ink extents remain gated except where
    topology makes a proxy meaningless (asc/desc extents, dotted tittles,
    diagonal / multi-arch letters whose H/V or stem-band samples are not
    comparable to control ``n``).
    """
    skip: list[str] = [
        "entry_rail_y",
        "exit_rail_y",
        "exit_slant_deg",
    ]
    if ref in _ASCENDERS or cand in _ASCENDERS:
        skip.extend(["ink_ymax", "bowl_center_y"])
    if ref in _DESCENDERS or cand in _DESCENDERS:
        skip.extend(["ink_ymin", "bowl_center_y"])
    if ref in _BASELINE_HOOKS or cand in _BASELINE_HOOKS:
        # ``t`` hook spring often sits below baseline without a full descender.
        skip.extend(["ink_ymin"])
    if ref in _DOTTED or cand in _DOTTED:
        # Tittle constructions often use a lighter stem than control ``n``.
        skip.extend(["ink_ymax", "bowl_center_y", "contrast_ratio", "stem_median"])
    if ref in _DIAGONALS or cand in _DIAGONALS:
        # Diagonal stem bands are not vertical-stem comparable to ``n``.
        skip.extend(["contrast_ratio", "stem_median"])
    if ref in _MULTI_ARCH or cand in _MULTI_ARCH:
        # Double/triple arches: H/V contrast probes hit joins, not stems.
        skip.extend(["contrast_ratio"])
    if ref in _CURVED_SPINE or cand in _CURVED_SPINE:
        # ``s`` has no stable vertical stem band — probes hit the spine curve.
        skip.extend(["stem_median", "contrast_ratio"])
    if ref in _CLOSED_BOWLS or cand in _CLOSED_BOWLS:
        # Round bowls (``c``/``e``/``o``): H/V contrast vs stem ``n`` is not
        # comparable — openings and crossbars dominate horizontal probes.
        skip.extend(["contrast_ratio"])
    if ref in _OPEN_ROUNDS or cand in _OPEN_ROUNDS:
        # Open ``c``/``e``: vertical probes hit the opening hairline or eye bar.
        skip.extend(["stem_median"])
    return tuple(dict.fromkeys(skip))


def controls_body_tolerances() -> StyleConsistencyTolerances:
    """Budgets for Controls Latin body sequences (related forms from ``n``/``o``).

    Stem band is 18 (above the raw default 12) so heavy masters with
    ``with_stem_relief`` still gate verticals without false refuses from
    probe noise on ``l`` / bowl side walls. Contrast is slightly wider than
    raw ``StyleConsistencyTolerances`` because bowl vs shoulder H/V samples
    drift ~0.3–0.4 across stock related forms without a construction bug —
    still far tighter than greenwashing rails/slant.
    """
    return StyleConsistencyTolerances(
        stem_median=18.0,
        stem_median_rel=0.16,
        contrast_ratio=0.45,
        entry_rail_y=36.0,
        exit_rail_y=36.0,
        exit_slant_deg=35.0,
        bowl_center_y=55.0,
        ink_ymin=55.0,
        ink_ymax=400.0,
    )



def unlock_controls_body(
    controls: Controls,
    *,
    control: str = "n",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> DesignSequence:
    """Module alias for :meth:`DesignSequence.unlock_controls_body`."""
    return DesignSequence.unlock_controls_body(
        controls,
        control=control,
        order=order,
        tolerances=tolerances,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=skip_checks_for_pair,
    )


def unlock_controls_body_ladder(
    template: Controls,
    stems: Sequence[float] | None = None,
    *,
    control: str = "n",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> dict[float, DesignSequence]:
    """Unlock the Latin body on each weight-ladder master (VF / family path).

    Builds a stem-tuned copy of ``template`` per stem (with
    :meth:`~typekernel.parts.family.Controls.with_stem_relief` past onset) and
    runs :meth:`DesignSequence.unlock_controls_body`. Raises on the first
    refused master so agents redesign that weight before compose.

    ``stems`` defaults to :data:`~typekernel.qa.trial_protocol.WEIGHT_LADDER_STEMS`.
    """
    from typekernel.qa.trial_protocol import (
        WEIGHT_LADDER_STEMS,
        controls_at_ladder_stem,
    )

    ladder = tuple(stems) if stems is not None else WEIGHT_LADDER_STEMS
    out: dict[float, DesignSequence] = {}
    for stem in ladder:
        sheet = controls_at_ladder_stem(template, float(stem))
        out[float(stem)] = DesignSequence.unlock_controls_body(
            sheet,
            control=control,
            order=order,
            tolerances=tolerances,
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,
        )
    return out


class DesignSequenceError(ValueError):
    """Raised when a glyph is refused or export is incomplete."""

    def __init__(
        self,
        message: str,
        *,
        reports: Sequence[StyleConsistencyReport] = (),
    ) -> None:
        super().__init__(message)
        self.reports = tuple(reports)

    @property
    def hints(self) -> tuple[str, ...]:
        out: list[str] = []
        for rep in self.reports:
            out.extend(rep.fix_hints())
        return tuple(out)


@dataclass
class DesignSequence:
    """Mutable designer session with a hard unlock gate.

    Typical agent loop::

        seq = DesignSequence.start("n", controls.build("n"))
        for ch in ("o", "h", "u"):
            report = seq.try_add(ch, controls.build(ch))
            if not report.passed:
                # read report.fix_hints(), redesign, retry — do not skip
                ...
        glyphs = seq.export_glyphs(require_complete=False)
    """

    control: str
    tolerances: StyleConsistencyTolerances = field(
        default_factory=StyleConsistencyTolerances
    )
    compare_to_previous: bool = True
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None
    planned_order: tuple[str, ...] = ()
    _glyphs: MutableMapping[str, ComposedGlyph] = field(default_factory=dict)
    _unlocked: list[str] = field(default_factory=list)
    _last_reports: tuple[StyleConsistencyReport, ...] = ()

    @classmethod
    def start(
        cls,
        control_name: str,
        control_glyph: ComposedGlyph,
        *,
        tolerances: StyleConsistencyTolerances | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
        planned_order: Sequence[str] = (),
    ) -> DesignSequence:
        """Open a session with the control glyph already unlocked."""
        if not control_name:
            raise ValueError("control_name must be non-empty")
        planned = tuple(planned_order) if planned_order else ()
        if planned and planned[0] != control_name and control_name not in planned:
            planned = (control_name, *planned)
        seq = cls(
            control=control_name,
            tolerances=tolerances or StyleConsistencyTolerances(),
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,
            planned_order=planned,
        )
        seq._glyphs[control_name] = control_glyph
        seq._unlocked.append(control_name)
        return seq

    @classmethod
    def from_controls(
        cls,
        controls: Controls,
        *,
        control: str = "n",
        order: Sequence[str] | None = None,
        tolerances: StyleConsistencyTolerances | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
    ) -> DesignSequence:
        """Start from a :class:`~typekernel.parts.family.Controls` sheet.

        Builds **only** the control glyph. Remaining letters in ``order``
        (default: :data:`DEFAULT_BODY_DESIGN_ORDER`) must be unlocked via
        :meth:`try_add` / :meth:`add` — not via ``build_all``.
        """
        planned = tuple(order) if order is not None else default_body_design_order()
        if control not in planned or planned[0] != control:
            planned = (control, *[c for c in planned if c != control])
        skips = skip_checks_for_pair
        if skips is None:
            skips = latin_topology_skip_checks
        tol = tolerances if tolerances is not None else controls_body_tolerances()
        return cls.start(
            control,
            controls.build(control),
            tolerances=tol,
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skips,
            planned_order=planned,
        )


    @classmethod
    def unlock_controls_body(
        cls,
        controls: Controls,
        *,
        control: str = "n",
        order: Sequence[str] | None = None,
        tolerances: StyleConsistencyTolerances | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
    ) -> DesignSequence:
        """Unlock the Controls Latin body one glyph at a time, then export.

        This is the required gate after locking ``n``/``o`` (and any
        ``with_glyph`` / ``tuned_glyph`` masters). It builds each letter via
        ``controls.build(ch)`` and refuses on style failure — agents must
        redesign that letter, not call :meth:`~typekernel.parts.family.Controls.build_all`
        to skip the sequence.

        ``build_all`` remains valid **after** this gate for punctuation,
        figures, and caps derivation at compile time.
        """
        seq = cls.from_controls(
            controls,
            control=control,
            order=order,
            tolerances=tolerances,
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,
        )
        for ch in seq.planned_order:
            if ch == seq.control:
                continue
            seq.add(ch, controls.build(ch))
        return seq

    @classmethod
    def unlock_controls_body_ladder(
        cls,
        template: Controls,
        stems: Sequence[float] | None = None,
        *,
        control: str = "n",
        order: Sequence[str] | None = None,
        tolerances: StyleConsistencyTolerances | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
    ) -> dict[float, DesignSequence]:
        """Class alias for :func:`unlock_controls_body_ladder`."""
        return unlock_controls_body_ladder(
            template,
            stems,
            control=control,
            order=order,
            tolerances=tolerances,
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,
        )

    @property
    def unlocked(self) -> tuple[str, ...]:
        return tuple(self._unlocked)

    @property
    def glyphs(self) -> Mapping[str, ComposedGlyph]:
        """Unlocked glyphs only (refused candidates are not kept)."""
        return {ch: self._glyphs[ch] for ch in self._unlocked}

    @property
    def last_reports(self) -> tuple[StyleConsistencyReport, ...]:
        return self._last_reports

    @property
    def is_complete(self) -> bool:
        if not self.planned_order:
            return False
        return all(ch in self._unlocked for ch in self.planned_order)

    def next_planned(self) -> str | None:
        """Next letter in ``planned_order`` that is not yet unlocked."""
        for ch in self.planned_order:
            if ch not in self._unlocked:
                return ch
        return None

    def _pair_reports(
        self, name: str, glyph: ComposedGlyph
    ) -> tuple[StyleConsistencyReport, ...]:
        if name == self.control:
            raise DesignSequenceError(
                f"{name!r} is the control — already unlocked at start"
            )
        if self.control not in self._glyphs:
            raise DesignSequenceError("session has no control glyph")
        reports: list[StyleConsistencyReport] = []
        skip_c: Sequence[str] = ()
        if self.skip_checks_for_pair is not None:
            skip_c = tuple(self.skip_checks_for_pair(self.control, name) or ())
        reports.append(
            compare_glyph_styles(
                self._glyphs[self.control],
                glyph,
                reference_name=self.control,
                candidate_name=name,
                tolerances=self.tolerances,
                skip_checks=skip_c,
            )
        )
        if self.compare_to_previous and self._unlocked:
            prev = self._unlocked[-1]
            if prev != self.control:
                skip_p: Sequence[str] = ()
                if self.skip_checks_for_pair is not None:
                    skip_p = tuple(self.skip_checks_for_pair(prev, name) or ())
                reports.append(
                    compare_glyph_styles(
                        self._glyphs[prev],
                        glyph,
                        reference_name=prev,
                        candidate_name=name,
                        tolerances=self.tolerances,
                        skip_checks=skip_p,
                    )
                )
        return tuple(reports)

    def try_add(self, name: str, glyph: ComposedGlyph) -> StyleConsistencyReport:
        """Propose ``glyph`` as ``name``. Unlock only if every gate passes.

        Returns the **control** comparison report (always). When a previous
        letter exists, both control and previous must pass; the returned
        report's ``passed`` is True only if all comparisons passed. Inspect
        :attr:`last_reports` for every comparison and
        :meth:`StyleConsistencyReport.fix_hints` for actionable text.
        """
        reports = self._pair_reports(name, glyph)
        self._last_reports = reports
        ok = all(r.passed for r in reports)
        if ok:
            self._glyphs[name] = glyph
            if name not in self._unlocked:
                self._unlocked.append(name)
        # Primary report = vs control (first); annotate aggregate pass.
        primary = reports[0]
        if len(reports) > 1 and primary.passed and not reports[1].passed:
            # Surface previous failure as the returned pass flag.
            return StyleConsistencyReport(
                reference_name=reports[1].reference_name,
                candidate_name=reports[1].candidate_name,
                checks=reports[1].checks,
                passed=False,
                reference=reports[1].reference,
                candidate=reports[1].candidate,
            )
        return primary

    def add(self, name: str, glyph: ComposedGlyph) -> ComposedGlyph:
        """Like :meth:`try_add` but raise :exc:`DesignSequenceError` on refuse."""
        report = self.try_add(name, glyph)
        if not report.passed:
            hints = "; ".join(self.last_reports and self.hints_from_last() or [])
            raise DesignSequenceError(
                f"refused glyph {name!r}: style gate failed"
                + (f" — {hints}" if hints else ""),
                reports=self._last_reports,
            )
        return glyph

    def hints_from_last(self) -> tuple[str, ...]:
        out: list[str] = []
        for rep in self._last_reports:
            out.extend(rep.fix_hints())
        return tuple(out)

    def export_glyphs(self, *, require_complete: bool = True) -> dict[str, ComposedGlyph]:
        """Copy unlocked glyphs. Refuse if ``require_complete`` and plan unfinished."""
        if require_complete and self.planned_order and not self.is_complete:
            missing = [ch for ch in self.planned_order if ch not in self._unlocked]
            raise DesignSequenceError(
                f"sequence incomplete; still need {missing!r} "
                f"(unlocked={list(self._unlocked)!r})"
            )
        return dict(self.glyphs)

    def sequence_report(self) -> SequenceStyleReport:
        """Re-run the batch gate over currently unlocked glyphs."""
        order = self._unlocked if self._unlocked else (self.control,)
        return check_design_sequence(
            self.glyphs,
            order,
            control=self.control,
            tolerances=self.tolerances,
            compare_to_previous=self.compare_to_previous,
            skip_checks_for_pair=self.skip_checks_for_pair,
        )
