# 角色权限矩阵（Role & Permission Matrix）

> loopforge 的**职责隔离契约**。
> 铁律：**写代码 / 跑测试 / 审计 三者永不同体**。

---

## 1. 为什么必须隔离

同一个 agent 兼任两职，就有作弊动机。三条真实失效路径：

| 违规组合 | 失效��式 | 后果 |
|:--|:--|:--|
| **写代码 + 跑测试** | 测试红了，改断言比改代码容易 | 断言被弱化到永远通过，假绿 |
| **写测试 + 跑测试** | 断言凑不绿，调容差/加 skip | KNOWN_GAPS 膨胀，缺口被合法化 |
| **写代码 + 审计** | 审自己的实现，认知偏差 | 自证自洽，P0 永远发现不了 |
| **自检 + 终审** | 自检时已形成"这没问题"的判断 | 终审只是复读自检结论，双轮变单轮 |

上下文隔离是**手段**，权限隔离是**保险**。只靠 prompt 说"你不要改测试"不够——要在 `tools:` 白名单层面让它**做不到**。

---

## 2. 角色矩阵

| 角色 | Agent | 写 impl | 写 test | 写 docs | 跑命令 | 判定门 | 审计 |
|:--|:--|:--:|:--:|:--:|:--:|:--:|:--:|
| **编排者** | 主 Claude | ❌ | ❌ | ✅ **仅编排状态**¹ | ✅ **仅 git**¹ | ❌ | ❌ |
| **目标架构** | `goal-architect` | ❌ | ❌ | ✅ goal-doc.md | ❌ | ❌ | ❌ |
| **拷问官** | `req-interrogator` | ❌ | ❌ | ✅ srs-raw/ | ❌ | ❌ | ❌ |
| **SRS 起草** | `srs-drafter` | ❌ | ❌ | ✅ srs/ | ❌ | ❌ | ❌ |
| **设计作者** | `design-author` | ❌ | ❌ | ✅ design/ | ❌ | ❌ | ❌ |
| **实现者** | `impl-coder` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **测试作者** | `test-author` | ❌ | ✅ | ✅ testplan | ❌ | ❌ | ❌ |
| **测试执行** | `test-runner` | ❌ | ❌ | ❌ **报告走返回值**² | ✅ | ❌ | ❌ |
| **门判定** | `gate-checker` | ❌ | ❌ | ❌ **报告走返回值**² | ✅ 只跑判定命令 | ✅ | ❌ |
| **审计员** | `goal-auditor` | ❌ | ❌ | ❌ **报告走返回值**³ | ❌ | ❌ | ✅ |

**¹ 主 Claude 的例外（原表写全 ❌，与流程要求直接矛盾）**：
流程强制要求主 Claude 做四件需要写/执行的事——维护 `docs/loop-status.md`、维护 `docs/goal.md`、给 `goal-auditor` 的报告落盘到 `docs/audit/`、打 git 基线。原矩阵把它标成全 ❌，等于**契约上无人可写状态表**，防死循环计数器、越权台账、审计报告全部无处存放。

主 Claude 的真实权限边界：

| 允许 | 禁止 |
|:--|:--|
| 写 `docs/loop-status.md` `docs/goal.md` `docs/audit/**` | 写 `$IMPL_ROOT` `$TEST_ROOT` 下任何文件 |
| 跑 `git add/commit/status/diff/log`（基线协议） | 跑测试、跑构建、跑类型检查 |
| 调 Agent / Skill / 读全仓 | 自己下"这代码没问题"的结论 |

**² `test-runner` / `gate-checker` 的报告不落盘**：它们的 `tools:` 里没有 Write。报告通过**返回值**传给主 Claude。原矩阵标"✅ 报告"与它们各自文档的红线条款（"禁止写任何文件"）直接冲突。

**³ `goal-auditor` 同理**：它只有 `Read, Grep, Glob`。审计报告内容由它返回，**由主 Claude 落盘**到 `docs/audit/`。这是它没有 Write 却能产出报告文件的唯一路径。

**读权限**：全角色可读全仓（审计需要看全貌）。隔离的是**写**和**执行**。

---

## 3. 工具白名单（硬约束）

写进各 agent 的 frontmatter `tools:` 字段——harness 层强制，agent 想违规也调不到工具。

| Agent | `tools:` | 说明 |
|:--|:--|:--|
| `goal-architect` | `Read, Write, Grep, Glob` | 无 Bash → 跑不了命令；只写 goal-doc |
| `req-interrogator` | `Read, Write, Grep, Glob` | 无 Bash → 跑不了任何命令 |
| `srs-drafter` | `Read, Write, Grep, Glob` | 同上 |
| `design-author` | `Read, Write, Grep, Glob` | 同上 |
| `impl-coder` | `Read, Edit, Write, Grep, Glob` | **无 Bash → 跑不了测试** ← 关键 |
| `test-author` | `Read, Edit, Write, Grep, Glob` | **无 Bash → 跑不了测试** ← 关键 |
| `test-runner` | `Read, Bash, Grep, Glob` | 无 Edit/Write，但见下方 ⚠️ |
| `gate-checker` | `Read, Bash, Grep, Glob` | 同上，只跑 goal.md 里的判定命令 |
| `goal-auditor` | `Read, Grep, Glob` | **无 Bash 无 Edit → 只能看** ← 关键 |

> `goal-auditor` 连 Bash 都不给：审计员要跑测试，说明它在验证而非审计——验证是 `test-runner` 的活。审计只读产物（代码 / 文档 / test-runner 的报告）。

### ⚠️ 必须承认的一条：Bash ⊇ Write

**"无 Edit/Write → 改不了代码"这句话是错的。**

持有 Bash 的 agent（`test-runner`、`gate-checker`）可以用 `>` 重定向、`python -c`、`perl -pi`、`patch`、`git apply`、`cat <<EOF>` 等等写入任意文件。而它们**同时能跑测试** —— 这意味着单个 agent 在原理上就能独立闭合「改被测物 → 跑测试 → 报告结果」全回路。

这是本套件隔离设计的**已知缺口**，不是可以靠 prompt 消除的：

| 防线 | 对 Bash 写入是否有效 |
|:--|:--|
| L1 `tools:` 白名单 | ❌ 无效——Bash 就是被授予的工具 |
| L2 `settings.json` deny | ⚠️ 部分——能挡 `sed -i`、`tee` 等命令名，**挡不住 shell 重定向**（`>` 是语法不是命令） |
| L3 文档红线条款 | ⚠️ 靠自觉 |
| L4 G5.x git 事后检测 | ✅ **有效**——不管用什么手段写的，`git status --porcelain` 都看得见 |

**结论：对这两个角色，L4 是唯一真防线**，L1 对它们不起作用。G5.3（test-runner 零改动）因此是阻断级，且必须每轮跑。

真要硬隔离，只有两条路：
1. 开启 sandbox（OS 级文件系统隔离，官方文档指明这是唯一的强制手段）
2. 配 `PreToolUse` 钩子，拦截 Bash 命令做路径级校验

在没做这两件事之前，**不要在对外材料里宣称"改不了代码"** —— 准确表述是"改了会被 G5.x 抓到并作废重跑"。

---

## 4. 路径边界（软约束 + 事后检测）

`tools:` 只能管住"有没有这个工具"，管不住"写到哪个目录"。路径边界靠两层：

**第一层：prompt 硬规则**（每个 agent 文档里写死）

```
impl-coder:   只允许写 src/**。碰 tests/** 立即停止并报告越权。
test-author:  只允许写 tests/** + docs/verification/testplan-*.md。碰 src/** 立即停止。
test-runner:  不允许写任何文件（报告用返回值传出，不落盘）。
```

**第二层：事后 git 检测**（Goal 门 G5.x，见 `goal-template.md`）

```bash
# 修复轮（impl-coder 跑完）后检查：只动了 src/，没动 tests/
git diff --name-only HEAD | grep -q '^tests/' && echo "🔴 越权：修复轮动了测试文件"

# 测试生成轮（test-author 跑完）后检查：只动了 tests/，没动 src/
git diff --name-only HEAD | grep -q '^src/' && echo "🔴 越权：测试轮动了实现代码"
```

> 非 git 仓库用 hash 快照替代。跑前 `find "$TEST_ROOT" -type f | sort | xargs shasum > /tmp/tests.pre`，跑后比对。（用 `shasum` 不用 `md5sum` —— **macOS 没有 `md5sum`**，只有 `md5`；`shasum` 三平台都有。）

---

## 5. 上下文隔离规则

| 规则 | 内容 | 违反后果 |
|:--|:--|:--|
| **每次 Agent() 都是 fresh** | 不复用同一 agent 实例跨阶段 | 上下文污染，判断被前序结论锚定 |
| **不传递结论，只传递产物** | 给 agent 的是文件路径，不是"上一轮说这里有问题" | 引导性输入 = 变相自证 |
| **Round 2 禁读 Round 1** | 显式在 prompt 里禁止读 `round1-*.md` | 双轮退化为单轮 |
| **gate-checker ≠ goal-auditor** | 门判定（机械）与审计（判断）分属两个 agent | 自检形成的印象污染终审 |
| **test-runner 报告只含事实** | PASS/FAIL/耗时/输出，不含"我觉得是 XX 原因" | 归因带偏修复方向 |

---

## 6. Stage 4 的正确编排（关键改动）

**旧版（违规）**：`loop-driver` 一个 agent 既调 develop-tests 生成测试，又调 phase-verify 跑测试。

**新版（合规）**：主 Claude 编排三个单一职责 agent 交替：

```
Stage 4 内循环（主 Claude 编排，自己不写代码）

  [1] test-author      写测试 → tests/test_R*.py + run_<组>.py
       ↓ (无 Bash，交不出运行结果)
  [2] test-runner      跑测试 → 事实报告（PASS/FAIL/GAP/skip/弱断言）
       ↓ (无 Edit，改不了任何东西)
  [3] 主 Claude 读报告 → 判定是缺实现还是缺测试
       ├── 缺实现 → [4] impl-coder 改 src/ → 回 [2]
       └── 缺测试/断言弱 → 回 [1] test-author 改 tests/ → 回 [2]
       ↓ 全绿
  [5] gate-checker     跑 G3.x 判定命令 → 门报告
       ↓ 不过 → 回 [3]
       ↓ 全过 → 出 Stage 4
```

**每一环的不可能性**：
- `test-author` 想让测试变绿？它没 Bash，看不到红绿。
- `impl-coder` 想改测试凑绿？它写 test 目录会被 G5.x git 检测抓到，且 prompt 硬规则要求它自停。
- `test-runner` 想"顺手修一下"？没有 Edit/Write —— **但它有 Bash，能用 `>` 写文件**（见 §3 的 Bash ⊇ Write）。真防线是 G5.3。
- `gate-checker` 想放水？判定命令写死在 `docs/goal.md`。**但它有 Bash，能改 goal.md** —— `settings.json` 的 `ask` 规则绑的是 Edit/Write 工具，走 Bash 不触发。真防线是把 `docs/goal.md` 纳入 G5.x 的越权路径检测。

---

## 7. 主 Claude 的角色收权

主 Claude **是编排者，不是实现者**。它可以：

- ✅ 读任何文件（判断该派谁）
- ✅ 调 Agent / Skill
- ✅ 读 agent 返回的报告并决策路由
- ✅ 写 `docs/loop-status.md` `docs/goal.md` `docs/audit/**`（编排状态与报告落盘）
- ✅ 跑 `git add/commit/status/diff/log`（派工基线协议）

它**不可以**：

- ❌ 直接 Edit/Write `$IMPL_ROOT` 或 `$TEST_ROOT` 下任何文件 —— 派 `impl-coder` / `test-author`
- ❌ 直接跑测试 / 构建 / 类型检查 —— 派 `test-runner`
- ❌ 自己下"这代码没问题"的结论 —— 派 `goal-auditor`

> 为什么主 Claude 也要收权：它的上下文里塞满了需求、设计、历史修复记录——最容易产生"我知道这里是对的"的偏差。让它只做路由，判断交给上下文干净的专职 agent。

### ⚠️ 主 Claude 的收权是纪律级，不是强制级

必须说清楚：**没有任何机制能硬性限制主线程的工具**。

| 手段 | 为什么不管用 |
|:--|:--|
| agent frontmatter `tools:` | 主 Claude 不是 subagent，没有 frontmatter |
| Skill 的 `disallowed-tools` | **回合级**——下一条用户消息即失效，而 Loop 横跨 6 阶段数十轮 |
| `settings.json` `permissions.deny` | **会话全局**——deny 了 `Write(src/**)`，`impl-coder` 也一起被 deny 了 |

所以主 Claude 的边界只有两层保障：

1. **纪律**（本文档 + SKILL.md 写死）
2. **G5.6 事后检测**——比对 `loop-status.md` 的机读派工块 `allowed:` 字段与实际改动范围。主 Claude 若绕过 agent 直接改代码，而当轮 `allowed:` 不含该路径，一样被抓。

G5.6 原判据字面写的是"人工核对"却是阻断级、每阶段都跑，等于每阶段卡一个人工门。已改为自动判定（见 `goal-template.md` G5.6 节）。

**不要宣称主 Claude"被收权"是硬约束** —— 准确表述是"越权会被 G5.6 抓到并作废本轮"。

---

## 8. 违规自查清单

每轮 Stage 4 结束，主 Claude 自查：

- [ ] 本轮改实现的是 `impl-coder` 吗？（不是主 Claude、不是 test-author）
- [ ] 本轮改测试的是 `test-author` 吗？（不是 impl-coder）
- [ ] 本轮跑测试的是 `test-runner` 吗？（不是写代码的那个）
- [ ] `git status --porcelain` 的改动范围与 `loop-status.md` 的 `allowed:` 一致吗？
- [ ] `goal-auditor` 这轮被调用过 Bash 吗？（应该完全没有——它没这工具）
- [ ] 派工前打过基线吗？（先写 loop-status → `git add -A && git commit` → 再派工）

任一项否 → 记为越权事件，写入 `docs/loop-status.md`，本轮结果作废重跑。

> 用 `git status --porcelain` 不用 `git diff --name-only HEAD`：后者**看不见新建文件**，而"新建一个测试文件"是越权最自然的形态。

---

## 9. 降级方案（工具不支持时）

若你的 harness 不支持 agent 级 `tools:` 白名单：

| 隔离手段 | 强度 | 做法 |
|:--|:--|:--|
| `tools:` frontmatter | 硬 | 首选 |
| settings.json `permissions.deny` | 硬但全局 | 见 `settings-permissions.json`，配合会话切换 |
| prompt 硬规则 + 自停 | 软 | 每个 agent 文档首段写死红线 |
| git diff 事后检测 | 硬（事后） | G5.x 门，越权即作废重跑 |
| 人工 review 派工记录 | 软 | `docs/loop-status.md` 记录每轮谁干的 |

**最低要求**：即使全软，也必须有 **git diff 事后检测**——这是唯一不依赖 agent 自觉的关卡。
