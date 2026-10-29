"""Case-sensitive punctuation (.case) for P4-3 case feature."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, dot, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("period.case", unicodes=(), group="punct.case", traits=("punct", "no-stem"))
def period_case(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 50.0)) * 0.4
    size = st * 0.95
    return dot((lsb + size / 2.0, cap * 0.55), size, shape="square", name="dot")


@glyph("comma.case", unicodes=(), group="punct.case", traits=("punct", "no-stem"))
def comma_case(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 50.0)) * 0.4
    # Slot-free comma: square head + stem tail
    head = dot((lsb + st * 0.55, cap * 0.55), st * 0.9, shape="square", name="dot")
    tail = stem(
        lsb + st * 0.25,
        lsb + st * 0.25 + st * 0.55,
        cap * 0.28,
        cap * 0.5,
        name="stem",
        foot="none",
        top="none",
    )
    return head + tail


@glyph("hyphen.case", unicodes=(), group="punct.case", traits=("punct", "no-stem"))
def hyphen_case(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 50.0)) * 0.4
    length = float(WIDTHS.get("hyphen", 220))
    return crossbar(lsb, lsb + length, cap * 0.52, thick=st * 0.75, name="bar", ends="none")
