# 示例：三个设计母版 → 一个可变字体

字重不是描边加粗：Light / Regular / Bold 各自从一张控制表画出来。字重加大时竖干变粗，同时字怀让出空间（`tuned_n(counter=…)` 收窄 `n` 字怀，`tuned_o(rx=…)` 让碗略宽），这是设计师控制灰度和字宽的做法。可变字体在这些画好的母版之间插值。

```bash
pip install -e ".[dev,specimen,compile,boolean]"
python examples/variable_family/build_vf.py
```

产物在 `out/`（除 `proof.png` 外默认不进 git）：

| 文件 | 说明 |
| --- | --- |
| `TypekernelVar-VF.ttf` | TrueType 可变字体（`fvar` / `gvar` / `HVAR`），`wght` 200–800 |
| `TypekernelVar-VF.otf` | CFF2 可变字体 |
| `TypekernelVar.designspace` + `masters/*.ufo` | 母版源文件，可用其他工具打开 |
| `proof.png` | 用可变字体在 200–800 各取一档排的校样 |

## 用了哪些 API

- `typekernel.font.Master` — 把一个 `Font` 放到轴上的位置（第一个是默认母版）
- `typekernel.font.check_masters` — 编译前检查字形集、轮廓结构、组件、锚点、字偶组是否一致
- `typekernel.compile.build_variable_font` — 写母版 UFO 和 designspace，编出 TTF / CFF2 可变字体

![variable family proof](../../docs/images/variable-family-proof.png)
