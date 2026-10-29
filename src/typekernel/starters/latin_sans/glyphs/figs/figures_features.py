"""Figure feature variants .tf / .osf (tnum / onum)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl, crossbar, open_bowl, stem
from typekernel.project import glyph
from typekernel.system import System

_FIG_W = 500.0
_NAMES = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
)


def _fig_system(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.5
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    return st, thin, xh, lsb, ov, exp


def _zero(system, *, y0: float, h: float, tag: str):
    st, thin, _xh, lsb, ov, exp = _fig_system(system)
    w = _FIG_W
    return bowl(
        (lsb + w / 2, y0 + h / 2),
        w * 0.38,
        h * 0.48,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov * 0.3,
        name=f"bowl.{tag}",
    )


def _one(system, *, y0: float, h: float, tag: str):
    st, thin, _xh, lsb, ov, exp = _fig_system(system)
    w = _FIG_W
    x0 = lsb + (w - st) / 2
    return stem(x0, x0 + st, y0, y0 + h, name=f"stem.{tag}", foot="none", top="none")


def _generic_bar_digit(system, *, y0: float, h: float, tag: str):
    """Stable placeholder digit: stem + mid bar (used for several .tf/.osf)."""
    st, thin, _xh, lsb, ov, exp = _fig_system(system)
    w = _FIG_W
    x0 = lsb + w * 0.35
    body = stem(x0, x0 + st, y0, y0 + h, name=f"stem.{tag}", foot="none", top="none")
    bar = crossbar(lsb + w * 0.15, lsb + w * 0.85, y0 + h * 0.5, thick=thin, name=f"bar.{tag}", ends="none")
    return body + bar


_BUILDERS = {
    "zero": _zero,
    "one": _one,
}


def _build(name: str, system: System, *, y0: float, h: float, tag: str):
    fn = _BUILDERS.get(name, _generic_bar_digit)
    return fn(system, y0=y0, h=h, tag=tag)


# Register .tf and .osf for each figure.
def _register():
    xh_frac = 0.92
    for name in _NAMES:

        def make_tf(n=name):
            @glyph(f"{n}.tf", unicodes=(), group="figs.tf", traits=("figure", "tabular"))
            def _tf(system: System, n=n):
                xh = float(system.zones.x)
                return _build(n, system, y0=0.0, h=xh * xh_frac, tag="tf")

            return _tf

        def make_osf(n=name):
            @glyph(f"{n}.osf", unicodes=(), group="figs.osf", traits=("figure",))
            def _osf(system: System, n=n):
                xh = float(system.zones.x)
                desc = float(system.zones.desc)
                # Oldstyle: hang some digits slightly below baseline
                hang = desc * 0.35 if n in {"3", "5", "7", "9", "four", "five", "seven", "nine", "three"} else 0.0
                # name is zero..nine
                hang = desc * 0.35 if n in {"three", "five", "seven", "nine"} else 0.0
                return _build(n, system, y0=hang, h=xh * 0.75, tag="osf")

            return _osf

        make_tf()
        make_osf()


_register()
