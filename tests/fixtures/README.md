# Test fixtures

## `synthetic_O.json`

A **synthetic** ring-like `O`, built from four-cubic Bézier approximations of
two circles. It is not derived from, traced from, or a copy of any real
typeface, and specifically **not** taken from LihuiT or zayJu. It exists so the
geo-kernel has a stable, hand-checkable golden fixture without borrowing
someone else's outlines.

Geometry (`unitsPerEm` = 1000):

| Contour | Role | Circle | Winding |
| --- | --- | --- | --- |
| 1 | outer | centre (500, 350), r = 350 | counter-clockwise |
| 2 | counter | centre (500, 350), r = 210 | clockwise |

The outer circle is tangent to the baseline (`y = 0`) and reaches `y = 700`, so
bounds assertions have exact expected values (`0 <= y <= 700`,
`150 <= x <= 850`). The counter winds the **opposite** way from the outer
contour, so a non-zero fill rule yields a hole — without that, the fixture
would not describe an `O` at all.

Each cubic is a flat list of eight numbers:

```
[x0, y0, x1, y1, x2, y2, x3, y3]
```

where `(x0, y0)` and `(x3, y3)` are on-curve endpoints and `(x1, y1)` and
`(x2, y2)` are off-curve control points. Circle control points use the standard
kappa offset `k = 4/3 * (sqrt(2) - 1)` times the radius. Coordinates are
rounded to three decimals.

### Schema

```json
{
  "glyph": "O",
  "unitsPerEm": 1000,
  "contours": [
    {"closed": true, "cubics": [[x0, y0, x1, y1, x2, y2, x3, y3]]}
  ]
}
```

`role` and `note` are descriptive extras; only `glyph`, `unitsPerEm` and
`contours[].{closed,cubics}` are contractual.

Loaded by `typekernel.geo.fixtures.load_synthetic_outline` (P0-020).
