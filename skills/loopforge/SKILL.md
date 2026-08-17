---
name: loopforge
description: 从模糊需求到交付闭环 —— Goal 门驱动 + 严格职责隔离（写代码/跑测试/审计三者永不同体）。Stage 0 定门 → 拷问 → SRS → 设计 → Loop → 双轮审计，任意门不过自动回退，全绿才交付。触发词：模糊需求/需求拷问/从想法到交付/goal 闭环/通用 Loop
user-invocable: true
---

# loopforge：Goal 门驱动 + 职责隔离的交付闭环

> 通用版（fork 自 KH OFDR `verification-loop-guide.md`，剥除领域特化）
> 权限契约：`<SKILL_DOCS>/role-permission-matrix.md` ← **先读这个**

## 🔴 路径解析规则（读任何文档前先看这条）

本 skill 引用两类文档，**存放位置不同，不要混**：

| 类别 | 位置 | 含哪些 | 谁写 |
|:--|:--|:--|:--|
| **套件文档**（只读模板/规范） | `<SKILL_DOCS>` = 本 SKILL.md 同级的 `docs/` | goal-template · goal-doc-template · role-permission-matrix · commands-spec · loop-status-spec · large-project-guide | 套件自带，永不修改 |
| **项目文档**（本项目的状态/产物） | `<项目根>/docs/loopforge/` | goal.md · goal-doc.md · loop-status.md · srs/ · design/ · audit/ · srs-raw/ · verification/ · change-log.md | Loop 运行时生成，不污染用户项目根 `docs/` |

`<SKILL_DOCS>` 的解析顺序：

```
1. $HOME/.claude/skills/loopforge/docs/     ← 全局安装（install.sh 装的）
2. <项目>/.claude/skills/loopforge/docs/    ← 项目级安装（loopforge-init.sh --local）
两处都没有 → 报错，指引跑 install.sh，不要凭记忆编模板内容
```

> **Windows**：`$HOME` 在 Git Bash 下正常展开；PowerShell/cmd 环境对应
> `%USERPROFILE%\.claude\skills\loopforge\docs\`。两者指向同一目录，
> 用哪种写法取决于你当前的 shell。**不要用 `~`** —— 部分调用方不展开它。

> **为什么要写死这条**：全局模式下 skill 在 `~/.claude/`，而项目产出文档在 `<项目>/docs/loopforge/`。
> 只写"读 `goal-template.md`"会去项目目录找模板 —— 找不到，agent 就自己编一份，
> 门判据全走样且没人发现。

## 部署模式

两种装法，编排逻辑完全相同，区别只在文件放哪：

| 模式 | 装法 | skill+agents+套件文档 在哪 | 适合 |
|:--|:--|:--|:--|
| **全局**（推荐） | `install.sh` → 每项目 `loopforge-init.sh` | `~/.claude/` | 多项目共用一份，装一次 |
| **本地** | 每项目 `loopforge-init.sh --local` | `<项目>/.claude/` | 不想动 `~/.claude`、各项目要用不同版本、要把套件随项目一起提交 |

两种模式下 `/loopforge` 命令都装在 `<项目>/.claude/commands/`（不放全局，避免覆盖 Claude Code 原生命令）。

`/loopforge` 首跑时若 `<项目>/docs/loopforge/goal.md` 不存在，从 `<SKILL_DOCS>/goal-template.md` 复制初始化（详见 `commands/loopforge.md`）。所有 loopforge 产出文档统一落在 `<项目>/docs/loopforge/`，不污染用户项目根 `docs/`。

## 四条铁律

1. **失败可见**：功能没实现就让它 FAIL，不 skip
2. **职责隔离**：**写代码 / 跑测试 / 审计 三者永不同体**（新增，v2.1 核心）
3. **作者不审自己**：审计用 fresh agent，Round 2 禁读 Round 1
4. **门可判定**：完成 = 可机器检查，不凭感觉

---

## 一、角色分工（先看这张表）

| 角色 | Agent | 工具白名单 | 能写 | 能跑 |
|:--|:--|:--|:--|:--|
| 编排者 | **主 Claude** | Agent, Skill, Read, Write, Bash | 仅 `docs/loopforge/loop-status.md` `docs/loopforge/goal.md` `docs/loopforge/goal-doc.md` `docs/loopforge/audit/**` | 仅 git 基线命令 |
| **目标架构** | `goal-architect` | Read Write Grep Glob | **`docs/loopforge/goal-doc*.md` only** | ❌ |
| 拷问 | `req-interrogator` | Read Write Grep Glob | `docs/loopforge/srs-raw/` | ❌ |
| SRS | `srs-drafter` | Read Write Grep Glob | `docs/loopforge/srs/` | ❌ |
| 设计 | `design-author` | Read Write Grep Glob | `docs/loopforge/design/` | ❌ |
| **实现** | `impl-coder` | Read Edit Write Grep Glob | **`$IMPL_ROOT` only** | **❌ 无 Bash** |
| **测试开发** | `test-author` | Read Edit Write Grep Glob | **`$TEST_ROOT` only** | **❌ 无 Bash** |
| **测试执行** | `test-runner` | Read **Bash** Grep Glob | ❌ 报告走返回值 | ✅ |
| 门判定 | `gate-checker` | Read Bash Grep Glob | ❌ 报告走返回值 | ✅ 只跑判定命令 |
| **审计** | `goal-auditor` | Read Grep Glob | ❌ 报告走返回值 | **❌ 无 Bash** |

**三处关键"做不到"**：
- `impl-coder` 无 Bash → 看不到测试红绿 → 没有改断言凑绿的动机
- `test-author` 无 Bash → 同上 → 断言强度只由 SRS 决定
- `goal-auditor` 无 Bash 无 Edit → 只能看 → 不可能"顺手修一下"再说没问题

**主 Claude 的边界**：它编排、路由、维护状态表、打 git 基线，但**不改 `$IMPL_ROOT`/`$TEST_ROOT`、不跑测试**。它的上下文塞满了历史，最容易产生"我知道这里没问题"的偏差。

> ⚠️ **两条必须说清的限制**（对外别说过头）：
> 1. **Bash ⊇ Write**。`test-runner`/`gate-checker` 有 Bash，能用 `>` 重定向写任意文件。它们的隔离**不靠 `tools:`，只靠 G5.x 事后检测**。准确表述是"改了会被抓到并作废"，不是"改不了"。
> 2. **主 Claude 的收权是纪律级不是强制级**。没有机制能持久限制主线程工具（Skill 的 `disallowed-tools` 是回合级，`settings.json` 是会话全局会连累 subagent）。真防线是 G5.6 事后比对派工记录。
>
> 详见 `<SKILL_DOCS>/role-permission-matrix.md` §3、§7。

---

## 二、流程总览（6 阶段 + 回退环）

```
Stage 0    定 Goal 门         主 Claude + 用户 → docs/loopforge/goal.md
   ↓
Stage 0.5  项目目标书          goal-architect ↔ 用户（多轮 Q&A） → docs/loopforge/goal-doc.md
   ↓ gate-checker 判 G0.5 ──不过──> 回 Stage 0.5
Stage 1    拷问               req-interrogator
   ↓ gate-checker 判 G0.x ──不过──> 回 Stage 1
Stage 2    起草 SRS           srs-drafter
   ↓ gate-checker 判 G1.x ──不过──> 回 Stage 2 / 1
Stage 3    设计文档           design-author
   ↓ gate-checker 判 G2.x ──不过──> 回 Stage 3 / 2
Stage 4    Loop（三角色交替）  test-author ↔ test-runner ↔ impl-coder
   ↓ gate-checker 判 G3.x ──不过──> 回 Stage 4 / 3
Stage 5    双轮独立审计       goal-auditor ×2（Round 2 禁读 Round 1）
   ↓ gate-checker 判 G4.x ──不过──> 回 Stage 4
✅ 交付
```

每个 `↓` 都**必须**调 `gate-checker`。不许"看着差不多"就进下一阶段。

---

## 三、Stage 0：定 Goal 门

**为什么先做**：门是 Loop 的唯一驱动器。门没定义，后面每步的"算不算完成"都是拍脑袋。

### 3.0 项目初始化（幂等，已初始化则跳过）

> 走 `/loopforge` 命令进来的，这步命令文件已做过；**直接调本 skill 进来的必须自己做**，
> 否则后面所有阶段都在没有门定义的情况下空转。

```bash
mkdir -p docs/loopforge
test -f docs/loopforge/goal.md     || cp <SKILL_DOCS>/goal-template.md docs/loopforge/goal.md
test -f docs/loopforge/goal-doc.md || echo "(待 goal-architect 填)" > docs/loopforge/goal-doc.md
git rev-parse --git-dir >/dev/null 2>&1 || echo "⚠️ 非 git 仓库 → G5.x 越权检测全族失效"
test -f .gitignore || printf '__pycache__/\n*.pyc\ntarget/\nnode_modules/\n.pytest_cache/\n' > .gitignore
```

`<SKILL_DOCS>` 见开头的「路径解析规则」——**不是**项目里的 `docs/`。

### 3.1 裁剪门清单

1. 主 Claude 与用户逐条裁剪 `docs/loopforge/goal.md`：
   - 删不适用的门（非物理项目删物理可信度门）
   - 判定命令改成本项目真实路径（`IMPL_ROOT` / `TEST_ROOT` / `TEST_CMD` / `RUNNER` / `TYPE_CMD`）
   - 加项目专属门（Web：API 契约/SLA 压测；数据：血缘/幂等；嵌入式：ROM/RAM）
2. 确认回退映射表 + **G5.x 角色越权检测门必须保留**

**退出**：`docs/loopforge/goal.md` 存在 + 每条门四字段齐 + 用户确认"这就是完成的定义"。

---

## 三之一、Stage 0.5：项目目标书（goal-doc 协作）

**为什么在 Stage 0 和 Stage 1 之间插入这一步**：Stage 0 解决了"完成的判据"，
但**项目本身的分解**（子系统、批次、技术栈、不变约束、范围外）必须先和用户对齐。
否则 Stage 1 拷问官会对着"做一个微信"这种模糊目标拷问出一堆不一致的拷问清单。

**产物**：`docs/loopforge/goal-doc.md`（用 `<SKILL_DOCS>/goal-doc-template.md` 填）

**关键纪律**：
- 这是 Loop 中**唯一**直接面对用户的阶段 —— `goal-architect` 的问题就是用户审的入口
- 多轮迭代：提问 → 写 → 用户审 → 再问 → 改 → 直到用户说"确认，下一阶段"
- **绝不允许跳过用户审查**进入 Stage 1 —— 那等于把所有项目级假设压在 agent 的猜测上

### 调用模板

```
# 初版
Agent(
    description="起项目目标书",
    prompt="读 <SKILL_DOCS>/goal-doc-template.md。用户输入：<原始想法 + 背景>。按模板写 docs/loopforge/goal-doc.md 初版（允许 [待确认] 标记）。返回 [WAITING FOR USER] 段含必答清单。",
    subagent_type="goal-architect"
)
# → 主 Claude 收到 [WAITING FOR USER] 后**直接呈现给用户**，让用户回答

# 修订轮
Agent(
    description="改项目目标书",
    prompt="读 docs/loopforge/goal-doc.md + 用户最新回答。仅修改与回答相关的章节，重新计算 [待确认] 标记数，返回新的 [WAITING FOR USER]。",
    subagent_type="goal-architect"
)
```

**退出条件**（主 Claude 自查）：
- 用户在对话里说过"确认，下一阶段"或等价表述
- goal-doc 七大章节齐
- `[待确认]` 标记数 ≤ 3
- gate-checker 跑 G0.5 全绿

详见 `<SKILL_DOCS>/goal-doc-template.md` 附录 C。

---

## 四、Stage 1：拷问

### 4.1 拷问环（草稿 → 问用户 → 回填 → 判门）

🔴 **这是 Loop 中唯二直接面对用户的阶段**（另一个是 Stage 0.5）。拷问草稿产出后**必须**问用户答卷，不许跳过——跳过等于把所有需求假设压在 agent 的推荐默认值上，G0.4 门会拦。

```
# [1] 草稿轮：req-interrogator 产出含推荐默认值的待答问卷
Agent(
    description="拷问模糊需求（草稿）",
    prompt="读 docs/loopforge/goal.md 的 G0.x 门 + docs/loopforge/goal-doc.md 判项目类型。对以下模糊需求做 6 维度拷问，每维度加 [推荐默认值] 行，产出 docs/loopforge/srs-raw/<需求名>-interrogation.md。回填状态=待用户答卷。返回 [WAITING FOR USER] 段含：（a）全面拷问（逐 Q 答）vs 接受推荐默认值的选择；（b）各维度推荐默认值摘要。原始需求：<...>",
    subagent_type="req-interrogator"
)
# → 主 Claude 收到 [WAITING FOR USER] 后直接呈现给用户：
#   "Stage 1 拷问：全面拷问（逐 Q 答）还是接受推荐默认值？"
#   - 用户选"接受推荐默认值" → 所有非冲突 Q 标"接受推荐默认值"
#   - 用户选"全面拷问"     → 逐 Q 问用户，收答案
#   - 冲突点无论选哪个都需用户裁决（按 NEWBIE-GUIDE §2 的"答具体选项"方式）

# [2] 修订轮：req-interrogator 回填用户答卷
Agent(
    description="回填拷问答卷",
    prompt="读 docs/loopforge/srs-raw/<需求名>-interrogation.md + 用户最新答卷。按答案回填每个 Q 的'用户的回答'列，接受默认值的填'接受推荐默认值'。冲突表裁决列填用户裁决。回填状态=全部回填。返回更新后的路径。",
    subagent_type="req-interrogator"
)
```

**用户选项路由**（主 Claude 在 [1] 与 [2] 之间执行）：

| 用户选择 | 主 Claude 行动 | Q 答卷列填什么 |
|:--|:--|:--|
| 接受推荐默认值 | 直接进 [2]，不逐 Q 问 | "接受推荐默认值" |
| 全面拷问 | 逐 Q 问用户，收齐答案后进 [2] | 用户的具体回答 |
| "按你的猜测走" | 同"接受推荐默认值" | "接受推荐默认值" |
| 含糊（"差不多都行"） | 按拷问原则 5 追问具体值，不替用户猜 | — |

### 4.2 退出自检

```
Agent(
    description="Stage 1 门判定",
    prompt="gate-checker：读 docs/loopforge/goal.md，跑 stage=1 的全部门（G0.1~G0.4）+ 角色越权检测。输出 PASS/FAIL + 回退建议。",
    subagent_type="gate-checker"
)
```

> **G0.4 答卷门**（v2.4 新增）：查拷问清单的"回填状态"是否为"全部回填"且无"（待填）"残留。原 G0.1~G0.3 只查问卷结构（6 维度齐/无未决词/冲突裁决），**不查答卷列填没填**——草稿产出后主 Claude 跳过用户答卷也能过三门冲进 Stage 2，把需求假设全压在 agent 猜测上。G0.4 堵这条。

---

## 五、Stage 2：起草 SRS

```
Agent(
    description="起草 SRS",
    prompt="读 docs/loopforge/goal.md 的 G1.x 门 + docs/loopforge/srs-raw/<需求名>-interrogation.md（含答卷），产出 docs/loopforge/srs/<需求名>.md。你只能写 docs/loopforge/srs/。",
    subagent_type="srs-drafter"
)
```

**退出自检**：`gate-checker` stage=2 → G1.1~G1.5。

---

## 六、Stage 3：设计文档

```
Agent(
    description="写设计文档",
    prompt="读 docs/loopforge/srs/<需求名>.md，产出 docs/loopforge/design/<需求名>.md。你只能写 docs/loopforge/design/。SRS 未定义的点不要自己发明，返回 [需求缺口]。",
    subagent_type="design-author"
)
```

> v2.1 改动：设计不再由主 Claude 直接写——主 Claude 手上有全部上下文，写出来的设计会隐含"我知道后面怎么实现"的假设，反而漏掉显式定义。交给上下文干净的 `design-author`。

**退出自检**：`gate-checker` stage=3 → G2.1~G2.5。

---

## 七、Stage 4：Loop（职责隔离的核心）

**主 Claude 编排三个 agent 交替，自己不写不跑**：

```
  [1] test-author   写测试 → loopforge-tests/test_R*.py + run_<组>.py + testplan
       ↓ （无 Bash，交不出运行结果）
  [2] test-runner   跑测试 → 事实报告（PASS/FAIL/GAP/skip/弱断言）
       ↓ （无 Edit/Write，改不了任何东西）
  [3] 主 Claude 读事实报告 → 只做路由判断
       ├── [GAP]/[FAIL] 缺实现  → [4] impl-coder 改 src/ → 回 [2]
       ├── 弱断言/可疑 skip     → 回 [1] test-author 改 loopforge-tests/ → 回 [2]
       └── 全绿                 → [5]
  [5] gate-checker  跑 G3.x + 越权检测
       ↓ 不过 → 回 [3] ；全过 → 出 Stage 4
```

### 调用模板

> 🔴 **每次派工前必走基线协议**，否则 G5.x 全族失效（新建文件看不见、状态表改动算到 agent 头上）。顺序不可颠倒。

```bash
# ── 派工前（主 Claude 做）──
# 1. 先写 docs/loopforge/loop-status.md 的机读派工块：
#    <!-- DISPATCH -->
#    round: 4-3
#    agent: impl-coder
#    allowed: $IMPL_ROOT
#    <!-- /DISPATCH -->
# 2. 打基线（把编排自身的改动并入，不算到 agent 头上）
git add -A && git commit -q -m "pre-dispatch: impl-coder round 4-3"
# 3. 再派 agent
```

```
# [1] 测试开发
Agent(
    description="生成测试",
    prompt="读 docs/loopforge/srs/<需求名>.md + docs/loopforge/design/<需求名>.md，为验证组 <组> 生成 testplan + 测试代码 + runner。你只能写 $TEST_ROOT 和 docs/loopforge/verification/。功能未实现 → 写会 FAIL 的断言，不许 skip，不许登记进 KNOWN_FAILURES。",
    subagent_type="test-author"
)

# [2] 测试执行
Agent(
    description="跑验收",
    prompt="跑 $TEST_CMD 全量 + 回归 + skip 审计 + 断言强度审计。只报事实，不做归因，不改任何文件（含不用 Bash 重定向写文件）。",
    subagent_type="test-runner"
)

# [4] 实现修复（仅当 [3] 判定为缺实现）
Agent(
    description="补实现",
    prompt="读 docs/loopforge/design/<需求名>.md。按以下缺口清单补实现，只能写 $IMPL_ROOT：\n<test-runner 报告的 [GAP]/[FAIL] 原文摘录>\n设计文档没定义的行为不要自己发明，返回 [设计缺口]。",
    subagent_type="impl-coder"
)

# [5] 门判定
Agent(
    description="Stage 4 门判定",
    prompt="gate-checker：读 docs/loopforge/goal.md，跑 stage=4 的全部门（G3.x）+ G5.x 越权检测。越权判定读 docs/loopforge/loop-status.md 的 DISPATCH 块取 allowed 字段。判定命令一律走 bash -c。",
    subagent_type="gate-checker"
)
```

### 主 Claude 在 [3] 的路由规则

| test-runner 报告 | 根因 | 派给 |
|:--|:--|:--|
| `[GAP]` 功能缺口 | 实现没写 | `impl-coder` |
| `[FAIL]` 新 Bug | 实现有错 | `impl-coder` |
| `⚠️ 弱断言` | 测试断言不足 | `test-author` |
| `⚠️ 可疑 skip` | 测试用 skip 掩盖 | `test-author` |
| `[设计缺口]`（agent 回报） | 设计没定义 | 回退 Stage 3 |
| `[需求缺口]`（agent 回报） | SRS 没定义 | 回退 Stage 2 |
| `[越界请求]`（agent 回报） | 该 agent 想跨界 | 主 Claude 改派对应角色 |
| `[无法判定]`/`[门定义错误]`（gate-checker 回报） | **判定命令本身有问题** | **回退 Stage 0 修 goal.md** |
| `[需人工]`（gate-checker 回报） | 判据是价值判断 | 主 Claude 裁决并记 loop-status |

> **最后两行是补的**：`gate-checker` 遇到跑不动的命令会报 `[无法判定]`，按其规则视同 FAIL。原路由表没有这两行，Loop 会卡死在该阶段反复重跑 agent——而问题根本不在 agent 身上，重跑一万次也改变不了命令跑不动。

**主 Claude 禁止**：自己 Edit `$IMPL_ROOT`/`$TEST_ROOT`、自己跑测试、自己下"这次应该能过"的判断。

---

## 八、Stage 5：双轮独立审计

```
# Round 1
Agent(
    description="Round 1 独立审计",
    prompt="你是交付审计员，Round 1。独立审计 A~E 维度（功能完整性/测试方案/测试真绿性/覆盖矩阵/红线合规）。输入：docs/loopforge/srs/ docs/loopforge/design/ src/ loopforge-tests/ + test-runner 最新报告 + gate-checker 门报告。你没有 Bash——不要跑测试，读产物判断。必须做≥3 处断言溯源抽查。产出 P0/P1/P2 清单。",
    subagent_type="goal-auditor"
)
# → 主 Claude 派 impl-coder / test-author 修全部 P0/P1 → 落 docs/loopforge/audit/round1-fixes.md

# Round 2（全新实例）
Agent(
    description="Round 2 独立审计",
    prompt="你是交付审计员，Round 2。🔴 禁止读取 docs/loopforge/audit/goal-audit-round1-*.md 与 docs/loopforge/audit/round1-fixes.md——当作这个项目从没被审过，独立重审。同 A~E 维度。",
    subagent_type="goal-auditor"
)
```

**出口**：Round 2 无 P0/P1 → ✅ 交付。仍有 → 修 → Round 3（上限 3）→ 仍有 → 升级给人。

---

## 九、Goal 门回退映射

| 门 | 不过 → 回 | 派谁修 |
|:--|:--|:--|
| G0.1~G0.4 | Stage 1 | `req-interrogator` 补拷问（G0.4 不过=回填用户答卷） |
| G1.1~G1.5 | Stage 2（根因在答卷→1） | `srs-drafter` |
| G2.1~G2.5 | Stage 3（根因在 SRS→2） | `design-author` |
| G3.1~G3.5 | Stage 4（根因在设计→3） | `impl-coder` 或 `test-author` |
| **G5.x 越权** | 当前 Stage | **回滚该 agent 改动 + 重派正确角色** |
| G4.1~G4.3 | Stage 4 | `impl-coder` / `test-author` |

**根因判定**（回退前先问）：

| 现象 | 表层回退 | 根因回退 |
|:--|:--|:--|
| SRS 缺验收口径 | Stage 2 补写 | 答卷里就没问性能指标 → Stage 1 |
| 设计缺接口定义 | Stage 3 补写 | SRS 没这条需求 → Stage 2 |
| 测试写不出断言 | Stage 4 补断言 | 设计没定行为边界 → Stage 3 |

---

## 十、防死循环 + 越权处置

| 情况 | 检测方式 | 处理 |
|:--|:--|:--|
| 同一门连续 3 轮不过 | 读状态表 `连续不过` 列 | 停自动回退，升级给人（门定义有问题 or 需求不可实现） |
| **两门交替失败**（A 过 B 挂 → B 过 A 挂，各自都没连续 3 次） | 读 `震荡对` 表，同一对门交替 ≥3 次 | 标门冲突，回 Stage 0 裁决优先级 |
| 累计回退 > 10 次 | 读状态表 `累计回退` 计数 | 回 Stage 0 复审门是否过严/自相矛盾 |
| **G5.x 检出越权** | gate-checker 报告 | **本轮结果作废** → 回滚该 agent 改动 → 重派正确角色 → 记入 loop-status |
| 同一 agent 二次越权 | 读越权事件表 | 停止，人工检查该 agent 的 `tools:` 是否真的生效 |
| Round 3 仍有 P0 | G4.3 判定 | 升级给人 |

**两条计数规则（原设计没规定，规则层面可以永远转下去）**：

1. **作废轮计入 `累计回退`，不计入 `连续不过`**。理由：越权作废不代表门判据有问题，但要计入总回退防止无限重跑。
2. **门从 FAIL 变 PASS 时，该门 `连续不过` 归零**；`累计回退` 只增不减。

> **为什么要显式规定**：原规则只说"同一门连续 3 轮不过"，没说作废轮算不算。若不算，两个活锁在规则上可以永远转；若全算，一次正常的越权回滚就可能误触发升级。

---

## 十一、状态表（主 Claude 维护）

`docs/loopforge/loop-status.md` —— 这份文件同时是**防死循环计数器的存储**和**G5.6 越权检测的输入**。主 Claude 上下文被压缩后，Loop 状态靠它恢复。

```markdown
## Loop 状态 - <需求名>

<!-- DISPATCH -->
round: 4-3
agent: impl-coder
allowed: src/
<!-- /DISPATCH -->

**累计回退**：7 / 10

| Stage | 状态 | 门 | 本阶段轮次 | 本轮派工 |
|:--|:--|:--|:--|:--|
| 0 定门 | ✅ | - | 1 | 主 Claude |
| 1 拷问 | ✅ | G0.1✅ G0.2✅ G0.3✅ | 2 | req-interrogator |
| 2 SRS | ✅ | G1.1~G1.5 ✅ | 1 | srs-drafter |
| 3 设计 | ✅ | G2.1~G2.5 ✅ | 1 | design-author |
| 4 Loop | 🔄 | G3.1✅ G3.3❌ G3.6✅ | 3 | test-author（补断言） |
| 5 审计 | ⏸ | - | 0 | - |

### 门连续不过计数（≥3 → 升级给人）
| 门 | 连续不过 | 最近一次 FAIL 原因 |
|:--|:--:|:--|
| G3.3 | 2 | 三处弱断言 test_R01:30 / test_R04:55 / test_R07:12 |
| G3.1 | 0 | （上轮已转 PASS，归零） |

### 震荡对检测（同一对门交替 ≥3 次 → 门冲突）
| 门 A | 门 B | 交替次数 | 说明 |
|:--|:--|:--:|:--|
| G3.1 | G3.3 | 2 | 补强断言→测试变红→改实现→别处断言又弱 |

**当前阻塞**：G3.3 三处弱断言
**下一步**：派 test-author 补量化断言 → test-runner 重跑 → gate-checker 重判

### 越权事件
| 轮 | Agent | 越权内容 | 处置 |
|:--|:--|:--|:--|
| 4-2 | impl-coder | 改了 loopforge-tests/test_R02.py:44 断言容差 | 已回滚，重派 test-author |
```

**三块内容都必须记**：

| 块 | 作用 | 不记的后果 |
|:--|:--|:--|
| `DISPATCH` 块 | G5.6 越权检测的输入 | 越权检测无法自动判定，退回人工门 |
| 连续不过 / 累计回退 / 震荡对 | 防死循环三条线的**存储** | 上下文一压缩，计数归零，永远触发不了升级 |
| 越权事件 | 判断"隔离是否真生效"的唯一证据 | 隔离失效了也不知道 |

> **计数器必须落盘，不能只存在对话里**。主 Claude 的上下文会被压缩，压缩后"这个门已经连续挂了 2 轮"这个事实就消失了——三条防死循环规则全部失去存储，等于没有。

---

## 十二、安装

不要手工拷文件——用脚本，它们带前置校验和装后验证：

```bash
# 方式 A · 全局（推荐，多项目共用）
bash scripts/install.sh                    # 一次
cd <项目> && bash <套件>/scripts/loopforge-init.sh    # 每项目

# 方式 B · 本地（整套装进项目，不碰 ~/.claude）
cd <项目> && bash <套件>/scripts/loopforge-init.sh --local
```

Windows 无 Git Bash 用 `.ps1` 版（`install.ps1` / `loopforge-init.ps1 -Local`）。

完整说明见套件根目录的 `INSTALL.md`。

## 十三、职责隔离自查（每轮 Stage 4 结束）

- [ ] 本轮改 `src/` 的是 `impl-coder`？（不是主 Claude、不是 test-author）
- [ ] 本轮改 `loopforge-tests/` 的是 `test-author`？（不是 impl-coder）
- [ ] 本轮跑测试的是 `test-runner`？（不是写代码那个）
- [ ] `git diff` 改动范围与派工职责一致？
- [ ] `goal-auditor` 这轮调用过 Bash 吗？（应该零——它没这工具）

任一项否 → 记越权事件，本轮结果作废重跑。
