# /loopforge 命令族规范（Commands Spec）

> 本文档定义 5 个 slash command 的完整规范。实现文件在 `commands/`。
> 装到项目级 `<project>/.claude/commands/`（由 `loopforge-init.sh` 完成）。

---

## 命令总表

| 命令 | 文件 | 读 | 写 | 派 agent | 破坏性 |
|:--|:--|:--|:--|:--|:--:|
| `/loopforge <需求>` | `loopforge.md` | SKILL.md, 模板 | docs/ 初始化文件 | goal-architect 等 9 个 | 否 |
| `/loopforge-status` | `loopforge-status.md` | loop-status.md | ❌ | ❌ | 否 |
| `/loopforge-resume` | `loopforge-resume.md` | 4 份状态文件 | loop-status.md（激活标记） | 按状态续派 | 否 |
| `/loopforge-cancel` | `loopforge-cancel.md` | loop-status.md | loop-status.md（CANCELLED 标记） | ❌ | 否 |
| `/loopforge-help` | `loopforge-help.md` | 状态文件探测 | ❌ | ❌ | 否 |

**只有 `/loopforge` 和 `/loopforge-resume` 会派 agent。其余三个是只读或标记操作。**

---

## 1. `/loopforge <需求>`

### 输入

- `$ARGUMENTS`：模糊需求文本（1 句 ~ 几段均可）
- **空输入** → 必须反问用户，禁止猜测

### 首次运行初始化（幂等）

| 检查 | 缺失时动作 |
|:--|:--|
| `docs/loopforge/` 目录 | `mkdir -p docs/loopforge` |
| `docs/loopforge/goal.md` | 从全局 skill 目录复制 `goal-template.md` |
| `docs/loopforge/goal-doc.md` | 创建占位（内容由 goal-architect 填） |
| git 仓库 | 警告"G5.x 越权检测失效"，不自动 init（用户决定） |
| `.gitignore` | 创建含测试产物模式的初始版 |

全局 skill 目录 = `~/.claude/skills/loopforge/`。找不到时报错并提示先跑 `install.sh`。

### 执行流

```
/loopforge <需求>
  ├─ 初始化检查（幂等）
  ├─ 读 ~/.claude/skills/loopforge/SKILL.md
  ├─ 派 goal-architect（Stage 0.5）传 <需求>
  ├─ [WAITING FOR USER] → 呈现给用户 → 等回答
  ├─ 用户回答 → 再派 goal-architect 修订 → 循环
  ├─ 用户说"确认，下一阶段" → gate-checker 判 G0.5~G0.7
  └─ 进入 Stage 1~5（按 SKILL.md 编排）
```

### 中断恢复

任何时刻中断，用 `/loopforge-resume`。状态全在文件里，不在对话记忆里。

---

## 2. `/loopforge-status`

### 输出格式（固定）

```
## Goal Loop 状态

当前阶段：<Stage N 名称>
当前轮次：<round>
当前阻塞：<门号 + 原因>（无则"无"）
下一步：<loop-status 的"下一步"字段>

### 门判定历史
| 门 | 状态 | 连续不过 |
|:--|:--|:--:|

### 计数器
累计回退：N / 10
越权事件：N 件

### 最近派工（DISPATCH）
<原样输出 DISPATCH 块>
```

### 边界情况

| 情况 | 输出 |
|:--|:--|
| loop-status.md 不存在 | "Goal Loop 尚未启动。用 `/loopforge <需求>` 启动" |
| 多批次（loop-status/batch-*.md） | 列出全部批次，问用户看哪个 |
| CANCELLED 标记存在 | 显示"⛔ 已取消 + 日期"，提示 `/loopforge-resume` 可重启 |
| loop-status.md 格式损坏 | 如实报"状态文件格式异常 + 位置"，不猜 |

**铁律：只读。不派 agent、不写文件、不推进。**

---

## 3. `/loopforge-resume`

### 恢复读取顺序（四份文件）

```
1. docs/loopforge/goal-doc.md     项目目标（做什么）
2. docs/loopforge/goal.md         门定义（怎么算完成）
3. docs/loopforge/loop-status.md  当前进度（卡在哪）
4. docs/loopforge/change-log.md   变更记录（多批次时）
```

缺任何一份：如实报缺哪份 + 询问用户是否继续（goal-doc 缺失时**禁止**继续编排——没有目标的 Loop 是空转）。

### 执行流

```
/loopforge-resume
  ├─ 读四份文件
  ├─ 报告恢复摘要（阶段/轮次/阻塞/下一步）
  ├─ git status 非空？→ 先跑 G5.x 越权检测
  ├─ 问用户"继续 / 先做别的"→ 等确认
  └─ 确认后按 SKILL.md 从当前 stage 接续
```

### 铁律

- **不信任对话记忆，只信任文件**
- CANCELLED 状态 → 先问"要重新激活吗"，确认后移除标记再续
- 某阶段无 gate-checker 判定记录 → 重跑该阶段判定，不默认通过

---

## 4. `/loopforge-cancel`

### 执行流

```
/loopforge-cancel
  ├─ 向用户确认"确定取消？"
  ├─ 确认 → loop-status.md 顶部追加 CANCELLED 标记（日期+原因）
  └─ 输出取消摘要（已完成/未完成/保留文件清单）
```

### 语义

| 做 | 不做 |
|:--|:--|
| 标记 loop-status.md | 删除任何文件 |
| 停止编排 | 回滚 git |
| 保留 src/ loopforge-tests/ docs/ 全部 | 清理 agent 产物 |

取消是可逆的：`/loopforge-resume` 会询问是否重新激活。

---

## 5. `/loopforge-help`

输出命令总表 + 本项目状态探测（goal.md / goal-doc.md / loop-status.md 存在性）+ 文档链接。只读。

---

## 跨命令约束

| 约束 | 理由 |
|:--|:--|
| 状态只存文件，不存对话 | 上下文会压缩/断，文件不会 |
| 所有命令幂等 | 重复执行不产生副作用 |
| 错误如实报，不猜 | "状态文件损坏"比"编个状态出来"好 |
| 全局层缺失时明确指引 | 报"先跑 install.sh"，不静默降级 |

---

## 与三层架构的关系

```
~/.claude/skills/ + ~/.claude/agents/     ← 全局能力（install.sh 装）
<project>/.claude/commands/loopforge*.md       ← 命令入口（loopforge-init.sh 装）
<project>/docs/loopforge/goal*.md + loop-status.md  ← 项目数据（/loopforge 首跑建）
```

命令文件只是入口薄层——真正编排在 SKILL.md，能力在 agents，状态在 docs/。
