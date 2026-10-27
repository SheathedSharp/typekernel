# Anti-patterns

| Don’t | Do instead |
| --- | --- |
| `from typekernel.parts import DesignContext` | Use `System` + project glyphs (`tk new --starter latin-sans`) |
| Add heal / blend / seal after boolean mess | Change the fragment / overlap construction |
| Stroke-expand to fake weight | Scale `system.stem` (and masters via `tuned`) |
| Letter builders inside `typekernel.*` kernel packages | Keep letters in the project starter only |
| Bbox-only advances forever | `spacing.py` metrics keys + `apply_spacing` |
| Silent mega-knobs (`aperture`, `roundness`) | Explicit tokens + element functions |
| Treating `tk audit` warnings as pass/fail cosmetics gate | Treat direction/compat as hard fail; stem/zone as fix list |
| Resurrecting yoke / FormSources / Style recipes | Follow ARCHITECTURE.md §4 |
