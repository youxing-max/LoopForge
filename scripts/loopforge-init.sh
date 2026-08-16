#!/usr/bin/env bash
# loopforge 项目级注册 —— 把 /loopforge 命令族装到 <当前项目>/.claude/commands/
#
# 用法:
#   cd <你的项目> && bash <path-to>/scripts/loopforge-init.sh
#       只装命令，依赖已装好的全局层（~/.claude/skills/loopforge）
#
#   cd <你的项目> && bash <path-to>/scripts/loopforge-init.sh --local
#       整套装进本项目（skill + agents + 套件文档 + 命令），不依赖全局层
#       适合：不想污染 ~/.claude、或每个项目要用不同版本
#
# 退出码: 0 成功 / 1 失败
set -eu

SRC="$(cd "$(dirname "$0")/.." && pwd)"
PROJ="$(pwd)"
LOCAL_MODE=0
[ "${1:-}" = "--local" ] && LOCAL_MODE=1

DRIVER_DOCS="goal-template.md goal-doc-template.md role-permission-matrix.md
             commands-spec.md loop-status-spec.md large-project-guide.md"

# ── 前置检查 ──
[ -d "$SRC/commands" ] || { echo "❌ 找不到 $SRC/commands"; exit 1; }
CMD_COUNT=$(ls "$SRC/commands/"loopforge*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$CMD_COUNT" -eq 5 ] || { echo "❌ commands/ 应有 5 个 loopforge*.md，实际 $CMD_COUNT"; exit 1; }
for f in "$SRC/commands/"loopforge*.md; do
  FIRST_LINE=$(grep -m1 -v '^[[:space:]]*$' "$f" | tr -d '\r' || true)
  [ "$FIRST_LINE" = "---" ] || { echo "❌ $f 首个非空行不是 ---（frontmatter 损坏）"; exit 1; }
  grep -q '^name:' "$f" || { echo "❌ $f 缺少 name: 行（frontmatter 损坏）"; exit 1; }
done

if [ "$LOCAL_MODE" -eq 1 ]; then
  # ── 本地模式：整套装进项目 ──
  AGENT_COUNT=$(ls "$SRC/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
  [ "$AGENT_COUNT" -eq 9 ] || { echo "❌ agents/ 应有 9 个文件，实际 $AGENT_COUNT"; exit 1; }
  for doc in $DRIVER_DOCS; do
    [ -f "$SRC/docs/$doc" ] || { echo "❌ 缺驱动文档 docs/$doc —— 套件不完整"; exit 1; }
  done

  mkdir -p "$PROJ/.claude/skills" "$PROJ/.claude/agents"
  rm -rf "$PROJ/.claude/skills/loopforge"
  cp -r "$SRC/skills/loopforge" "$PROJ/.claude/skills/"
  mkdir -p "$PROJ/.claude/skills/loopforge/docs"
  for doc in $DRIVER_DOCS; do
    cp "$SRC/docs/$doc" "$PROJ/.claude/skills/loopforge/docs/"
  done
  cp "$SRC"/agents/*.md "$PROJ/.claude/agents/"
  SKILL_LOC="$PROJ/.claude/skills/loopforge"
else
  # ── 默认模式：依赖全局层 ──
  SKILL_LOC="${HOME}/.claude/skills/loopforge"
  [ -f "$SKILL_LOC/SKILL.md" ] || {
    echo "❌ 全局层未安装（$SKILL_LOC/SKILL.md 不存在）"
    echo ""
    echo "   两个选择："
    echo "   1) 装全局层（推荐，所有项目共用）: bash $SRC/scripts/install.sh"
    echo "   2) 整套装进本项目（不碰 ~/.claude）: bash $SRC/scripts/loopforge-init.sh --local"
    exit 1
  }
fi

# ── 注册命令 ──
mkdir -p "$PROJ/.claude/commands"
cp "$SRC"/commands/loopforge*.md "$PROJ/.claude/commands/"

# ── 验证 ──
# 逐个确认本套件的 5 个都到位，不数目标目录的 loopforge*.md 总数 ——
# 用户可能已有自己的命令，全量计数会误报失败
INSTALLED=0
for f in "$SRC"/commands/loopforge*.md; do
  [ -f "$PROJ/.claude/commands/$(basename "$f")" ] && INSTALLED=$((INSTALLED+1))
done
[ "$INSTALLED" -eq 5 ] || { echo "❌ 注册不完整: $INSTALLED/5"; exit 1; }

if [ "$LOCAL_MODE" -eq 1 ]; then
  for doc in $DRIVER_DOCS; do
    [ -f "$SKILL_LOC/docs/$doc" ] || { echo "❌ 驱动文档未装上: $doc"; exit 1; }
  done
  LOCAL_AGENTS=0
  for f in "$SRC"/agents/*.md; do
    [ -f "$PROJ/.claude/agents/$(basename "$f")" ] && LOCAL_AGENTS=$((LOCAL_AGENTS+1))
  done
  [ "$LOCAL_AGENTS" -eq 9 ] || { echo "❌ agent 装漏: $LOCAL_AGENTS/9"; exit 1; }
  echo "✅ 整套已装进本项目（本地模式，不依赖全局层）"
  echo "   skill : $PROJ/.claude/skills/loopforge/"
  echo "   docs  : $PROJ/.claude/skills/loopforge/docs/ (6 份)"
  echo "   agents: $PROJ/.claude/agents/ (9 个)"
else
  echo "✅ /loopforge 命令族已注册（用全局层的 skill 与 agents）"
  echo "   skill : $SKILL_LOC/"
fi
echo "   命令  : $PROJ/.claude/commands/"
echo ""
echo "可用命令："
for f in "$SRC"/commands/loopforge*.md; do
  echo "   /$(basename "$f" .md)"
done
echo ""
echo "开始: /loopforge <你的模糊需求>"
echo ""
echo "开始: /loopforge <你的模糊需求>"
