"""The control sheet: draw ``n`` and ``o``, derive the lowercase from them.

:class:`Controls` holds the family proportions plus the ``n`` and ``o``
design records. :data:`RELATED_FORMS` says how every other letter derives
from those two drawn glyphs, so one adjustment (``tuned_n(counter=...)``)
moves the whole ``n`` family and ``tuned_o(rx=...)`` the ``o`` family.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

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

__all__ = ["CAP_FORMS", "RELATED_FORMS", "Controls", "Derivation"]

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

    @classmethod
    def from_context(cls, ctx: DesignContext) -> Controls:
        return cls(ctx, n_metrics(ctx), o_metrics(ctx))

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

    @property
    def supported(self) -> str:
        return "".join(sorted(RELATED_FORMS)) + "".join(sorted(CAP_FORMS))

    def control_glyphs(self) -> tuple[ComposedGlyph, ComposedGlyph]:
        """The drawn ``n`` and ``o`` every lowercase form derives from."""
        return build_n(self.context, self.n), build_o(self.context, self.o)

    def cap_control_glyphs(self) -> tuple[ComposedGlyph, ComposedGlyph]:
        """The drawn ``H`` and ``O`` every capital derives from."""
        return build_H(self.context, self.H), build_O(self.context, self.O)

    def build(self, ch: str) -> ComposedGlyph:
        return self.build_all(ch)[ch]

    def build_all(self, chars: str | None = None) -> dict[str, ComposedGlyph]:
        """Draw the controls once and derive ``chars`` (default: all supported)."""
        wanted = self.supported if chars is None else "".join(dict.fromkeys(chars))
        missing = [ch for ch in wanted if ch not in RELATED_FORMS and ch not in CAP_FORMS]
        if missing:
            raise KeyError(f"no related form for {missing}; have {self.supported!r}")
        out: dict[str, ComposedGlyph] = {}
        for forms, draw in (
            (RELATED_FORMS, self.control_glyphs),
            (CAP_FORMS, self.cap_control_glyphs),
        ):
            chars_here = [ch for ch in wanted if ch in forms]
            if chars_here:
                a, b = draw()
                for ch in chars_here:
                    out[ch] = forms[ch](a, b, self.context)
        return {ch: out[ch] for ch in wanted}
