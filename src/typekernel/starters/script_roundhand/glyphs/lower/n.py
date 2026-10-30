from elements import n_arch

from typekernel.project import glyph
from typekernel.system import System


@glyph("n", group="control")
def n(system: System):
    return n_arch(system)
