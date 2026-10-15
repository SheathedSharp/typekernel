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
5. **`skeleton`/pen 路径**：折线 `Centerline` 仍是默认；TK-308 spike 增加 `CubicCenterline` / `Stroke.beziers` + 单段偏移 cubic 拟合，**未**替代 `Controls` 主路径；`skeleton_recipes.skel_*` 仍委托 `Controls`。【代码】

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
- **本轮（部分）**：R4 ``extrema``（warn）用 ``geo.extrema.cubic_has_off_node_axis_extrema``；合成夹具 + 七 preset 直立回归仍绿；七 preset ``italic_design`` R4 清零（``test_italic_design_clears_r4_on_builtin_presets``，TK-402）。
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
- **本轮（部分）**：``m_crotch_shelf_thickness_over_stem`` + ``M_CROTCH_SHELF_MIN_OVER_STEM`` 冻结探针（三 preset 回归）。
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
- **本轮（部分）**：``test_preset_passes_family_gate`` 覆盖七内置 preset（``mono`` / ``display`` / ``paper_ink`` / ``open_print`` 与三 golden）。
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
- **本轮（部分）**：`&` 下环外轮廓 Q 式接左下尾笔（双 solid、双孔，无第三 solid）；golden `&` 三 preset 更新。
- **本轮（部分）**：`@` 外环 + 环内小 bowl（双孔），重字重缩小 belly 避免叠墨；golden `@` 三 preset 更新。
- **本轮（部分）**：`$` 改为腰接双环单 solid（`8` 式 S 脊柱、双孔，无第三 solid / union）；golden `$` 三 preset 更新；`&` / `$` 三 preset 字重插值 `check_interpolatable` 回归。
- **本轮（部分）**：`$` 外轮廓基线 + 顶环竖笔帽（`u0` 水平 split + `xl`–`xr` detour，`l2` split）；golden `$` 三 preset 更新。
- **本轮（部分）**：`test_dollar_waist_coupled_topology` 固化单 solid 双孔、腰墨、顶/底竖笔帽与外轮廓 15 段 VF 拓扑。
- **本轮（部分）**：`#` / `%` 三 preset 字重插值 `check_interpolatable` + `#` 外轮廓 28 段 VF 拓扑回归。
- **本轮（部分）**：`@` 重字重略缩小环内 belly（`heavy×0.10`），`geometric_sans` 阶梯 R8 通过；`@` 纳入 `COUNTER_PINCH_CHARSET` + VF 插值回归。
- **本轮（部分）**：`@` belly 随环内半径 `fill` 缩放 shrink、超重 `belly_k` 微调；字重阶梯 R8 覆盖七内置 preset。
- **本轮（部分）**：`&` 上下环壁厚相对 bowl 半径封顶（`wall_cap=0.36`），重 stem 孔洞不再塌缩；golden `&` 三 preset；`&` 纳入 `COUNTER_PINCH_CHARSET`。
- `$` 真 S 贯穿竖笔（非仅顶/底帽）仍非目标；`#`/`%` 实现见 `hash_from_n_o` / `percent_from_n_o`。

#### TK-203 消除 keyhole 轮廓　〔S〕
- **本轮**：三内置 preset 全字符 `R2_keyhole` 零报（`humanist_sans` / `code_clear` / `geometric_sans`）。
- `_ring_outline_small`（`punctuation.py:632`）、`_equal_outline`（`:119`）改成「外轮廓 + 独立孔」，与 `o` 的处理一致。
- **验收**：R2 在全部 98 字形零报。可与 TK-202 合并提交，但要在说明里分开列出。

#### TK-204 `m`、`u`　〔M〕
- **本轮（部分）**：`m` 双拱 `inner_crown` 抬高（`min(crown−0.55×stem, inner+0.32×stem)`）打开中柱 crotch；`u` 经 `mirror_x` 肩拱（非 180° 旋转），基线齐平回归 `test_b10_u_flat_baseline`。
- **本轮（部分）**：`m` 在双拱 metrics 之后将 `inner_crown` 抬至 `x-height`（上限 `crown−0.06×stem`），内肩可水平 split、中柱 crotch 接 shelf；golden `m` 三 preset 更新。
- **本轮（部分）**：直立 `u` 镜像后统一 `_ccw`（修复 R1）；golden `u` 三 preset 更新。
- **本轮（部分）**：低 roundness（``<0.35``）``u`` 左 baseline toe：G1 cubic + shelf（12 段）；高 roundness 仍 11 段镜像；golden ``u``（``code_clear`` / ``geometric_sans``）更新。
- **本轮（部分）**：``_bowl_stem_outline`` 将碗顶接点 x 对齐 stem 面（修复镜像 ``b`` even-odd 细缝）；``test_b_outer_ink_continuous_across_stem_bowl_join``；golden ``b``/``d``/``p``/``q``（及 ``a``/``g`` 连带）三 preset。
- **本轮（部分）**：碗底接点 x 同样对齐 stem 面；``test_p_outer_ink_continuous_across_stem_bowl_join``。
- **本轮（部分）**：``u_from_n`` 构建轮廓时抬高 ``inner_crown``（与 ``m`` 同上限），重字重肩拱 crotch 过 R8；golden ``u`` 五 preset 更新。

#### TK-205 钩类字形 `t j f g J`　〔M〕
- 共同现象：钩根与横笔细如发丝（`t_from_n :492`、`j_from_n :516`、`f_from_n :476`、`g_from_o :987`、`J_from_H caps.py:635`）。涉及 `_hook_record`（`:404`）、`_finish_hook_letter`（`:432`，`blend_corners` 半径 `max(5, join_radius*2)`）。**根因为假设**，先量局部厚度。
- **本轮（部分）**：`f`/`t` 横笔改为 `_r_outline` 固定段数 detour（去掉 pathops union）；`min_hook_thickness` 采样带 + `hook_min_thin_floor` 分档；golden `f`/`t` 三 preset 更新。
- **本轮（部分）**：`g` 钩腹单 cubic detour + 重字重 `join_y` 抬升（禁 `blend_corners`）；`test_g_hook_outer_segment_count_fixed_across_stems` / VF 阶梯回归；golden `g` 三 preset 更新。
- **本轮（部分）**：`J` 碗脚 spring 单 cubic detour（段数 8 不变）；golden `J` 三 preset 更新。
- **本轮（部分）**：`j` / dotless ``ȷ`` 去掉 ``blend_corners``，``_r_outline`` ``hook_belly`` cubic；golden ``j`` 三 preset 与 VF 阶梯回归。
- **本轮（部分）**：``g`` 重字重按 ``roundness`` 略减 ``_hook_record`` depth（``open_print`` 阶梯钩根）；``tests/qa/test_hook_weight_ladder.py`` 四 preset × ``stem`` 30–180（含 ``with_stem_relief()``）钩厚回归。
- **本轮（部分）**：``f``/``t`` 横笔 detour 用 ``_crossbar_counter``（relief 不全量加宽 counter）；``g`` 重 stem 略回拉 ``o`` bowl 以利钩根；``t`` 固定拓扑 ``hook_belly``；``humanist_sans`` ``stem=200``+relief 钩厚回归；golden ``t`` 三 preset。
- **本轮（部分）**：``t`` 高 roundness 黑体横笔额外 counter 回拉；neo-grotesque（``roundness≈0.28``）黑体略减 hook depth；钩厚阶梯含 ``stem=200`` 四 preset。
- **验收**：钩部最小局部厚度 ≥ 对应 `thin` 的某一比例（`hook_min_thin_floor` + `test_hook_root_thickness_*` 已冻结分档）。

#### TK-206 `3`、`G`、`s` 打磨　〔S〕
- **本轮（部分）**：`G_from_O` 内横杠转角改为 κ 圆角（替代折线 chamfer）；`3` 顶区 overshoot 回归测试。
- **本轮（部分）**：`s_from_o` 默认 `top_scale` 0.94→0.92，上环略收；golden `s`/`S` 三 preset 更新。
- **本轮（部分）**：``G`` spur κ 圆角随 cap stem 略增（重字重仍 ``use≤0.34`` 防自交）；``test_g_outer_segment_count_fixed_across_stems`` / VF 阶梯回归；golden ``G`` 三 preset 更新。
- **本轮（部分）**：``s`` VF 阶梯段数固定 + ``check_masters`` 回归（``test_s_outer_segment_count_fixed_across_stems`` / ``test_s_interpolates_across_weight_ladder``）。
- **本轮（部分）**： lining ``3`` VF 段数固定 + ``check_masters`` 回归（``test_three_outer_segment_count_fixed_across_stems`` / ``test_three_interpolates_across_weight_ladder``）。
- **本轮（部分）**：``3`` 上环 ``ry_u`` 乘 ``top_apex=1.06``（顶仍对齐 cap+overshoot，减少平顶）；golden ``3`` 三 preset 更新。
- **本轮（部分）**：``s_from_o`` 默认 ``top_scale`` 0.92→0.90（上环再收）；golden ``s``/``S`` 三 preset 更新。
- **本轮（部分）**：``one_from_H`` 顶旗随字重缩小，重 stem 肩区字腔满足 R8（见 TK-207 ``1``）。
- **本轮（部分）**：``five_from_O`` 按 ``DesignContext.stem`` 加宽下碗、略收环笔画与开口；极轻（``stem<44``）/极黑（``stem≥199``）再收 ``stroke_scale``；``test_five_stem_relief_opens_bowl_counter_midweights`` 覆盖七 preset × ``30…200``；golden ``5`` 五 preset。
- **本轮（部分）**：``K_from_H`` 阶梯加宽与 junction 抬高（见 TK-207 ``K``）；golden ``K`` 更新。
- **本轮（部分）**：``SSpec.top_scale`` 默认与 ``s_from_o`` 对齐（``tuned_glyph("s")`` 无参不再放宽上环）；``test_s_tuned_glyph_defaults_match_stock``。
- **本轮（部分）**：``Controls.build_all`` 仅把 ``glyph_overrides`` 并入对应表（小写不进 cap/figure 轮），修复 ``tuned_glyph("s")`` 被 cap ``H``/``O`` 二次覆盖。

#### TK-207 字重阶梯　〔M〕
- **做什么**：`stem` 从 30 到 200 做阶梯，把 `weight_relief` 从只管 `n/o` 扩展到「每个字形有字腔下限」；定义每字形的最小字腔，再按 R8 验证。
- **本轮（部分）**：`COUNTER_PINCH_CHARSET` 阶梯 R8 回归含 `stem=200`（`tests/qa/test_weight_ladder.py`）；三 golden preset × 阶梯；`family_gate` 三 preset 回归；`weight_ladder_sheet` 可写 PNG 且清理 UFO 临时目录；`.gitignore` 忽略 `_ladder_tmp`。
- **本轮（部分）**：`$` 纳入 `COUNTER_PINCH_CHARSET`（腰接双环后字重阶梯 R8 零报）。
- **本轮（部分）**：扩展 `COUNTER_PINCH_CHARSET`（`2`/`7`、`s`/`S`/`c`、大写 `CDEFOPQSTUZ`、`#`/`%`/`?`）；三 preset × 阶梯 R8 仍零报。
- **本轮（部分）**：``min_counter_gap`` 在 ``y0<0`` 时将采样带下限抬至 ``0.12×y1``，避免 ``p``/``q`` descender 竖缝误报；``test_descender_letters_skip_baseline_stem_pinch``。
- **本轮（部分）**：``min_counter_gap`` 对多轮廓 solid 用内孔包围盒、跳过 even-odd 竖缝误报；``b``/``d``/``g``/``p``/``q`` 纳入 ``COUNTER_PINCH_CHARSET``。
- **本轮（部分）**：大写 ``A``/``B``/``R`` 纳入 ``COUNTER_PINCH_CHARSET``（阶梯 R8 零报）。
- **本轮（部分）**：直立 ``u`` 纳入 ``COUNTER_PINCH_CHARSET``（七 preset × 阶梯 R8 零报）。
- **本轮（部分）**： lining ``4`` 纳入 ``COUNTER_PINCH_CHARSET``（七 preset × 阶梯 R8 零报）。
- **本轮（部分）**：``one_from_H`` 重字重缩小顶旗 ``fw``/``fv``（``stem_weight_fraction``）；``1`` 纳入 ``COUNTER_PINCH_CHARSET``；``test_one_heavy_stem_flag_relief_opens_pinch``（默认 master 哈希未变）。
- **本轮（部分）**：大写 ``H``/``J`` 纳入 ``COUNTER_PINCH_CHARSET``（七 preset × 阶梯 R8 零报）。
- **本轮（部分）**： lining ``5`` 纳入 ``COUNTER_PINCH_CHARSET``（七 preset × 阶梯 R8 零报）。
- **本轮（部分）**：``min_counter_gap`` 忽略 scanline 上小于 ``max(1, 0.09×stem)`` 的墨迹缝（竖笔–斜臂细缝）；``test_cap_k_ignores_stem_diagonal_micro_slivers``。
- **本轮（部分）**：``K_from_H`` 按 ``DesignContext.stem`` 分段加宽/抬高 junction；``K`` 纳入 ``COUNTER_PINCH_CHARSET``；``test_cap_k_passes_counter_floor_across_ladder``；golden ``K``（``humanist_sans``/``display`` 等）更新。
- **本轮（部分）**：``N_from_H`` 重/高 contrast 中段略加宽；``N`` 纳入 ``COUNTER_PINCH_CHARSET``；``test_cap_n_passes_counter_floor_across_ladder``（默认 master 哈希未变）。
- **本轮（部分）**：``M_from_H`` 按 stem/contrast 抬高顶点 apex、极轻/极黑略加宽；``M`` 纳入 ``COUNTER_PINCH_CHARSET``；``test_cap_m_passes_counter_floor_across_ladder``；golden ``M`` 更新。
- **本轮（部分）**：大写 ``G``/``I``/``L`` 纳入 ``COUNTER_PINCH_CHARSET``（七 preset × 阶梯 R8 零报；无轮廓变更）；``test_cap_stem_letters_pass_counter_floor_across_ladder``。
- **本轮（部分）**：``X_from_H``/``Y_from_H`` 中段阶梯微调；``X``/``Y`` 纳入 charset；``test_cap_x_passes_counter_floor_across_ladder`` / ``test_cap_y_passes_counter_floor_across_ladder``（默认 master 哈希未变）。
- **本轮（部分）**：``V_from_H``/``W_from_H`` 按 stem/contrast/roundness/aperture 分段加宽；``V``/``W`` 纳入 charset；``test_cap_v_passes_counter_floor_across_ladder`` / ``test_cap_w_passes_counter_floor_across_ladder``；golden ``W``（``humanist_sans``）更新。
- **本轮（部分）**：``y_from_n`` 字重阶梯加宽（含 contrast 分段）；``y`` 纳入 ``COUNTER_PINCH_CHARSET``；``test_y_passes_counter_floor_across_ladder``；golden ``y``（``humanist_sans``/``display``）。
- **本轮（部分）**：``v_from_n`` 字重阶梯加宽（对齐 cap ``V`` + 小写 ~70/150 band）；``v`` 纳入 charset；``test_v_passes_counter_floor_across_ladder``；golden ``v``（``humanist_sans`` 等）。
- **本轮（部分）**：``w_from_n`` 阶梯加宽（对齐 cap ``W``，小写不做 mid-contrast 收窄）；``w`` 纳入 charset；``test_w_passes_counter_floor_across_ladder``。
- **本轮（部分）**：``x_from_n`` 阶梯加宽（对齐 cap ``X`` + ~70 band）；``x`` 纳入 charset；``test_x_passes_counter_floor_across_ladder``。
- **本轮（部分）**：``k_from_n`` 阶梯加宽（对齐 cap ``K``，含极轻 stem relief）；``k`` 纳入 charset；``test_k_passes_counter_floor_across_ladder``；golden ``k``（``humanist_sans``/``display``）。
- **本轮（部分）**：小写 ``f``/``h``/``i``/``j``/``l``/``r``/``t``/``z`` 纳入 ``COUNTER_PINCH_CHARSET``（七 preset × 阶梯 R8 零报；无轮廓变更）；``test_stem_lowercase_pass_counter_floor_across_ladder``。
- **本轮（部分）**：默认 supported 标点（除 ``*``）纳入 ``COUNTER_PINCH_CHARSET``（七 preset × 阶梯 R8 零报；无轮廓变更）。
- **本轮（部分）**：``asterisk_from_n_o`` 外径 ``0.34→0.375`` 打开字腔；``*`` 纳入 charset；``test_asterisk_passes_counter_floor_across_ladder``；golden ``*`` 五 preset 更新。
- **本轮（部分）**：``COUNTER_PINCH_CHARSET`` 与默认 ``supported`` 一致（全字符 R8 回归）；``weight_ladder_sheet`` 默认阶梯含 ``stem=200``（对齐 ``test_weight_ladder``）。
- **验收**：`stem ∈ {30,70,110,150,180,200}` 上 `COUNTER_PINCH_CHARSET` 零 R8；`stem ≥ STEM_RELIEF_ONSET`（85）时 `with_stem_relief()`；`weight_ladder_sheet` 人审 PNG（本地 ``artifacts/specimens/``，不入库）；自动化已绿，人审待签。
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
  - **本轮（部分）**：`display` / `open_print` 纳入 `outline_hashes.json` 全字符回归；``o`` 横竖厚度比覆盖 ``display``/``open_print`` 默认 contrast；``3``/``5``/``8``/``9``/``G``/``Q``/``S`` contrast 响应探针。
  - **本轮（部分）**：``0``/``G``/``Q``/``S`` 构建结果 ``OMetrics`` 横竖笔比； lining ``3``/``5``/``8``/``9`` ``HMetrics.bar``；小写 ``s`` ``OMetrics`` 回归。
  - **本轮（部分）**：``ometrics_ink_horizontal_over_vertical_ratio`` 等墨迹探针（``0``/``G``/``Q``/``S``、``5``/``8``/``9``）；``3`` 仍仅 ``HMetrics``/形状响应（单轮廓右侧开口不稳）。

#### TK-302 应力轴（stress）　〔M〕
- **做什么**：圆形笔画的最细处不一定在顶/底。新增 `DesignContext.stress`（度，默认 0，加字段属公共 API 变更，先写签名草图），环构造按角度函数分配厚度。`humanist_sans` 是否采用非零值是设计决定，需人审。
- **本轮**：`stress` 字段；`bowl` / `_ring` 对 counter 施加绕 bowl 中心的旋转（`stress=0` 与改造前一致）；`tests/parts/test_stress.py` 探针。
- **本轮（部分）**：``test_knob_coverage`` 补 ``stress`` 旋钮覆盖（``ocCO0`` 形状响应）。
- **验收**：改变 `stress` 后，最薄点位置按角度移动（探针测试）；默认 0 时哈希不变。
- **依赖**：TK-301。

#### TK-303 字形规格记录与 `Controls.tuned_glyph` 〔M〕★ 优先
- **目的**：补上缺失的「中间层」——介于全局浮点（太浅）和手写 `PathBuilder`（太深）之间。
- **进展**：`glyph_specs.py` + `Controls.tuned_glyph` 覆盖 `f t j a s e` 与 cap **A–Z 除 H/I**（控制母形 / 单竖无旋钮）；`design_review` 记 `spec`；全 `supported` 默认哈希回归。
- **本轮（部分）**：``SSpec.top_scale`` 与 ``s_from_o`` 对齐；``build_all`` 按字形表路由 ``glyph_overrides``；``test_tuned_glyph_defaults_match_stock_derivation`` 参数化覆盖 ``f``/``t``/``j``/``a``/``e``/``s``。
- **本轮（部分）**：``KSpec``（``width``/``vertex``）+ ``tuned_glyph("K")``；``K_from_H`` 暴露 ``vertex`` 参数；``test_k_width_monotone_opens_outline``；默认 master 哈希未变。
- **本轮（部分）**：``VSpec``/``WSpec``/``XSpec``/``MSpec``/``NSpec`` + ``tuned_glyph`` 路由；默认哈希与单调性测试（``V`` width）。
- **本轮（部分）**：``CapASpec`` + ``tuned_glyph("A")``；``test_tuned_glyph_defaults_preserve_supported_charset_hashes``；``agent-recipes`` 规格表。
- **本轮（部分）**：``CapTSpec``/``LSpec``/``ZSpec`` + ``tuned_glyph``；``T`` width 单调性测试。
- **本轮（部分）**：``CapESpec``/``CapFSpec`` + ``tuned_glyph``；``E`` width 单调性测试。
- **本轮（部分）**：``DSpec``/``PSpec``（需 ``O`` 指数）+ ``D`` width 单调性测试。
- **本轮（部分）**：``BSpec``/``USpec``/``CapJSpec``/``CapCSpec``/``CapSSpec``；``C_from_O``/``S_from_O`` 暴露默认等价参数；``B``/``U``/``S`` 单调性测试。
- **本轮（部分）**：``QSpec``（``tail_reach``/``tail_drop``）+ ``Q_from_O`` 参数；``Q`` 尾长单调性测试。
- **本轮（部分）**：``test_width_spec_monotone_changes_outline`` / ``test_glyph_spec_field_monotone_changes_outline`` 覆盖剩余 cap 宽轴与多字段规格（``B``/``P``/``R``/``s``/``U`` 等）。
- **本轮（部分）**：``A``/``J``/``s`` 缺字段单调性补全；``test_m_apex_monotone_moves_baseline_vertex``（``stem=150``，避开阶梯覆盖带）。
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
- **本轮（部分）**：``WEAK_GLYPH_SPECS`` 全字段单调性回归（含 ``M.apex`` 在 ``stem=150``）；默认 ``supported`` 哈希回归仍绿。
- **验收**：每个字段有「单调效应」测试（改字段 → 对应测得量按预期变化）；默认值下 98 字形哈希不变；`docs/agent-recipes.md` 增加用法。
- **依赖**：TK-108。

#### TK-304 端点系统　〔M〕
- **做什么**：`terminal_openings.py` 将 `terminal_style` 接到 `c e s r f t j g y k a` 与 `C G S J F T` 等（开口 closure + `terminals` 切/剪）。
- **本轮（部分）**：``test_angled_terminal_counter_pinch_charset_passes_r8``（七 preset × 阶梯 R8）；``test_terminal_style_angled_reaches_open_stroke_glyphs``（≥20 字，含 cap ``F``/``T`` 与 ``k``）。
- **本轮（部分）**：cap ``F``/``T`` 在 ``angled`` 下用 ``shear_end``（``along=x``）替代 flat cut，避免 R8 细缝；``horizontal`` 仍 flat cut。
- **本轮（部分）**：``k`` 在 ``angled`` 下臂端 ``apply_terminal_shear``（``along=x``）+ 略加 advance（``w`` 约 +2.6%，轻字重再 +0.4%）以保住阶梯 R8。
- **本轮（部分）**：``terminal_style`` 扩展 ``ball``（``ball_end`` + 开口 closure）与 ``flared``（外扩 shear +18°）；``test_alt_terminal_counter_pinch_charset_passes_r8``（ball/flared × 七 preset × 阶梯）；旋钮覆盖 ``ball``/``flared`` ≥20 字。
- **验收**：TK-107 `terminal_style` xfail 已转正（``horizontal`` ≥20 字形）；默认 `vertical` 下 golden 哈希不变；``angled``/``ball``/``flared`` 字重阶梯 R8 零报（见本轮测试）。

#### TK-305 风格 DNA：离散拓扑选项　〔L〕
- **进展**：`Style` 六选项均已接线；`tests/parts/test_style_gate.py`（各选项 lint + identity 七 preset 抽检 + 非拓扑 / 双层 ``a``/``g`` 的 ``check_masters``）；`agent-recipes` Style 表。
- **本轮**：``g_form=double`` 经 ``normalize_master_outline`` + 轻量轮廓合并，在 ``code_clear`` 字重阶梯 ``check_masters`` 四母版全绿；``a_form=double`` 单外轮廓 + 双孔无布尔并集，stem 70–180 六母版全绿；``test_style_option_identity_spot_check_on_preset`` / ``test_styled_voice_identity_core_charset_on_preset``（七 preset × 各 Style 选项与组合，``abcdeoHOA!&#$%`` 等 identity 零 error）；默认 Style 哈希不变。
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
- **进展（部分）**：`parts/serifs.py` + `Style.serif`；cap ``H``/``I``/``L``/``E`` 内嵌 slab；`examples/slab_serif/`；`slab_serif()` 满足 L3 最近邻距离（``test_slab_serif_meets_l3_voice_distance``）；全 ``supported`` lint 零 error；多字形字重阶梯 ``check_masters``。
- **本轮（部分）**：``bracketed_serif()`` preset；``test_bracketed_serif_lint_clean_on_full_supported`` + ``n`` 四母版 ``check_masters``；cap ``H`` 仅 ``slab`` 内嵌（``bracketed`` 仍走锚点布尔）。
- **本轮（部分）**：``examples/slab_serif`` 产出 ``proof.png`` / ``proof_brief.png`` + ``tests/examples/test_slab_serif.py`` 构建烟测。
- **本轮（部分）**：修正 ``_bracket_serif`` 脚/顶垂直向；扩展 ``l``/``f``/``t``/``j``/``k`` 与 ``bracketed`` 下 ``b``/``d``/``p``/``q`` 脚锚点；``test_bracketed_serif_meets_l3_voice_distance``。
- **本轮（部分）**：大写 slab 内嵌或禁用错误锚点（``G``/``Q`` 与 ``C`` 同，无 H 宽假 stem 布尔）；碗形 ``B``/``D``/``P``/``R`` 为左 stem 脚底；``j``/``t`` slab 不走脚锚点（避免钩形段数漂移）。
- **本轮（部分）**：``test_slab_serif_masters_on_vf_stable_charset`` 覆盖全 ``supported`` 四档母版。
- **本轮（部分）**：``t`` slab 在 hook 母版 stem 脚底内嵌单轮廓衬线（``_r_outline`` 固定段数）。
- **本轮（部分）**：``c``/``C``/``G`` 开口竖切顶/底（``+x``）内嵌 slab；``G`` 顶托架与 ``C`` 底托架段数固定。
- **本轮（部分）**：``j`` 复用 hook ``_r_outline`` 脚底；``Q`` 尾端内嵌 slab。
- **本轮（部分）**：``tests/golden/outline_hashes.json`` 锁定 ``slab_serif`` 全 98 字；``examples/slab_serif`` 三档 sentence gate + proof 烟测通过。
- **本轮（部分）**：``examples/slab_serif/build_vf.py`` 四档 ``wght`` VF（与稳定字符集同 stem 阶梯）+ ``proof_vf.png``；``test_slab_serif_build_vf_script``；VF 与 ``build_family`` 共用 ``_voice``（``f`` arm 0.75）。
- **本轮（部分）**：大写 stem 锚点按字形跨度（``dual``/``left``/``none``）与 ``M``/``N``/``T``/``U`` 真实 stem 位；``bracketed`` 对角大写禁用假 stem 布尔；``f``/``t``/``j`` 与 ``b``/``d``/``p``/``q`` 钩脚/碗 stem 脚避免 VF 段数漂移；``test_bracketed_serif_masters_on_vf_stable_charset`` 全 ``supported`` 四档母版。
- **本轮（部分）**：``U``/``G``/``Q`` 等 ``bracketed`` 与 ``slab`` 共用内嵌顶/脚几何以过 ``deep_check_masters``；碗形 ``b``/``d``/``p``/``q`` 内嵌脚路径保持 G1≤slab 水平；``examples/bracketed_serif`` 三档 + ``build_vf.py`` + 烟测。
- **本轮（部分）**：``agent-recipes`` 补衬线 ``build_family`` / ``build_vf`` 人审 PNG 命令。
- **本轮（部分）**：``slab_serif`` / ``bracketed_serif`` 纳入 TK-207 字重阶梯 ``R8_counter_min`` 回归；衬线脚/对角在阶梯 stem 带加宽反挤压；``test_serif_voice_trial_snapshots`` 断言 ``weight_ladder_r8_failures==0``；``outline_hashes.json`` 更新受影响字形。
- **本轮（部分）**：``examples/human_review_bundle.py`` 生成本地校样 + ``REVIEW_CHECKLIST.md``（不写 ``approvals``）；``test_human_review_bundle`` 烟测（``--only serif`` / ``italic``）；``agent-recipes`` / ``approvals/README`` 对齐 gate 文件名。
- **本轮（部分）**：``bracketed_stem_foot_dims`` 粗 stem 缩尺 + 降部 ``p``/``q`` 脚帽；``examples/bracketed_serif`` Bold 碗形 ``b``/``d``/``p``/``q`` R3 清零；golden ``p``/``q`` 更新。
- **本轮（部分）**：``approvals/serif-*-voice.json``、``italic-vf-construct.json`` 占位（``approved: false``）；``test_repo_pending_human_review_templates``。
- **本轮（部分）**：``test_human_review_bundle_serif_only`` 烟测（含 VF proof、bracketed 阶梯、checklist gate 名）。
- **本轮（部分）**：``test_human_review_bundle_italic_only`` 断言 checklist 含 ``italic-vf-construct``。
- **本轮（部分）**：``serif-*-voice`` 占位 ``notes`` 列出 bundle 内 ``proof``/``proof_vf``/阶梯 PNG；``test_gates`` 固化路径提示。
- **本轮（部分）**：``human_review_bundle`` checklist 补斜体 ``write_approval`` 示例；``test_evidence`` 路径存在性回归。
- **本轮（部分）**：``test_bracketed_bowl_glyphs_inline_foot_extends_left_of_plain_stem`` 固化 ``b``/``d``/``p``/``q`` 内嵌脚衬线外伸。
- **本轮（部分）**：``inline_stem_foot_serif_path`` / ``inline_hook_cap_serif_path`` 外角 cubic 托架圆角（``f``/``t``/``j`` 顶脚 + 碗形脚底）；``test_bracketed_inline_bowl_foot_uses_cubic_bracket_corner``；golden ``b``/``d``/``f``/``j``/``p``/``q``/``t``。
- **本轮（部分）**：大写 ``V`` 内嵌脚底托架圆角（``_v_cap_bracketed_outline``，``slab`` 仍折线）；``test_bracketed_cap_v_*``；golden ``V``。
- **本轮（部分）**：大写 ``W``/``X`` 内嵌脚底/顶脚托架圆角（``_append_baseline_foot_pad`` / ``_append_upward_cap_foot_pad``）；``test_bracketed_cap_w_and_x_*``；golden ``W``/``X``。
- **本轮（部分）**：大写 ``A`` 双竖脚内嵌托架圆角（``_write_a_cap_bracketed_outer`` / ``_finish_baseline_foot_pad``）；``test_bracketed_cap_a_*``；golden ``A``。
- **本轮（部分）**：大写 ``Y`` ``bracketed`` 内嵌脚/臂顶托架圆角（``_y_cap_bracketed_outline``）；修正 ``_y_cap_foot_dims`` 的 ``y_side`` 索引（``slab``/``bracketed`` 脚厚）；``test_bracketed_cap_y_*``；golden ``Y``（``slab`` + ``bracketed``）。
- **本轮（部分）**：大写 ``Z``/``K`` ``bracketed`` 内嵌托架圆角（``_z_cap_bracketed_outline`` / ``_k_cap_bracketed_outline``）；``K`` 中重 stem 略加宽过 R8；``test_bracketed_cap_z_and_k_*``；golden ``Z``/``K``。
- **本轮（部分）**：``test_bracketed_hook_letters_cap_serif_adds_cubic_fillet`` / ``test_bracketed_ftj_masters_interpolate_on_weight_ladder`` 固化钩形 ``f``/``t``/``j`` 顶脚托架与 VF 段数。
- **本轮（部分）**：控制字形 ``H`` ``bracketed`` 内嵌双 stem 托架圆角（``_write_h_bracketed_outer``，不再走锚点布尔）；``test_bracketed_cap_h_*``；golden ``H``。
- **本轮（部分）**：大写 ``I``/``L`` ``bracketed`` 内嵌单 stem 托架圆角（``_write_i_bracketed_outer`` / ``_write_l_bracketed_outer``）；``test_bracketed_cap_i_and_l_*``；golden ``I``/``L``。
- **本轮（部分）**：大写 ``E``/``F``/``T`` ``bracketed`` 内嵌托架圆角（``_write_e_bracketed_outer`` 等）；``test_bracketed_cap_e_f_t_*``；golden ``E``/``F``/``T``。
- **本轮（部分）**：大写 ``M`` ``bracketed`` 四脚内嵌托架圆角（``_write_m_bracketed_outer``）；轻 stem 略加宽过 R8；``test_bracketed_cap_m_*``；golden ``M``。
- **本轮（部分）**：大写 ``N`` ``bracketed`` 四脚内嵌托架圆角（``_write_n_bracketed_outer``）；重 stem 加宽与 ``M`` 同系；``test_bracketed_cap_n_*``；golden ``N``（``bracketed_serif``）。
- **本轮（部分）**：碗形大写 ``D``/``P``/``R``/``B`` ``bracketed`` 左 stem 脚底 cubic 托架（``_bowl_cap_bracketed_*``）；``test_bracketed_bowl_caps_dprb_*``；golden ``D``/``P``/``R``/``B``；``tk502`` ``brief-2-bracketed`` ``voice_distance``。
- **本轮（部分）**：大写 ``U`` ``bracketed`` 双 stem 顶脚 cubic 托架（``_write_u_bracketed_outer``，闭合不重复左顶衬线以免 R3）；``test_bracketed_cap_u_*``；golden ``U``。
- **本轮（部分）**：大写 ``G``/``Q`` ``bracketed`` 开口顶/尾脚 cubic 托架（``_opening_top_bracketed_move`` / ``_finish_foot_pad_below``）；``test_bracketed_cap_gq_*``；golden ``G``/``Q``。
- **本轮（部分）**：``c_from_o`` ``bracketed`` 上下开口 cubic 托架（``_opening_bottom_bracketed_detour``，托架辅助迁入 ``control.py``）；``test_bracketed_c_*``；golden ``c``/``C``/``()``/``?``；``tk502`` ``brief-2-bracketed`` ``voice_distance``。
- **本轮（部分）**：大写 ``J`` ``slab``/``bracketed`` 右 stem 顶脚内嵌（同 ``U`` 右半）；``test_bracketed_cap_j_*``；golden ``J``（``slab`` + ``bracketed``）。
- **本轮（部分）**：小写 ``e`` ``bracketed`` 下开口 cubic 托架（``e_from_o`` + ``_opening_bottom_bracketed_detour``）；``test_bracketed_e_*``；golden ``e``。
- **本轮（部分）**：小写 ``s``/大写 ``S`` ``bracketed`` 上下开口 cubic 托架（``s_from_o``）；``test_bracketed_s_*``；golden ``s``/``S``。
- **本轮（部分）**：小写 ``e`` ``slab`` 下开口内嵌（``e_from_o`` + ``_opening_bottom_slab_detour``）；``test_slab_e_opening_changes_outline``；golden ``slab_serif`` ``e``。
- **本轮（部分）**：小写 ``s``/大写 ``S`` ``slab`` 上下开口内嵌（``s_from_o``）；``test_slab_s_*``；golden ``slab_serif`` ``s``/``S``。
- **本轮（部分）**：``test_opening_glyph_masters_interpolate_on_weight_ladder`` 锁定 ``slab``/``bracketed`` 开口族 ``cCeEsSGQ()?`` VF 段数。
- **本轮（部分）**：``test_bracketed_cap_inline_masters_interpolate_on_weight_ladder`` 锁定内嵌托架大写（除 ``O``）四档 VF 段数；小写 ``i``/``l`` 与 cap ``I`` 同配方内嵌托架。
- **本轮（部分）**：``n``/``h`` ``bracketed`` 左 stem 脚底内嵌（``_n_bracketed_left_foot_detour`` + stem 底圆角）；``u`` 仍右脚锚点；``test_bracketed_n_*`` / ``test_bracketed_nh_masters_*``；golden ``n``/``h``（``bracketed_serif``）。
- **本轮（部分）**：``n``/``h`` ``slab`` 左 stem 脚底内嵌（``_n_slab_left_foot_detour``，脚底矩形 + stem 底圆角）；``test_slab_n_left_stem_foot_is_inlined`` / ``test_slab_nh_masters_*``；golden ``n``/``h``（``slab_serif``）。
- **本轮（部分）**：``m`` 左 stem 脚底内嵌（``inline_stem_foot_serif_path``，保留 ``stem_L_t``）；``test_slab_m_masters_*`` / ``test_bracketed_m_masters_*``；golden ``m``。
- **本轮（部分）**：``r`` 左 stem 脚底内嵌（同 ``m`` 左 shelf 配方）；``test_slab_r_masters_*`` / ``test_bracketed_r_masters_*``；golden ``r``。
- **本轮（部分）**：``u`` 右脚内嵌（镜像 ``n`` 左 shelf 脚 + ``inline_right_foot``）；``_n_begin_left_stem`` 统一左 stem 起步；``test_slab_u_masters_*`` / ``test_bracketed_u_masters_*``；golden ``u``。
- **本轮（部分）**：``n``/``h`` 右 stem 脚底内嵌（``inline_stem_foot_serif_path_right`` + ``inline_right_foot`` 省略 ``stem_R_b``）；``bracketed`` ``u`` 随 ``n`` 右脚几何更新；golden ``n``/``h``（``slab`` + ``bracketed``）、``u``（``bracketed_serif``）。
- **本轮（部分）**：``m`` 中/右 stem 脚底内嵌（``s1.r0`` shelf + ``s2.r1`` 右 shelf）；省略 ``stem_M_b``/``stem_R_b``；golden ``m``（``slab`` + ``bracketed``）。
- **本轮（部分）**：``u`` 去掉碗侧误挂的 ``stem_L_b``（``left_foot=False``）；``test_serif_u_has_no_spurious_left_foot_anchor``；golden ``u``（``slab`` + ``bracketed``）。
- **本轮（部分）**：``h`` 升部左 stem 顶衬线内嵌（``inline_stem_cap_serif_path``，仅 ``y > x_height``；``n`` 肩口仍 ``stem_L_t`` 布尔）；``left_cap``/``u`` ``left_cap=False``；``test_serif_h_ascender_cap_inlined_skips_boolean_serif``；golden ``h``/``u``。
- **本轮（部分）**：``test_serif_n_family_inlined_feet_omit_bottom_stem_anchors`` 固化 ``n``/``m``/``r``/``u`` 脚底内嵌后无 ``stem_*_b``；``n`` 肩口顶衬线内嵌仍因 R3 未合入。
- **本轮（部分）**：``r`` ``slab`` 左肩口顶衬线内嵌（``inline_shoulder_left_cap_slab_path`` + ``inline_left_top``）；``test_slab_r_shoulder_cap_inlined_skips_left_top_anchor``；golden ``r``（``slab_serif``）。
- **本轮（部分）**：``m`` ``slab`` 左肩口顶衬线内嵌（同 ``r`` 左缘配方）；``test_slab_m_shoulder_cap_inlined_skips_left_top_anchor``；golden ``m``（``slab_serif``）。
- **待续**：人设 ``approved: true`` 签字；``primitives.serif_bracket`` 梯形/楔形实验 G1 恶化已回退 ``rounded_rect``。
- **做什么**：新增 `parts/serifs.py`，以现有 `primitives.serif_bracket`（自述为 stub）为种子；让竖笔暴露「脚/顶」附着锚点；`Style.serif ∈ {none, slab, bracketed}`，参数含长度、厚度、托架半径。
- **验收**：`slab_serif()` / `bracketed_serif()` 全 98 字 lint 零错误、四档 VF ``check_masters``、``AGENT_SENTENCE`` gate（``test_*_serif_passes_agent_sentence_gate``）与 L3 距离；人审；``examples/slab_serif`` + ``examples/bracketed_serif``。
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
- **本轮（部分）**：``geo.stroke.CubicCenterline`` / ``CubicBezier``；``flatten_cubic_centerline`` + ``expand_cubic`` + ``CenterlineExpandReport``（弦高误差预算）；``tests/geo/test_stroke_expand.py`` 合成夹具。
- **本轮（部分）**：``Stroke.beziers`` / ``from_beziers`` + ``Skeleton.from_mapping`` 的 ``beziers`` 键；``trace_letter`` 走 ``expand_cubic``。
- **本轮（部分）**：单段开放 cubic + ``butt`` cap 偏移轨 cubic 链拟合（``max_offset_fit_error`` / ``offset_fit_budget``）。
- **本轮（部分）**：闭合 cubic 中线（多段）偏移轨道拟合 → 双轮廓环（``_expand_closed_cubic_offset``）。
- **本轮（部分）**：``cubic_centerline_to_polyline``（弦高折线 → ``expand``）；多段开放 ``expand_cubic`` 与该路径等价（``test_cubic_centerline_to_polyline_*``）。
- **本轮（部分）**：多段开放 + ``butt`` 走拼接偏移轨采样 + miter + cubic 拟合（``_expand_open_multi_cubic_offset``）；``CubicBezier.line`` 端点切线修正。
- **本轮（部分）**：``_fit_offset_rail_piecewise`` 在方向折点拆分 + 共线轨退化为 ``CubicBezier.line``（L 形 ``max_offset_fit_error`` 入预算）。
- **本轮（部分）**：开放 cubic 偏移轨路径支持 ``round``/``square`` cap 与 ``round``/``bevel`` join（``_finish_open_cubic_offset_outline``）；``offset_fit_budget=0`` 仍走弦高折线。
- **本轮（部分）**：闭合环 ``_stitched_offset_rail_closed`` + segment 接头 join（``round`` join 与折线 ``expand`` bbox 回归）。
- **本轮（部分）**：``Stroke.offset_fit_budget`` 允许 ``0``（强制弦高折线路径）；``test_trace_letter_closed_cubic_ring_has_counter``。
- **本轮（部分）**：``Skeleton.from_mapping`` ``join``/``cap`` 键烟测。

### M4 真斜体

#### TK-401～404 真斜体母版　〔M〕
- **TK-401**：`italic_design(regular, ItalicStyle)`；`italic_controls` 弃用并 `DeprecationWarning`；`DesignContext.italic_slant_deg` 在 `build_all` 施加构造倾角；TK-002 xfail 已转正。
- **TK-402**：倾角作为**重画母版时的构造参数**（不是对输出做 shear）：竖笔倾角、笔画厚度补偿（倾斜后水平厚度会变）、曲线极值点重平衡。
- **本轮（部分）**：`horizontal_slant_compensation` 用于 `o` 环 `thickness_h`、`f`/`t`/`e` 横笔、`#` 横杠；竖笔倾角 ±0.5° 回归测试；``OBLIQUE_COMPAT_EXCLUDE`` 仅 ``e``（预切在 ``e_from_o`` / ``outline_e_oblique_splits``，含 bold eye 段数对齐）；``hmnru`` oblique 预切 + ``mu`` ``OBLIQUE_PRE_EXTREMA``；VF 直立 ``vf_compat_oblique_splits`` 分支拱；七内置 preset 斜体 R4 清零（见 TK-101 回归）。**人审**仍待（校样命令见 ``human_review_bundle.py``）。
- **本轮（部分）**：``examples/italic_family/build_italic_vf.py`` 产出 ``proof.png`` / ``proof_vf.png``（``AGENT_SENTENCE`` + 字重阶梯）；人审 bundle / 烟测断言。
- **TK-403**：拓扑差异：`n m h r u` 的拱从竖笔中段分出（branching）、`f` 可下伸、`a` 保持单层、宽度收窄。
- **本轮**：`n`/`h`/`r`/`u`/`m` 分支拱；单层 `a` 略收窄；斜体 `f` 下伸（inline 横笔、无 blend）；`tests/parts/test_italic_topology.py`。
- **TK-404**：`wght×ital` VF 示例改用真斜体；`check_masters` 通过。直立母版设 `vf_compat_stem_segments=True` 与分支斜体对齐段数（不影响 preset 哈希）。
- **本轮（部分）**：``vf_italic_pair`` 统一直立/斜体预切倾角；``examples/italic_family/build_italic_vf.py`` 四母版示例；``test_vf_italic_pair_check_masters_on_builtin_presets`` 七 preset 全字符 ``check_masters``。
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
- **本轮（部分）**：``agent-recipes`` 增加 TK-207 ``weight_ladder_sheet`` 人审片段（本地 ``artifacts/specimens/``）。
- **本轮（部分）**：SKILL preset 表补 ``slab_serif``/``bracketed_serif``、L3 指针与 ``examples/*_serif``；TK-306 验收行与 bracketed 对齐。
- **本轮（部分）**：``agent-recipes`` 补 ``Style`` 默认值行 + ``serif``；``AGENT_GOAL`` L3 行对齐 ``Style`` API（不再写「待 TK-305」）。
- **本轮（部分）**：``reference.md`` 补 Style DNA 表 + 斜体 / ``oblique_compat`` 指针。
- **本轮（部分）**：SKILL Step 3 补 ``Style`` 指针（与 ``agent-recipes`` / ``reference`` 对齐）。
- **本轮（部分）**：``reference.md`` M5 agent trial 工具链（``build_reference_family`` / ``design_*``）。
- **本轮（部分）**：``AGENT_TRIALS`` 终验流程 + ``human_review_bundle`` 指针（TK-502 与人审分工）。
- **本轮（部分）**：``agent-recipes`` + ``reference.md`` 补 TK-308 骨架/三次中线（非默认管线、勿当字重轴）。
- **本轮（部分）**：``test_skeleton`` 闭合 cubic stroke 烟测（``trace_letter`` → 环带实体）。
- **本轮（部分）**：``Stroke.offset_fit_budget`` 透传 ``expand_cubic``；多段开放折线化与 ``expand`` 包围盒回归。
- **本轮（部分）**：``agent-recipes`` / ``reference.md`` 补 ``cubic_centerline_to_polyline`` 与多段开放路径说明。
- **本轮（部分）**：``agent-recipes`` / ``reference`` 对齐 TK-402 斜体 ``proof.png`` / ``proof_vf.png`` 与人审 gate 名。

#### TK-502 Agent 试验协议与基线对比　〔M〕
- 见第 6 节。**这是程序级验收，不可省略。**
- **本轮**：`docs/AGENT_TRIALS.md`、`qa/trial_protocol.py`（`voice_distance`、快照 JSON）、`examples/agent_trial/snapshot_presets.py`、`artifacts/trials/` gitignore。
- **本轮（部分）**：``snapshot_serif_voices.py`` + ``AGENT_TRIALS`` brief-2/衬线基线说明；``test_serif_voice_trial_snapshots_meet_l3`` + ``test_snapshot_serif_voices_script``。
- **本轮（部分）**：三 brief 参考试作（``design_*`` + ``snapshot_design.py``，L3 + gate/R8）；``build_reference_family.py``（三 brief Regular+Bold）；``test_agent_trial_reference`` / ``test_agent_trial_build``。
- **本轮（部分）**：三 brief 参考试作指标写入 ``AGENT_TRIALS.md`` 摘要表 + ``tests/fixtures/tk502_reference_metrics.json``（``test_reference_metrics_match_committed_fixture``）。
- **本轮（部分）**：brief-2 衬线参考试作 ``design_editorial_slab.py`` / ``design_editorial_bracketed.py``（``--variant slab|bracketed``）；``snapshot_reference_trials`` 含 ``brief-2-slab`` / ``brief-2-bracketed``。
- **本轮（部分）**：``weight_ladder_r8_failures`` / ``snapshot_trial`` 在字重阶梯上保留 trial ``Controls`` 的 ``Style``、``tuned_glyph``、``with_glyph``（``controls_at_ladder_stem``）。
- **本轮（部分）**：``WEIGHT_LADDER_STEMS`` 与 TK-207 对齐（含 stem 200）；``test_weight_ladder_stems_match_tk207_regression``。
- **本轮（部分）**：``AGENT_TRIALS.md`` §终验流程（程序侧步骤、作废条件）；``tk502_reference_metrics`` 含 ``brief-2-slab``；SKILL/reference 同步。
- **本轮（部分）**：``tests/docs/test_agent_trials_doc.py`` 固化 ``AGENT_TRIALS`` 终验与人审指针。
- **待续**：**终验**（独立 agent 试验 + 人评 1–5）；参考试作 ≠ 终验。
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
| 骨架/笔（折线 + TK-308 cubic spike） | `parts/skeleton.py`、`parts/pen.py`、`geo/stroke.py` |
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
