# BuildManifest

When typekernel compiles a UFO to a font binary, it records a small JSON
**BuildManifest** so builds stay auditable: which tools ran, on which inputs,
and whether any contour filters were requested.

## Intent

- **Reproducibility aid**, not a lockfile. Versions identify the toolchain that
  produced a binary; pin environments separately if you need bit-identical
  rebuilds.
- **Thin by default.** The compile bridge does not beautify contours. The
  `filters` field is empty unless a caller deliberately records filter choices.
  Overlap removal is off unless explicitly enabled upstream of this record.
- Cubic→quadratic conversion for TrueType (fontTools `cu2qu` via ufo2ft) is
  normal compile-boundary behaviour, not a design-layer “beautify”.

## Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `fonttools_version` | string or null | Installed `fonttools` distribution version |
| `fontmake_version` | string or null | Installed `fontmake` version, if present |
| `ufo2ft_version` | string or null | Installed `ufo2ft` version |
| `timestamp` | string | UTC ISO-8601 time when the build finished |
| `inputs` | object | At least `ufo` and `output` path strings |
| `filters` | string array | Contour/glyph filters requested; default `[]` |
| `output_format` | string | `"ttf"` or `"otf"` |

## Example

```json
{
  "fonttools_version": "4.66.1",
  "fontmake_version": "3.12.2",
  "ufo2ft_version": "3.9.1",
  "timestamp": "2026-10-12T06:00:00+00:00",
  "inputs": {
    "ufo": "artifacts/build/Example.ufo",
    "output": "artifacts/build/Example.ttf"
  },
  "filters": [],
  "output_format": "ttf"
}
```

## API

See `typekernel.compile.BuildManifest` and
`typekernel.compile.build_ttf_from_ufo`. Install the optional extra:

```bash
pip install -e ".[compile]"
```
