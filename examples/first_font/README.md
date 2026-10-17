# 示例：从比例到一个能安装的字体文件

按设计师的顺序走一遍：比例 → 控制字 `n` / `o`（小写）和 `H` / `O`（大写、数字）→ 派生出 a–z、A–Z、0–9 共 62 个字形 → 光学侧距（数字再统一成等宽）→ 类字偶 → `Font` → OTF / TTF → 用编译出的字体文件排校样。

校样第二行只改了控制表里的一处：`tuned_n(counter=…)`。`n` 家族的字一起变宽，`o` 家族不动。

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
| `variant/` | 改过控制表的对照字体 |
| `*.manifest.json` | 工具版本记录 |
| `proof.png` | 用 **编译后的 OTF** 排的校样 |

## 用了哪些 API

- `typekernel.parts.Controls` — 控制表：`DesignContext` + `n` / `o` / `H` / `O` 的设计记录；`tuned_n` / `tuned_o` / `tuned_cap_h` / `tuned_cap_o` 改一处。正文先经 `DesignSequence` / `unlock_body` 一字一闸；锁定后再用 `build_all()` 派生标点/大写/数字（compose）
- `typekernel.parts.tabular` — 数字统一字宽、墨迹居中（等宽数字）
- `typekernel.font.Font.from_context` — 字族信息、竖直度量、对齐区（blue zones）、`.notdef`、`space` 都从 `DesignContext` 来
- `Font.add_chars` — `{字符: ComposedGlyph}`，自动取 AGL 字形名、映射码位、统一轮廓绕向，并带上控制字的锚点
- `Font.add_class_kern_table` — 类字偶 → UFO `public.kern1/kern2` 组 → GPOS `kern`
- `typekernel.compile.build_font` — 校验 → UFO → OTF + TTF

![first font proof](../../docs/images/first-font-proof.png)
