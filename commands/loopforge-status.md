---
name: loopforge-status
description: 查看 Goal Loop 当前进度（只读，不做编排操作）。
---

读 `<cwd>/docs/loop-status.md`，按以下格式输出摘要：

```
## Goal Loop 状态

当前阶段：<Stage N 名称>
当前轮次：<round>
当前阻塞：<门号 + 原因（如有）>
下一步：<派工计划>

### 门判定历史
<表格：门 | 状态 | 连续不过次数>

### 计数器
累计回退：N / 10
越权事件：N 件

### 最近派工
<DISPATCH 块内容>
```

## 规则

- **只读**。不派 agent、不改文件、不推进 Loop
- 若 `docs/loop-status.md` 不存在：输出"Goal Loop 尚未启动。用 `/loopforge <需求>` 启动"
- 若存在多个批次状态文件（`docs/loop-status/batch-*.md`）：列出全部批次 + 询问用户看哪个
