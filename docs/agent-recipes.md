# Agent 配方

给 coding agent 的短路径。完成分级在 [AGENT_GOAL.md](AGENT_GOAL.md)，步骤在 [skill](../.agents/skills/typekernel-font-design/SKILL.md)。

## Brief → preset

先写用途、字重、是否斜体、字符集，再 **点名一个 preset**。不要从空白 `DesignContext(...)` 起笔。

| 用途 | preset |
| --- | --- |
| 代码 / UI 正文，等高、侧距松 | `code_clear()` |
| 人文主义无衬线，开口大、有对比 | `humanist_sans()` |
| 几何无衬线 | `geometric_sans()` |
| 方衬线编辑体（`Style.serif=slab`） | `slab_serif()` |
| 托架衬线人文体（`Style.serif=bracketed`） | `bracketed_serif()` |
| 等宽感觉 | `mono()` |
| 标题 | `display()` |
| 纸书、墨更重 | `paper_ink()` |

Regular 上每次只改 **一个字段**，写成相对该 preset 当前值的增量，然后跑 `design_review`。preset 的 `sidebearing_ratio` 若是 `0.10`，试 `0.11` 是一次决定；不要写与 preset 无关的 `stem=78`。

大改 `stem` 属于 **另一套母版**（Light / Bold），不要拿去和 Regular 的未改 preset 比 gap。

## Style DNA（离散拓扑）

在 preset 之上用 `Controls.from_context(ctx, style=Style(...))` 或 `controls.with_style(...)`。默认值与未传 `style` 相同，**不会**改变 golden preset 哈希。

| 字段 | 非默认取值 | 主要影响 |
| --- | --- | --- |
| `i_dot` | `square` / `diamond` | `i` `j` 点形 |
| `a_form` | `double` | 双层 `a` |
| `g_form` | `double` | 双层 `g` |
| `l_tail` | `tailed` | `l` 底弯钩 |
| `y_tail` | `curved` | `y` 右下弧 |
| `t_cut` | `slanted` | `t` 底端斜切（可独立于 `terminal_style`） |

`g_form=double` 在 `code_clear` 字重阶梯上已通过四母版 `check_masters`。`a_form=double` 在 `code_clear` stem **70–180** 六母版阶梯上已通过 `check_masters`（见 `test_double_a_form_masters_interpolate_on_weight_ladder`）。各 Style 选项与典型组合在七 preset 上已通过 identity 抽检（`test_style_option_identity_spot_check_on_preset`、`test_styled_voice_identity_core_charset_on_preset`）。其余非拓扑 Style 在 `code_clear` 字重阶梯上已通过 `check_masters` 抽检。

## 弱字

默认派生经常先在这些字上露馅：`f` `t` `j` `a` `s` `e`。L0 至少对其中两个 `with_glyph`。builder 签名是 `(n_glyph, o_glyph, ctx)`。

优先用 **`Controls.tuned_glyph`**（类型化规格，默认等于派生行为）：

```python
controls = (
    Controls.from_context(ctx)
    .tuned_glyph("f", arm=0.82)
    .tuned_glyph("t", arm=0.58, rise=0.28)
    .tuned_glyph("e", bar_raise=0.15)
)
```

规格类型在 `typekernel.parts.glyph_specs`；`tuned_glyph(ch, **fields)` 只接受该字 `spec_fields(ch)` 里的字段名。Cap 仍从 `H`/`O` 派生。

| 字 | 类型 | 字段（默认） |
| --- | --- | --- |
| `f` | `FSpec` | `arm` (0.75) |
| `t` | `TSpec` | `arm` (0.6), `rise` (0.3) |
| `j` | `JSpec` | `arm` (0.75) |
| `a` | `ASpec` | `join` (0.85) |
| `e` | `ESpec` | `bar_raise` (0.25), `aperture` (None) |
| `s` | `SSpec` | `width`, `top_scale`, `spine`, `aperture` |
| `A` | `CapASpec` | `width` (1.02), `apex` (0.35), `bar` (0.28) |
| `B` | `BSpec` | `width`, `top_scale`, `straight`, `waist` |
| `C` | `CapCSpec` | `aperture` (None → preset) |
| `D` | `DSpec` | `width` (1.05), `straight` (0.4) |
| `J` | `CapJSpec` | `width`, `spring`, `hook` |
| `S` | `CapSSpec` | `width` (0.86) |
| `U` | `USpec` | `width` (0.96), `spring` (0.38) |
| `E` | `CapESpec` | `width` (0.84) |
| `F` | `CapFSpec` | `width` (0.82) |
| `G` | `GSpec` | `bar_reach` (0.1) |
| `P` | `PSpec` | `width`, `straight`, `bowl`（默认同 `R` 碗区，无 `leg_at`） |
| `Q` | `QSpec` | `tail_reach` (1.0), `tail_drop` (0.1) |
| `K` | `KSpec` | `width` (0.92), `vertex` (0.42) |
| `R` | `RSpec` | `width`, `straight`, `bowl`, `leg_at` |
| `Y` | `YSpec` | `width` (0.98), `junction` (0.42) |
| `L` | `LSpec` | `width` (0.78) |
| `T` | `CapTSpec` | `width` (0.92) |
| `Z` | `ZSpec` | `width` (0.88) |
| `V` `W` `X` `M` `N` | `VSpec` … `NSpec` | 以 `width` 为主；`M` 另有 `apex` (0.35) |

`design_review` 的 `notes` 会列出 `spec f: {...}`。

仍可直接 `with_glyph` 挂自定义 builder：

```python
from typekernel.parts.control import f_from_n, t_from_n, j_from_n

controls = controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.82))
```

改完看 `design_review` 里该字的 `g1_errors`，以及 `AGENT_SENTENCE` 的 optical ratio **没有**差于 preset。一个 `f` 不算试字完成。

`a` / `s` / `e` 没有单独的 arm 旋钮时，不要用全局 `aperture` 掩盖一颗字。要么接受派生并在 review 里记下 G1，要么为这一颗写 builder。

## 何时离开 Controls，手绘轮廓

`Controls` + `tuned_*` + `with_glyph(现成 *_from_n)` 仍是 **同一套 sans 拓扑**。人文主义字段不会长出新的笔画逻辑。

下面任一成立，就下沉到路径，而不是继续拧 float：

- 用户要的形状和 `n` / `o` 派生对不上（另一套衬线、另一套字怀、连笔）
- 两轮 `design_review` 之后，弱字 G1 或 pair 撞字没有下降
- 需要参考一张已有字稿的结构，而不是它的 stem 数字

最小完整例子：[`examples/zayju_letter/design_n.py`](../examples/zayju_letter/design_n.py)（`PathBuilder` 画一颗 `n`）。画完用 `with_glyph` 挂回 `Controls`，间距与特性仍走 `compose_font_from_controls`。不要把参考轮廓拷进字库冒充自己的设计。

## 过关句与第二张校样

```python
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate

_report, failures = check_sentence_gate(controls, baseline=baseline_controls())
```

`failures` 非空就改设计。把 brief 句传进 `text=` 会直接失败。brief 句只用 `proof_context` 另存 `sentence_brief.png`。

固定 pair：`Ta` `To` `fi` `fl` `rn` `011`。光学间距 ≤ 0 算撞字。这组 **不** 证明字偶已经好看；间距仍是库内专项（见 AGENT_GOAL「库内仍未完成」）。

## 字重阶梯校样（TK-207）

R8 自动化已覆盖全部 `supported` 字符；人审时用阶梯 PNG 看字腔是否塌：

```python
from pathlib import Path
from typekernel.parts import DesignContext
from typekernel.qa.sheet import weight_ladder_sheet

weight_ladder_sheet(
    DesignContext.humanist_sans(),
    Path("artifacts/specimens/weight_ladder_humanist.png"),
)
```

默认 `stems=(30, 70, 110, 150, 180, 200)`，与 `tests/qa/test_weight_ladder.py` 一致。输出目录在 `.gitignore` 内，本地生成即可。

## 人审

数字门槛通过之后，视觉接受必须由人写入 `approvals/*.json`（`typekernel.qa.gates.write_approval`）。gate 与 `design_review` 都不会自动批准。没有这份记录，就还不是被接受的试作。
