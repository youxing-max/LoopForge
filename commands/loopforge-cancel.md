---
name: loopforge-cancel
description: 取消当前 Goal Loop（标记状态，不回滚数据）。
---

## 执行

1. 向用户确认："确定取消？当前进度会保留在文件里，但 Loop 停止编排。"
2. 用户确认后，在 `docs/loopforge/loop-status.md` 顶部追加：

   ```markdown
   > ⛔ **CANCELLED** — <日期> — 原因：<用户给的或"用户要求">
   > 后续若要重启，用 `/loopforge-resume`（会询问是否重新激活）。
   ```

3. 输出取消摘要：已完成阶段 / 未完成阶段 / 保留的文件清单。

## 规则

- **不删除任何文件**。src/ loopforge-tests/ docs/ 全保留——用户决定去留
- **不回滚 git**。如需回滚用户自己操作
- 取消后 Loop 停止。若 goal-architect 正在 Q&A 循环中，告知用户直接不再回答即可
