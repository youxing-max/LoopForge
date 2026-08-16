#!/usr/bin/env bash
# 跨平台环境自检 —— Stage 0 之前跑，确认这套 Goal 门在你机器上能真跑
#
# 用法: bash scripts/preflight.sh [项目根目录]
# 退出码: 0=可用 / 1=有阻断项
#
# 背景：门判定命令大量用 awk/grep/git。三个平台的差异会让门"静默失效"——
# 不报错，只是永远判不出问题。这个脚本就是把静默失效变成显式报错。

set -u
ROOT="${1:-.}"
cd "$ROOT" || exit 1

FAIL=0
WARN=0

say()  { printf '%s\n' "$*"; }
ok()   { printf '  ✅ %s\n' "$*"; }
bad()  { printf '  ❌ %s\n' "$*"; FAIL=$((FAIL+1)); }
warn() { printf '  ⚠️  %s\n' "$*"; WARN=$((WARN+1)); }

say ""
say "loopforge 环境自检"
say "========================================"

# ── 1. 平台识别 ──
say ""
say "[1] 平台"
UNAME="$(uname -s 2>/dev/null || echo unknown)"
case "$UNAME" in
  Linux*)             PLAT=linux ;;
  Darwin*)            PLAT=macos ;;
  MINGW*|MSYS*|CYGWIN*) PLAT=windows ;;
  *)                  PLAT=unknown ;;
esac
say "  平台: $PLAT ($UNAME)"
[ "$PLAT" = unknown ] && warn "无法识别平台，后续检查可能不准"

# ── 2. shell ──
say ""
say "[2] Shell"
if [ -n "${BASH_VERSION:-}" ]; then
  ok "bash $BASH_VERSION"
else
  bad "不是 bash。门判定命令含单引号 awk 程序，cmd.exe/PowerShell 下会静默输出空且退出码 0"
fi

# ── 3. 必需命令 ──
say ""
say "[3] 必需命令"
for c in awk grep sed git sort cut wc comm find xargs; do
  if command -v "$c" >/dev/null 2>&1; then
    ok "$c"
  else
    bad "$c 缺失 —— 门判定命令依赖它"
  fi
done

# hash 工具：三平台名字不同
if command -v shasum >/dev/null 2>&1; then
  ok "shasum（非 git 仓库快照用）"
elif command -v sha1sum >/dev/null 2>&1; then
  ok "sha1sum（非 git 仓库快照用）"
else
  warn "无 shasum/sha1sum —— 非 git 仓库的快照方案不可用（git 仓库不受影响）"
fi

# ── 4. GNU vs BSD 行为差异 ──
say ""
say "[4] 工具方言（macOS 用 BSD 版，行为与 GNU 不同）"

# awk：substr/index/match 是 POSIX，三平台一致；gensub 是 gawk 专有
if echo "abc" | awk '{if (index($0,"b")==2) print "ok"}' | grep -q ok; then
  ok "awk index/substr 行为一致"
else
  bad "awk 基础函数行为异常"
fi

# grep -P：GNU 扩展，BSD 没有
if echo "x" | grep -qP 'x' 2>/dev/null; then
  say "  ℹ️  grep 支持 -P（GNU）—— 但门判定命令刻意不用它，保持可移植"
else
  say "  ℹ️  grep 不支持 -P（BSD/macOS）—— 门判定命令未使用 -P，无影响"
fi

# grep -E：POSIX，必须有
if echo "ab" | grep -qE 'a|b'; then
  ok "grep -E 可用"
else
  bad "grep -E 不可用"
fi

# 中文/UTF-8 处理
if printf '未实现\n' | grep -q '未实现'; then
  ok "grep 中文匹配正常（skip 审计依赖）"
else
  bad "grep 中文匹配异常 —— 检查 locale，G3.2 会漏判"
fi

# ── 5. 不该依赖的命令（用到就是 bug）──
say ""
say "[5] 非常备命令（门判定不应依赖）"
for c in bc jq; do
  if command -v "$c" >/dev/null 2>&1; then
    say "  ℹ️  $c 存在（但门判定不应依赖它——别的机器可能没有）"
  else
    say "  ℹ️  $c 不存在（正常，门判定不依赖它）"
  fi
done

# ── 6. git 仓库状态 ──
say ""
say "[6] git（G5.x 越权检测的基础）"
if git rev-parse --git-dir >/dev/null 2>&1; then
  ok "是 git 仓库"

  # .gitignore 覆盖测试产物 —— 不覆盖会触发 G5.3 活锁
  if [ -f .gitignore ]; then
    MISSING=""
    for pat in '__pycache__' 'target' 'node_modules' '.pytest_cache' 'build' 'dist'; do
      grep -q "$pat" .gitignore 2>/dev/null || MISSING="$MISSING $pat"
    done
    if [ -z "$MISSING" ]; then
      ok ".gitignore 覆盖常见测试产物"
    else
      warn ".gitignore 未覆盖:$MISSING —— 跑测试后 G5.3 会误判越权（活锁）"
    fi
  else
    bad "无 .gitignore —— 跑一次测试即产生未忽略文件 → G5.3 恒判越权 → 活锁"
  fi

  # core.autocrlf：Windows 上会让整个文件显示为改动
  ACRLF="$(git config core.autocrlf 2>/dev/null || echo unset)"
  if [ "$PLAT" = windows ] && [ "$ACRLF" = "true" ]; then
    warn "core.autocrlf=true —— 换行符转换会让 git status 报出大量非实际改动，干扰 G5.x。建议设 false 或用 .gitattributes"
  else
    ok "core.autocrlf=$ACRLF"
  fi

  # 工作区是否干净（派工基线协议要求）
  DIRTY="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$DIRTY" = "0" ]; then
    ok "工作区干净（可直接打基线）"
  else
    say "  ℹ️  工作区有 $DIRTY 处改动 —— 派工前记得 git add -A && git commit 打基线"
  fi
else
  bad "不是 git 仓库 —— G5.x 全族失效，职责隔离只剩 agent 自觉"
fi

# ── 7. 路径变量合理性 ──
say ""
say "[7] 路径变量（G5.x 引用）"
if [ -f docs/goal.md ]; then
  IMPL="$(grep -m1 '^IMPL_ROOT=' docs/goal.md 2>/dev/null | tr -d '\r' | sed 's/.*=//; s/"//g')"
  TEST="$(grep -m1 '^TEST_ROOT=' docs/goal.md 2>/dev/null | tr -d '\r' | sed 's/.*=//; s/"//g')"
  if [ -n "$IMPL" ] && [ -n "$TEST" ]; then
    ok "IMPL_ROOT=$IMPL  TEST_ROOT=$TEST"
    # 致命组合：Maven 布局下两者互为前缀
    case "$TEST" in
      "$IMPL"*) bad "TEST_ROOT 以 IMPL_ROOT 开头（Maven 布局？）—— G5.1 恒判 0 = 永远绿灯。必须改按文件名/后缀判，不能用路径前缀" ;;
      *)        ok "两个路径不互为前缀" ;;
    esac
  else
    warn "docs/goal.md 未声明 IMPL_ROOT/TEST_ROOT —— 沿用默认 src//tests/ 假设"
  fi
else
  warn "无 docs/goal.md —— Stage 0 还没做（cp docs/goal-template.md docs/goal.md）"
fi

# ── 8. 实跑一条真判据 ──
say ""
say "[8] 判据冒烟测试"
TMP="$(mktemp -d 2>/dev/null || echo /tmp/ftspre.$$)"
mkdir -p "$TMP"
printf '### R-01 x\n**正常路径**：a\n**边界条件**：b\n**异常路径**：c\n' > "$TMP/s.md"
OUT="$(awk '/^### R-/{if(n)printf "%s:%d ",n,c; n=$2;c=0} /\*\*(正常路径|边界条件|异常路径)\*\*/{c++} END{if(n)printf "%s:%d\n",n,c}' "$TMP/s.md" 2>/dev/null)"
if [ "$OUT" = "R-01:3" ]; then
  ok "G1.1 型 awk 判据实跑正常（输出 $OUT）"
else
  bad "G1.1 型判据输出异常: '$OUT'（期望 R-01:3）—— awk 方言或引号处理有问题"
fi
rm -rf "$TMP" 2>/dev/null

# ── 汇总 ──
say ""
say "========================================"
if [ "$FAIL" -gt 0 ]; then
  say "❌ $FAIL 项阻断 / $WARN 项警告 —— 修完再跑 Stage 0"
  exit 1
elif [ "$WARN" -gt 0 ]; then
  say "⚠️  0 项阻断 / $WARN 项警告 —— 可以开始，但建议先处理警告"
  exit 0
else
  say "✅ 环境就绪"
  exit 0
fi
