# 旧版说明与迁移指南（Legacy & Migration）

> 本文档记录 loopforge 三个版本的设计缺陷与修法，以及从 KH OFDR 原套件迁入的路径。
> 目的：让"为什么这样改"可追溯——不然下次有人会把删掉的东西重新加回来。

---

## 一、版本谱系

```
KH OFDR 验证闭环套件 v1.3（领域专属）
   │  剥物理特化 + 加"从模糊需求起步"
   ▼
loopforge v1.0     ← 5 阶段单向流水线
   │  加 Stage 0 定门 + 全阶段 Goal 驱动回退
   ▼
loopforge v2.0     ← 6 阶段 + Goal 门驱动
   │  拆职责 + tools 白名单 + 越权检测
   ▼
loopforge v2.1     ← 当前版
```

---

## 二、v1.0 的缺陷（已修）

### 缺陷 1：不是真闭环，是单向流水线

**当时的设计**：

```
Stage 1 拷问 → Stage 2 SRS → Stage 3 设计 → Stage 4 Loop → Stage 5 审计
   每阶段"退出判据"写在各自阶段文档里，满足就进下一阶段
```

**问题**：只有 Stage 4 内部有循环（develop-tests ↔ phase-verify）。Stage 1→2→3→5 之间是单向的。每个阶段的"退出判据"是阶段内私有判据，不是统一门。

**具体后果**：

| 场景 | v1.0 行为 | 应有行为 |
|:--|:--|:--|
| SRS 写完但验收口径是"性能良好" | 用户签字就进 Stage 3 | 门 G1.2 判定不可机读 → 回 Stage 2 |
| 设计文档缺接口签名 | 写完就进 Stage 4 | 门 G2.5 判定 → 回 Stage 3 |
| 测试覆盖率不足 | 测试全绿就进 Stage 5 | 门判定 → 回 Stage 4 |

**v2.0 修法**：加 Stage 0 定义统一 Goal 门集合（`docs/loopforge/goal.md`），每阶段退出**强制**跑门判定，不过按回退映射表跳转。判据从"散在各阶段"改为"集中单一 home"。

### 缺陷 2：Goal 门没有单一 home

**当时**：判据散落在 SKILL.md 各阶段的"退出判据"小节 + 各 agent 文档的"退出判据"小节。同一条判据可能在两处写得不一致。

**v2.0 修法**：全部收进 `docs/loopforge/goal.md`，每条门四字段固定：`自动判定命令` / `通过判据` / `失败回退到` / `严重级`。SKILL.md 和 agent 文档只引用不复述。

---

## 三、v2.0 的缺陷（已修）—— 职责隔离缺失

这是最严重的一类，v1.0 和 v2.0 都有。

### 违规 1：`loop-driver` 既写测试又跑测试 🔴

**当时的设计**（已删除的 `agents/loop-driver.md`）：

```
loop-driver agent 的工作流程：
  Step 1: 调 develop-tests skill  → 生成 loopforge-tests/test_R*.py
  Step 2: 调 phase-verify skill   → 跑测试
  Step 3: 判定结果 → 有缺口就上报
```

一个 agent 同时持有"生成测试"和"执行测试"两项职责。

**为什么是问题**：测试红了，改断言比改实现容易得多。同一个上下文里既知道断言长什么样、又看得到红绿，就有了最短路径——把 `assert peak == approx(0.5, abs=5e-3)` 的容差放宽到 `abs=0.5`，报告立刻变绿。

这不需要 agent "有意作弊"。它只是在优化"让任务完成"这个目标，而放宽断言恰好是代价最小的路径。

**v2.1 修法**：删掉 `loop-driver`，拆成三个：

| 拆出的 agent | 职责 | 关键约束 |
|:--|:--|:--|
| `test-author` | 写测试 | **无 Bash** → 看不到红绿 |
| `test-runner` | 跑测试 | **无 Edit/Write** → 改不了任何东西 |
| `impl-coder` | 写实现 | **无 Bash** → 看不到红绿 |

Stage 4 改由主 Claude 编排三方交替。

### 违规 2：主 Claude 既编排又写代码 🔴

**当时**：`loop-driver` 上报缺口 → **主 Claude 自己改 `src/`** → 重跑。

**为什么是问题**：主 Claude 的上下文里塞满了需求、设计、拷问答卷、历次修复记录。这是全场信息最多的角色——也是最容易产生"我知道这里其实没问题"的角色。让它动手改代码，等于让信息最脏的上下文做最需要客观性的事。

**v2.1 修法**：主 Claude 收权为**纯编排**——只做路由判断（这个缺口该派谁修），不 Edit `src/` `loopforge-tests/`，不跑 pytest。

### 违规 3：`goal-auditor` 兼任自检与终审 🔴

**当时**：`goal-auditor` 有两种模式——`--self-check`（每阶段退出跑轻量自检）和 `--full`（Stage 5 双轮终审）。

**为什么是问题**：虽然每次 `Agent()` 调用都是 fresh 上下文，但**角色定义本身**混了两种性质的工作。自检是机械判定（跑命令对判据），终审是价值判断（这绿得可不可疑）。写在同一个 agent 文档里，"自检时形成的宽松标准"会渗进终审的行为模式——文档里那些"如何快速判定"的指引，会让终审也倾向于走捷径。

**v2.1 修法**：拆成两个 agent：

| Agent | 性质 | 工具 | 能不能说"虽然 FAIL 但没关系" |
|:--|:--|:--|:--|
| `gate-checker` | 机械判定 | 有 Bash（跑判定命令） | ❌ 不能，只执行不解释 |
| `goal-auditor` | 价值判断 | **无 Bash**（只读产物） | ✅ 能，但要带论证 |

### 违规 4：审计员有 Bash 🔴

**当时**：`goal-auditor` 的 `--self-check` 模式需要跑判定命令，所以给了 Bash。

**为什么是问题**：审计员能跑测试，就会去跑测试——然后基于"我跑了一遍，绿的"下结论。但**跑测试是验证，不是审计**。审计要回答的是"这绿是真的吗"——测试本身可能就是假的。审计员亲自跑一遍绿的测试，只是再次确认了假绿。

**v2.1 修法**：`goal-auditor` 工具收到 `Read, Grep, Glob`——**连 Bash 都没有**。它只能读产物：读代码、读测试、读 `test-runner` 的事实报告。要看运行结果 → 读别人的报告，不自己跑。

---

## 四、v2.1 的隔离设计

### 四层防线

| 层 | 手段 | 强度 | 失效场景 |
|:--|:--|:--|:--|
| L1 | agent frontmatter `tools:` 白名单 | 硬 | harness 不支持 `tools:` 时失效 |
| L2 | settings.json `permissions.deny` | 硬但全局 | 会话级，非 per-agent |
| L3 | agent 文档红线条款 | 软 | agent 不遵守就失效 |
| L4 | `gate-checker` G5.x git diff 事后检测 | 硬（事后） | **唯一不依赖自觉的关卡** |

**L4 不能省**。L1 管得住"有没有这个工具"，管不住"写到哪个目录"——`impl-coder` 有 Write，理论上能写 `loopforge-tests/`。挡住它的是 L3 的红线条款（软）+ L4 的事后检测（硬）。

### 权限不变式（可自动验证）

`scripts/validate_suite.py` 的 L2 层检查这些：

```
核心不变式：没有任何 agent 同时持有 Bash 和 Edit/Write
  → 写代码+跑测试同体 = 可改断言凑绿

三集合互不相交：
  写者 = {有 Edit/Write，无 Bash}  = impl-coder, test-author, srs-drafter, design-author, req-interrogator
  执行者 = {有 Bash}               = test-runner, gate-checker
  审计者 = {无 Edit/Write，无 Bash} = goal-auditor
```

---

## 五、迁移指南

### 5.1 从 loopforge v1.0 / v2.0 迁移

| 步骤 | 动作 |
|:--|:--|
| 1 | **删** `.claude/agents/loop-driver.md` |
| 2 | **加** 5 个新 agent：`impl-coder` `test-author` `test-runner` `gate-checker` `design-author` |
| 3 | **换** `goal-auditor.md`（收权为只读，删掉 `--self-check` 模式） |
| 4 | **加** `tools:` 到 `req-interrogator` `srs-drafter` 的 frontmatter |
| 5 | **换** `SKILL.md`（Stage 3/4 编排全改） |
| 6 | **加** `docs/role-permission-matrix.md` |
| 7 | **加** `docs/loopforge/goal.md` 的 G5.1~G5.6 越权检测门 |
| 8 | **跑** `python scripts/validate_suite.py` 确认 74 项全绿 |

**进行中的项目怎么办**：Stage 0~3 的产物（goal.md / 拷问清单 / SRS / 设计文档）可直接复用。Stage 4 若已开始，建议重跑一轮 `test-runner` 拿干净的事实报告，再按新编排继续——旧的验收报告可能被"写测试的自己跑"污染过。

### 5.2 从 KH OFDR 原套件迁移

原套件（`../` 同级目录）的组件对应关系：

| 原套件组件 | 在 v2.1 的去向 | 说明 |
|:--|:--|:--|
| `develop-tests` skill | → `test-author` agent | 职责相同，但收了 Bash 权限 |
| `phase-verify` skill | → `test-runner` agent + `gate-checker` | 拆开：跑测试 vs 判门 |
| `req-design-verifier` skill | → `design-author` 自查 + `gate-checker` G2.x | 一致性检查进门判定 |
| `delivery-acceptance` skill | → `goal-auditor` 双轮 + Stage 5 | goal 门 G1~G7 → 通用 G0~G5 |
| `doc-consistency-checker` agent | → `gate-checker` G2.1~G2.3 | 引用单向性/纯度进门 |
| `test-requirement-analyzer` agent | → `test-author` Step 1 | 合并 |
| `test-coverage-analyzer` agent | → `goal-auditor` 维度 D | 合并 |
| `physics-*` agent（4 个） | ❌ 删除 | 领域专属，换成你领域的审查 agent |
| `hdf5-inspector` skill | ❌ 删除 | 数据格式专属 |
| `physics-formula-validator` skill | ❌ 删除 | 领域专属 |

> ⚠️ **原套件的三个 skill 不满足职责隔离，不能直接复用**：
> - `develop-tests` 内含 `code-reviewer` 调用（生成测试 + 审查测试同体）
> - `phase-verify` 内含 `physics-reviewer` 调用（跑测试 + 物理审查同体）
> - `delivery-acceptance` 编排全流程（编排 + 审计同体）
>
> 想复用必须先按 v2.1 的角色边界拆开。

### 5.3 迁移后验证

```bash
# 1. 白名单生效
grep -l "^tools:" .claude/agents/*.md    # 应列出 8 个

# 2. 套件自校验
python scripts/validate_suite.py         # 应 74 PASS / 0 FAIL

# 3. 跑一轮 Stage 4，用 G5.x 验证隔离真的生效
#    故意让 impl-coder 改一个测试文件 → gate-checker 应报 🔴 越权
```

第 3 步是**唯一能证明隔离真实生效**的验证。前两步只证明配置写对了，不证明 harness 真的执行了。

---

## 六、不要改回去的东西

以下设计有人会想"简化"，但改回去就退回旧版缺陷：

| 有人会想 | 为什么不行 |
|:--|:--|
| "给 `impl-coder` 加 Bash，让它自己跑测试验证一下" | 这就是违规 1。它会改断言 |
| "`goal-auditor` 加 Bash 方便它核实" | 这就是违规 4。审计变验证 |
| "`gate-checker` 和 `goal-auditor` 合并，少一个 agent" | 这就是违规 3。自检污染终审 |
| "主 Claude 直接改个小 bug，派 agent 太麻烦" | 这就是违规 2。信息最脏的上下文动手 |
| "Round 2 读一下 Round 1，效率高" | 双轮退化为单轮复读，白跑一轮 |
| "G5.x 越权检测太啰嗦，去掉" | 去掉后隔离只剩自觉，L4 防线消失 |
| "`无法判定` 当 PASS 处理，不然卡住" | 检查失败被当通过混过去，门形同虚设 |

每条都在 `scripts/validate_suite.py` 里有对应检查项——改回去会被自校验抓到。

---

## 七、修订记录

| 版本 | 日期 | 变更 |
|:--|:--|:--|
| v1.0 | 2026-08-08 | 从 KH OFDR 套件通用化，5 阶段单向 |
| v2.0 | 2026-08-09 | 加 Stage 0 定门，全阶段 Goal 驱动回退 |
| v2.1 | 2026-08-09 | 职责隔离：删 loop-driver，拆 8 单一职责 agent，加 tools 白名单 + G5.x 越权检测 |
