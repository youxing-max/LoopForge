# LoopForge

> **Goal 门驱动 + 职责隔离的 AI 交付闭环**——让 Claude Code 把「模糊需求 → 项目目标书 → SRS → 设计 → 代码 → 测试 → 验收」跑成一条人能验收、机器能判定的流水线。v2.3 · 2026-08-15。

适用：任何中大型复杂项目，需求不一次性脚本、玩具、MVP 试错期。

## 这是什么

一套装在 Claude Code 里的 **7 阶段交付闭环**，由一条 `/loopforge` 命令驱动。核心不是 prompt 提醒 agent「别作弊」，而是用 `tools:` 白名单 + `permissions.deny` + git diff 事后检测，**让越权做不到**：写代码的看不到测试红绿，跑测试的改不了代码，审计的既不能跑也不能改。

```
Stage 0   定 Goal 门         主 Claude + 用户 → docs/loopforge/goal.md
Stage 0.5 项目目标书          goal-architect（多轮 Q&A）
Stage 1   拷问                req-interrogator  → G0.x
Stage 2   起草 SRS            srs-drafter       → G1.x
Stage 3   设计文档            design-author     → G2.x
Stage 4   Loop（三方交替）    test-author ↔ test-runner ↔ impl-coder → G3.x + G5.x
Stage 5   双轮独立审计        goal-auditor ×2（Round 2 禁读 Round 1）→ G4.x
✅ 交付 = 全绿
```

任一门不过自动回退到对应阶段；同一门连 3 轮不过升级给人。

## 四条铁律

1. **失败可见**——功能没实现就 FAIL，不 skip，缺口可见才能被修。
2. **职责隔离**——写代码 / 跑测试 / 审计 三者永不同体（靠 `tools:` 白名单硬约束，不靠自觉）。
3. **作者不审自己**——审计用 fresh agent，Round 2 禁读 Round 1，防自我维护偏差。
4. **门可判定**——完成 = 可机器检查的命令 + 预期，不凭感觉。

## 装（两步 5 分钟）

```bash
# 1. 全局层（一次）
bash scripts/install.sh          # Windows 无 Git Bash 用 install.ps1

# 2. 项目级（每项目一次）
cd <你的项目> && bash <套件路径>/scripts/loopforge-init.sh

# 3. 在 Claude Code 里
/loopforge 我要做一个 TODO CLI
```

命令族：`/loopforge`（启动）· `/loopforge-status`（查进度）· `/loopforge-resume`（恢复）· `/loopforge-help`· `/loopforge-cancel`。

两套脚本（`.sh` / `.ps1`）覆盖 macOS / Linux / Windows Git Bash / PowerShell。三平台通用，但门判定命令**必须走 `bash -c`**——cmd.exe/PowerShell 下单引号 awk 静默输出空且退出码 0，门看着跑了实际什么都没判。`scripts/preflight.sh` 把这条和平台方言逐条测出来。

详见 [INSTALL.md](INSTALL.md)。

## 包内容

```
loopforge/
├── commands/        /loopforge 命令族（loopforge-init 装到项目）
├── skills/loopforge/ 主 Skill（编排 7 阶段 + 回退环）
├── agents/           9 个单一职责 agent，全带 tools: 白名单
│   ├── goal-architect     项目目标书（Stage 0.5）
│   ├── req-interrogator   拷问（只写 docs/loopforge/srs-raw/）
│   ├── srs-drafter        起草 SRS（只写 docs/loopforge/srs/）
│   ├── design-author      设计文档（只写 docs/loopforge/design/）
│   ├── impl-coder         实现（只写 src/，无 Bash）
│   ├── test-author        测试开发（只写 loopforge-tests/，无 Bash）
│   ├── test-runner        测试执行（无 Edit/Write）
│   ├── gate-checker       门机械判定 + 越权检测
│   └── goal-auditor       双轮独立审计（无 Bash 无 Edit）
├── scripts/         install / loopforge-init / preflight / validate_suite.py
└── docs/            详解、新手指南、命令规范、权限矩阵、大项目指南、迁移
```

## 跑自校验（套件是规格不是代码，但设计本身可测）

```bash
python scripts/validate_suite.py
```

六层：L1 结构 / **L2 权限不变式** / L3 引用一致 / L4 闭环完整 / L5 契约一致 / **L6 门命令实跑**。跑一次应全绿——不写死项数，加减检查后写死数字必然失真。

L2 的判据被独立审计推翻过一次：原写「三集合互斥」，审计员穷举 128 个子集证明**恒真**——按那个定义三桶天然互斥，不管 frontmatter 怎么写都 PASS，零证据价值。现改逐角色断言 + 两两不同体。这是这套件审自己的方式落到代码上的证据。

## 版本演进

| 维度 | v1.0 | v2.0 | v2.1 | v2.2→v2.3 |
|:--|:--|:--|:--|:--|
| 阶段数 | 5 | 6 | 6 | **7（加 Stage 0.5 项目目标书）** |
| 职责隔离 | ❌ | ❌ | ✅ 8 agent | ✅ **9 agent + tools 白名单** |
| 主 Claude 权限 | 编排+写代码 | 同 | ✅ 纯编排 | ✅ 纯编排 |
| 越权检测 | 无 | 无 | ✅ G5.1~G5.6 | ✅ +G0.5~G0.7 |
| 项目目标书 | ❌ | ❌ | ❌ | ✅ goal-doc.md + goal-architect |

v2.1 删掉了 `loop-driver`——它一个 agent 既生成测试又跑测试，正是要禁的组合。Stage 4 改主 Claude 编排 test-author ↔ test-runner ↔ impl-coder 三方交替。

各版本缺陷与迁移：[docs/legacy-and-migration.md](docs/legacy-and-migration.md)，含「不要改回去的七种简化」。

## 出处

- 基于 KH OFDR 套件 v1.3 → v2.0 Goal 驱动 → v2.1 职责隔离 → v2.2 项目目标书
- 理论依据：`docs/proactive-skill-system.md`（Skill 流程/验证两面性）
- 上游原套件：同级 `../`（验证闭环 Skill + Agent 分享）

## 不适合

一次性脚本 / 玩具 / MVP 试错期（需求变太快）/ 纯主观审美类项目。
