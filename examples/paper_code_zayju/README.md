# Example: paper + coding-friendly triad for `zayju`

No commercial reference columns. Same `typekernel.parts` recipes, three
`DesignContext` directions side by side:

| Panel | Context | Brief |
| --- | --- | --- |
| Ink Book | `DesignContext.paper_ink()` | Solid stems, open counters — paper first |
| Code Clear | `DesignContext.code_clear()` | Tall x-height, even sidebearings — coding first |
| Open Print | `DesignContext.open_print()` | Soft joins, wide aperture — print-open |

## Render

```bash
pip install -e ".[specimen,boolean]"
python examples/paper_code_zayju/design_specimen.py
```

Outputs:

- `out/triad.png`
- `docs/images/zayju-paper-code-triad.png`
