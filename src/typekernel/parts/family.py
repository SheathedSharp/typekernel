"""The control sheet: draw ``n`` and ``o``, derive the lowercase from them.

:class:`Controls` holds the family proportions plus the ``n`` and ``o``
design records. :data:`RELATED_FORMS` says how every other letter derives
from those two drawn glyphs, so one adjustment (``tuned_n(counter=...)``)
moves the whole ``n`` family and ``tuned_o(rx=...)`` the ``o`` family.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from typekernel.parts.caps import (
    A_from_H,
    B_from_H,
    C_from_O,
    D_from_H,
    E_from_H,
    F_from_H,
    G_from_O,
    HMetrics,
    I_from_H,
    J_from_H,
    K_from_H,
    L_from_H,
    M_from_H,
    N_from_H,
    P_from_H,
    Q_from_O,
    R_from_H,
    S_from_O,
    T_from_H,
    U_from_H,
    V_from_H,
    W_from_H,
    X_from_H,
    Y_from_H,
    Z_from_H,
    build_H,
    build_O,
    cap_o_metrics,
    h_cap_metrics,
)
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    NMetrics,
    OMetrics,
    a_from_o,
    b_from_o,
    build_n,
    build_o,
    c_from_o,
    d_from_o,
    e_from_o,
    f_from_n,
    g_from_o,
    h_from_n,
    i_from_n,
    j_from_n,
    l_from_n,
    m_from_n,
    n_metrics,
    o_metrics,
    p_from_o,
    q_from_o,
    r_from_n,
    s_from_o,
    t_from_n,
    u_from_n,
)
from typekernel.parts.diagonals import k_from_n, v_from_n, w_from_n, x_from_n, y_from_n, z_from_n
from typekernel.parts.extended_latin import EXTENDED_LATIN_CAP_FORMS, EXTENDED_LATIN_FORMS
from typekernel.parts.figures import (
    eight_from_O,
    five_from_O,
    four_from_H,
    nine_from_O,
    one_from_H,
    seven_from_H,
    six_from_O,
    three_from_O,
    two_from_O,
    zero_from_O,
)
from typekernel.parts.glyph_specs import WEAK_GLYPH_SPECS, build_from_spec, merge_spec
from typekernel.parts.punctuation import PUNCT_FORMS
from typekernel.parts.style import DEFAULT_STYLE, Style

__all__ = [
    "CAP_FORMS",
    "FIGURE_FORMS",
    "PUNCT_FORMS",
    "RELATED_FORMS",
    "Controls",
    "Derivation",
]

Derivation = Callable[[ComposedGlyph, ComposedGlyph, DesignContext], ComposedGlyph]

RELATED_FORMS: dict[str, Derivation] = {
    "n": lambda n, o, c: n,
    "o": lambda n, o, c: o,
    "h": lambda n, o, c: h_from_n(n, c),
    "m": lambda n, o, c: m_from_n(n, c),
    "r": lambda n, o, c: r_from_n(n, c),
    "u": lambda n, o, c: u_from_n(n, c),
    "i": lambda n, o, c: i_from_n(n, c),
    "l": lambda n, o, c: l_from_n(n, c),
    "b": lambda n, o, c: b_from_o(o, n, c),
    "d": lambda n, o, c: d_from_o(o, n, c),
    "p": lambda n, o, c: p_from_o(o, n, c),
    "q": lambda n, o, c: q_from_o(o, n, c),
    "a": lambda n, o, c: a_from_o(o, n, c),
    "c": lambda n, o, c: c_from_o(o, c),
    "e": lambda n, o, c: e_from_o(o, c),
    "v": lambda n, o, c: v_from_n(n, c),
    "w": lambda n, o, c: w_from_n(n, c),
    "y": lambda n, o, c: y_from_n(n, c),
    "x": lambda n, o, c: x_from_n(n, c),
    "z": lambda n, o, c: z_from_n(n, c),
    "k": lambda n, o, c: k_from_n(n, c),
    "f": lambda n, o, c: f_from_n(n, c),
    "t": lambda n, o, c: t_from_n(n, c),
    "j": lambda n, o, c: j_from_n(n, c),
    "g": lambda n, o, c: g_from_o(o, n, c),
    "s": lambda n, o, c: s_from_o(o, c),
}
"""Character → how it derives from control ``n`` and ``o``."""

CAP_FORMS: dict[str, Derivation] = {
    "H": lambda H, O, c: H,
    "O": lambda H, O, c: O,
    "I": lambda H, O, c: I_from_H(H, c),
    "L": lambda H, O, c: L_from_H(H, c),
    "E": lambda H, O, c: E_from_H(H, c),
    "F": lambda H, O, c: F_from_H(H, c),
    "T": lambda H, O, c: T_from_H(H, c),
    "C": lambda H, O, c: C_from_O(O, c),
    "G": lambda H, O, c: G_from_O(O, H, c),
    "Q": lambda H, O, c: Q_from_O(O, H, c),
    "S": lambda H, O, c: S_from_O(O, c),
    "D": lambda H, O, c: D_from_H(H, O, c),
    "U": lambda H, O, c: U_from_H(H, O, c),
    "J": lambda H, O, c: J_from_H(H, O, c),
    "P": lambda H, O, c: P_from_H(H, O, c),
    "R": lambda H, O, c: R_from_H(H, O, c),
    "B": lambda H, O, c: B_from_H(H, O, c),
    "A": lambda H, O, c: A_from_H(H, c),
    "V": lambda H, O, c: V_from_H(H, c),
    "W": lambda H, O, c: W_from_H(H, c),
    "X": lambda H, O, c: X_from_H(H, c),
    "Y": lambda H, O, c: Y_from_H(H, c),
    "Z": lambda H, O, c: Z_from_H(H, c),
    "K": lambda H, O, c: K_from_H(H, c),
    "M": lambda H, O, c: M_from_H(H, c),
    "N": lambda H, O, c: N_from_H(H, c),
}
"""Capital → how it derives from control ``H`` and ``O``."""

FIGURE_FORMS: dict[str, Derivation] = {
    "0": lambda H, O, c: zero_from_O(O, H, c),
    "1": lambda H, O, c: one_from_H(H, c),
    "2": lambda H, O, c: two_from_O(O, H, c),
    "3": lambda H, O, c: three_from_O(O, H, c),
    "4": lambda H, O, c: four_from_H(H, c),
    "5": lambda H, O, c: five_from_O(O, H, c),
    "6": lambda H, O, c: six_from_O(O, H, c),
    "7": lambda H, O, c: seven_from_H(H, c),
    "8": lambda H, O, c: eight_from_O(O, H, c),
    "9": lambda H, O, c: nine_from_O(O, H, c),
}
"""Lining figure → how it derives from control ``H`` and ``O``."""


@dataclass(frozen=True, slots=True)
class Controls:
    """The family's control sheet: proportions plus the control-glyph records.

    Lowercase derives from ``n`` / ``o``, capitals from ``H`` / ``O``::

        controls = Controls.from_context(ctx).tuned_n(counter=280)
        glyphs = controls.build_all()          # {"n": ..., "h": ..., "H": ...}

    The cap records follow the current ``n`` stem unless set explicitly with
    :meth:`tuned_cap_h` / :meth:`tuned_cap_o`.
    """

    context: DesignContext
    n: NMetrics
    o: OMetrics
    cap_h: HMetrics | None = None
    cap_o: OMetrics | None = None
    glyph_overrides: Mapping[str, Derivation] = field(default_factory=dict)
    glyph_specs: Mapping[str, Any] = field(default_factory=dict)
    style: Style = field(default_factory=Style)

    @classmethod
    def from_context(cls, ctx: DesignContext, *, style: Style | None = None) -> Controls:
        chosen = style or DEFAULT_STYLE
        effective = ctx if chosen == DEFAULT_STYLE else replace(ctx, style=chosen)
        return cls(effective, n_metrics(ctx), o_metrics(ctx), style=chosen)

    def with_style(self, **kwargs: str) -> Controls:
        """Return a sheet with updated :class:`~typekernel.parts.style.Style` fields."""
        return self.from_context(self.context, style=self.style.tuned(**kwargs))

    @property
    def H(self) -> HMetrics:
        return self.cap_h or h_cap_metrics(self.context, self.n)

    @property
    def O(self) -> OMetrics:
        return self.cap_o or cap_o_metrics(self.context, self.n)

    def tuned_n(self, **kwargs: float) -> Controls:
        return replace(self, n=self.n.tuned(**kwargs))

    def tuned_o(self, **kwargs: float) -> Controls:
        return replace(self, o=self.o.tuned(**kwargs))

    def tuned_cap_h(self, **kwargs: float) -> Controls:
        return replace(self, cap_h=self.H.tuned(**kwargs))

    def tuned_cap_o(self, **kwargs: float) -> Controls:
        return replace(self, cap_o=self.O.tuned(**kwargs))

    def with_stem_relief(self) -> Controls:
        """Widen ``n``/``o`` counters for heavy ``context.stem`` (black masters)."""
        from typekernel.parts.weight_relief import STEM_RELIEF_ONSET, relieve_n_o

        if self.context.stem < STEM_RELIEF_ONSET:
            return self
        n, o = relieve_n_o(self.n, self.o, self.context.stem)
        return replace(self, n=n, o=o)

    def with_glyph(self, ch: str, builder: Derivation) -> Controls:
        """Replace one codepoint's derivation (designer-style single-glyph master)."""
        merged = dict(self.glyph_overrides)
        merged[ch] = builder
        return replace(self, glyph_overrides=merged)

    def with_glyphs(self, builders: Mapping[str, Derivation]) -> Controls:
        """Replace several derivations at once."""
        merged = dict(self.glyph_overrides)
        merged.update(builders)
        return replace(self, glyph_overrides=merged)

    def tuned_glyph(self, ch: str, **kwargs: float) -> Controls:
        """Override one weak glyph via its typed spec (see ``glyph_specs``)."""
        if ch not in WEAK_GLYPH_SPECS:
            raise KeyError(
                f"tuned_glyph: no spec for {ch!r}; have {sorted(WEAK_GLYPH_SPECS)}"
            )
        spec = merge_spec(ch, self.glyph_specs.get(ch), **kwargs)

        def builder(n: ComposedGlyph, o: ComposedGlyph, c: DesignContext) -> ComposedGlyph:
            return build_from_spec(ch, spec, n, o, c)

        specs = dict(self.glyph_specs)
        specs[ch] = spec
        overrides = dict(self.glyph_overrides)
        overrides[ch] = builder
        return replace(self, glyph_specs=specs, glyph_overrides=overrides)

    @property
    def supported(self) -> str:
        return (
            "".join(sorted(RELATED_FORMS))
            + "".join(sorted(CAP_FORMS))
            + "".join(sorted(FIGURE_FORMS))
            + "".join(sorted(PUNCT_FORMS))
        )

    def control_glyphs(self) -> tuple[ComposedGlyph, ComposedGlyph]:
        """The drawn ``n`` and ``o`` every lowercase form derives from."""
        return build_n(self.context, self.n), build_o(self.context, self.o)

    def cap_control_glyphs(self) -> tuple[ComposedGlyph, ComposedGlyph]:
        """The drawn ``H`` and ``O`` every capital derives from."""
        return build_H(self.context, self.H), build_O(self.context, self.O)

    def build(self, ch: str) -> ComposedGlyph:
        return self.build_all(ch)[ch]

    def design_sequence(
        self,
        order: Sequence[str] | None = None,
        *,
        control: str = "n",
        tolerances: object | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: object | None = None,
    ) -> object:
        """Start a gated :class:`~typekernel.qa.design_sequence.DesignSequence`.

        Builds **only** the control glyph. Agents must ``try_add`` / ``add``
        each next letter (typically ``self.build(ch)``) and redesign on refuse.
        Do **not** use :meth:`build_all` as the design method for new letters —
        ``build_all`` is stock derivation after controls are locked.
        """
        from typekernel.qa.design_sequence import DesignSequence, controls_body_tolerances

        tol = tolerances if tolerances is not None else controls_body_tolerances()
        return DesignSequence.from_controls(
            self,
            control=control,
            order=order,
            tolerances=tol,  # type: ignore[arg-type]
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,  # type: ignore[arg-type]
        )

    def unlock_body(
        self,
        order: Sequence[str] | None = None,
        *,
        control: str = "n",
        tolerances: object | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: object | None = None,
    ) -> object:
        """Run the Latin body through :class:`~typekernel.qa.DesignSequence` gates.

        Required after locking controls (and any ``with_glyph`` / ``tuned_glyph``
        masters). Raises on refuse. Prefer this over ungated :meth:`build_all`
        when proving the body is style-consistent. Use :meth:`build_all` only
        afterward for punctuation / figures / caps at compose time.
        """
        from typekernel.qa.design_sequence import DesignSequence

        return DesignSequence.unlock_controls_body(
            self,
            control=control,
            order=order,
            tolerances=tolerances,  # type: ignore[arg-type]
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,  # type: ignore[arg-type]
        )

    def unlock_body_ladder(
        self,
        stems: Sequence[float] | None = None,
        *,
        control: str = "n",
        order: Sequence[str] | None = None,
        tolerances: object | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: object | None = None,
    ) -> object:
        """Unlock the Latin body on each weight-ladder master (VF / family).

        See :func:`~typekernel.qa.design_sequence.unlock_controls_body_ladder`.
        """
        from typekernel.qa.design_sequence import unlock_controls_body_ladder

        return unlock_controls_body_ladder(
            self,
            stems,
            control=control,
            order=order,
            tolerances=tolerances,  # type: ignore[arg-type]
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,  # type: ignore[arg-type]
        )

    def unlock_caps(
        self,
        order: Sequence[str] | None = None,
        *,
        control: str = "H",
        tolerances: object | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: object | None = None,
    ) -> object:
        """Run capitals through :func:`~typekernel.qa.design_sequence.unlock_controls_caps`."""
        from typekernel.qa.design_sequence import unlock_controls_caps

        return unlock_controls_caps(
            self,
            control=control,
            order=order,
            tolerances=tolerances,  # type: ignore[arg-type]
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,  # type: ignore[arg-type]
        )

    def unlock_digits(
        self,
        order: Sequence[str] | None = None,
        *,
        control: str = "1",
        tolerances: object | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: object | None = None,
    ) -> object:
        """Run lining figures through :func:`~typekernel.qa.design_sequence.unlock_controls_digits`."""
        from typekernel.qa.design_sequence import unlock_controls_digits

        return unlock_controls_digits(
            self,
            control=control,
            order=order,
            tolerances=tolerances,  # type: ignore[arg-type]
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,  # type: ignore[arg-type]
        )

    def unlock_digits_ladder(
        self,
        stems: Sequence[float] | None = None,
        *,
        control: str = "1",
        order: Sequence[str] | None = None,
        tolerances: object | None = None,
        compare_to_previous: bool = True,
        skip_checks_for_pair: object | None = None,
    ) -> object:
        """Unlock lining figures on each weight-ladder master.

        See :func:`~typekernel.qa.design_sequence.unlock_controls_digits_ladder`.
        """
        from typekernel.qa.design_sequence import unlock_controls_digits_ladder

        return unlock_controls_digits_ladder(
            self,
            stems,
            control=control,
            order=order,
            tolerances=tolerances,  # type: ignore[arg-type]
            compare_to_previous=compare_to_previous,
            skip_checks_for_pair=skip_checks_for_pair,  # type: ignore[arg-type]
        )

    def build_all(self, chars: str | None = None) -> dict[str, ComposedGlyph]:
        """Derive ``chars`` from locked controls (default: all supported).

        Stock derivation helper for compose / VF after the designer-order body
        gate (:meth:`unlock_body` / :class:`~typekernel.qa.DesignSequence`).
        Not a substitute for sequential design of new letters.
        """
        wanted = self.supported if chars is None else "".join(dict.fromkeys(chars))
        cap_forms = {**CAP_FORMS, **FIGURE_FORMS}
        extended = {**EXTENDED_LATIN_FORMS, **EXTENDED_LATIN_CAP_FORMS}
        missing = [
            ch
            for ch in wanted
            if ch
            not in RELATED_FORMS
            and ch not in PUNCT_FORMS
            and ch not in extended
            and ch not in cap_forms
        ]
        if missing:
            raise KeyError(f"no related form for {missing}; have {self.supported!r}")
        related = {
            **RELATED_FORMS,
            **{k: v for k, v in self.glyph_overrides.items() if k in RELATED_FORMS},
        }
        cap_forms_merged = {
            **cap_forms,
            **{k: v for k, v in self.glyph_overrides.items() if k in cap_forms},
        }
        out: dict[str, ComposedGlyph] = {}
        for forms, draw in (
            (related, self.control_glyphs),
            (PUNCT_FORMS, self.control_glyphs),
            (extended, self.control_glyphs),
            (cap_forms_merged, self.cap_control_glyphs),
        ):
            chars_here = [ch for ch in wanted if ch in forms]
            if chars_here:
                a, b = draw()
                for ch in chars_here:
                    glyph = forms[ch](a, b, self.context)
                    slant = self.context.italic_slant_deg
                    from typekernel.parts.oblique_compat import (
                        OBLIQUE_PRE_EXTREMA,
                        apply_oblique_compat_glyph,
                        oblique_compat_charset,
                    )

                    compat = ch in oblique_compat_charset(self.supported)
                    if compat and (
                        abs(slant) > 1e-9 or self.context.vf_compat_oblique_splits
                    ):
                        angle = (
                            slant
                            if abs(slant) > 1e-9
                            else self.context.vf_oblique_split_deg
                        )
                        glyph = apply_oblique_compat_glyph(
                            glyph,
                            angle,
                            slant=abs(slant) > 1e-9,
                            pre_axis_extrema=ch in OBLIQUE_PRE_EXTREMA,
                        )
                    elif abs(slant) > 1e-9:
                        from typekernel.parts.italic import slant_composed_glyph

                        glyph = slant_composed_glyph(glyph, slant)
                    if self.context.style.serif != "none":
                        from typekernel.parts.serifs import apply_glyph_serifs

                        glyph = apply_glyph_serifs(glyph)
                    out[ch] = glyph
        return {ch: out[ch] for ch in wanted}
