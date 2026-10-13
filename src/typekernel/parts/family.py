"""The control sheet: draw ``n`` and ``o``, derive the lowercase from them.

:class:`Controls` holds the family proportions plus the ``n`` and ``o``
design records. :data:`RELATED_FORMS` says how every other letter derives
from those two drawn glyphs, so one adjustment (``tuned_n(counter=...)``)
moves the whole ``n`` family and ``tuned_o(rx=...)`` the ``o`` family.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

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
    t_from_n,
    u_from_n,
)
from typekernel.parts.diagonals import k_from_n, v_from_n, w_from_n, x_from_n, y_from_n, z_from_n

__all__ = ["RELATED_FORMS", "Controls", "Derivation"]

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
}
"""Character → how it derives from control ``n`` and ``o``."""


@dataclass(frozen=True, slots=True)
class Controls:
    """The family's control sheet: proportions plus the ``n`` and ``o`` records.

    Every related form is derived from the two control glyphs this sheet
    draws::

        controls = Controls.from_context(ctx).tuned_n(counter=280)
        glyphs = controls.build_all()          # {"n": ..., "h": ..., ...}
    """

    context: DesignContext
    n: NMetrics
    o: OMetrics

    @classmethod
    def from_context(cls, ctx: DesignContext) -> Controls:
        return cls(ctx, n_metrics(ctx), o_metrics(ctx))

    def tuned_n(self, **kwargs: float) -> Controls:
        return replace(self, n=self.n.tuned(**kwargs))

    def tuned_o(self, **kwargs: float) -> Controls:
        return replace(self, o=self.o.tuned(**kwargs))

    @property
    def supported(self) -> str:
        return "".join(sorted(RELATED_FORMS))

    def control_glyphs(self) -> tuple[ComposedGlyph, ComposedGlyph]:
        """The drawn ``n`` and ``o`` every related form derives from."""
        return build_n(self.context, self.n), build_o(self.context, self.o)

    def build(self, ch: str) -> ComposedGlyph:
        return self.build_all(ch)[ch]

    def build_all(self, chars: str | None = None) -> dict[str, ComposedGlyph]:
        """Draw ``n`` / ``o`` once and derive ``chars`` (default: all supported)."""
        wanted = self.supported if chars is None else "".join(dict.fromkeys(chars))
        missing = [ch for ch in wanted if ch not in RELATED_FORMS]
        if missing:
            raise KeyError(f"no related form for {missing}; have {self.supported!r}")
        n, o = self.control_glyphs()
        return {ch: RELATED_FORMS[ch](n, o, self.context) for ch in wanted}
