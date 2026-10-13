# Agent 配方

给 coding agent 的短路径。完成分级在 [AGENT_GOAL.md](AGENT_GOAL.md)，步骤在 [skill](../.agents/skills/typekernel-font-design/SKILL.md)。

## Brief → preset

先写用途、字重、是否斜体、字符集，再 **点名一个 preset**。不要从空白 `DesignContext(...)` 起笔。

| 用途 | preset |
| --- | --- |
| 代码 / UI 正文，等高、侧距松 | `code_clear()` |
| 人文主义无衬线，开口大、有对比 | `humanist_sans()` |
| 几何无衬线 | `geometric_sans()` |
| 等宽感觉 | `mono()` |
| 标题 | `display()` |
| 纸书、墨更重 | `paper_ink()` |

Regular 上每次只改 **一个字段**，写成相对该 preset 当前值的增量，然后跑 `design_review`。preset 的 `sidebearing_ratio` 若是 `0.10`，试 `0.11` 是一次决定；不要写与 preset 无关的 `stem=78`。

大改 `stem` 属于 **另一套母版**（Light / Bold），不要拿去和 Regular 的未改 preset 比 gap。

## 弱字

默认派生经常先在这些字上露馅：`f` `t` `j` `a` `s` `e`。L0 至少对其中两个 `with_glyph`。builder 签名是 `(n_glyph, o_glyph, ctx)`。

已有、可直接调用的单字 master（参数是臂长一类的比例，不是绝对 stem）：

```python
from typekernel.parts.control import f_from_n, t_from_n, j_from_n

controls = controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.82))
controls = controls.with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.58))
controls = controls.with_glyph("j", lambda n, o, c: j_from_n(n, c, arm=0.75))
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

## 人审

数字门槛通过之后，视觉接受必须由人写入 `approvals/*.json`（`typekernel.qa.gates.write_approval`）。gate 与 `design_review` 都不会自动批准。没有这份记录，就还不是被接受的试作。
