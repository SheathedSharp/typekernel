# typekernel 开发计划书

> 状态：草案 v1（待人确认第 9 节的 3 项决策；未确认时按「推荐默认」执行）
> 日期：2026-10-14　基线：`main` @ `1ffa9c1`
> 读者：接手开发的模型。**先读第 0、1 节，再按第 4 节的任务编号逐个做。**

---

## 0. 接手者必读：工作约定

这些约定来自仓库既有规则（`.agents/00-principles.md`、`docs/dev-standards.md`、`docs/AGENT_GOAL.md`），不是新增限制。

**怎么做**

1. 一次只做一个任务（`TK-xxx`），一个任务一个 commit。提交信息用 `type(scope): summary`，如 `feat(qa): add glyph lint rules`。
2. 每个任务结束前三项必须全绿：
   ```bash
   source .venv/bin/activate
   pytest -q && ruff check src tests && mypy -p typekernel
   ```
   **基线并不干净**（见 TK-001），先清掉再做别的。
3. 新增公共符号：先在任务里写签名草图，只在对应模块 `__all__` 暴露，不要为了方便全部导出。
4. 改动 `parts/`、`compile/` 或推荐管线时，同步更新 `.agents/skills/typekernel-font-design/SKILL.md` 与 `docs/AGENT_GOAL.md`。
5. 凡是改变字形外观的任务，提交里要附 before/after 校样图（放 `docs/images/` 或 `artifacts/`），并在提交说明里列出「哪些字形变了」。

**绝对不要做**

- 修改 `AGENT_SENTENCE`，或为了让 gate 通过而放宽阈值、缩小字符集、删减测试。**阈值变更必须独立成一个提交，并说明理由。**
- 用 shear / `lean` / tracking 冒充 italic（项目红线：Oblique ≠ Italic）。
- 把「描边外扩」当字重（红线：字重是 designed deltas）。
- 在 `compile/` 层「顺手美化」字形。
- 自己写 `approvals/*.json`。视觉门禁必须由人写下，遇到就停下来请人批准。

**环境事实**（已核实）：Python 3.13，`.venv` 里有 `fonttools / pillow / skia-pathops / ufo2ft`，**没有 numpy**，不要为 QA 引入 numpy。`pytest -q` 约 13 秒。

**一个已踩过的坑**：多数 `examples/*/out` 被 gitignore，但**部分校样图是被 git 跟踪的**（例如 `examples/variable_family/out/proof.png`、`docs/images/variable-family-proof.png`、`examples/first_font/out/proof.png`）。运行对应示例脚本会覆盖它们。跑完示例后先 `git status`，不是有意更新就用 `git checkout -- <文件>` 恢复。

---

## 1. 目标与成功定义

产品目标（原文见 `docs/AGENT_GOAL.md`）：让 coding agent 通过 typekernel 像人类字体设计师一样创建一款字体，包括各字重、符号等。

把它拆成三条**可测**的能力，本计划所有任务都服务于这三条：

| 编号 | 能力 | 当前是否达成 | 可测标准（最终验收） |
| --- | --- | --- | --- |
| **C1 独特** | agent 能得到和任何内置 preset 在**拓扑或形状**上显著不同的字体 | 否 | `voice_distance` 指标 + 人审（TK-307） |
| **C2 优秀（可用）** | 声明的全部字符都能用：无结构缺陷、字形可辨、字重阶梯不崩 | 否 | 全字符集 lint + identity 为零错误；`stem` 30–180 阶梯无坍塌 |
| **C3 可验证** | 验收覆盖声明的全部字符，指标能区分好坏，且不能被钻空子 | 否 | `check_family_gate` 覆盖 100% 声明字符；阈值有锁定测试 |

> 完成程序级验收的唯一办法是**真让 agent 做几款字**（第 6 节「Agent 试验」）。仅靠单元测试变绿不算完成。

---

## 2. 现状诊断（证据）

### 2.1 可信度说明

下面每条结论标注来源：**【实测】** 我写脚本实际跑出来的；**【代码】** 读源码确认；**【推断】** 由前两者推出，未直接验证。复现脚本见附录 E。

### 2.2 不需要动的部分

- 编译链路机械上可用：静态 OTF/TTF、`build_variable_font`、`wght×ital` VF、`examples/agent_family` 三字重、`examples/variable_family` 均能构建 **【实测】**。
- 基线测试：593 个全部通过 **【实测】**。
- `geo/`（三次曲线核、路径、join、boolean）与 `optics/` 的主体不是瓶颈。

→ **本计划不动 `compile/` 的构建逻辑**（只做 TK-001 的类型修复）。

### 2.3 基线并不干净 【实测】

`dev-standards.md` 要求 `pytest + ruff + mypy` 全绿，但现在 **ruff 9 个错误，mypy 24 个错误**（位置见 TK-001）。其中 `parts/context.py:78` 的 `OpticalContext` 是真实的未定义名（只因 `from __future__ import annotations` 没在运行时炸）。

### 2.4 三个结构性缺口

#### 缺口 A（天花板）：设计空间太窄，agent 做不出「独特」的字体

| 证据 | 来源 |
| --- | --- |
| 7 个 preset × 98 个字形，**线段类型序列 98/98 完全相同**；换 preset 只是同一骨架的缩放与变粗 | 【实测】 |
| `DesignContext` 只有 14 个字段；决定字形性格的东西（笔角、端点、衬线、连接方式）硬编码在配方里。`control/caps/figures/punctuation/primitives/diagonals/skeleton_recipes/terminals` 8 个文件里约 1000 个小数字面量，agent 够不到 | 【代码】粗略计数 |
| agent 想独特只有两条路：拧浮点（太浅），或像 `examples/zayju_letter/design_n.py` 那样手写整个字（183 行画一个 `n`，太深）。**缺中间层** | 【代码】 |
| `Controls` 是围绕 `n/o` 与 `H/O` 两对控制字的星形派生；`Derivation = Callable[[n, o, ctx], ComposedGlyph]` | 【代码】`parts/family.py` |
| 不少亲缘字是**几何变换**得到的：`u` = `n` 旋转 180°，`j` = `r` 旋转，`t` = `f` 翻转。人类设计师只把它当起点 | 【代码】`parts/control.py` |

#### 缺口 B（地板）：默认字形底座不够好，agent 是在烂底子上微调

见附录 B「缺陷登记」。要点：

- 标点：`&` 就是 `e`、`#` 就是加号、`!` 的圆点画在竖笔**上方**（等于 `i`）、`$` 没有 S、`%` 比例失衡 **【实测+代码】**。
- 小写：`m`（两拱之间平线直连，形成黑块）、`u`、`t`、`j`、`g` 有明显缺陷；大写 `J`、`G`、数字 `3` 同样。
- 字重：`stem ≥ 150` 时字腔坍塌（`3 a e m n u`）**【实测】**。
- 扩展拉丁（`ç é ñ` 等）默认不在字体里，需 opt-in **【实测】**。

#### 缺口 C（反馈）：验收测错了对象

| 证据 | 来源 |
| --- | --- |
| 句子门禁只覆盖 **20/98** 个字符；`design_review` 只看 11 个字（`n o H O a s e r t f I`） | 【实测】 |
| 7 个 preset 的门禁**全部通过**；`stem=200`、字腔明显塌陷的版本也通过 | 【实测】 |
| 非端点 G1 在不同 preset 间几乎恒定（96–97）：它统计的是构造接缝数，不是质量信号 | 【实测】 |
| 标点测试只断言 `advance > 0`（`tests/parts/test_punctuation.py`），所以 `&` 等于 `e` 也能过 | 【代码】 |
| 上一次真实 agent 试字（见历史会话）的行为：拧几个浮点、换短句直到 gate 通过、宣布完成 | 【会话记录】 |

### 2.5 第二轮核查新发现的问题（比最初汇报更严重）

1. **`contrast` 对圆形字母完全无效** 【实测】
   `contrast` 从 1.0 改到 0.25：`o` 的侧边笔画恒为 70、顶底恒为 69。`contrast=0.5` 时**不变**的字形：`a b c d g i j l o p q C I O 0`。同一款字体里会出现「横笔变细、圆碗仍是等线」的不一致。`parts/primitives.py:148` 留着注释 `reserved for future contrast-aware counters`。
2. **`terminal_style` 只影响 5 个字形**（`c C ( ) ?`）【实测】。`a e r f t j s y g k` 等该有端点的字都没有。
3. **`italic_controls` 不是斜体** 【实测+代码】
   实现是把 `n` 字腔与 `o` 碗宽放大 3.5%、`contrast` 降 4%（`parts/italic.py`）。母版**没有任何倾斜**，渲染出来是略宽的直立体。但文档把它当作「斜体是另一套母版」的实现推荐给 agent（`AGENT_GOAL.md` 第 16、41 行，SKILL 第 170 行「Italic axis: `italic_controls(regular_sheet)` per italic master」）。`AGENT_GOAL.md` 第 93 行同时承认「真斜体母版仍未完成」，所以文档自相矛盾，agent 照做会得到一个直立的「斜体」，与项目红线「Oblique ≠ Italic」的精神冲突。
4. **「字重 delta」只是关于 `stem` 的线性启发式**（`parts/weight_relief.py`），只调 `n/o` 的字腔与碗宽；`examples/agent_family` 里 Light/Bold 与 Regular 的差别就是一个 `stem` 数字加 `with_stem_relief()`。【代码】
5. **`skeleton`/pen 路径有结构限制**：`geo/stroke.py` 的 `Centerline` 只支持折线，笔扩展对曲线中线没有原生支持；`skeleton_recipes.skel_*` 现在反过来委托给 `Controls`。【代码】

### 2.6 对我早先汇报的三处更正

| 早先说法 | 更正 |
| --- | --- |
| 「`$ % = @ °` 有轮廓重叠」 | **不准确。** 精确检查后没有重叠，是**单条轮廓里的零宽接缝（keyhole）**：`_ring_outline_small`（`punctuation.py:632`）与 `_equal_outline`（`:119`）。渲染正常，属中低优先级的结构稳健性问题。 |
| 「`s` 读起来像 5」 | 只是小字号观感。230px 下 `s` 可读，仅偏生硬，列为低优先级。 |
| 「建议把 skeleton+pen 提升为一等路径」 | **撤回。** 它与作者原则冲突（`00-principles.md`：「默认 pen-expand 字重链」不做；`type-designer-workflow.md` 把 pen 定位为造部件手段），且当前 `Centerline` 不支持曲线。主路径改为「字形规格记录 + 风格 DNA」，pen 仅作可选 spike（TK-308）。 |

另外，我曾想用「栅格化 + 3×3 方形腐蚀求最大内切圆」检测黑块，**这个办法有 √2 偏置**（正常的 `o` 也会测出约 1.6×stem；几何上 `o` 环实际最大厚度只有 stem 的 1.05–1.08 倍）。**TK-102 必须用几何法或欧氏距离，并先用合成夹具验证后才能做门禁。**

---

## 3. 总体策略与阶段

**原则：先装眼睛，再修地板，再抬天花板。** 没有可靠的测量，后面的每次改动都无法验收。

```
M0 基线与诚实化 ──► M1 眼睛(lint/identity/校样/gate) ──► M2 修地板(缺陷字形、字重)
                                   │                          │
                                   └──────────────┬───────────┘
                                                  ▼
                              M3 抬天花板(对比度真实化 → 字形规格 → 风格DNA/衬线 → 原创度)
                                                  ▼
                                          M4 真斜体
                                                  ▼
                                   M5 文档与 Agent 试验(程序级验收)
```

| 阶段 | 目标 | 规模 | 出口标准 |
| --- | --- | --- | --- |
| **M0** | 基线干净，文档不再说谎 | S（约 0.5–1 天） | 三项检查全绿；italic 的虚假声明被更正并有 strict-xfail 测试 |
| **M1** | 有一套能发现坏字的测量与校样 | M（约 1–1.5 周） | 在当前 HEAD 上检出附录 B 中「可自动检出」的缺陷；gate 覆盖声明字符 100% |
| **M2** | 默认字形全部可用 | M（约 1–1.5 周） | 全字符 lint+identity 零错误；strict-xfail 登记清空；人审通过 |
| **M3** | 设计空间显著变宽 | L（约 3–5 周） | `contrast`/端点/风格旋钮覆盖达标；至少 3 种可辨识 voice；`voice_distance` 可用 |
| **M4** | 真斜体 | M（约 1–2 周） | 实测倾角、拓扑与 oblique 不同、VF 兼容；人审通过 |
| **M5** | 工作流与验收闭环 | S–M（约 3–5 天） | 文档同步；Agent 试验报告达标 |

**如果只能做一部分**：M0 + M1 + M2 能让现有能力变得「诚实且可用」；M3 的 TK-301/303（对比度真实化 + 字形规格记录）是性价比最高的天花板提升，可单独交付。

---

## 4. 任务清单

任务格式：**目标 / 做什么 / 涉及文件 / 验收（可执行）/ 规模 / 依赖**。数值阈值中标注「待校准」的，必须先在原型上校准，再写进测试，**不得为了过关而调阈值**。

### M0 基线与诚实化

#### TK-001 清零 ruff 与 mypy　〔S〕
- **ruff（9）**：`compile/__init__.py`（I001、RUF022）；`compile/family_build.py`（I001、F401 未用的 `Mapping`）；`optics/__init__.py`（RUF022）；`parts/context.py:78`（UP037、F821）；`tests/axes/test_slant_types.py`、`tests/parts/test_letter_e.py`（I001）。其中 8 个可 `ruff --fix`。
- **mypy（24）**：
  - `parts/context.py:72` `tuned(**kwargs: float)` 与 `terminal_style: Literal[...]` 冲突，改成接受真实字段类型。
  - `parts/context.py:78` 用 `TYPE_CHECKING` 导入 `OpticalContext`。
  - `optics/glyph_polish.py:32`、`qa/sentence_gate.py:71`（`_spaced`）、`qa/proof.py`（`_require_pil` 返回类型、`_save` 的 `str|Path`）补注解。
  - `compile/family_build.py:113` `dict` 不变性，改 `Mapping`。
- **验收**：`pytest -q && ruff check src tests && mypy -p typekernel` 退出码 0；测试数不少于 593。

#### TK-002 文档去虚：更正 italic 声明　〔S〕
- 更新 `docs/AGENT_GOAL.md`（第 16、41、93 行）、`SKILL.md`（第 170 行「Weights & variable fonts」）、`docs/VISION.md`、`README.md`、`parts/italic.py` 文档字符串、`examples/italic_family/build_italic_vf.py` 的说明：明确 `italic_controls` 目前只是**度量微调，不是斜体**，真斜体见 M4。
- 在 `tests/parts/test_italic_controls.py` 加一个 `@pytest.mark.xfail(strict=True)` 的测试：`italic_controls(regular)` 的竖笔倾角实测应 ≥ 6°（现在为 0°，所以 xfail）。M4 完成后该标记必须被移除。
- **验收**：全部文档不再声称现有 italic 是真斜体；新增 xfail 测试存在且为 strict。

### M1 眼睛：测量、校样、验收

> 共同要求：QA 采样（把三次曲线离散）只用于测量，**不得写回字形**，符合 `dev-standards.md`「Sampling may be derived on demand」。

#### TK-101 字形体检 `qa/lint.py`　〔M〕
- **本轮（部分）**：R1 对「单 solid 多轮廓」按外轮廓 CCW 判定，内环负面积不再误报；`_pack` / `_pack_holes` 与标点镜像统一 solid CCW、孔 CW，`humanist_sans` 全字符 R1 error 清零。
- **做什么**：新增 `lint_glyph(glyph, ctx)` 与 `lint_controls(controls, chars=None) -> LintReport`；`LintIssue(glyph, rule, severity, detail)`。规则：
  | 规则 | 检查 | 严重度 |
  | --- | --- | --- |
  | R1 winding | 外轮廓/孔的绕向不一致 | error |
  | R2 keyhole | 单条轮廓含零宽接缝（`pathops` 简化后轮廓数改变） | warn |
  | R3 self-intersect | 轮廓自相交 | error |
  | R4 extrema | 三次段的极值点缺少 on-curve 点 | warn |
  | R5 zones | 字形顶/底偏离 baseline、x-height、cap、ascender、descender 对齐区（允许 overshoot） | warn |
  | R6 degenerate | 零长度段、过小的散点轮廓 | error |
  | R7 sidebearing | 墨迹超出 advance、负侧距 | error |
  | R8 counter-min | 字腔最窄处小于下限（待校准） | error |
- **涉及文件**：新增 `src/typekernel/qa/lint.py`、`tests/qa/test_lint.py`；`qa/__init__.py` 导出。
- **验收**：每条规则有合成坏字形夹具（必须报）与好字形夹具（必须不报）；在 HEAD 上对 `$ % = @ °` 报 R2；`pytest` 时间增加不超过 10 秒。
- **依赖**：TK-001。

#### TK-102 局部笔画厚度度量与异常规则　〔M〕
- **做什么**：实现**几何或欧氏距离**的局部厚度度量（沿内法线的弦长，或欧氏距离变换），新增规则 R9 `thickness_outlier`：同一字形内最大局部厚度相对「控制字 `n/o/H/O` 的对应分位数」的比值。
- **禁止**：用 3×3 方形腐蚀做内切圆（有 √2 偏置，见 2.6）。
- **验证要求（先于门禁使用）**：
  - 合成单线圆环 → 最大厚度/stem ≤ 1.1（几何真值 1.05–1.08）。
  - 单根竖笔 `l` → 1.00 ± 0.02。
  - `m` 的黑块区域厚度应显著大于同字重 `n`（**待校准**）。
- **涉及文件**：`qa/lint.py` 或 `qa/thickness.py`；`tests/qa/test_thickness.py`。
- **依赖**：TK-101。

#### TK-103 字形身份检查 `qa/identity.py`　〔M〕
- **做什么**：为全部 98 个支持字符建立「期望表」`EXPECTATIONS`，规则化而非图像分类（不引入参考字体，避免授权问题；见决策 D4）。每个字符声明：孔数、分离部件数、高度类（x-height / cap / ascender / descender）、部件相对位置（如 `i`/`j` 点在上、`!` 点在下）、左右/上下对称性、是否应有伸出。
- **验收**：在当前 HEAD 上必须检出 `!`（点在上）与 `&`（高度类应为 cap，现为 x-height）；`# $` 的孔数/伸出类期望不符；对**肉眼正常**的字形（`a b c d e o H O A` 等）在 5 个 preset 上零误报。
- **涉及文件**：新增 `qa/identity.py`、`tests/qa/test_identity.py`。
- **依赖**：TK-101。

#### TK-104 全字符校样与对比叠图 `qa/sheet.py`　〔M〕
- **做什么**：`contact_sheet(controls_or_font, out, chars=None, sizes=(72, 36), zones=True)`：全部声明字符，标注字形名，画 baseline/x-height/cap/asc/desc 线，**单张宽度 ≤ 1600px**（保证 agent 能直接看图）。另提供 `weight_ladder_sheet`（同一批字在 `stem` 阶梯上的并排图）与 `diff_overlay`（相对 baseline 的红/蓝叠图）。输出统一进 `out/review/`，并写 `index.json` 列出文件。
- **验收**：对 HEAD 生成的 contact sheet 能肉眼看出 `& # ! $ m` 的问题；`design_review` 自动调用并列出路径。
- **依赖**：TK-101。

#### TK-105 家族级门禁 `qa/family_gate.py`　〔M〕
- **本轮**：`examples/agent_studio/build.py` 与 `examples/agent_family/build_family.py` 在 `charset_failures` 非空时 `exit(1)`（与 sentence/L0 门禁并列）。
- **做什么**：`check_family_gate(controls, charset=None, baseline=None, masters=None) -> list[str]`：对**声明字符集**（默认 `controls.supported`）跑 lint + identity，error 级即失败；对多母版逐个检查。接入 `examples/agent_studio/build.py`、`examples/agent_family/build_family.py` 与 `design_review`。
- **防钻空子**：
  - 声明字符集必须来自 `FamilyBuildOptions.chars` / `controls.supported`，门禁不接受更小的字符集。
  - 新增 `tests/qa/test_gate_thresholds_locked.py`，断言所有阈值常量等于冻结值：改阈值必须显式改这个测试。
  - 保留现有句子门禁与 pair 门禁不变（`AGENT_SENTENCE` 不动）。
- **验收**：`collect_family_gate_failures(humanist_sans)` 零 error（TK-101/202 后已达成）；多母版 `check_family_gate` 同样零 error。
- **依赖**：TK-101、TK-103。

#### TK-106 缺陷登记（strict-xfail）　〔S〕
- **做什么**：把附录 B 中可自动检出的缺陷写成参数化测试 `tests/parts/test_known_defects.py`，每条用 `@pytest.mark.xfail(strict=True, reason="B-xx")`。M2 修好一个，测试会变成 XPASS 而失败，**强制移除标记**，保证登记表与现实同步。
- **验收**：测试套件通过；登记条目与附录 B 的编号一一对应。
- **依赖**：TK-101、TK-103。

#### TK-107 旋钮覆盖测试　〔S〕
- **做什么**：`tests/parts/test_knob_coverage.py`，把附录 C 的敏感度实验固化：每个 `DesignContext` 字段改动后，受影响字形集合不得小于下限。`contrast` 与 `terminal_style` 两条 strict-xfail 已转正（TK-301、TK-304）。
- **验收**：测试通过；xfail 条目与 TK-301/TK-304 对应。

#### TK-108 字形哈希快照　〔S〕
- **做什么**：用现有 `qa/outline_hash.py` 为 `humanist_sans / geometric_sans / code_clear` × 98 字形生成 `tests/golden/outline_hashes.json`，加回归测试。以后**每次字形变更，哪些字形的哈希变了就必须和任务声明一致**，更新快照的提交要在说明里列出变更字形。
- **验收**：快照存在；故意改一个字形能让测试失败。

### M2 修地板

> 每个字形任务的共同验收：①对应 TK-106 登记条目转为通过并移除 xfail；②在 5 个 preset 与 `stem` 50/70/110/150 上通过 lint + identity；③附 before/after 校样；④更新 TK-108 快照并列出变更字形。字形设计须保持**连续三次曲线轮廓**，不允许退回折线或「布尔拼装」做主定义。

#### TK-201 `!` `?`　〔S〕
- **完成**：`exclam_from_n_o` / `question_from_n_o`（cap 竖笔 + 基线圆点 + `?` 钩肩）；`test_known_defects` B-01/B-02 与 identity 回归。

#### TK-202 `&` `@` `$` `#` `%` 真实字形　〔M〕
- **本轮（部分）**：闭引号在已排版墨迹中心镜像（非 `n.width/2`），`'"''""` R7 清零；`humanist_sans` 默认 preset `family_gate` 全过。
- `&`：双环已落地；**尾笔**须与 `wght×ital` VF 同拓扑（第三 solid 在斜体 deep_check 上 `wrong_start_point`），待与 TK-402/403 一并接。
- `$`：S 形加贯穿竖笔（现为两个小环 + 短竖笔，`:688`）。`#`：双竖加双横，可带倾角（现为 `_plus_outline`，`:589`）。`%`：两个**小环**加斜线，比例重做（现为两个点 + 细斜线，`:607`）。`@`：外环 + 内部小 a + 尾（现为环 + 点，`:671`）。

#### TK-203 消除 keyhole 轮廓　〔S〕
- **本轮**：三内置 preset 全字符 `R2_keyhole` 零报（`humanist_sans` / `code_clear` / `geometric_sans`）。
- `_ring_outline_small`（`punctuation.py:632`）、`_equal_outline`（`:119`）改成「外轮廓 + 独立孔」，与 `o` 的处理一致。
- **验收**：R2 在全部 98 字形零报。可与 TK-202 合并提交，但要在说明里分开列出。

#### TK-204 `m`、`u`　〔M〕
- **本轮（部分）**：`m` 双拱 `inner_crown` 抬高（`min(crown−0.55×stem, inner+0.32×stem)`）打开中柱 crotch；`u` 经 `mirror_x` 肩拱（非 180° 旋转），基线齐平回归 `test_b10_u_flat_baseline`。
- `m`：内拱在 x-height 的 V 形缺口仍待（内肩曲线常够不到 `xh`，水平 split 失败时无法插点）。
- **本轮（部分）**：直立 `u` 镜像后统一 `_ccw`（修复 R1）；golden `u` 三 preset 更新。
- `u`：低 roundness preset 拱脚局部仍偏细，与 `n` 对称；需时可加专用接合几何。

#### TK-205 钩类字形 `t j f g J`　〔M〕
- 共同现象：钩根与横笔细如发丝（`t_from_n :492`、`j_from_n :516`、`f_from_n :476`、`g_from_o :987`、`J_from_H caps.py:635`）。涉及 `_hook_record`（`:404`）、`_finish_hook_letter`（`:432`，`blend_corners` 半径 `max(5, join_radius*2)`）。**根因为假设**，先量局部厚度。
- **本轮（部分）**：`f`/`t` 横笔改为 `_r_outline` 固定段数 detour（去掉 pathops union）；`min_hook_thickness` 采样带 + `hook_min_thin_floor` 分档；golden `f`/`t` 三 preset 更新。
- **验收**：钩部最小局部厚度 ≥ 对应 `thin` 的某一比例（`hook_min_thin_floor` + `test_hook_root_thickness_*` 已冻结分档）。

#### TK-206 `3`、`G`、`s` 打磨　〔S〕
- **本轮（部分）**：`G_from_O` 内横杠转角改为 κ 圆角（替代折线 chamfer）；`3` 顶区 overshoot 回归测试；`s` 仍低优先。
- `3`：平顶「Ʒ」形（`figures.py:389`）；`G` 的 spur（`caps.py:278`）；`s` 偏生硬（低优先）。

#### TK-207 字重阶梯　〔M〕
- **做什么**：`stem` 从 30 到 200 做阶梯，把 `weight_relief` 从只管 `n/o` 扩展到「每个字形有字腔下限」；定义每字形的最小字腔，再按 R8 验证。
- **本轮（部分）**：`COUNTER_PINCH_CHARSET` 阶梯 R8 回归含 `stem=200`（`tests/qa/test_weight_ladder.py`）；三 golden preset × 阶梯；`family_gate` 三 preset 回归；`weight_ladder_sheet` 可写 PNG 且清理 UFO 临时目录；`.gitignore` 忽略 `_ladder_tmp`。
- **验收**：`stem ∈ {30,70,110,150,180}` 上 `COUNTER_PINCH_CHARSET`（`qa/counter.py`）零 R8；`stem ≥ STEM_RELIEF_ONSET`（85）时调用 `with_stem_relief()`；附 `weight_ladder_sheet`；人审。全 98 字 R8 仍待扩展（竖笔细缝误报）。
- **依赖**：TK-101、TK-104、TK-204、TK-205。

#### TK-208 扩展拉丁默认策略　〔S，可选〕
- 决定 `ç é ñ` 等是否进默认集；无论进不进，composite 字形都必须过 lint（重音碰撞）。

### M3 抬天花板

> 这是工作量最大、最需要人审的阶段。**每个子任务都必须保证默认值下输出与旧版哈希一致**（除非任务明确声明改变并经人批准），这样不会回归。

#### TK-301 让 `contrast` 真实起作用　〔M〕★ 优先
- **做什么**：`OMetrics` 拆成 `thickness_v` / `thickness_h`（`stem` 与 `stem * contrast`）；`bowl`、`_bowl_stem_outline`、`_ring`、`s_from_o`、标点环与 `0` 等接上；`i/j/l/I` 用对比度梯形竖笔与横扁 tittle。
- **验收**（已完成核心）：
  - `contrast=0.5` 时圆形字母集合全动；TK-107 `contrast` xfail 已转正。
  - 探针：`test_o_contrast_top_to_side_thickness_ratio`（`o` 顶/底 ÷ 侧边 ≈ `contrast` ± 0.05）。
  - `code_clear` / `geometric_sans` 哈希不变；`humanist_sans` 快照已更新。
  - 待续：`display` / `open_print` 快照、数字 `3 5 8 9` 与 `G Q S` 的独立 contrast 审计（多数经 `O` 已连带变化）。

#### TK-302 应力轴（stress）　〔M〕
- **做什么**：圆形笔画的最细处不一定在顶/底。新增 `DesignContext.stress`（度，默认 0，加字段属公共 API 变更，先写签名草图），环构造按角度函数分配厚度。`humanist_sans` 是否采用非零值是设计决定，需人审。
- **本轮**：`stress` 字段；`bowl` / `_ring` 对 counter 施加绕 bowl 中心的旋转（`stress=0` 与改造前一致）；`tests/parts/test_stress.py` 探针。
- **验收**：改变 `stress` 后，最薄点位置按角度移动（探针测试）；默认 0 时哈希不变。
- **依赖**：TK-301。

#### TK-303 字形规格记录与 `Controls.tuned_glyph` 〔M〕★ 优先
- **目的**：补上缺失的「中间层」——介于全局浮点（太浅）和手写 `PathBuilder`（太深）之间。
- **进展**：`glyph_specs.py` + `Controls.tuned_glyph` 覆盖 `f t j a s e` 与 cap `G R Y`；`design_review` 记 `spec`；`tests/parts/test_glyph_specs.py` 单调性 + 默认哈希。
- **做什么**：为弱字及其近亲定义**带类型、带文档的规格记录**，字段是设计师会谈论的量，默认值等于当前行为：
  | 记录 | 字段示例 |
  | --- | --- |
  | `TSpec` | 横笔高度、左右长度、钩深、脚长、切口角 |
  | `FSpec` / `JSpec` | 臂长、钩半径、横笔高度、下伸长度 |
  | `ASpec` | 碗高、碗宽、尾部形态 |
  | `ESpec` | 横笔高度、开口、端点角 |
  | `SSpec` | 脊线角度、上下碗比例、开口 |
  | `GSpec` / `RSpec` / `YSpec` | 尾深、耳、臂落差、尾形 |
  让 `Controls.tuned_glyph(ch, **fields)` 修改**该字形所用规格**，而不必写完整 builder。`design_review` 列出被改的规格；`WEAK_GLYPHS` 的 L0 要求允许用 `tuned_glyph` 满足（但必须真的改了字段）。
- **验收**：每个字段有「单调效应」测试（改字段 → 对应测得量按预期变化）；默认值下 98 字形哈希不变；`docs/agent-recipes.md` 增加用法。
- **依赖**：TK-108。

#### TK-304 端点系统　〔M〕
- **做什么**：`terminal_openings.py` 将 `terminal_style` 接到 `c e s r f t j g y k a` 与 `C G S J F T` 等（开口 closure + `terminals` 切/剪）；`ball` / `flared` 仍待扩展。
- **验收**：TK-107 `terminal_style` xfail 已转正（≥20 字形）；默认 `vertical` 下 golden 哈希不变。字重阶梯与 `angled` 全族审计待续。

#### TK-305 风格 DNA：离散拓扑选项　〔L〕
- **进展**：`Style` 六选项均已接线；`tests/parts/test_style_gate.py`（各选项 lint + 非拓扑 style 的 `check_masters`）；`agent-recipes` Style 表。待续：`a_form`/`g_form` 跨字重 VF 兼容、全族 lint/identity 清零。
- **做什么**：新增冻结数据类 `Style`（名称为草案），**只含少量高杠杆的离散选择**，由配方读取；默认值 = 现有行为。建议首批：
  | 选项 | 取值 | 备注 |
  | --- | --- | --- |
  | `a_form` | `single`（现状）/ `double` | 对 voice 影响最大 |
  | `g_form` | `single`（现状）/ `double` | 次优先 |
  | `l_tail` | `none` / `tailed` | |
  | `y_tail` | `straight` / `curved` | |
  | `i_dot` | `round` / `square` / `diamond` | |
  | `t_cut` | `flat` / `slanted` | |
  `Controls.from_context(ctx, style=Style())`。**不要贪多**：每个选项都必须有视觉人审，并在整个字重阶梯上保持点位兼容。
- **验收**：默认哈希不变；每个选项构建全字符 lint + identity 零错误；同一 `Style` 内跨字重通过 `check_masters`。
- **依赖**：TK-303、TK-207。

#### TK-306 衬线系统（先 slab，后 bracketed）　〔L〕
- **做什么**：新增 `parts/serifs.py`，以现有 `primitives.serif_bracket`（自述为 stub）为种子；让竖笔暴露「脚/顶」附着锚点；`Style.serif ∈ {none, slab, bracketed}`，参数含长度、厚度、托架半径。
- **验收**：`serif="slab"` 构建全 98 字形 lint 零错误，并在 ≥ 3 个字重通过；人审；对应 preset（如 `slab_serif()`）与示例。
- **依赖**：TK-305。
- **说明**：衬线是目前最大的拓扑缺口（无衬线之外没有任何品类）。若决策 D2 选择「暂不做衬线」，本任务顺延，M3 出口标准里的「3 种 voice」改由 TK-305 的选项组合满足。

#### TK-307 原创度指标与 L3 定义　〔M〕
- **做什么**：新增 `qa/originality.py`：
  - `topology_signature(glyph)`：每条轮廓的段类型序列 + 孔数。
  - `voice_distance(a, b)`：两套 `Controls` 之间「拓扑签名不同的字形占比」，及按 `stem/x_height` 归一化后的形状距离。
  - `originality_report(controls)`：对所有内置 preset 取最近邻距离。
  在 `AGENT_GOAL.md` 新增 **L3「独特声音」**：最近邻 `voice_distance` ≥ 阈值（待校准，初值建议 0.35）**且** lint+identity 全过**且**经人审。
- **本轮**：`originality.py`（7 preset）、`trial_protocol.voice_distance` 委托 `nearest_voice_distance`；`AGENT_GOAL` L3 行；`tests/qa/test_originality.py`（preset 拓扑基线、自最近邻为 0）。
- **防钻空子**：随机噪声、纯缩放不能通过——必须先过 lint/identity，并要求拓扑差异来自 `Style` 或 `tuned_glyph`/`with_glyph`，而不是数值抖动。
- **验收**：当前 7 个 preset 两两**拓扑**距离为 0（形状距离 > 0）；TK-305/306 产出的 voice 与所有 preset 的距离 ≥ 阈值。

#### TK-308 曲线感知的笔偏移（可选 spike，默认不做）　〔L〕
- 给 `Centerline` 增加三次曲线中线，笔偏移输出三次曲线并附误差报告（类似现有 `ConversionReport` 的诚实原则）。**只作构造手段，不作字重机制，不进入默认管线。**
- 仅在决策 D3 选择「做」时执行。

### M4 真斜体

#### TK-401～404 真斜体母版　〔M〕
- **TK-401**：`italic_design(regular, ItalicStyle)`；`italic_controls` 弃用并 `DeprecationWarning`；`DesignContext.italic_slant_deg` 在 `build_all` 施加构造倾角；TK-002 xfail 已转正。
- **TK-402**：倾角作为**重画母版时的构造参数**（不是对输出做 shear）：竖笔倾角、笔画厚度补偿（倾斜后水平厚度会变）、曲线极值点重平衡。
- **本轮（部分）**：`horizontal_slant_compensation` 用于 `o` 环 `thickness_h`、`f`/`t`/`e` 横笔、`#` 横杠；竖笔倾角 ±0.5° 回归测试；极值点重平衡待续（须与 VF 段数兼容）。
- **TK-403**：拓扑差异：`n m h r u` 的拱从竖笔中段分出（branching）、`f` 可下伸、`a` 保持单层、宽度收窄。
- **本轮**：`n`/`h`/`r`/`u`/`m` 分支拱；单层 `a` 略收窄；斜体 `f` 下伸（inline 横笔、无 blend）；`tests/parts/test_italic_topology.py`。
- **TK-404**：`wght×ital` VF 示例改用真斜体；`check_masters` 通过。直立母版设 `vf_compat_stem_segments=True` 与分支斜体对齐段数（不影响 preset 哈希）。
- **本轮**：全 charset `check_masters` + VF 编译；`vf_upright_controls`；`#` 轮廓起点规范化 + `deep_check_masters` 回归。
- **验收**：
  - 竖笔实测倾角 = 目标 ± 0.5°。
  - 与构造 oblique（`slant_composed_glyph`）比较：至少 8/13 个字母（`a e f g h k m n r u v w y`）轮廓哈希不同，且 ≥4 个拓扑签名不同（`test_italic_topology.py`）。
  - TK-002 加的 strict-xfail 测试转正并移除标记。
  - 人审。
- **依赖**：M2、TK-305。

### M5 工作流与验收闭环

#### TK-501 文档与 skill 同步　〔S〕
- **本轮**：`AGENT_GOAL`、`SKILL`、`reference.md`、`VISION`、`README`、`examples/italic_family` 已对齐 `tuned_glyph`、`italic_design`、TK-301/304 状态；`VISION`/`AGENT_GOAL` 同步 M4 斜体与 TK-205 `f`/`t`。
- **本轮（部分）**：SKILL / `reference.md` 补充 `charset_failures`、family gate、`snapshot_trial` 与 `agent_studio` 退出码行为；`agent-recipes` / SKILL / `reference.md` 同步 TK-303 cap `G R Y` 的 `tuned_glyph` 规格表。
- **待续**：`Style`（TK-305）、L3 验收全文、与 `agent-recipes` 的最终统一核对。

#### TK-502 Agent 试验协议与基线对比　〔M〕
- 见第 6 节。**这是程序级验收，不可省略。**
- **本轮**：`docs/AGENT_TRIALS.md`、`qa/trial_protocol.py`（`voice_distance`、快照 JSON）、`examples/agent_trial/snapshot_presets.py`、`artifacts/trials/` gitignore。
- **待续**：由 agent 按 brief 真改字形并填摘要表；L3 终验与人评。
- **本轮（部分）**：库维护者跑 `snapshot_presets.py` → `artifacts/trials/preset-baseline-2026-10-14/`；三 brief 未改 preset 现 `gate_ok=True`（`preset-baseline-2026-10-14-gate-clear/`），`test_preset_brief_snapshots_pass_gate` 固化。

---

## 5. 依赖与建议顺序

```
TK-001 ─► TK-101 ─► TK-102
   │        ├────► TK-103 ─► TK-105 ─► TK-106
   │        └────► TK-104
   └─► TK-002          TK-107, TK-108（可与 M1 并行）

M2：TK-201 → TK-202+203 → TK-204 → TK-205 → TK-206 → TK-207 →（TK-208）
M3：TK-301 → TK-302 → TK-303 → TK-304 → TK-305 → TK-306 → TK-307  （TK-308 可选）
M4：TK-401 → TK-402 → TK-403 → TK-404
M5：TK-501（贯穿）→ TK-502
```

**建议的第一周**：TK-001 → TK-002 → TK-101 → TK-103 → TK-104 → TK-106。这几步做完，就能自动、可视地看到全部问题，之后的开发才有方向感。

---

## 6. Agent 试验协议（程序级验收）

目的：验证「库真的让 agent 做出独特且可用的字」，这是原始假设，至今**没有被直接检验过**。

- **时机**：M1 完成后跑一次**基线试验**（记录「改造前」），M5 再跑一次**终验试验**。
- **三个 brief**（固定，不得因结果调整）：
  1. 温暖的人文主义 UI 无衬线（Regular + Bold）。
  2. 编辑排版用的 slab 衬线（Regular + Bold；若 D2 为不做，则改为「几何感无衬线，单层 a/g」）。
  3. 编程等宽、端点带明显外扩，要求有符号集（ASCII 全部标点）。
- **每次试验记录**：使用的 API（是否用了 `tuned_glyph`/`Style`/`with_glyph`）、轮次、lint/identity 错误数、`voice_distance`、字重阶梯结果、是否换句子/改阈值（**一旦发现作弊，该次试验作废**）、人对 contact sheet 的评分（1–5，维度：可读、统一、独特、符号完整）。
- **成功标准**（初值，待首次基线后校准）：
  - 终验试验中三个 brief 均通过 `check_family_gate` 且 lint/identity 零错误；
  - 至少 2/3 的 brief `voice_distance` ≥ L3 阈值；
  - 人评「独特」「符号完整」两项平均 ≥ 3.5，且高于基线试验。
- 产物放 `artifacts/trials/<日期>-<模型>/`，不进版本库的大文件用 `.gitignore`；摘要写进 `docs/AGENT_TRIALS.md`。

---

## 7. 风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| 风格选项膨胀，维护成本失控 | M3 拖长、回归增多 | 首批 ≤ 6 个选项；每个都要人审与全字重阶梯通过；默认值哈希不变 |
| 指标被钻空子（agent 或开发者调阈值过关） | 验收失真 | 阈值锁定测试、独立提交、禁止改句子；L3 必须过 lint+identity 并要求拓扑差异来源 |
| 自动化无法判断「好看」 | 质量仍依赖人 | 保留人审门禁（`approvals/*.json` 由人写）；校样图标准化、尺寸可被 agent 直接查看 |
| 新拓扑破坏插值兼容 | VF 不可用 | 同一 `Style` 内必须保持点位兼容并跑 `check_masters`；跨 `Style` 不要求兼容 |
| 对比度真实化改变现有 preset 外观 | 旧校样图过期 | TK-301 明确声明受影响 preset；需人审；更新快照与 `docs/images` |
| QA 度量本身有偏置（如前述 √2 偏置） | 误报/漏报 | 每个度量先用合成夹具验证，再进门禁；记录已知局限 |
| 度量性能 | CI 变慢 | 用几何法与采样上限；`pytest` 总增量 ≤ 30 秒；contact sheet 不进默认单测 |

---

## 8. 程序级完成定义

全部满足才算完成：

1. `pytest -q`、`ruff check src tests`、`mypy -p typekernel` 全绿。
2. 附录 B 的缺陷登记全部关闭，TK-106 的 xfail 为空。
3. `check_family_gate` 在 3 个主 preset 与 TK-305/306 产出的 voice 上，对**全部声明字符**零错误。
4. `contrast`、`terminal_style` 的旋钮覆盖达标（TK-107 无 xfail）。
5. 真斜体通过实测倾角与拓扑差异检查，TK-002 的 xfail 已移除。
6. 第 6 节 Agent 试验终验通过。
7. `AGENT_GOAL.md`、`SKILL.md`、`agent-recipes.md`、`VISION.md`、`README.md` 与实现一致。

---

## 9. 已确认决策（2026-10-14）

| 编号 | 决策 | 结论 |
| --- | --- | --- |
| **D1** | 真斜体是否纳入本程序？ | **做**（M4，TK-401～404） |
| **D2** | 是否做衬线？ | **做**（先 slab，TK-306） |
| **D3** | 是否做曲线感知笔偏移（TK-308）？ | **做**（M3 末 / 与骨架实验衔接，需扩展 `geo/stroke.Centerline`） |
| D4 | 身份检查用规则期望表，还是内置参考字体做最近邻？ | **规则期望表**（无授权问题，CI 稳定） | 参考字体更准，但涉及授权与体积 |
| D5 | `Controls` 保持 `n/o/H/O` 星形，还是允许新增控制字对？ | **保持星形**，用 `tuned_glyph`/`Style` 拓宽 | 新增控制字对会改动 `Controls` 核心接口 |

---

## 附录 A　模块速查（给接手者）

| 想找什么 | 去哪 |
| --- | --- |
| 比例与 preset | `src/typekernel/parts/context.py` |
| 控制字与派生（小写） | `parts/control.py`（`n/o` 记录、`_n_family_outline`、`m/u/f/t/j/g/s/a`）、`parts/family.py`（`Controls`、`RELATED_FORMS`） |
| 大写 / 数字 / 标点 | `parts/caps.py`、`parts/figures.py`、`parts/punctuation.py`（`PUNCT_FORMS`） |
| 斜线类字形 | `parts/diagonals.py`（`_hwidth`、`k/v/w/x/y/z`） |
| 字重 | `parts/weight_relief.py`、`axes/weight_delta.py` |
| 端点 | `parts/terminals.py`、`parts/aperture.py` |
| 骨架/笔（当前仅折线） | `parts/skeleton.py`、`parts/pen.py`、`geo/stroke.py` |
| 间距/字偶 | `optics/space.py`、`parts/metrics.py` |
| 构建 | `compile/family_build.py`（`compose_font_from_controls`）、`compile/build.py` |
| QA | `qa/sentence_gate.py`、`qa/design_review.py`、`qa/score.py`、`qa/proof.py`、`qa/specimen_png.py`、`qa/gates.py` |
| 字形装配与侧距 | `parts/compose.py`（`GlyphAssembler.build` 自动按 `sidebearing_ratio` 打包侧距） |
| 示例 | `examples/agent_studio`（L0）、`examples/agent_family`（L2 模板） |

---

## 附录 B　缺陷登记（M1 的 TK-106 据此建 xfail，M2 据此修复）

「根因」列：**已确认**＝读代码并看到对应行为；**假设**＝合理推断，修之前先验证。

| 编号 | 字形 | 症状 | 根因 | 位置 | 可自动检出 |
| --- | --- | --- | --- | --- | --- |
| B-01 | `!` | 圆点在竖笔上方，等价于 `i`；竖笔只有 `0.72×x-height` | 已确认 | `punctuation.py:239` | identity |
| B-02 | `?` | 缩放的 `c` 加圆点，没有向下的竖笔 | 已确认 | `punctuation.py:252` | identity |
| B-03 | `&` | 就是 `e_from_o`，docstring 自述占位 | 已确认 | `punctuation.py:663` | identity（高度类） |
| B-04 | `#` | 就是加号（`_plus_outline`） | 已确认 | `punctuation.py:589` | identity（孔数） |
| B-05 | `$` | 两个小环 + 短竖笔，无 S | 已确认 | `punctuation.py:688` | identity |
| B-06 | `%` | 两个点 + 细斜线，应为小环，比例失衡 | 已确认 | `punctuation.py:607` | identity |
| B-07 | `@` | 环 + 点，无字母 a | 已确认 | `punctuation.py:671` | identity |
| B-08 | `= ° $ % @` | 单条轮廓含零宽接缝（keyhole），pathops 简化后轮廓数改变；渲染正常 | 已确认（现象） | `punctuation.py:119, 632` | lint R2 |
| B-09 | `m` | 两拱之间平线直连，顶部形成实心黑块，无内角缺口 | 已确认 | `control.py:575` | lint R9（待校准） |
| B-10 | `u` | 左下重脚（类 slab） | **假设**：`n` 旋转 180° 后肩–腿接合变成重脚 | `control.py:604` | lint R9（待校准） |
| B-11 | `t` | 横笔与钩根细如发丝 | **假设**：钩深/rise 参数 + `blend_corners` 圆角过大 | `control.py:492`、`_finish_hook_letter :432` | lint R9 |
| B-12 | `j f g J` | 钩根细、尾部尖 | **假设**：同源于 `_hook_record` | `control.py:516, 476, 987`、`caps.py:635` | lint R9 |
| B-13 | `3` | 平顶「Ʒ」形 | 视觉确认，根因未查 | `figures.py:389` | 视觉 |
| B-14 | `G` | spur 生硬 | 视觉确认，根因未查 | `caps.py:278` | 视觉 |
| B-15 | `s` | 偏生硬（可读） | 视觉确认；低优先 | `control.py:1037` | 视觉 |
| B-16 | 重字重 | `stem ≥ 150` 时 `3 a e m n u` 字腔坍塌 | 已确认（现象） | `weight_relief.py` | lint R8 |
| B-17 | `contrast` | 对圆形字母无效 | **已修**（TK-301） | `OMetrics` 横竖厚度 | — |
| B-18 | `terminal_style` | 只影响 `c C ( ) ?` | 已确认 | 多处 | TK-107 |
| B-19 | italic | 无拓扑分支 | 部分修（TK-401 倾角） | `italic_design` | TK-403 |
| B-20 | 扩展拉丁 | 默认不在字体中 | 已确认（设计如此） | `family.py` / `FamilyBuildOptions` | 决策（TK-208） |

---

## 附录 C　旋钮敏感度实验（TK-107 的基线）

基准：`humanist_sans`，单项改动，统计 98 个字形中「形状改变」（排除纯平移，阈值 0.5 单位）的数量。**【实测】**

| 旋钮 | 改动 | 受影响字形数 | 备注 |
| --- | --- | --- | --- |
| `stem` | ×1.15 | 95 | 正常 |
| `aperture` | 0.95 | 75 | 正常 |
| `x_height` | ×1.1 | 57 | 正常 |
| `contrast` | 0.5 | 61 | **不变**：`a b c d g i j l o p q C I O 0` |
| `roundness` | 0.9 | 45 | |
| `overshoot` | ×2 | 40 | |
| `cap_height` | ×1.1 | 36 | |
| `descender` | ×1.2 | 19 | |
| `ascender` | ×1.1 | 15 | |
| `sharp_overshoot` | 30 | 5 | `v w A V W`，合理 |
| `terminal_style` | horizontal / angled | **5** | 仅 `c C ( ) ?` |
| `sidebearing_ratio` | 0.2 | 1 | 间距旋钮，几何基本不变，合理 |
| `tracking` | 40 | 0 | 间距旋钮，合理 |

---

## 附录 D　`o` 环的真实厚度（验证用的数值真值）

`o` 的内圈由 `rx − t, ry − t` 构造。沿内法线的真实厚度（单位：设计单位）**【实测，几何计算】**：

| preset | stem | 0° | 20° | 45° | 70° | 90° | 最大/stem |
| --- | --- | --- | --- | --- | --- | --- | --- |
| humanist_sans | 70 | 70.0 | 71.1 | 73.4 | 71.5 | 70.0 | 1.05 |
| geometric_sans | 90 | 90.0 | 91.7 | 96.4 | 92.6 | 90.0 | 1.07 |
| code_clear | 86 | 86.0 | 87.6 | 93.0 | 88.6 | 86.0 | 1.08 |
| mono | 88 | 88.0 | 89.6 | 94.7 | 90.7 | 88.0 | 1.08 |

用途：TK-102 的厚度度量必须在合成 `o` 环上复现这组数（≤ 1.1×stem），否则度量本身有偏置。

---

## 附录 E　复现实验（接手者可直接改成测试）

**E1　拓扑签名：7 个 preset 是否同拓扑**

```python
from typekernel.parts import Controls, DesignContext
from typekernel.geo.contour import CubicSegment

names = ["humanist_sans", "geometric_sans", "mono", "display",
         "paper_ink", "code_clear", "open_print"]

def signature(glyph):
    return tuple(
        tuple("C" if isinstance(s, CubicSegment) else "L" for s in ct.segments)
        for o in (*glyph.solids, *glyph.holes) for ct in o.contours
    )

sigs = {n: {ch: signature(g) for ch, g in
            Controls.from_context(getattr(DesignContext, n)()).build_all().items()}
        for n in names}
base = sigs["humanist_sans"]
same = [ch for ch in base if all(sigs[n][ch] == base[ch] for n in names)]
print(len(same), "/", len(base))   # 当前：98 / 98
```

**E2　`contrast` 对圆形字母无效**

```python
from typekernel.parts import Controls, DesignContext
from typekernel.optics.space import ink_intervals_at_y

base = DesignContext.humanist_sans()
for c in (1.0, 0.82, 0.5, 0.25):
    ctx = base.tuned(contrast=c)
    o = Controls.from_context(ctx).build_all("o")["o"]
    iv = ink_intervals_at_y(list(o.solids), ctx.x_height / 2)
    print(c, "side stroke =", round(iv[0][1] - iv[0][0], 1))   # 恒为 70.0
```

**E3　门禁放行坏字体**

```python
from typekernel.parts import Controls, DesignContext
from typekernel.qa.sentence_gate import check_sentence_gate

c = Controls.from_context(DesignContext.humanist_sans().tuned(stem=200.0)).with_stem_relief()
_report, failures = check_sentence_gate(c)
print(failures)   # 当前：[]（通过）
```

**E4　全字符大图（肉眼检查）**：用 `compose_font_from_controls(controls, name, options=FamilyBuildOptions(liga=True))` 编译 `controls.supported`，再用 Pillow 逐字渲染。注意 `qa.agent_preview.build_glyph_preview` 只编译你传入的字符，不会带出大写与标点。

**E5　`italic_controls` 不倾斜**：`italic_controls(Controls.from_context(DesignContext.humanist_sans()))` 的 `l` 字形包围盒宽度仍等于 `stem`（70.0），与 Regular 相同。
