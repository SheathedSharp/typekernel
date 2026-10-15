"""Built-in :class:`DesignContext` factories for ``examples/*`` CLIs."""

from __future__ import annotations

from collections.abc import Callable

from typekernel.parts import DesignContext

PRESET_FACTORIES: dict[str, Callable[[], DesignContext]] = {
    "humanist_sans": DesignContext.humanist_sans,
    "code_clear": DesignContext.code_clear,
    "geometric_sans": DesignContext.geometric_sans,
    "mono": DesignContext.mono,
    "display": DesignContext.display,
    "paper_ink": DesignContext.paper_ink,
    "open_print": DesignContext.open_print,
    "slab_serif": DesignContext.slab_serif,
    "bracketed_serif": DesignContext.bracketed_serif,
}
