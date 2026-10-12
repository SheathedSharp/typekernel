"""typekernel — optical / design-semantics kernel for fonts-as-code.

Depends on fontTools for compilation; does not rebuild OpenType tables.

The geo-kernel public API is available under ``typekernel.geo`` (cubic-first
outlines, path building, pen bridge, and compile-boundary quadratic conversion).
Optical / design-semantics primitives are the next layer on top of that
geometry — this package's long-term mission, not yet exposed as a public API.
"""

__version__ = "0.0.0"
