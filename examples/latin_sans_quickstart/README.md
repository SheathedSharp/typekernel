# latin-sans quickstart

Builds a throwaway project from the in-repo starter and compiles an OTF.

```bash
# from repo root, with the package installed editable
python examples/latin_sans_quickstart/build.py
```

Or by hand (ARCHITECTURE.md 标准工作流):

```bash
tk new myface --starter latin-sans
cd myface
# edit system.py / glyphs / spacing.py / font.py
tk build .
tk proof control .
tk audit .
```
