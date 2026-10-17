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
    "DEFAULT_CAP_DESIGN_ORDER",
    "DEFAULT_DIGIT_DESIGN_ORDER",
    "DEFAULT_PUNCT_DESIGN_ORDER",
    "DesignSequence",
    "DesignSequenceError",
    "charset_unlock_needs",
    "controls_body_tolerances",
    "controls_cap_tolerances",
    "controls_digit_tolerances",
    "controls_punct_tolerances",
    "default_body_design_order",
    "default_cap_design_order",
    "default_digit_design_order",
    "default_punct_design_order",
    "ensure_controls_body_unlocked",
    "ensure_controls_unlocked_for_charset",
    "ensure_mark_composites_gated",
    "extended_latin_topology_skip_checks",
    "italic_topology_skip_checks",
    "latin_cap_topology_skip_checks",
    "latin_digit_topology_skip_checks",
    "latin_punct_topology_skip_checks",
    "latin_topology_skip_checks",
    "script_sequence_tolerances",
    "script_topology_skip_checks",
    "try_unlock_script_builders",
    "unlock_controls_body",
    "unlock_controls_body_ladder",
    "unlock_controls_caps",
    "unlock_controls_digits",
    "unlock_controls_digits_ladder",
    "unlock_controls_extended_latin",
    "unlock_controls_italic_body",
    "unlock_controls_punct",
    "unlock_script_builders",
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


# Cap control H/O then related capitals (designer-order sketch).
DEFAULT_CAP_DESIGN_ORDER: tuple[str, ...] = (
    "H",
    "O",
    "I",
    "L",
    "E",
    "F",
    "T",
    "U",
    "D",
    "B",
    "P",
    "R",
    "C",
    "G",
    "Q",
    "S",
    "J",
    "A",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "K",
    "M",
    "N",
)


def default_cap_design_order() -> tuple[str, ...]:
    """Default uppercase designer order for Controls-derived Latin faces."""
    return DEFAULT_CAP_DESIGN_ORDER


# Lining figures derive from cap H/O (:data:`~typekernel.parts.family.FIGURE_FORMS`).
# Designer order: stem control ``1``, round ``0``, then H-stem figures, open
# bowls, closed bowls — mirrors H/O then related for caps.
DEFAULT_DIGIT_DESIGN_ORDER: tuple[str, ...] = (
    "1",
    "0",
    "7",
    "4",
    "2",
    "5",
    "3",
    "6",
    "9",
    "8",
)


def default_digit_design_order() -> tuple[str, ...]:
    """Default lining-figure designer order for Controls-derived Latin faces."""
    return DEFAULT_DIGIT_DESIGN_ORDER


# Topology roles where some style metrics are meaningless across letters.
_CLOSED_BOWLS: frozenset[str] = frozenset({"o", "O", "0", "Q", "G"})  # open c/e/C live in _OPEN_ROUNDS
# Openings / crossbars make vertical stem probes hit hairlines or eye bars.
_OPEN_ROUNDS: frozenset[str] = frozenset({"c", "e", "C"})
_ASCENDERS: frozenset[str] = frozenset(
    {"b", "d", "f", "h", "k", "l", "t", "B", "D", "F", "H", "K", "L", "P", "R", "T"}
)
_DESCENDERS: frozenset[str] = frozenset({"g", "j", "p", "q", "y", "J", "Q"})
_DOTTED: frozenset[str] = frozenset({"i", "j"})
_DIAGONALS: frozenset[str] = frozenset({"v", "w", "x", "y", "z", "k"})
# Diagonals with stable oriented-stem pairwise compare (no descender / arm chaos).
_STABLE_DIAGONALS: frozenset[str] = frozenset({"v", "w"})
# Residual stem skips for letters whose probes are still untrustworthy after
# oriented + vertical-equiv gating in :mod:`style_consistency`. Empty for the
# geometric_sans ladder (``x``/``z``/``k``/``y`` are gated). If a letter must
# return here, document *why* and add a regression that fails when measurement
# becomes wrongly confident (see tests/qa/test_design_sequence.py).
_UNSTABLE_DIAG_STEM: frozenset[str] = frozenset()
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
    # Oriented stem only for stable diagonal pairs (``v``/``w``/``x``).
    if not (ref in _STABLE_DIAGONALS and cand in _STABLE_DIAGONALS):
        skip.append("oriented_stem")
    if ref in _ASCENDERS or cand in _ASCENDERS:
        skip.extend(["ink_ymax", "bowl_center_y"])
    if ref in _DESCENDERS or cand in _DESCENDERS:
        skip.extend(["ink_ymin", "bowl_center_y"])
    if ref in _BASELINE_HOOKS or cand in _BASELINE_HOOKS:
        # ``t`` hook spring often sits below baseline without a full descender.
        skip.extend(["ink_ymin"])
    if ref in _DOTTED or cand in _DOTTED:
        # Tittle extent / centre differ from ``n``; stem of the upright shaft is
        # comparable and stays gated (probes hit the stem, not the tittle).
        skip.extend(["ink_ymax", "bowl_center_y", "contrast_ratio"])
    if ref in _DIAGONALS or cand in _DIAGONALS:
        # H/V contrast on diagonals is meaningless; stem is gated via body /
        # oriented probes (see ``extract_glyph_style_metrics``). Serif feet /
        # sharp overshoot make ink_ymin non-comparable to upright controls.
        skip.extend(["contrast_ratio", "ink_ymin"])
    # Pairwise stem among unlike diagonals (``x``↔``z``, ``k``↔``v``, …) is not
    # comparable — constructions differ. Each still gates stem against control
    # ``n``. Stable ``v``↔``w`` keep pairwise stem + oriented.
    if (
        ref in _DIAGONALS
        and cand in _DIAGONALS
        and not (ref in _STABLE_DIAGONALS and cand in _STABLE_DIAGONALS)
    ):
        skip.append("stem_median")
    if ref in _UNSTABLE_DIAG_STEM or cand in _UNSTABLE_DIAG_STEM:
        skip.extend(["stem_median"])
    if ref in _MULTI_ARCH or cand in _MULTI_ARCH:
        # Double/triple arches: H/V contrast probes hit joins, not stems.
        skip.extend(["contrast_ratio"])
    if ref in _CURVED_SPINE or cand in _CURVED_SPINE:
        # ``s`` has no stable vertical stem band — probes hit the spine curve.
        skip.extend(["stem_median", "contrast_ratio"])
    # Closed ``o`` and open ``c``/``e``: contrast gated via polar / midbar
    # probes (black ``e`` midbar collapse falls back to polar). Stem stays
    # gated via back-stem / aperture-aware ``_body_stem_median``.
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
        stem_median_rel=0.20,
        contrast_ratio=0.45,
        entry_rail_y=36.0,
        exit_rail_y=36.0,
        exit_slant_deg=35.0,
        bowl_center_y=55.0,
        ink_ymin=55.0,
        ink_ymax=400.0,
    )


# ---------------------------------------------------------------------------
# Script / skeleton DesignSequence (letter-writing faces, not Controls Latin)
# ---------------------------------------------------------------------------

# Role sets for calligraphy / writing-script topology (rails stay gated).
_SCRIPT_CLOSED_BOWLS: frozenset[str] = frozenset({"o", "O"})
_SCRIPT_ASCENDERS: frozenset[str] = frozenset(
    {"d", "h", "D", "l", "b", "k", "f", "t"}
)
_SCRIPT_DESCENDERS: frozenset[str] = frozenset({"j", "y", "g", "p", "q"})
_SCRIPT_DOTTED: frozenset[str] = frozenset({"i", "j"})


def script_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Metric skips across script topology roles (rails stay meaningful).

    Unlike :func:`latin_topology_skip_checks`, entry/exit rails and exit slant
    are **gated** for same-role body letters — they are the writing-connection
    language. Closed bowls omit rails; ascenders/descenders/dotted letters omit
    extents and rail metrics that topology makes meaningless.
    """
    skip: list[str] = []
    if ref in _SCRIPT_CLOSED_BOWLS or cand in _SCRIPT_CLOSED_BOWLS:
        skip.extend(["entry_rail_y", "exit_rail_y", "exit_slant_deg"])
    if cand in _SCRIPT_ASCENDERS or ref in _SCRIPT_ASCENDERS:
        skip.extend(["ink_ymax", "bowl_center_y", "exit_rail_y", "exit_slant_deg"])
    if cand in _SCRIPT_DESCENDERS or ref in _SCRIPT_DESCENDERS:
        # Descender loops poison lower-band exit-angle samples.
        skip.extend(["ink_ymin", "bowl_center_y", "entry_rail_y", "exit_slant_deg"])
    if cand in _SCRIPT_DOTTED or ref in _SCRIPT_DOTTED:
        # Single stem + tittle: vertical-stem probes are not comparable to
        # dual-stem body letters.
        skip.extend(
            [
                "exit_rail_y",
                "exit_slant_deg",
                "ink_ymax",
                "bowl_center_y",
                "stem_median",
            ]
        )
    return tuple(dict.fromkeys(skip))


def script_sequence_tolerances() -> StyleConsistencyTolerances:
    """Budgets for full script DesignSequence unlock (control → charset).

    Rails/slant/stem stay near body defaults. Contrast is wider than
    :func:`~typekernel.qa.style_consistency.script_body_tolerances` to allow
    multi-vertical pen stress (``u``/``h``) without phrase-batch fudge — still
    paired with :func:`script_topology_skip_checks`, not a blank cheque.
    Same-role pairs (``a`` vs ``e``) should prefer ``script_body_tolerances``.
    """
    return StyleConsistencyTolerances(
        stem_median=14.0,
        contrast_ratio=0.95,
        entry_rail_y=40.0,
        exit_rail_y=42.0,
        exit_slant_deg=40.0,
        bowl_center_y=55.0,
        ink_ymin=55.0,
        ink_ymax=120.0,
    )


def try_unlock_script_builders(
    builders: Mapping[str, Callable[[], ComposedGlyph]],
    *,
    control: str,
    order: Sequence[str],
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> tuple[DesignSequence, SequenceStyleReport]:
    """Unlock a script/skeleton face one glyph at a time (soft refuse).

    Builds each letter via ``builders[ch]()``. On the first style refuse,
    returns the partial :class:`DesignSequence` plus a
    :class:`~typekernel.qa.style_consistency.SequenceStyleReport` that includes
    the refused candidate for diagnostics — later letters are not built.
    On full unlock, ``report.passed`` is True.
    """
    seq = DesignSequence.from_builders(
        builders,
        control=control,
        order=order,
        tolerances=tolerances,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=skip_checks_for_pair,
    )
    skips = seq.skip_checks_for_pair
    tol = seq.tolerances
    for ch in seq.planned_order:
        if ch == seq.control:
            continue
        if ch not in builders:
            raise KeyError(f"no builder for planned glyph {ch!r}")
        glyph = builders[ch]()
        report = seq.try_add(ch, glyph)
        if not report.passed:
            drawn = dict(seq.glyphs)
            drawn[ch] = glyph
            full = check_design_sequence(
                drawn,
                tuple(drawn.keys()),
                control=control,
                tolerances=tol,
                compare_to_previous=compare_to_previous,
                skip_checks_for_pair=skips,
            )
            return seq, full
    return seq, seq.sequence_report()


def unlock_script_builders(
    builders: Mapping[str, Callable[[], ComposedGlyph]],
    *,
    control: str,
    order: Sequence[str],
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> DesignSequence:
    """Like :func:`try_unlock_script_builders` but raise on the first refuse."""
    seq, report = try_unlock_script_builders(
        builders,
        control=control,
        order=order,
        tolerances=tolerances,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=skip_checks_for_pair,
    )
    if not report.passed:
        hints: list[str] = []
        for rep in report.failures:
            hints.extend(rep.fix_hints())
        raise DesignSequenceError(
            "script DesignSequence refused a glyph"
            + (f" — {'; '.join(hints)}" if hints else ""),
            reports=tuple(report.failures),
        )
    return seq


# ---------------------------------------------------------------------------
# True italic Controls DesignSequence (construct slant ≠ oblique_font)
# ---------------------------------------------------------------------------

# Branching arches (TK-403): H/V contrast probes differ from upright ``n``.
_ITALIC_BRANCHING: frozenset[str] = frozenset({"n", "h", "r", "u", "m"})


def italic_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Latin topology skips plus construct-italic realities.

    - ``f`` reaches the descender zone under italic topology → skip ``ink_ymin``.
    - Branching ``n``/``h``/``r``/``u``/``m`` change H/V samples → skip contrast.

    Does **not** widen absolute tolerances. Diagonals ``k``/``v``/``w``/``x``/
    ``y``/``z`` use cursive-cubic italic constructions (topology differs from
    shear); non-diagonal branching uses a shared stem→shoulder fillet; further letterform craft remains open.
    """
    skip = list(latin_topology_skip_checks(ref, cand))
    if ref in {"f"} or cand in {"f"}:
        skip.append("ink_ymin")
    if ref in _ITALIC_BRANCHING or cand in _ITALIC_BRANCHING:
        skip.append("contrast_ratio")
    return tuple(dict.fromkeys(skip))


def unlock_controls_italic_body(
    regular: Controls,
    *,
    style: object | None = None,
    control: str = "n",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> DesignSequence:
    """Unlock Latin body on an :func:`~typekernel.parts.italic.italic_design` sheet.

    Agent path for true italic (construct slant + branching), **not**
    :func:`~typekernel.compile.oblique.oblique_font`. Defaults to
    :func:`italic_topology_skip_checks` and :func:`controls_body_tolerances`.
    """
    from typekernel.parts.italic import ItalicStyle, italic_design

    if style is not None and not isinstance(style, ItalicStyle):
        raise TypeError("style must be ItalicStyle | None")
    ital = italic_design(regular, style=style)
    skips = skip_checks_for_pair or italic_topology_skip_checks
    return unlock_controls_body(
        ital,
        control=control,
        order=order,
        tolerances=tolerances,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=skips,
    )


# ---------------------------------------------------------------------------
# Extended Latin outline forms (æø / ÆØ) — gated, not silent ship
# ---------------------------------------------------------------------------

_DEFAULT_EXTENDED_LATIN_ORDER: tuple[str, ...] = ("æ", "ø", "Æ", "Ø")


def extended_latin_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Skips for outline extended Latin vs body/cap controls.

    ``æ``/``Æ`` are dual-letter ligatures — stem/contrast vs single controls
    are not comparable. ``ø`` slash shifts bowl centre vs ``o``. ``Ø`` keeps
    Latin cap skips aside from ligature exemptions on ``Æ``.
    """
    if cand in {"Æ", "Ø"} or ref in {"Æ", "Ø"}:
        skip = list(latin_cap_topology_skip_checks(ref, cand))
        if cand == "Æ" or ref == "Æ":
            skip.extend(["stem_median", "contrast_ratio"])
        return tuple(dict.fromkeys(skip))
    skip = list(latin_topology_skip_checks(ref, cand))
    if cand == "æ" or ref == "æ":
        skip.extend(["stem_median", "contrast_ratio"])
    if cand == "ø" or ref == "ø":
        skip.append("bowl_center_y")
    return tuple(dict.fromkeys(skip))


def unlock_controls_extended_latin(
    controls: Controls,
    *,
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = False,
) -> DesignSequence:
    """Gate outline extended Latin after body (and caps when present) unlock.

    Order defaults to ``æ ø Æ Ø`` filtered to forms the sheet can build.
    Each letter is style-checked against a related control (``a``/``o``/``H``/
    ``O``) with :func:`extended_latin_topology_skip_checks` — not ungated
    ``build_all`` alone.
    """
    from typekernel.parts.extended_latin import (
        EXTENDED_LATIN_CAP_FORMS,
        EXTENDED_LATIN_FORMS,
    )

    planned = tuple(order) if order is not None else _DEFAULT_EXTENDED_LATIN_ORDER
    # Ensure base unlocks first.
    need_caps = any(ch in EXTENDED_LATIN_CAP_FORMS for ch in planned)
    unlock_controls_body(controls)
    if need_caps:
        unlock_controls_caps(controls)

    # Pick first available lowercase as session control for the sequence object.
    control = "a" if "æ" in planned or "ø" in planned else "H"
    if control == "a":
        control_glyph = controls.build("a")
        tol = tolerances if tolerances is not None else controls_body_tolerances()
    else:
        control_glyph = controls.build("H")
        tol = tolerances if tolerances is not None else controls_cap_tolerances()

    seq = DesignSequence.start(
        control,
        control_glyph,
        tolerances=tol,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=extended_latin_topology_skip_checks,
        planned_order=(control, *planned),
    )

    pair_control = {
        "æ": "a",
        "ø": "o",
        "Æ": "H",
        "Ø": "O",
    }
    for ch in planned:
        if ch in EXTENDED_LATIN_FORMS or ch in EXTENDED_LATIN_CAP_FORMS:
            glyph = controls.build(ch)
        else:
            raise KeyError(f"no extended Latin form for {ch!r}")
        # Force comparison against the related control by temporarily using
        # try_add (compares vs session control + previous). For æ/ø session
        # control is a; for caps-only it is H. Also compare explicitly to pair.
        ref_name = pair_control[ch]
        ref_glyph = controls.build(ref_name)
        skip = extended_latin_topology_skip_checks(ref_name, ch)
        report = compare_glyph_styles(
            ref_glyph,
            glyph,
            reference_name=ref_name,
            candidate_name=ch,
            tolerances=tol if ch.islower() else controls_cap_tolerances(),
            skip_checks=skip,
        )
        if not report.passed:
            raise DesignSequenceError(
                f"extended Latin refused {ch!r} vs {ref_name!r}",
                reports=(report,),
            )
        # Record unlock without re-running mismatched session control pairs.
        seq._glyphs[ch] = glyph
        if ch not in seq._unlocked:
            seq._unlocked.append(ch)
        seq._last_reports = (report,)
    return seq


def latin_cap_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Metric skips for uppercase DesignSequence (H/O control path).

    Reuses lowercase role sets where letters overlap, plus cap diagonals
    ``A V W X Y Z K M N``. Round/soft caps gate contrast except spine ``S``.
    """
    skip: list[str] = [
        "entry_rail_y",
        "exit_rail_y",
        "exit_slant_deg",
    ]
    cap_diags = frozenset({"A", "V", "W", "X", "Y", "Z", "K", "M", "N"})
    # Cap diagonals (especially ``W`` vs ``V``) inflate oriented pairwise; gate
    # stem against control ``H`` via stem_median / vertical-equiv instead.
    skip.append("oriented_stem")
    if ref in _ASCENDERS or cand in _ASCENDERS:
        skip.extend(["ink_ymax", "bowl_center_y"])
    if ref in _DESCENDERS or cand in _DESCENDERS:
        skip.extend(["ink_ymin", "bowl_center_y"])
    if ref in _DIAGONALS or cand in _DIAGONALS or ref in cap_diags or cand in cap_diags:
        skip.extend(["contrast_ratio"])
    # Pairwise stem among unlike cap diagonals is not comparable (``V``↔``W``,
    # ``A``↔``X``, …). Each still gates stem against control ``H``, except
    # ``W`` whose four diagonals are intentionally lighter than ``H`` by
    # construction (:func:`~typekernel.parts.caps.W_from_H`).
    if ref in cap_diags and cand in cap_diags:
        skip.append("stem_median")
    if ref in {"W", "w"} or cand in {"W", "w"}:
        skip.append("stem_median")
    # Contrast: gate closed/open/soft bowls plus ``R``/``U`` (narrow bar /
    # base-arc probes). Keep skip for ``S`` — spine waist vs ``H`` bar is not
    # stable at light weights (geo default Q→S).
    _cap_contrast_skip = frozenset({"S"})
    if ref in _cap_contrast_skip or cand in _cap_contrast_skip:
        skip.extend(["contrast_ratio"])
    if ref in _OPEN_ROUNDS or cand in _OPEN_ROUNDS:
        skip.extend(["stem_median"])
    if ref in _CURVED_SPINE or cand in _CURVED_SPINE:
        skip.extend(["stem_median", "contrast_ratio"])
    return tuple(dict.fromkeys(skip))


def controls_cap_tolerances() -> StyleConsistencyTolerances:
    """Budgets for Controls Latin capital sequences (from ``H``/``O``)."""
    return StyleConsistencyTolerances(
        stem_median=20.0,
        stem_median_rel=0.20,
        contrast_ratio=0.50,
        entry_rail_y=36.0,
        exit_rail_y=36.0,
        exit_slant_deg=35.0,
        bowl_center_y=80.0,
        ink_ymin=55.0,
        ink_ymax=120.0,
    )



def ensure_mark_composites_gated(
    controls: Controls,
    charset: str,
    *,
    require: bool = True,
) -> Controls:
    """Refuse silent ship of mark composites without base DesignSequence unlock.

    When *charset* contains any :data:`~typekernel.parts.diacritics.COMPOSITE_LATIN`
    character (or the caller passes the full composite set), runs body / caps
    unlocks as needed. Does **not** style-gate each precomposed accent — those
    are mark attachments — but bases must have passed
    :func:`unlock_controls_body` / :func:`unlock_controls_caps`.

    Pass ``require=False`` only for documented stock / specimen compiles.
    """
    from typekernel.parts.diacritics import COMPOSITE_LATIN

    if not require:
        return controls
    composite_chars = {row[0] for row in COMPOSITE_LATIN}
    present = [ch for ch in charset if ch in composite_chars]
    if not present:
        return controls
    need_body, need_caps, _, _ = charset_unlock_needs("".join(present))
    if need_body:
        unlock_controls_body(controls)
    if need_caps:
        unlock_controls_caps(controls)
    return controls




def charset_unlock_needs(charset: str) -> tuple[bool, bool, bool, bool]:
    """Which DesignSequence unlocks a charset requires.

    Returns ``(body, caps, digits, punct)``. Outline extended Latin (``æø`` /
    ``ÆØ``) and mark composites (``á``/``É``/…) count as body / caps so compose
    cannot ship them after skipping the base unlocks.
    """
    from typekernel.parts.diacritics import COMPOSITE_LATIN
    from typekernel.parts.extended_latin import (
        EXTENDED_LATIN_CAP_FORMS,
        EXTENDED_LATIN_FORMS,
    )
    from typekernel.parts.family import CAP_FORMS, FIGURE_FORMS, PUNCT_FORMS, RELATED_FORMS

    composite_chars = {row[0] for row in COMPOSITE_LATIN}
    need_body = any(
        ch in RELATED_FORMS
        or ch in EXTENDED_LATIN_FORMS
        or (ch in composite_chars and ch.islower())
        for ch in charset
    )
    # Uppercase composites and any composite that uses a cap base need caps.
    need_caps = any(
        ch in CAP_FORMS
        or ch in EXTENDED_LATIN_CAP_FORMS
        or (ch in composite_chars and ch.isupper())
        for ch in charset
    )
    # Lowercase composites whose base is a related form already set need_body;
    # ñ/ç etc. still need body. Cap composites like Ç need caps (above).
    if any(ch in composite_chars for ch in charset):
        need_body = True
    need_digits = any(ch in FIGURE_FORMS for ch in charset)
    need_punct = any(ch in PUNCT_FORMS for ch in charset)
    return need_body, need_caps, need_digits, need_punct


def ensure_controls_unlocked_for_charset(
    controls: Controls,
    charset: str,
    *,
    require: bool = True,
) -> Controls:
    """Run body / caps / digits / punct DesignSequence unlocks present in ``charset``.

    Shared gate for compose / preview / kern-class entrypoints. When ``require``
    is true (default), refuses if any applicable subset fails. Pass
    ``require=False`` only for documented stock / specimen compiles.
    """
    if not require:
        return controls
    from typekernel.parts.extended_latin import (
        EXTENDED_LATIN_CAP_FORMS,
        EXTENDED_LATIN_FORMS,
    )

    need_body, need_caps, need_digits, need_punct = charset_unlock_needs(charset)
    if need_body:
        unlock_controls_body(controls)
    if need_caps:
        unlock_controls_caps(controls)
    if need_digits:
        unlock_controls_digits(controls)
    if need_punct:
        unlock_controls_punct(controls)
    extended = [
        ch
        for ch in charset
        if ch in EXTENDED_LATIN_FORMS or ch in EXTENDED_LATIN_CAP_FORMS
    ]
    if extended:
        unlock_controls_extended_latin(controls, order=tuple(dict.fromkeys(extended)))
    ensure_mark_composites_gated(controls, charset, require=True)
    return controls


def ensure_controls_body_unlocked(
    controls: Controls,
    *,
    require: bool = True,
    control: str = "n",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> Controls:
    """Body-only gate (legacy). Prefer :func:`ensure_controls_unlocked_for_charset`.

    When ``require`` is true (default), runs :func:`unlock_controls_body` and
    re-raises :class:`DesignSequenceError`. Compose / preview use the charset
    helper so caps and digits cannot ship ungated. Pass ``require=False`` only
    for documented stock / specimen compile paths.
    """
    if require:
        unlock_controls_body(
            controls,
            control=control,
            order=order,
            tolerances=tolerances,
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,
        )
    return controls


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




# Digit topology roles (lining figures at cap height from H/O).
_DIGIT_OPEN: frozenset[str] = frozenset({"2", "3", "5"})
# Openings / crossbars: vertical stem probes hit hairlines or bars (like ``c``/``e``).
_DIGIT_CLOSED: frozenset[str] = frozenset({"0", "6", "9"})
_DIGIT_DOUBLE_BOWL: frozenset[str] = frozenset({"8"})
# Waist / double-counter probes are not a single stem band vs control ``1``.
_DIGIT_DIAGONAL: frozenset[str] = frozenset({"4", "7"})


def latin_digit_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Metric skips for lining-figure DesignSequence (control ``1`` path).

    Rails/slant are script proxies — always omitted. Stem stays gated for
    stem-like figures (``1``/``4``/``7``/``0``/``6``/``9``); open ``2``/``3``/``5``
    and double-bowl ``8`` skip stem where probes are unreliable. Contrast is
    gated for closed and open figures (polar/bar H/V); omitted for diagonal
    ``4``/``7`` where H/V samples are unstable.
    """
    skip: list[str] = [
        "entry_rail_y",
        "exit_rail_y",
        "exit_slant_deg",
        "oriented_stem",
    ]
    if (
        ref in _DIGIT_OPEN
        or cand in _DIGIT_OPEN
        or ref in _DIGIT_DOUBLE_BOWL
        or cand in _DIGIT_DOUBLE_BOWL
    ):
        # Stem probes still unreliable on opens / ``8``; contrast is gated below.
        skip.append("stem_median")
    # Contrast: gate closed ``0``/``6``/``9`` and opens/``8`` (polar/bar H/V).
    # Keep skip for diagonal ``4``/``7`` only.
    _digit_contrast_skip = _DIGIT_DIAGONAL
    if ref in _digit_contrast_skip or cand in _digit_contrast_skip:
        skip.append("contrast_ratio")
    if (
        ref in _DIGIT_CLOSED
        or cand in _DIGIT_CLOSED
        or ref in _DIGIT_OPEN
        or cand in _DIGIT_OPEN
        or ref in _DIGIT_DOUBLE_BOWL
        or cand in _DIGIT_DOUBLE_BOWL
    ):
        # Slight overshoot on rounds vs flat ``1`` baseline.
        skip.append("ink_ymin")
    return tuple(dict.fromkeys(skip))


def controls_digit_tolerances() -> StyleConsistencyTolerances:
    """Budgets for Controls lining figures (from stem control ``1``).

    Figures sit at cap height with ``FIGURE_STEM_RATIO`` strokes — slightly
    wider absolute stem band than body, same relative slack as caps.
    """
    return StyleConsistencyTolerances(
        stem_median=20.0,
        stem_median_rel=0.20,
        contrast_ratio=0.50,
        entry_rail_y=36.0,
        exit_rail_y=36.0,
        exit_slant_deg=35.0,
        bowl_center_y=80.0,
        ink_ymin=55.0,
        ink_ymax=120.0,
    )


def unlock_controls_digits(
    controls: Controls,
    *,
    control: str = "1",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> DesignSequence:
    """Unlock Controls lining figures one glyph at a time (``1``-first order).

    Stock presets must complete :data:`DEFAULT_DIGIT_DESIGN_ORDER` under
    :func:`controls_digit_tolerances`. Figures derive from cap ``H``/``O``;
    run after caps are locked when redesigning figure masters.
    """
    planned = tuple(order) if order is not None else default_digit_design_order()
    if control not in planned or planned[0] != control:
        planned = (control, *[c for c in planned if c != control])
    skips = skip_checks_for_pair
    if skips is None:
        skips = latin_digit_topology_skip_checks
    tol = tolerances if tolerances is not None else controls_digit_tolerances()
    seq = DesignSequence.start(
        control,
        controls.build(control),
        tolerances=tol,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=skips,
        planned_order=planned,
    )
    for ch in seq.planned_order:
        if ch == seq.control:
            continue
        seq.add(ch, controls.build(ch))
    return seq


def unlock_controls_digits_ladder(
    template: Controls,
    stems: Sequence[float] | None = None,
    *,
    control: str = "1",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> dict[float, DesignSequence]:
    """Unlock lining figures on each weight-ladder master (VF / family path).

    Same stem-master construction as :func:`unlock_controls_body_ladder`.
    """
    from typekernel.qa.trial_protocol import (
        WEIGHT_LADDER_STEMS,
        controls_at_ladder_stem,
    )

    ladder = tuple(stems) if stems is not None else WEIGHT_LADDER_STEMS
    out: dict[float, DesignSequence] = {}
    for stem in ladder:
        sheet = controls_at_ladder_stem(template, float(stem))
        out[float(stem)] = unlock_controls_digits(
            sheet,
            control=control,
            order=order,
            tolerances=tolerances,
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,
        )
    return out


def unlock_controls_caps(
    controls: Controls,
    *,
    control: str = "H",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> DesignSequence:
    """Unlock Controls capitals one glyph at a time (H/O-first designer order).

    Partial but real API: stock presets must complete
    :data:`DEFAULT_CAP_DESIGN_ORDER` under :func:`controls_cap_tolerances`.
    """
    planned = tuple(order) if order is not None else default_cap_design_order()
    if control not in planned or planned[0] != control:
        planned = (control, *[c for c in planned if c != control])
    skips = skip_checks_for_pair
    if skips is None:
        skips = latin_cap_topology_skip_checks
    tol = tolerances if tolerances is not None else controls_cap_tolerances()
    seq = DesignSequence.start(
        control,
        controls.build(control),
        tolerances=tol,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=skips,
        planned_order=planned,
    )
    for ch in seq.planned_order:
        if ch == seq.control:
            continue
        seq.add(ch, controls.build(ch))
    return seq



# ---------------------------------------------------------------------------
# Punctuation DesignSequence (control "." — period as the atomic mark)
# ---------------------------------------------------------------------------

DEFAULT_PUNCT_DESIGN_ORDER: tuple[str, ...] = (
    ".",
    ",",
    ";",
    ":",
    "!",
    "?",
    "'",
    '"',
    "\u2018",
    "\u2019",
    "\u201c",
    "\u201d",
    "\u00b0",
    "*",
    "-",
    "\u2212",
    "\u2013",
    "\u2014",
    "_",
    "=",
    "+",
    "<",
    ">",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    "/",
    "\\",
    "#",
    "&",
    "%",
    "@",
    "$",
)

_PUNCT_QUOTES: frozenset[str] = frozenset(
    {"'", '"', "\u2018", "\u2019", "\u201c", "\u201d"}
)
_PUNCT_RINGS: frozenset[str] = frozenset({"\u00b0", "*"})
_PUNCT_BAR_CORE: frozenset[str] = frozenset({"-", "\u2013", "\u2014", "\u2212"})
_PUNCT_BARS: frozenset[str] = frozenset(
    {"-", "\u2013", "\u2014", "\u2212", "_", "=", "+", "<", ">"}
)
_PUNCT_BRACKETS: frozenset[str] = frozenset({"(", ")", "[", "]", "{", "}"})
_PUNCT_BRACKET_PAIRS: tuple[frozenset[str], ...] = (
    frozenset({"(", ")"}),
    frozenset({"[", "]"}),
    frozenset({"{", "}"}),
)
_PUNCT_SLASHES: frozenset[str] = frozenset({"/", "\\"})
_PUNCT_COMPLEX: frozenset[str] = frozenset({"#", "&", "%", "@", "$"})


def default_punct_design_order() -> tuple[str, ...]:
    """Default punctuation designer order for Controls-derived Latin faces."""
    return DEFAULT_PUNCT_DESIGN_ORDER


def latin_punct_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Metric skips for punctuation DesignSequence (control ``.`` path).

    Same-role pairs keep honest gates; cross-role pairs (including most marks
    vs period) skip metrics that would false-fail. Period bridges keep
    ``ink_ymax`` for ``,`` and stem / ``ink_ymin`` for ``!``.
    """
    skip: list[str] = [
        "entry_rail_y",
        "exit_rail_y",
        "exit_slant_deg",
        "oriented_stem",
    ]
    pair = frozenset({ref, cand})

    if pair == {".", ","}:
        skip.extend(["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymin"])
        return tuple(dict.fromkeys(skip))
    if pair == {".", "!"}:
        # Period tittle is size-capped (``x_height×0.145``); bang stem tracks
        # ``n.stem`` — stem compare is not the same role at heavy weights.
        skip.extend(
            ["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymax"]
        )
        return tuple(dict.fromkeys(skip))  # keep ink_ymin (shared baseline sit)
    if "." in pair:
        skip.extend(
            ["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymin", "ink_ymax"]
        )
        return tuple(dict.fromkeys(skip))

    if pair == {",", ";"}:
        skip.extend(
            ["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymin", "ink_ymax"]
        )
        return tuple(dict.fromkeys(skip))
    if pair == {"!", "?"}:
        skip.extend(["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymax"])
        return tuple(dict.fromkeys(skip))

    if ref in _PUNCT_QUOTES and cand in _PUNCT_QUOTES:
        skip.extend(["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymin"])
        return tuple(dict.fromkeys(skip))
    if ref in _PUNCT_RINGS and cand in _PUNCT_RINGS:
        skip.extend(
            ["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymin", "ink_ymax"]
        )
        return tuple(dict.fromkeys(skip))

    if ref in _PUNCT_BAR_CORE and cand in _PUNCT_BAR_CORE:
        skip.extend(["stem_median", "contrast_ratio"])
        return tuple(dict.fromkeys(skip))
    if ref in _PUNCT_BARS and cand in _PUNCT_BARS:
        skip.extend(
            ["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymin", "ink_ymax"]
        )
        return tuple(dict.fromkeys(skip))

    if ref in _PUNCT_BRACKETS and cand in _PUNCT_BRACKETS:
        # Only matching pairs share stem language; braces are thinner than [].
        if not any(pair <= group for group in _PUNCT_BRACKET_PAIRS):
            skip.extend(
                [
                    "stem_median",
                    "contrast_ratio",
                    "bowl_center_y",
                    "ink_ymin",
                    "ink_ymax",
                ]
            )
        else:
            skip.extend(["contrast_ratio", "bowl_center_y"])
        return tuple(dict.fromkeys(skip))

    if ref in _PUNCT_SLASHES and cand in _PUNCT_SLASHES:
        skip.extend(["contrast_ratio", "bowl_center_y", "ink_ymin", "ink_ymax"])
        return tuple(dict.fromkeys(skip))
    if ref in _PUNCT_COMPLEX and cand in _PUNCT_COMPLEX:
        skip.extend(["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymax"])
        return tuple(dict.fromkeys(skip))

    skip.extend(
        ["stem_median", "contrast_ratio", "bowl_center_y", "ink_ymin", "ink_ymax"]
    )
    return tuple(dict.fromkeys(skip))


def controls_punct_tolerances() -> StyleConsistencyTolerances:
    """Budgets for Controls punctuation sequences (from period control ``.``)."""
    return StyleConsistencyTolerances(
        stem_median=18.0,
        stem_median_rel=0.22,
        contrast_ratio=0.55,
        entry_rail_y=36.0,
        exit_rail_y=36.0,
        exit_slant_deg=35.0,
        bowl_center_y=80.0,
        ink_ymin=55.0,
        ink_ymax=120.0,
    )


def unlock_controls_punct(
    controls: Controls,
    *,
    control: str = ".",
    order: Sequence[str] | None = None,
    tolerances: StyleConsistencyTolerances | None = None,
    compare_to_previous: bool = True,
    skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
) -> DesignSequence:
    """Unlock Controls punctuation one glyph at a time (period-first order).

    Stock presets must complete :data:`DEFAULT_PUNCT_DESIGN_ORDER` under
    :func:`controls_punct_tolerances`.
    """
    planned = tuple(order) if order is not None else default_punct_design_order()
    if control not in planned or planned[0] != control:
        planned = (control, *[c for c in planned if c != control])
    skips = skip_checks_for_pair
    if skips is None:
        skips = latin_punct_topology_skip_checks
    tol = tolerances if tolerances is not None else controls_punct_tolerances()
    seq = DesignSequence.start(
        control,
        controls.build(control),
        tolerances=tol,
        compare_to_previous=compare_to_previous,
        skip_checks_for_pair=skips,
        planned_order=planned,
    )
    for ch in seq.planned_order:
        if ch == seq.control:
            continue
        seq.add(ch, controls.build(ch))
    return seq


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
    def from_builders(
        cls,
        builders: Mapping[str, Callable[[], ComposedGlyph]],
        *,
        control: str,
        order: Sequence[str],
        tolerances: StyleConsistencyTolerances | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: Callable[[str, str], Sequence[str]] | None = None,
    ) -> DesignSequence:
        """Start a session from zero-arg glyph builders (script / skeleton faces).

        Builds **only** the control glyph. Remaining letters in ``order`` unlock
        via :meth:`try_add` / :meth:`add`, or use :func:`try_unlock_script_builders`.
        Defaults to :func:`script_sequence_tolerances` and
        :func:`script_topology_skip_checks`.
        """
        if control not in builders:
            raise KeyError(f"control {control!r} missing from builders")
        planned = tuple(order)
        if not planned:
            raise ValueError("order must be non-empty")
        if control not in planned or planned[0] != control:
            planned = (control, *[c for c in planned if c != control])
        skips = skip_checks_for_pair
        if skips is None:
            skips = script_topology_skip_checks
        tol = (
            tolerances if tolerances is not None else script_sequence_tolerances()
        )
        return cls.start(
            control,
            builders[control](),
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
