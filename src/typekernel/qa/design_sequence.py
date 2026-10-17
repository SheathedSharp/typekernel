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
    "latin_cap_topology_skip_checks",
    "latin_digit_topology_skip_checks",
    "latin_punct_topology_skip_checks",
    "latin_topology_skip_checks",
    "unlock_controls_body",
    "unlock_controls_body_ladder",
    "unlock_controls_caps",
    "unlock_controls_digits",
    "unlock_controls_digits_ladder",
    "unlock_controls_punct",
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
    if ref in _OPEN_ROUNDS or cand in _OPEN_ROUNDS:
        # Open ``c``/``e``: H/V contrast vs stem ``n`` is not comparable —
        # aperture hairlines and crossbars dominate horizontal probes.
        skip.extend(["contrast_ratio"])
    # Closed ``o``: contrast stays gated (measurable and stable across
    # geometric_sans + slab_serif + humanist_sans). Open-round stem stays
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





def latin_cap_topology_skip_checks(ref: str, cand: str) -> tuple[str, ...]:
    """Metric skips for uppercase DesignSequence (H/O control path).

    Reuses lowercase role sets where letters overlap, plus cap diagonals
    ``A V W X Y Z K M N`` and round caps ``C G O Q S``.
    """
    skip: list[str] = [
        "entry_rail_y",
        "exit_rail_y",
        "exit_slant_deg",
    ]
    cap_diags = frozenset({"A", "V", "W", "X", "Y", "Z", "K", "M", "N"})
    cap_rounds = frozenset({"C", "G", "O", "Q", "S", "D", "B", "P", "R", "U"})
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
    if (
        ref in _CLOSED_BOWLS
        or cand in _CLOSED_BOWLS
        or ref in cap_rounds
        or cand in cap_rounds
    ):
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



def charset_unlock_needs(charset: str) -> tuple[bool, bool, bool, bool]:
    """Which DesignSequence unlocks a charset requires.

    Returns ``(body, caps, digits, punct)``.
    """
    from typekernel.parts.family import CAP_FORMS, FIGURE_FORMS, PUNCT_FORMS, RELATED_FORMS

    need_body = any(ch in RELATED_FORMS for ch in charset)
    need_caps = any(ch in CAP_FORMS for ch in charset)
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
    need_body, need_caps, need_digits, need_punct = charset_unlock_needs(charset)
    if need_body:
        unlock_controls_body(controls)
    if need_caps:
        unlock_controls_caps(controls)
    if need_digits:
        unlock_controls_digits(controls)
    if need_punct:
        unlock_controls_punct(controls)
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
    omitted for rounds / opens / diagonals (H/V samples are not figure stems).
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
        skip.extend(["stem_median", "contrast_ratio"])
    if (
        ref in _DIGIT_CLOSED
        or cand in _DIGIT_CLOSED
        or ref in _DIGIT_OPEN
        or cand in _DIGIT_OPEN
        or ref in _DIGIT_DOUBLE_BOWL
        or cand in _DIGIT_DOUBLE_BOWL
        or ref in _DIGIT_DIAGONAL
        or cand in _DIGIT_DIAGONAL
    ):
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
