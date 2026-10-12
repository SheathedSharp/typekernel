# fontTools / pathops reuse map

typekernel adds typed cubic-first values and optical semantics; it does **not**
reimplement Bézier math or OpenType compilation. Short mapping:

| typekernel | Delegates to | Role |
| --- | --- | --- |
| `Point`, `LineSegment`, `CubicSegment` | — (typed holders) | Design-space geometry; hand tuples to fontTools when needed |
| `Contour` / `Outline` | — | Containers; no raw float polylines as truth |
| `PathBuilder` | pen-like API (local) | Build outlines without rounding by default |
| `draw_outline` | `fontTools.pens.basePen.AbstractPen` | Replay cubics/lines; never flatten |
| `signed_area` (orientation) | local shoelace on on-curve points | Sign only; exact area → `AreaPen` if needed |
| `bounds` (control-point AABB) | local min/max of controls | Tight curve bounds → `BoundsPen` / `calcCubicBounds` |
| `to_quadratic` / `ConversionReport` | `fontTools.cu2qu` (`curve_to_quadratic`) | Compile-boundary TT; error estimate sampled locally |
| cubic/quadratic eval in reports | `fontTools.misc.bezierTools` (`cubicPointAtT`, `quadraticPointAtT`) | Measurement only |
| `boolean_op` (stub) | optional `pathops` (skia-pathops) | Curve booleans later; **not** Shapely |
| rounding for font units (future) | `fontTools.misc.roundTools.otRound` | Half-away-from-zero; `quantize` is *not* that |
| UFO / OT compile (future bridge) | fontTools / ufo2ft / fontmake | No custom OT table writers |

When adding geometry helpers, prefer calling an existing fontTools facility over
copying its algorithm into typekernel.
