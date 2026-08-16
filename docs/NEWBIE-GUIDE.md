# Goal 方案用户指南

> 你是想从 0 到 1 做一个复杂项目（如 "微信"、"电商后台"、"数据平台"）的人。
> 这份文档告诉你怎么用 loopforge 这套方案。
> 全文 5 分钟读完。

---

## 0. 三句话定位

- **你**：有一个模糊想法 + 想做出能用的项目
- **方案**：6 阶段 + 1 阶段目标书（7 个阶段）的 Goal 门驱动闭环
- **承诺**：完成 = 通过所有 Goal 门 —— 不是"感觉差不多了"

---

## 1. 第一次使用（安装）

### 1.1 准备

- 你正在用 Claude Code（CLI 或 IDE 插件）
- 项目目录里能跑 bash（macOS/Linux 原生；Windows 用 Git Bash）
- 有 git（用于变更追踪）

### 1.2 一键安装

在 Claude Code 里输入：

```
请按 loopforge docs/NEWBIE-GUIDE.md 第 1.2 节安装套件到当前项目
```

主 Claude 会按文档执行 5 步：复制 skill/agent/文档/脚本 → 跑 `preflight.sh` 验证。

如果你想自己装：

```bash
cp -r .claude/skills/loopforge/*  .claude/skills/
cp -r .claude/agents/*  .claude/agents/         # 假设套件已展开
cp docs/goal-template.md       docs/goal.md
cp docs/goal-doc-template.md   docs/goal-doc-template.md
cp -r scripts .

bash scripts/preflight.sh      # 必须 0 阻断
```

---

## 2. 启动一个项目（标准流程）

### 2.1 一句话触发

在 Claude Code 里输入你的模糊想法：

```
我想做一个微信这样的聊天 App，支持单聊、群聊、文件传输
```

或：

```
我要做一个 TODO CLI
```

主 Claude 看到模糊需求，会自动派 `goal-architect` agent。

### 2.2 回答问题（Stage 0.5 目标书协作）

`goal-architect` 会反复问你问题。**这是关键环节**：

```
🔴 必答（影响项目能否开始）
Q1: 项目的核心用户群是什么？（我猜：普通消费者，10 万级）
Q2: 第一个里程碑交付什么？（我猜：单聊 + 群聊）

🟡 待澄清
Q3: 多端是否一次到位？（Web/iOS/Android）
Q4: 离线消息要支持吗？

确认方式：
1. 答 "Q1=A, Q2=B, Q3=C..."
2. 或说 "按你的猜测走"
3. 我会改 goal-doc，再次请你审
```

**怎么回答**：

| 你的反应 | 含义 |
|:--|:--|
| 答具体选项 | 推翻猜测，按你的回答写 |
| 说"按你的猜测走" | 接受猜测 → agent 改 doc → 你再审 |
| 说"再说" | 不准 → 会在风险章节标注，主 Claude 后续会回头追问 |
| 答含糊（"差不多都行"） | agent 必追问具体值，**不会替你猜** |

**循环直到你说**：`确认，下一阶段`（或等价表述）。

### 2.3 产出物

你会看到 `docs/goal-doc.md` 落盘，里面 7 个章节：

```
## 0. 一句话定义
## 1. 系统边界
## 2. 顶层子系统划分
## 3. 里程碑与批次
## 4. 每批次的关键决策
## 5. 跨批次不变约束
## 6. 风险与未决
## 7. 范围之外
```

**这时候检查清单**：
- [ ] §0 一句话定义 ≤ 30 字
- [ ] §1 系统边界无遗漏
- [ ] §2 子系统 ≥ 1 行
- [ ] §3 批次 0 = 契约
- [ ] §4 关键决策 ≥ 3 行
- [ ] §5 不变约束 ≥ 1 条
- [ ] §6 风险表有标题
- [ ] §7 范围外 ≥ 1 条（"什么不做"比"什么做"更重要）

---

## 3. 自动执行（你基本不用动手）

goal-doc 确认后，主 Claude 自动编排：

```
Stage 1   拷问             主 Claude 派 req-interrogator
Stage 2   起草 SRS         主 Claude 派 srs-drafter
Stage 3   设计文档         主 Claude 派 design-author
Stage 4   Loop（三角色交替）test-author ↔ test-runner ↔ impl-coder
Stage 5   双轮独立审计     goal-auditor ×2
```

**任何门不过 → 自动回退**。你不需要懂 Stage 4 内部怎么转。

### 3.1 你会被打断的 4 种情况

| 情况 | 触发 | 你做什么 |
|:--|:--|:--|
| Goal 门不过 | 实现没写完 / 测试不达标 | 主 Claude 显示"回退建议"，按它说的办 |
| 同一门连续 3 轮失败 | 需求不可行 / 门定义过严 | **人工介入**——查 goal-doc / goal.md |
| 累计回退 > 10 次 | 门定义互相矛盾 | **人工介入**——回到 Stage 0 |
| 审计报告有 P0 | 严重问题 | 立刻看，自己裁决要不要修 |

### 3.2 终止条件

任何时候可以叫停：
- `Ctrl+C` 取消当前 agent
- 上下文被压缩 → 主 Claude 读 `docs/loop-status.md` 恢复
- 决定改方向 → 告诉主 Claude，主 Claude 派 `goal-architect` 改 goal-doc，或重做阶段

---

## 4. 日常使用的 5 个命令

```bash
# 1. 检查套件能不能跑
bash scripts/preflight.sh

# 2. 检查自己项目能做到什么程度（套件自校验）
python scripts/validate_suite.py

# 3. 看当前进度（跨会话恢复）
cat docs/loop-status.md

# 4. 看 Goal 门定义
cat docs/goal.md

# 5. 看项目目标书
cat docs/goal-doc.md
```

---

## 5. 大项目怎么做（多批次）

如果你说"我要做一个微信"，agent 会建议你**分批次**：

| 批次 | 内容 | 跑通条件 |
|:--|:--|:--|
| **0 契约** | API schema / 错误码 / 模块边界 | 跑 `tests/run_contract.py` 全绿 |
| A 数据层 | 数据库 schema / 模型 | 跑 A 批测试 + 契约 |
| B 业务层 | 核心逻辑 | 跑 B 批 + 契约 + A 批回归 |
| ... | ... | ... |

**依赖批次全绿才能开工**。批次 0 冻结后所有批次不许改契约。

完整指南：`docs/large-project-guide.md`。

---

## 6. 三个真相

### 真相 1：模糊需求 ≠ 多了好

你说"做一个微信"——`goal-architect` 一定会问：
- 什么端（Web / iOS / Android）？
- 单聊先做还是群聊先做？
- 第一版要不要离线消息？

这不是刁难。**没回答的问题，后面 Stage 拷问会反复撞同一面墙**。早答比晚答省 10 倍时间。

### 真相 2：失败不是错

测试红了 → 修复 → 通过 = 正常流程。

但**用 skip 跳过 = 缺口被隐藏**。套件强制要"功能没实现就 FAIL"。

### 真相 3：审计发现你不想要看的

Round 2 审计（fresh agent，禁读 Round 1）会找到你之前没注意的问题：

- 数值断言被改成"== 0"（无效）
- 实现调用了 config 而不是算法（绿色但假）
- 测试断言的"期望值"是从实现输出回抄的

**审计报告列 P0/P1/P2**：先看 P0，全部修完再走下一轮。

---

## 7. 你不需要懂的事

| 你不需要 | 因为 |
|:--|:--|
| 哪个 agent 该派 | 主 Claude 编排 |
| 怎么写 SRS | `srs-drafter` 写 |
| 怎么写测试 | `test-author` 写 |
| 怎么跑测试 | `test-runner` 跑 |
| 门怎么判 | `gate-checker` 机械判定 |
| 质量怎么审 | `goal-auditor` 双轮审计 |

**你只需要**：回答问题 + 看审计报告 + 在关键路径拍板。

---

## 8. 第一次完整示例（不真跑）

```
用户：我要做一个 TODO CLI
   ↓
goal-architect：
   Q1: 命令名是？(todo)
   Q2: 存储格式？(JSON)
   Q3: 并发安全？(单用户不涉及)
   ...
   [用户答完，goal-doc 落盘]
用户：「确认，下一阶段」
   ↓
[Stage 1] req-interrogator → docs/srs-raw/todo-interrogation.md
[Stage 2] srs-drafter      → docs/srs/todo.md（R-01~R-05）
[Stage 3] design-author    → docs/design/todo.md
[Stage 4] test-author      → tests/test_R*.py + tests/run_todo.py
         test-runner       → FAIL（实现还没写）
         impl-coder        → 改 src/todo.py
         test-runner       → ✅ PASS
[Stage 5] goal-auditor     → 0 P0 → ✅ 交付
```

整个过程你只回答了 3~5 个问题 + 看了 2 份报告。

---

## 9. 故障速查

| 现象 | 原因 | 解决 |
|:--|:--|:--|
| `preflight.sh` 报阻断 | bash/git/awk 缺失 | 装工具；Windows 用 Git Bash |
| 门报"无法判定" | 命令跑不动 | 装缺失工具，或装 back `goal.md` |
| 同一门连续 3 轮失败 | 需求不可行 / 门过严 | 回到 Stage 0 复审 |
| 累计回退 > 10 次 | 门定义矛盾 | 回到 Stage 0 |
| Round 3 仍有 P0 | 实现问题严重 | 升级 — 决定要修还是要改 goal-doc |
| 上下文被压缩 | 主 Claude 上下文归零 | 不影响 —— 读 `docs/loop-status.md` 恢复 |

---

## 10. 你现在该做什么

```bash
# 1. 在 Claude Code 里输入
"我想做一个 <你的项目名>，<一句话描述>"

# 2. 看到 Q&A 后逐项回答

# 3. 看到 goal-doc 后说 "确认，下一阶段"

# 4. 看着它自动跑完
```

**如果不知道做什么项目**：

```
"我想做一个 TODO CLI"
"我想做一个天气预报命令行工具"
"我想做一个记账小程序"
```

从小项目试起。第一个项目跑通 1 次就能掌握整套流程。

---

## 11. 推荐安装方式：全局 + /loopforge 命令（v2.3）

上面 §1 的手动复制是项目级装法。**推荐用全局安装**——装一次，所有项目 `/loopforge` 直接用：

```bash
# 第一步：全局层（一次，所有项目共用）
cd <loopforge 套件目录>
bash scripts/install.sh

# 第二步：项目级注册（每个新项目跑一次）
cd <你的项目>
bash <套件路径>/scripts/loopforge-init.sh
```

**Windows 没装 Git Bash？** 用 PowerShell 版：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <套件路径>\scripts\install.ps1
cd <你的项目>
powershell -NoProfile -ExecutionPolicy Bypass -File <套件路径>\scripts\loopforge-init.ps1
```

> ⚠️ `.ps1` 只解决**安装**。真跑 Loop 时 Goal 门判定命令仍需 bash——
> PowerShell 下单引号 awk 会静默输出空且退出码 0，门看着跑了实际什么都没判。
> 建议还是装 Git for Windows（自带 Git Bash）。

装完可用 5 个命令：

| 命令 | 作用 |
|:--|:--|
| `/loopforge <需求>` | 启动 7 阶段闭环（首跑自动初始化 docs/） |
| `/loopforge-status` | 看进度（只读） |
| `/loopforge-resume` | 会话断了恢复 |
| `/loopforge-help` | 列命令 + 项目状态 |
| `/loopforge-cancel` | 取消（保留全部数据） |

**全局安装不动你的** `~/.claude/commands/` `~/.claude/CLAUDE.md` `~/.claude/settings.json`——不覆盖 Claude Code 原生任何东西。

完整安装/验证/卸载：`INSTALL.md`。命令规范：`docs/commands-spec.md`。

---

读完这份指南，你已经会用 loopforge 了。**最快上手**：装好后 `/loopforge 我要做一个 X`。
