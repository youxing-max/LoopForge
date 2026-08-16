#!/usr/bin/env bash
# loopforge 全局层安装 —— skill + agents 装到 ~/.claude/，所有项目可用
# 用法: bash install.sh
# 退出码: 0 成功 / 1 失败
set -eu

SRC="$(cd "$(dirname "$0")/.." && pwd)"
DST="${HOME}/.claude"

# ── 前置检查 ──
[ -d "$SRC/skills/loopforge" ] || { echo "❌ 找不到 $SRC/skills/loopforge"; exit 1; }
[ -d "$SRC/agents" ]                  || { echo "❌ 找不到 $SRC/agents"; exit 1; }
AGENT_COUNT=$(ls "$SRC/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$AGENT_COUNT" -eq 9 ]              || { echo "❌ agents/ 应有 9 个文件，实际 $AGENT_COUNT"; exit 1; }
CMD_COUNT=$(ls "$SRC/commands/"loopforge*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$CMD_COUNT" -eq 5 ]                || { echo "❌ commands/ 应有 5 个 loopforge*.md（loopforge-init.sh 依赖），实际 $CMD_COUNT"; exit 1; }

# 运行时驱动文档 —— 缺一份，全局模式下 agent 读不到就会自己编内容
DRIVER_DOCS="goal-template.md goal-doc-template.md role-permission-matrix.md
             commands-spec.md loop-status-spec.md large-project-guide.md"
for doc in $DRIVER_DOCS; do
  [ -f "$SRC/docs/$doc" ] || { echo "❌ 缺驱动文档 docs/$doc —— 套件不完整，重新下载"; exit 1; }
done

# ── 安装 ──
mkdir -p "$DST/skills" "$DST/agents"

# skill：先删旧版再拷（避免残留过期文件）
rm -rf "$DST/skills/loopforge"
cp -r "$SRC/skills/loopforge" "$DST/skills/"

# 驱动文档带进 skill 目录的 docs/ 子目录 ——
# SKILL.md 与 agents 里写的是相对路径 docs/xxx.md，装到 skill 根会对不上
mkdir -p "$DST/skills/loopforge/docs"
for doc in $DRIVER_DOCS; do
  cp "$SRC/docs/$doc" "$DST/skills/loopforge/docs/"
done

# agents：逐个覆盖
cp "$SRC"/agents/*.md "$DST/agents/"

# ── 验证 ──
# 只数本套件的 9 个，不数目标目录里的全部 agent ——
# 用户 ~/.claude/agents/ 里可能已有别的 agent，全量计数会把装漏也撑成"看着对"
INSTALLED_AGENTS=0
for f in "$SRC"/agents/*.md; do
  [ -f "$DST/agents/$(basename "$f")" ] && INSTALLED_AGENTS=$((INSTALLED_AGENTS+1))
done
[ "$INSTALLED_AGENTS" -eq 9 ] || { echo "❌ agent 装漏: $INSTALLED_AGENTS/9"; exit 1; }
[ -f "$DST/skills/loopforge/SKILL.md" ] || { echo "❌ SKILL.md 未装上"; exit 1; }
# 驱动文档逐个确认——少一份，运行时 agent 读不到就会自己编
for doc in $DRIVER_DOCS; do
  [ -f "$DST/skills/loopforge/docs/$doc" ] || { echo "❌ 驱动文档未装上: $doc"; exit 1; }
done

echo "✅ 全局层已装到 $DST"
echo "   skill : $DST/skills/loopforge/"
echo "   docs  : $DST/skills/loopforge/docs/ (6 份驱动文档)"
echo "   agents: $DST/agents/ (本套件 $INSTALLED_AGENTS 个)"
echo ""
echo "下一步：到每个项目目录跑 loopforge-init.sh 注册 /loopforge 命令族"
