---
name: loopforge-resume
description: 从 loop-status 恢复 Goal Loop（上下文压缩/会话中断后）。
---

按顺序读四份文件恢复状态（缺一不可，缺了如实报）：

```
1. docs/goal-doc.md          → 项目目标（做什么）
2. docs/goal.md              → 门定义（怎么算完成）
3. docs/loop-status.md       → 当前进度（卡在哪）
4. docs/change-log.md        → 变更记录（如有）
```

## 恢复步骤

1. 读上述文件
2. 向用户报告：
   ```
   ## 恢复上下文
   - 项目：<一句话定义 from goal-doc §0>
   - 上次停在：Stage <N>，第 <round> 轮
   - 阻塞中：<门 + 原因>
   - 下一步原计划：<loop-status 的"下一步"字段>
   ```
3. **问用户**："继续执行下一步，还是先做别的？" —— 等确认
4. 用户确认后，按 SKILL.md 从当前 stage 接续编排

## 规则

- 不跳过中间阶段（即使状态显示某阶段已完成，若 gate-checker 没跑过判定记录，重跑）
- 不信任对话记忆，只信任文件
- 若 loop-status.md 的 DISPATCH 块显示有 agent 改动未检查（git status 非空），先跑 G5.x 越权检测再继续
