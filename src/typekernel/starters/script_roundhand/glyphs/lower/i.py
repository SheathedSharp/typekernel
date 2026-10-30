from elements import stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("i", group="lc")
def i(system: System):
    # Upright stem only — keep topology quiet for the starter demo.
    return stem(system, 140.0)
