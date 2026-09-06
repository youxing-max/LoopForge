# LoopForge：Goal 门驱动 + 职责隔离的交付闭环（通用版）


> 版本 v2.3（全局部署 + /loopforge 命令族）· 2026-08-15
> 适用：任何需要「模糊需求 → 项目目标书 → SRS → 设计 → 代码 → 测试 → 验收」闭环的复杂项目
> 🚀 **安装看 [INSTALL.md](INSTALL.md)**（两步 5 分钟）· **新手看 [docs/NEWBIE-GUIDE.md](docs/NEWBIE-GUIDE.md)** · **想搞懂每个文件干啥看 [docs/PROJECT-EXPLAINED.md](docs/PROJECT-EXPLAINED.md)**

## 🛠️ LoopForge · 大白话 5 分钟

> 让 AI 写代码这件事，像工厂流水线一样靠谱

<details>
<summary>📄 <b>点击展开 / 折叠完整图文介绍</b>（移动端友好）</summary>

<div align="center">

# 🛠️ LoopForge
**让 AI 写代码这件事，像工厂流水线一样靠谱**

</div>

---

## 它解决什么问题？

<div align="center">

### AI 写代码 = 不可信

</div>

<table>
<tr>
<td width="50%" bgcolor="#3b1f1f">

😵 **现状痛点：**
- 写代码的 AI 自己测自己 = 自吹自擂
- 测试红了？改断言比改代码快 = 造假
- 代码写完没人盯 = 出问题没人认

</td>
<td width="50%" bgcolor="#0f2e1f">

✅ **LoopForge 的解法：**
- 把"写 / 测 / 审"三件事**锁给三个不同的人**
- 互相看不见对方的工作区

</td>
</tr>
</table>

---

## 🏭 一句话理解

<div align="center">

### 工厂流水线 + 互相不串岗

*像汽车工厂：焊接工、车床工、质检员各管各的，谁也不能抢别人的活。*

</div>

---

## 👥 9 个角色，干 3 件事

<table>
<tr><th colspan="2" align="left">✍️ 写代码的（5 个）</th></tr>
<tr><td><code>goal-architect</code></td><td>目标架构师 · 问清楚你要啥</td></tr>
<tr><td><code>req-interrogator</code></td><td>需求拷问机 · 追问模糊点</td></tr>
<tr><td><code>srs-drafter</code></td><td>需求文档起草员 · 把需求写死</td></tr>
<tr><td><code>design-author</code></td><td>设计文档作者 · 画架构图</td></tr>
<tr><td><code>impl-coder</code></td><td>码农 · 只写 <code>src/</code></td></tr>

<tr><th colspan="2" align="left">📝 写测试的（1 个）</th></tr>
<tr><td><code>test-author</code></td><td>测试员 · 只写 <code>tests/</code></td></tr>

<tr><th colspan="2" align="left">🏃 跑测试的（1 个）</th></tr>
<tr><td><code>test-runner</code></td><td>跑分员 · 只跑不写，汇报事实</td></tr>

<tr><th colspan="2" align="left">🔍 审计的（3 个）</th></tr>
<tr><td><code>gate-checker</code></td><td>门卫 · 机械检查清单 ✓✗</td></tr>
<tr><td><code>goal-auditor</code></td><td>终审 · 双轮独立审计（fresh agent）</td></tr>
<tr><td>主 Claude</td><td>调度员 · 只传话，不干活</td></tr>
</table>

---

## 🔒 锁权限 · 关键一招

<div align="center">

### 🔴 写代码的 <span style="color:#ef4444">跑不了测试</span>
### 🔴 跑测试的 <span style="color:#ef4444">改不了代码</span>
### 🔴 审计的 <span style="color:#ef4444">啥都不能动</span>

</div>

不是靠"道德提醒"，是 **工具菜单直接砍掉**：

| Agent | 允许的 tools | 禁用 |
|:--|:--|:--|
| 码农 `impl-coder` | `Read, Edit, Write, Grep, Glob` | ~~Bash~~ |
| 测试员 `test-author` | `Read, Edit, Write, Grep, Glob` | ~~Bash~~ |
| 跑分员 `test-runner` | `Read, Bash, Grep, Glob` | ~~Edit / Write~~ |
| 终审 `goal-auditor` | `Read, Grep, Glob` | ~~Bash / Edit~~ |

---

## 🔄 流水线长这样

<table align="center">
<tr>
<td align="center">0️⃣<br><b>定目标</b><br><sub>goal.md</sub></td>
<td align="center">➡️</td>
<td align="center">1️⃣<br><b>拷问需求</b><br><sub>req-*</sub></td>
<td align="center">➡️</td>
<td align="center">2️⃣<br><b>写 SRS</b><br><sub>srs-drafter</sub></td>
<td align="center">➡️</td>
<td align="center">3️⃣<br><b>写设计</b><br><sub>design-author</sub></td>
<td align="center">➡️</td>
<td align="center">4️⃣<br><b>写→跑→改</b><br><sub>三方交替</sub></td>
<td align="center">➡️</td>
<td align="center">5️⃣<br><b>双轮审计</b><br><sub>2 个 fresh agent</sub></td>
<td align="center">➡️</td>
<td align="center" bgcolor="#22c55e"><b>✅ 交付</b></td>
</tr>
</table>

> 🚧 **Stage 4 内循环（最核心）：**
>
> `test-author` 写测试 → `test-runner` 跑 → 主 Claude 看报告 → fail 就派 `impl-coder` 改 → 再跑 → 全绿才放行

---

## 🚪 Goal 门 · 每阶段必须过

<table>
<tr>
<td align="center">🚪<br><b>G0</b><br>需求拷问够清</td>
<td align="center">🚪<br><b>G1</b><br>SRS 可机读</td>
<td align="center">🚪<br><b>G2</b><br>设计覆盖全</td>
<td align="center">🚪<br><b>G3</b><br>测试全绿</td>
<td align="center" bgcolor="#3b1f1f">🚨<br><b>G5</b><br>越权检测</td>
<td align="center">🚪<br><b>G4</b><br>双轮审计</td>
</tr>
</table>

> 🚨 **G5 越权门最狠：** 事后 `git diff` 检查有没有人越权。发现 → 本轮作废 → 滚回去重派。

---

## 🆚 对比一下

<table>
<tr>
<td width="50%">

😬 **普通 Claude Code：**
> 一个 AI 写 + 测 + 审 = 自欺欺人

</td>
<td width="50%" bgcolor="#0f2e1f">

😎 **LoopForge：**
> 9 个 AI 各管一摊 + 工具锁死 + 门卫把门 + 双轮审计

</td>
</tr>
</table>

---

## 🎯 适合谁？

<table>
<tr>
<td align="center">✅ 中大型项目</td>
<td align="center">✅ 需求模糊但要交付</td>
<td align="center">✅ 怕 AI 偷懒造假</td>
</tr>
<tr>
<td align="center" bgcolor="#3b1f1f">❌ 一次性脚本</td>
<td align="center" bgcolor="#3b1f1f">❌ 玩具 / MVP 试错</td>
<td align="center" bgcolor="#3b1f1f">❌ 5 分钟小工具</td>
</tr>
</table>

---

## ⏱️ 安装

```bash
bash scripts/install.sh        # 全局层（一次）
bash loopforge-init.sh        # 项目内（每项目一次）
/loopforge 我要做 XXX          # 开跑
```

⚡ **两步 5 分钟装完**

---

## 🎓 一句话总结

<div align="center">

## 不是"提醒 AI 别作弊"
## 而是"让作弊做不到"

</div>

---

📄 完整带样式版已嵌入上方折叠块。

<sub align="center">LoopForge v2.3 · 2026-08-15</sub>

</details>

---

## 快速开始

```bash
# 1. 全局层（一次）
bash scripts/install.sh

# 2. 项目级（每项目一次）
cd <你的项目> && bash <套件路径>/scripts/loopforge-init.sh

# 3. 在 Claude Code 里
/loopforge 我要做一个 TODO CLI
```

Windows 无 Git Bash 时改用 PowerShell 版（`install.ps1` / `loopforge-init.ps1`），见 [INSTALL.md](INSTALL.md)。

命令族：`/loopforge`（启动）· `/loopforge-status`（查进度）· `/loopforge-resume`（恢复）· `/loopforge-help`（帮助）· `/loopforge-cancel`（取消）
规范见 `docs/commands-spec.md`。

## 一、套件组成

```
loopforge/
├── README.md                            ← 本文件
├── INSTALL.md                           ← 两步安装指南
├── commands/                            ← /loopforge 命令族（loopforge-init.sh 装到项目）
│   ├── loopforge.md                          ← /loopforge 启动 7 阶段闭环
│   ├── loopforge-status.md                   ← /loopforge-status 查进度（只读）
│   ├── loopforge-resume.md                   ← /loopforge-resume 从中断恢复
│   ├── loopforge-cancel.md                   ← /loopforge-cancel 取消（保留数据）
│   └── loopforge-help.md                     ← /loopforge-help 列命令
├── docs/
│   ├── PROJECT-EXPLAINED.md             ← 📖 项目详解（每个文件干啥 + 完整流程）
│   ├── NEWBIE-GUIDE.md                  ← 新手指南（11 节）
│   ├── commands-spec.md                 ← /loopforge* 命令完整规范
│   ├── loop-status-spec.md              ← loop-status.md 字段规范
│   ├── goal-template.md                 ← Goal 门模板（Stage 0 复制到项目 docs/loopforge/goal.md）
│   ├── goal-doc-template.md             ← 项目目标书模板（Stage 0.5，含"微信"完整示例）
│   ├── role-permission-matrix.md        ← 🔴 职责隔离契约（先读这个）
│   ├── large-project-guide.md           ← 大型项目实战（批次/契约冻结/变更/并行/成本）
│   ├── legacy-and-migration.md          ← 旧版缺陷说明 + 迁移指南
│   └── settings-permissions.json        ← 权限硬约束参考配置
├── scripts/
│   ├── install.sh / install.ps1         ← 全局层安装（bash / PowerShell 双版）
│   ├── loopforge-init.sh / loopforge-init.ps1     ← 项目级注册（bash / PowerShell 双版）
│   ├── preflight.sh                     ← 跨平台环境自检
│   └── validate_suite.py                ← 套件自校验（L1~L6 六层，含门命令实跑）
├── skills/
│   └── loopforge/SKILL.md        ← 主 Skill（编排 7 阶段 + 回退环）
└── agents/                              ← 9 个单一职责 agent，全带 tools: 白名单
    ├── goal-architect.md                ← 项目目标书（Stage 0.5，多轮 Q&A）
    ├── req-interrogator.md              ← 拷问（只写 docs/loopforge/srs-raw/）
    ├── srs-drafter.md                   ← 起草 SRS（只写 docs/loopforge/srs/）
    ├── design-author.md                 ← 设计文档（只写 docs/loopforge/design/）
    ├── impl-coder.md                    ← 实现（只写 src/，无 Bash）
    ├── test-author.md                   ← 测试开发（只写 loopforge-tests/，无 Bash）
    ├── test-runner.md                   ← 测试执行（无 Edit/Write）
    ├── gate-checker.md                  ← 门机械判定 + 越权检测
    └── goal-auditor.md                  ← 双轮独立审计（无 Bash 无 Edit）
```

## 一之二、套件自校验

套件是规格集不是代码，但设计本身可以测。跑：

```bash
python scripts/validate_suite.py
```

六层检查：

| 层 | 查什么 | 例 |
|:--|:--|:--|
| L1 结构完整性 | 文件齐、frontmatter 合法、无残留旧组件 | `loop-driver` 是否真删了 |
| L2 **权限不变式** | **职责隔离的硬约束是否成立** | 写者持有 Bash 吗、审计者能写吗 |
| L3 引用一致性 | 跨文档引用可解析、无孤岛、**门不引用套件外组件** | 有门要 `gate-checker` 调它没有的 Agent 工具吗 |
| L4 闭环完整性 | 每门有回退、防死循环规则齐、双轮纪律在 | G5.x 越权门是否存在 |
| L5 契约一致性 | 权限矩阵声明 vs frontmatter 实际 | 矩阵说的和文件写的一致吗 |
| L6 **门命令实跑** | **造样例真跑判定命令 + 已修 bug 回归** | 清空验收矩阵，G1.3 真能判 FAIL 吗 |

**L6 是后加的，因为 L1~L5 只查文档结构、从不执行门命令** —— 四个 bug 藏在这个盲区里，包括一条无解死锁（G1.2 要求验收口径写命令、G1.4 禁止出现代码路径，而验收命令必然含代码路径）和一条恒真假绿（验收矩阵清空也 PASS）。

**L2 的判据被独立审计推翻过一次**：原来写的是"写者/执行者/审计者三集合互不相交"，审计员穷举 7 种工具的全部 128 个子集证明它**恒真** —— 按那个定义三个桶天然互斥，不管 frontmatter 怎么写都 PASS，零证据价值。现改为逐角色断言 + 具体角色两两不同体。

跑一次应全绿。**不写死项数** —— 加减检查项后写死的数字必然失真（这条本身也是一个检查项 R3.7）。

## 二、v2.1 核心：职责隔离

**写代码 / 跑测试 / 审计 —— 三者永不同体**。不是靠 prompt 提醒，是靠 `tools:` 白名单让它**做不到**。

| 违规组合 | 失效方式 | 隔离手段 |
|:--|:--|:--|
| 写代码 + 跑测试 | 测试红了，改断言比改代码容易 | `impl-coder` **无 Bash**，看不到红绿 |
| 写测试 + 跑测试 | 断言凑不绿，调容差/加 skip | `test-author` **无 Bash**，同上 |
| 跑测试 + 改代码 | "顺手修一下"，报告不可信 | `test-runner` **无 Edit/Write** |
| 审计 + 改代码 | 审自己的修复，自证自洽 | `goal-auditor` **无 Bash 无 Edit** |
| 自检 + 终审 | 自检印象污染终审 | `gate-checker`（机械）与 `goal-auditor`（判断）分属两个 agent |

**主 Claude 也被收权**：只编排、路由、维护状态表，不直接改 `src/` `loopforge-tests/`，不跑 pytest。它上下文里塞满历史，最容易"我知道这里没问题"。

**四层防线**：

| 层 | 手段 | 强度 |
|:--|:--|:--|
| L1 | agent frontmatter `tools:` 白名单 | 硬（harness 强制） |
| L2 | settings.json `permissions.deny` | 硬（防 Bash 绕过） |
| L3 | agent 文档红线条款 | 软（靠自觉） |
| L4 | `gate-checker` G5.x git diff 事后检测 | 硬（**唯一不依赖自觉的关卡**） |

## 三、版本演进

| 维度 | v1.0 | v2.0 | v2.1 | **v2.2（本版）** |
|:--|:--|:--|:--|:--|
| 阶段数 | 5 | 6（加 Stage 0 定门） | 6 | **7（加 Stage 0.5 项目目标书）** |
| 循环范围 | 只有 Stage 4 内循环 | 全阶段 Goal 驱动回退 | 同 v2.0 | 同 v2.1 |
| 判据位置 | 散在各阶段 | 集中 `docs/loopforge/goal.md` | 同 v2.0 | 同 v2.1 |
| **目标书** | ❌ | ❌ | ❌ | ✅ **`docs/loopforge/goal-doc.md` + `goal-architect` agent** |
| **职责隔离** | ❌ | ❌ | ✅ 8 个 agent | ✅ **9 个 agent + tools 白名单** |
| **主 Claude 权限** | 编排 + 写代码 | 同左 | ✅ 纯编排 | ✅ 纯编排（含 goal-doc 落盘） |
| **越权检测** | 无 | 无 | ✅ G5.1~G5.6 | ✅ G5.1~G5.6 + G0.5~G0.7 |
| goal-auditor | 兼任自检 + 终审 | 同左 | ✅ 拆出 gate-checker | 同 v2.1 |

**v2.1 删掉了 `loop-driver`** —— 它一个 agent 既调 develop-tests 生成测试，又调 phase-verify 跑测试，正是要禁的组合。Stage 4 改由主 Claude 编排 `test-author` ↔ `test-runner` ↔ `impl-coder` 三方交替。

> 各版本缺陷的完整说明（每个违规点为什么是问题、怎么修的）+ 迁移步骤：见 **[`docs/legacy-and-migration.md`](docs/legacy-and-migration.md)**。
> 里面还有一节「不要改回去的东西」——列出七种会退回旧版缺陷的"简化"，每条都有自校验项兜底。

## 四、四条铁律

1. **失败可见**：功能没实现就让它 FAIL，不 skip
2. **职责隔离**：写代码 / 跑测试 / 审计 三者永不同体
3. **作者不审自己**：审计用 fresh agent，Round 2 禁读 Round 1
4. **门可判定**：完成 = 可机器检查，不凭感觉

## 五、6 阶段 + 回退环

```
Stage 0  定 Goal 门        主 Claude + 用户 → docs/loopforge/goal.md
   ↓
Stage 1  拷问              req-interrogator
   ↓ gate-checker 判 G0.x ──不过──> 回 Stage 1
Stage 2  起草 SRS          srs-drafter
   ↓ gate-checker 判 G1.x ──不过──> 回 Stage 2 / 1
Stage 3  设计文档          design-author
   ↓ gate-checker 判 G2.x ──不过──> 回 Stage 3 / 2
Stage 4  Loop（三方交替）   test-author ↔ test-runner ↔ impl-coder
   ↓ gate-checker 判 G3.x + G5.x ──不过──> 回 Stage 4 / 3
Stage 5  双轮独立审计      goal-auditor ×2（Round 2 禁读 Round 1）
   ↓ gate-checker 判 G4.x ──不过──> 回 Stage 4
✅ 交付
```

### Stage 4 内循环（职责隔离的核心）

```
  [1] test-author   写测试        （无 Bash，交不出运行结果）
       ↓
  [2] test-runner   跑测试报事实  （无 Edit，改不了任何东西）
       ↓
  [3] 主 Claude 读报告 → 只做路由
       ├── [GAP]/[FAIL]  → [4] impl-coder 改 src/ → 回 [2]
       ├── 弱断言/可疑skip → 回 [1] test-author → 回 [2]
       └── 全绿 → [5]
  [5] gate-checker  判 G3.x + G5.x 越权检测
```

## 六、Goal 门骨架

| 门 | 阶段 | 内容 | 不过 → 回退 |
|:--|:--|:--|:--|
| G0.1~G0.3 | 1 拷问 | 6 维度全覆盖 / 模糊度达标 / 冲突已裁决 | Stage 1 |
| G1.1~G1.5 | 2 SRS | 三层级 / 可机读验收口径 / 验收矩阵 / 纯度 / 优先级 | Stage 2 |
| G2.1~G2.5 | 3 设计 | 引用单向性 / 内部一致 / 纯度 / R-XX 全覆盖 / 接口签名 | Stage 3 |
| G3.1~G3.5 | 4 Loop | 测试全绿 / 零可疑 skip / 零弱断言 / 回归 / 类型干净 | Stage 4 |
| **G5.1~G5.6** | **全阶段** | **角色越权检测（git diff）** | **结果作废重派** |
| G4.1~G4.3 | 5 审计 | Round 1 完成 / P0P1 全修 / Round 2 无 P0P1 | Stage 4 |

**全绿 = 唯一交付条件**。

## 七、防死循环 + 越权处置

| 情况 | 处理 |
|:--|:--|
| 同一门连续 3 轮不过 | 停自动回退，升级给人 |
| 累计回退 > 10 次 | 回 Stage 0 复审门是否过严/矛盾 |
| 两门互相拉扯 | 标"门冲突"，回 Stage 0 裁决优先级 |
| **G5.x 检出越权** | **本轮结果作废** → 回滚 → 重派正确角色 → 记 loop-status |
| 同一 agent 二次越权 | 停止，人工检查 `tools:` 是否真生效 |
| Round 3 仍有 P0 | 升级给人 |

## 八、安装

```bash
# 1. skill + agent
cp -r loopforge/skills/*  <项目>/.claude/skills/
cp -r loopforge/agents/*  <项目>/.claude/agents/

# 2. Goal 门模板 + 权限契约 + 脚本
mkdir -p <项目>/docs/loopforge
cp loopforge/docs/goal-template.md          <项目>/docs/loopforge/goal.md
cp loopforge/docs/role-permission-matrix.md <项目>/docs/
cp -r loopforge/scripts                     <项目>/

# 3. 🔴 先跑环境自检（三平台通用，0 阻断项才继续）
bash scripts/preflight.sh

# 4. 权限硬约束（第二层保险，可选但建议）
#    参考 loopforge/docs/settings-permissions.json
#    把 permissions 块合并进 <项目>/.claude/settings.json（删掉 _ 开头的说明键）

# 5. 验证白名单生效
grep -l "^tools:" <项目>/.claude/agents/*.md   # 应列出全部 8 个
```

### 平台兼容

三平台（Windows Git Bash / macOS / Linux）通用，但有前提：

| 平台 | 注意 |
|:--|:--|
| **全平台** | 判定命令**必须走 `bash -c`**。cmd.exe/PowerShell 下单引号 awk 会静默输出空且退出码 0——门看起来跑了，实际什么都没判 |
| **Windows** | `git config core.autocrlf false`，否则换行符转换让 `git status` 报大量非实际改动，干扰 G5.x 越权判定 |
| **macOS** | 用 BSD 工具。判定命令刻意不用 `grep -P`（BSD 无）、不用 `md5sum`（macOS 无，用 `shasum`）、不用 `bc`（Git Bash 无） |

`scripts/preflight.sh` 会把这些逐条测出来——包括平台识别、工具方言、git 配置、路径变量互为前缀（Maven 布局   致命组合）、以及实跑一条真判据冒烟。

### 大型项目（0 → 1 从零开发）

单需求 Loop 撑不住上百条需求、跨月、多人的项目。见 **[`docs/large-project-guide.md`](docs/large-project-guide.md)**：

- **批次调度** —— 按子系统切，批次 0 永远是契约，依赖批次全绿才开工
- **需求编号分段** —— `R-001~R-999` 按域分段，否则上百条必撞号
- **Runner 分层** —— smoke(<30s) / batch(<5min) / full，全量跑不动
- **两条追加门** —— G0.4 契约未破坏、G3.7 跨批回归
- **多批次状态** —— 一批一份 `loop-status/batch-X.md`
- **变更流程** —— 改已完成批次要返工，改契约最贵
- **跨会话恢复** —— 四份文件是唯一事实来源，不靠上下文记忆
- **成本预估** —— 一个批次 20~35 次 agent 调用，附轻量档裁剪方案

> **注意**：本套件不自带 `develop-tests` / `phase-verify` / `req-design-verifier` skill。v2.1 已把它们的职责拆进 `test-author` / `test-runner` / `design-author` + `gate-checker`，可直接用；若你想复用 KH OFDR 原套件的那三个 skill，注意它们**不满足职责隔离**（develop-tests 内含 code-reviewer 调用，phase-verify 内含物理审查调用），需要拆分后再用。

## 九、职责隔离自查（每轮 Stage 4 结束）

- [ ] 本轮改 `src/` 的是 `impl-coder`？（不是主 Claude、不是 test-author）
- [ ] 本轮改 `loopforge-tests/` 的是 `test-author`？（不是 impl-coder）
- [ ] 本轮跑测试的是 `test-runner`？（不是写代码那个）
- [ ] `git diff` 改动范围与派工职责一致？
- [ ] `goal-auditor` 这轮调用过 Bash 吗？（应该零——它没这工具）

任一项否 → 记越权事件，本轮结果作废重跑。

## 十、移植适配清单

| KH OFDR 专属 | 改成你的项目 |
|:--|:--|
| `docs/loopforge/srs/` `docs/loopforge/design/` `docs/loopforge/audit/` | 你团队的文档目录约定 |
| 6 组验证 runner | 你的子系统分组（frontend/backend/db/infra） |
| physics-* agent | 你领域的审查 agent（security / api / sql / ...） |
| `loopforge-tests/run_<组>.py` | 你的测试栈入口 |
| SRS 编号 R-XX | 你的需求编号体系 |
| Goal 门细节 | Stage 0 逐条裁剪 + 加项目专属门 |
| **G5.x 路径规则** | **改成你的实际目录（`src/` `loopforge-tests/` 若不同名必须同步改）** |

**建议加的项目专属门**：

| 项目类型 | 建议门 |
|:--|:--|
| Web 后端 | API 契约冻结 / SLA 压测 / 注入扫描 |
| 数据处理 | 数据血缘 / Schema 演进 / 幂等性 |
| 嵌入式 | ROM/RAM 占用 / 中断延迟 / 掉电恢复 |
| 桌面应用 | 跨平台兼容 / 安装包大小 / 冷启动 |
| AI/ML | 模型版本冻结 / 推理延迟 / 偏差检测 |

## 十一、适用判断

**适合**：中大型复杂项目 / 有明确需求文档 / 需交付质量门 / 多人协作 / 强可验证领域（后端·CLI·数据·嵌入式·算法）

**不适合**：一次性脚本 / 玩具项目 / MVP 试错期（需求变太快）/ 纯主观审美类项目

## 十二、出处

- 本套件 v2.1 · 2026-08-09
- 基于 KH OFDR 套件 v1.3 → v2.0 Goal 驱动改造 → v2.1 职责隔离改造
- 理论依据：`../docs/proactive-skill-system.md`（Skill 双面性）
- 原套件：`../`（同级目录）
