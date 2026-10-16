# typekernel — Coding Agent 产品目标

## 定位（一句话）

**typekernel 的定位应该是让 coding agent 通过使用这个基础库，像人类字体设计时一样去创建一种字体「包括各个字重，符号等等」。**

脚手架 = **库 API + 设计师顺序 + 校样工具**；不是「执行仓库里现成脚本就得到成品字」。Agent 必须用代码表达 brief、比例与字形决策（`DesignContext` / `Controls` / `with_glyph` / 自建 `build_*.py`），再编译与 proof。

## 这意味着什么

| 人类字体设计师 | Agent 通过 typekernel 应对齐的行为 |
| --- | --- |
| 先定 brief / 比例 / 字族性格 | 选或调 `DesignContext`（preset + 有记录的 override），写清 family 用途 |
| 画 control 字（n/o、H/O）再扩族 | `Controls.from_context` → 验证 control → `build_all()`，不是逐字随机堆轮廓 |
| 每个字重是 **重画母版**，不是描粗 | 每个 `wght` 独立 `Controls`（stem + `with_stem_relief()` 等 **designed delta**） |
| 斜体是 **另一套母版** | `italic_design(regular)` 给出独立 control sheet + **构造倾角**（`italic_slant_deg`，默认约 10°），`n/h/r/u/m` 分支拱、`f` 下伸等拓扑与直立不同；可与 Regular 做 `wght×ital` VF（`vf_upright_controls` 对齐段数）。`ital=1` 用 `italic_design`，不要用 `oblique_font` 冒充 Italic 风格名 |
| 符号、数字、变音属于同一族 | 标点 / figures / extended Latin / 特性 glyph 与 `features.fea` **同时存在** |
| 侧距与字偶是设计的一部分 | `space_font` → class kern；VF 各母版 **同一 kern groups** |
| 用固定句子 proof 验收 | 编译后 `qa.proof`。过关句锁死 `AGENT_SENTENCE`；brief 句只作第二张 specimen。`design_review` 给出相对 preset 的 delta、弱字与最差 pair |
| 特性与 glyph 一致 | 优先 `compose_font_from_controls` + `FamilyBuildOptions`，避免幽灵 `.tf`/`.case` |
| 单字 master | `Controls.tuned_glyph(ch, **spec)` 或 `with_glyph(ch, builder)`，而非只拧 context |

## 不是什么

- 不是「调几个 float 就得到任意书法 / 花体」——**品类**（sans / serif / script）由 **拓扑与 glyph 集** 决定，缺拓扑要扩 `parts` 或 import UFO，而不是 shear。
- 不是 fontmake 替代品：OpenType 表与二进制编译 **依赖 fontTools / ufo2ft**。
- 不是可跳过 proof 的导出脚本：能安装 ≠ 设计完成。

## 完成分级（交付前自检）

`check_sentence_gate` 是 **回归刹车**，不是设计奖。先选定级别。用户要的是字族时，停在更低一级算未完成。

| 级别 | 落在哪 | 完成条件 |
| --- | --- | --- |
| **L0 试字** | `examples/agent_studio/` | 点名一个 preset；只做 **有记录的字段增量**（相对该 preset 的值，而不是无参照的 `stem=78`）；`tuned_glyph` 或 `with_glyph` 至少覆盖 `f t j a s e` 中的 **两个**。过关文本只能是 `AGENT_SENTENCE`。`design_review(..., baseline=未改过的 preset)` 上，optical gap ratio 与非端子 G1 **不得差于** 该 preset。 |
| **L1 单 style 可读** | 仍是一个字重 | L0，且固定 pair/word（`Ta` `To` `fi` `fl` `rn` `011`）**无撞字**（光学间距 ≤ 0 即失败）。pair 检查已经做进 `check_sentence_gate`。 |
| **L2 字族** | `examples/agent_family/` 或自建 `examples/<family>/build_*.py` | Regular + Light/Bold（或 VF），每个字重独立 `Controls`。Bold 用 `with_stem_relief()`。`compose_font_from_controls` + 各母版共用 `reference_kern_classes`。 |
| **L3 独特声音** | 与 L2 同级或在其之上 | 相对**最近**内置 preset 的 `nearest_voice_distance` ≥ **0.35**（`L3_VOICE_DISTANCE_THRESHOLD`）且 `topology_fraction_vs_nearest_presets` ≥ **0.05**（`L3_MIN_TOPOLOGY_FRACTION`，`l3_voice_criteria_met` 锁定）。`check_family_gate` 与 lint **零错误**。差异须来自 `Style`、`tuned_glyph` / `with_glyph` 等**有记录的** API，而不是无拓扑的纯缩放或噪声。**人审**（`approvals/*.json`）仍为必选项。 |

字族级还要同时满足：

1. **字符集声明与实现一致**：`build_all` 子集、`features`、UFO 里 glyph 名一致（无 `.tf` / `.case` 幽灵引用）。italic 若承诺，须用 `italic_design` 等可实测倾角（≥ 6° 竖笔）的斜体母版，而不是把 `oblique_font` 标成 Italic。
2. **两张校样**：锁死句 `sentence.png`（参与 pass/fail）+ brief 句 `sentence_brief.png`（不参与）。正文字号约 24–36 px。
3. **可复现**：上述脚本一键 build；依赖 `[compile,specimen,boolean]` 写进 README。

### 反模式（出现即未完成）

- 为了过关而换短句、或把 brief 句传进 `check_sentence_gate`。
- 以 `sentence gate ok` 加一张 PNG 宣布字族完成。
- 在同一套 n/o 拓扑上把 counter / rx 乘 `1.0x`，当作新造型。
- 只改一个 `f`，没有第二轮：读 `design_review`（control PNG、弱字 G1、最差 pair、相对 preset 的 delta）再改。
- 在 `agent_studio` 里交付 Light/Bold。完整字族必须落在 `agent_family` 或新的 `examples/<family>/`。
- 用 shear、`lean`、tracking 冒充 italic 或 copperplate / 连笔 script。缺拓扑就说缺：扩 `parts`，或 UFO import 后让 typekernel 管间距与特性。

## Agent 创作与验收

**L0**：改 `examples/agent_studio/design.py`，再跑：

```bash
pip install -e ".[compile,specimen,boolean]"
python examples/agent_studio/build.py
```

看 `out/grid.png`、`out/sentence.png`、`out/sentence_brief.png` 和 `out/review/review.json`。说明 brief、相对哪个 preset 改了哪个字段、哪两个弱字是 `with_glyph`。gate 失败时进程非 0，不许改句重试。

**L2**：从 `examples/agent_family/` 复制到 `examples/<family>/`，填 `design_light` / `design_bold`（或 VF 母版）和 `build_family.py`。Regular 才和未改 preset 比；Light/Bold 是另一套母版，不要拿 Bold 的 gap 去跟 Regular preset 比。

库内等价调用：

```python
from typekernel.qa.design_review import design_review

review = design_review(my_controls, baseline=Controls.from_context(DesignContext.humanist_sans()))
# review.failures 为空只说明刹车没响，不说明字族完成。
```

校样导出（句子参数用锁死句；brief 另存一张，不传入 gate）：

```python
from typekernel.qa.agent_preview import build_glyph_preview
from typekernel.qa.sentence_gate import AGENT_SENTENCE

paths = build_glyph_preview(
    my_controls, family="…", focus="n o a f", sentence=AGENT_SENTENCE, out_dir="out"
)
```

## 工程债已清、仍须人完成的

脚手架与默认构造（间距类 kern、`DEFAULT_PAIR_KERN_EXCEPTIONS`、sans `s`/`I`/`J` G1 软默认、`frac`/`ordn`、`opsz`、斜体 oblique 预切等）已在库内落地；agent 开局少拧 `tuned_glyph`。下面这些 **不是** 再写一份 prompt 就能出现的。

- **视觉回归 / 终验**：数字刹车之外，人审 JSON（`qa.gates.write_approval`）必须由人写下。gate 不会自动批准。衬线/斜体 `approvals/*.json` 仍为 false，终验与 §8.6 人评不能单靠快照。试作被接受后才记 `approvals/`。
- **程序级验收入口**：固定三 brief、`snapshot_trial`、L3 `voice_distance` 见 [AGENT_TRIALS.md](AGENT_TRIALS.md)；`examples/run_program_exit.py`（`--gate all` 含 §8、`test_knob_coverage`、`test_extended_latin_policy`、`test_stress`、`test_glyph_specs`、`test_stroke_program_acceptance`、`test_zayju_script` 等烟测，可选 `--with-linters`）、`examples/agent_trial/validate_snapshot.py`（审计已写 `snapshot.json`）、`examples/human_review_bundle.py`（`--only appendix-b` → `appendix_b_three_g_humanist.png` / B-13–B-15）、`examples/contact_sheet.py`、`examples/regenerate_outline_hashes.py`；衬线程序验收 `test_serif_voice_meets_program_acceptance`。剩的是人跑校样与签字，不是缺 API。
- **审美余量**：pair gate 只抓撞字；开口松紧、字偶「好看」、与 oh-my-font / zayJu 的参考距离仍要人眼与 `tuned_glyph` / 手绘下沉（`examples/zayju_letter/design_n.py`）。

配方与调参范围：[agent-recipes.md](agent-recipes.md)。

## 维护

- Agent 工作流说明书： [`.agents/skills/typekernel-font-design/SKILL.md`](../.agents/skills/typekernel-font-design/SKILL.md)
- 改 `parts` / `compile` / 推荐管线时，**同步更新** 该 skill 与本文（若目标变化）。
