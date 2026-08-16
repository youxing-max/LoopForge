---
name: loopforge
description: 启动 Goal 门驱动的 7 阶段闭环（loopforge）。首次运行自动初始化项目目录。
---

用户输入 `/loopforge $ARGUMENTS`。$ARGUMENTS 是模糊需求（如"做一个 TODO CLI"）。

**如果 $ARGUMENTS 为空**：询问用户想做什么项目，不要猜测。

## 执行步骤

0. **解析 skill 根目录**（后续步骤都依赖它）：

   ```
   优先 $HOME/.claude/skills/loopforge/          ← 全局安装
   其次 <当前项目>/.claude/skills/loopforge/     ← 项目级安装（loopforge-init --local）
   两处都无 SKILL.md → 报错并指引 install.sh，不要继续
   ```

   bash 下用 `$HOME`，**不要用 `~`**（部分调用方不展开）。
   Windows 的 PowerShell/cmd 环境下同一目录写作 `%USERPROFILE%\.claude\skills\loopforge\`。
   下文 `<SKILL>` 指该目录。套件文档在 `<SKILL>/docs/`，
   **项目文档在 `<当前项目>/docs/`，两者不是一回事**。

1. **初始化检查**（首次运行自动做，已初始化则跳过）：

   ```bash
   mkdir -p docs
   test -f docs/goal.md        || cp <SKILL>/docs/goal-template.md docs/goal.md
   test -f docs/goal-doc.md    || echo "(待 goal-architect 填)" > docs/goal-doc.md
   git rev-parse --git-dir >/dev/null 2>&1 || echo "⚠️ 非 git 仓库，G5.x 越权检测失效"
   test -f .gitignore || printf '__pycache__/\n*.pyc\ntarget/\nnode_modules/\n.pytest_cache/\n' > .gitignore
   ```

2. **加载编排手册**：读 `<SKILL>/SKILL.md`，按它编排后续所有阶段。

3. **启动 Stage 0.5**：按 SKILL.md §三之一 派 `goal-architect` agent，传入用户的模糊需求。

4. **Q&A 循环**：goal-architect 返回 `[WAITING FOR USER]` 时，直接呈现给用户并等待回答。用户回答后再次派 goal-architect 修订。循环直到用户说"确认，下一阶段"。

5. **后续阶段**：goal-doc 确认后，按 SKILL.md 编排 Stage 1~5，每阶段退出调 gate-checker。

## 约束

- 不跳过用户审查
- 不替用户拍板
- 每阶段退出必须跑 gate-checker
- 中断后恢复用 `/loopforge-resume`
