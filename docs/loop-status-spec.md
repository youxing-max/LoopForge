# loop-status.md 字段规范（Loop Status Spec）

> `docs/loop-status.md` 是 Loop 的**唯一状态来源**。上下文会压缩、会话会断——
> 这份文件不会。所有命令（/loopforge /loopforge-status /loopforge-resume /loopforge-cancel）
> 都读写它。字段不齐 = 恢复失败 = Loop 白跑。

---

## 完整模板

```markdown
## Loop 状态 - <项目名/需求名>

<!-- DISPATCH -->
round: <stage>-<N>
agent: <agent 名>
allowed: <允许写的路径前缀>
<!-- /DISPATCH -->

**累计回退**：N / 10

| Stage | 状态 | 门 | 本阶段轮次 | 本轮派工 |
|:--|:--|:--|:--|:--|
| 0 定门 | ✅ | - | 1 | 主 Claude |
| 0.5 目标书 | ✅ | G0.5✅ G0.6✅ G0.7✅ | 2 | goal-architect |
| 1 拷问 | ✅ | G0.1✅ G0.2✅ G0.3✅ | 1 | req-interrogator |
| 2 SRS | ✅ | G1.1~G1.5 ✅ | 1 | srs-drafter |
| 3 设计 | ✅ | G2.1~G2.5 ✅ | 1 | design-author |
| 4 Loop | 🔄 | G3.1✅ G3.3❌ G3.6✅ | 3 | test-author（补断言） |
| 5 审计 | ⏸ | - | 0 | - |

### 门连续不过计数
| 门 | 连续不过 | 最近一次 FAIL 原因 |
|:--|:--:|:--|
| G3.3 | 2 | 三处弱断言 test_R01:30 |

### 震荡对检测
| 门 A | 门 B | 交替次数 |
|:--|:--|:--:|
| G3.1 | G3.3 | 2 |

### 越权事件
| 轮 | Agent | 越权内容 | 处置 |
|:--|:--|:--|:--|
| 4-2 | impl-coder | 改了 tests/test_R02.py:44 | 已回滚，重派 |

**当前阻塞**：<门号 + 原因，或"无">
**下一步**：<具体派工计划>
```

---

## 字段定义

### DISPATCH 块（机读，G5.6 的输入）

| 字段 | 类型 | 值域 | 谁写 | 何时写 |
|:--|:--|:--|:--|:--|
| `round` | string | `<stage>-<N>`，如 `4-3` | 主 Claude | 每次派 agent **之前** |
| `agent` | string | 9 个 agent 名之一 | 主 Claude | 同上 |
| `allowed` | string | 路径前缀，如 `src/` `tests/` `docs/design/` | 主 Claude | 同上 |

**格式硬约束**：
- 必须包在 `<!-- DISPATCH -->` / `<!-- /DISPATCH -->` 之间（gate-checker 用这个锚点提取）
- 同一时刻只有**一个** DISPATCH 块（新派工覆盖旧的）
- `allowed` 必须与被派 agent 的权限契约一致（impl-coder→`src/`，test-author→`tests/`，goal-architect→`docs/goal-doc`，等等）

**顺序铁律**：先写 DISPATCH → `git add -A && git commit` 打基线 → 再派 agent。颠倒 = 主 Claude 的状态改动被算进 agent 越权 = 活锁。

### 主状态表

| 列 | 值域 | 说明 |
|:--|:--|:--|
| Stage | `0` `0.5` `1`~`5` | 0.5 是目标书阶段 |
| 状态 | `⏸`（未开始）`🔄`（进行中）`✅`（通过）`❌`（卡住）`⛔`（取消） | |
| 门 | `G<号>✅/❌` 列表，或 `-` | 本阶段各门判定结果 |
| 本阶段轮次 | ≥1 | 进入该阶段后派了几轮 agent |
| 本轮派工 | agent 名或 `主 Claude` | 当前轮正在干活的角色 |

### 计数器

| 计数器 | 阈值 | 触发动作 | 归零条件 |
|:--|:--:|:--|:--|
| 门连续不过 | 3 | 停自动回退，升级给人 | 该门从 FAIL 转 PASS |
| 累计回退 | 10 | 回 Stage 0 复审门定义 | 不归零（只增） |
| 震荡对交替 | 3 | 标门冲突，回 Stage 0 | 门冲突裁决后 |
| 越权事件 | 2（同一 agent） | 停止，人工查 tools: 是否生效 | 不归零 |

**计数规则**：
- 越权作废轮计入 `累计回退`，**不计入** `连续不过`
- 门转 PASS 时该门 `连续不过` 归零；`累计回退` 只增不减

### 越权事件表

| 列 | 说明 |
|:--|:--|
| 轮 | DISPATCH 的 round 值 |
| Agent | 越权的 agent 名 |
| 越权内容 | 具体文件:行 + 干了什么 |
| 处置 | `已回滚，重派 X` / `已接受（主 Claude 裁决）` 等 |

---

## 谁写谁读

| 角色 | 读 | 写 |
|:--|:--:|:--:|
| 主 Claude | ✅ 全部 | ✅ 全部（唯一写者） |
| gate-checker | ✅ DISPATCH 块（G5.6 判定输入） | ❌（报告走返回值） |
| goal-auditor | ⚠️ Round 1 只读越权事件表；**Round 2/3 禁读全文件**（独立性） | ❌ |
| goal-architect | ❌（不需要） | ❌ |
| 其他 agent | ❌ | ❌ |
| /loopforge-status 命令 | ✅ 全部 | ❌ |
| /loopforge-resume 命令 | ✅ 全部 | ✅（仅 CANCELLED 标记的移除） |
| /loopforge-cancel 命令 | ✅ | ✅（仅追加 CANCELLED 标记） |

---

## CANCELLED 标记

`/loopforge-cancel` 在文件顶部追加：

```markdown
> ⛔ **CANCELLED** — 2026-08-14 — 原因：用户要求
> 重启用 /loopforge-resume
```

`/loopforge-resume` 遇到此标记：先问用户"重新激活？"，确认后删除这两行再续。

---

## 多批次变体

大型项目每批次一份：`docs/loop-status/batch-A.md` 等，字段同上。
外加 `docs/batches.md` 总表。G5.6 判定命令需把本批次状态文件加进白名单：

```bash
git status --porcelain | cut -c4- \
  | awk -v ok="$ALLOWED" 'index($0,ok)==1{print}' \
  | grep -v "^docs/loop-status/batch-${BATCH}\.md$"
```

---

## 损坏处理

任何命令读到格式损坏的 loop-status.md：
1. 如实报"格式异常 + 位置"
2. **禁止**猜内容或编造状态
3. 询问用户：手工修 / 从 git 恢复 / 重启 Loop
