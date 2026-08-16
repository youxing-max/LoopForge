---
name: loopforge-help
description: 列出 Goal Loop 全部可用命令与当前项目状态。
---

输出以下内容：

```
## Goal Loop 命令族

| 命令 | 作用 | 何时用 |
|:--|:--|:--|
| /loopforge <需求> | 启动 7 阶段闭环 | 项目开始 |
| /loopforge-status | 查看进度（只读） | 任何时候 |
| /loopforge-resume | 从中断处恢复 | 上下文压缩/换会话后 |
| /loopforge-cancel | 取消 Loop（保留数据） | 不做了 |

## 本项目状态

<检查并输出：>
- docs/goal.md 存在？ <是/否 — 否则 /loopforge 会自动建>
- docs/goal-doc.md 已确认？ <是/否/未启动>
- Loop 进行中？ <读 docs/loop-status.md 判断>

## 更多文档

- 命令规范：<SKILL_DOCS>/commands-spec.md
- 门定义：docs/goal.md（本项目的，可裁剪）
- 新手上手 / 项目详解：套件源目录的 docs/NEWBIE-GUIDE.md 与 docs/PROJECT-EXPLAINED.md
  （给人读的，不随安装拷贝）
```

`<SKILL_DOCS>` 是 skill 安装目录下的 `docs/`，两种部署模式都能解析：

| 模式 | 路径 |
|:--|:--|
| 全局 | `$HOME/.claude/skills/loopforge/docs/`（Windows: `%USERPROFILE%\.claude\skills\loopforge\docs\`） |
| 本地 | `<项目>/.claude/skills/loopforge/docs/` |

按上面顺序找，先全局后本地；都没有就说"套件文档未安装，跑 install.sh 或 loopforge-init.sh --local"。

## 规则

- 只读。不派 agent 不改文件
- 状态检查失败（文件不存在等）如实报，不要装作有状态
