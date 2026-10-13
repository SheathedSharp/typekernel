# 示例：从比例到一个能安装的字体文件

按设计师的顺序走一遍：比例 → 控制字 `n` / `o` → 派生 `h` / `u` / `i` → 光学侧距 → 类字偶 → `Font` → OTF / TTF → 用编译出的字体文件排校样。

## 跑起来

```bash
# 在 typekernel 仓库根目录
pip install -e ".[dev,specimen,compile,boolean]"
python examples/first_font/build_font.py
```

产物在 `out/`（除 `proof.png` 外默认不进 git）：

| 文件 | 说明 |
| --- | --- |
| `TypekernelFirst-Regular.otf` | CFF（三次曲线），可直接双击安装 |
| `TypekernelFirst-Regular.ttf` | TrueType（编译边界转二次） |
| `TypekernelFirst-Regular.ufo` | 中间源，可用 Glyphs / FontForge 打开检查 |
| `*.manifest.json` | 工具版本记录 |
| `proof.png` | 用 **编译后的 OTF** 排的瀑布校样 |

## 用了哪些 API

- `typekernel.font.Font.from_context` — 字族信息、竖直度量、对齐区（blue zones）、`.notdef`、`space` 都从 `DesignContext` 来
- `Font.add_chars` — `{字符: ComposedGlyph}`，自动取 AGL 字形名并映射码位、统一轮廓绕向
- `Font.add_class_kern_table` — 类字偶 → UFO `public.kern1/kern2` 组 → GPOS `kern`
- `typekernel.compile.build_font` — 校验 → UFO → OTF + TTF

![first font proof](../../docs/images/first-font-proof.png)
