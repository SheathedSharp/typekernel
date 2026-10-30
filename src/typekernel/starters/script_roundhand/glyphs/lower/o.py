from elements import oval

from typekernel.project import glyph
from typekernel.system import System


@glyph("o", group="control")
def o(system: System):
    return oval(system)
