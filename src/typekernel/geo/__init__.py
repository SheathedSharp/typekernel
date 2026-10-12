"""geo-kernel: cubic-first geometry.

Cubic Bézier segments are the design truth of a typekernel outline; sampled
polylines are never a canonical contour.

The typed geometry layer (point, segment, contour, outline) lives here, along
with the bridges to fontTools pens and to cu2qu. Bézier math itself is not
reimplemented: it defers to ``fontTools.misc.bezierTools``.

No public symbols are exported yet. Symbols are re-exported from this module
only once their API sketch task has been completed and approved.
"""
