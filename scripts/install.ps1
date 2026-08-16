# loopforge 全局层安装（Windows PowerShell 版）
# skill + agents 装到 $HOME\.claude\，所有项目可用
#
# 用法: powershell -ExecutionPolicy Bypass -File scripts\install.ps1
# 退出码: 0 成功 / 1 失败
#
# 与 install.sh 行为等价。Windows 无 bash 时用这个。

$ErrorActionPreference = 'Stop'

$SRC = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DST = Join-Path $HOME '.claude'

function Fail([string]$msg) {
    Write-Host "[X] $msg" -ForegroundColor Red
    exit 1
}

# ── 前置检查 ──
if (-not (Test-Path "$SRC\skills\loopforge" -PathType Container)) {
    Fail "找不到 $SRC\skills\loopforge"
}
if (-not (Test-Path "$SRC\agents" -PathType Container)) {
    Fail "找不到 $SRC\agents"
}

$agentCount = @(Get-ChildItem "$SRC\agents\*.md" -ErrorAction SilentlyContinue).Count
if ($agentCount -ne 9) {
    Fail "agents/ 应有 9 个文件，实际 $agentCount"
}

$cmdCount = @(Get-ChildItem "$SRC\commands\loopforge*.md" -ErrorAction SilentlyContinue).Count
if ($cmdCount -ne 5) {
    Fail "commands/ 应有 5 个 loopforge*.md（loopforge-init.ps1 依赖），实际 $cmdCount"
}

# 运行时驱动文档 —— 缺一份，全局模式下 agent 读不到就会自己编内容
$DRIVER_DOCS = @(
    'goal-template.md', 'goal-doc-template.md', 'role-permission-matrix.md',
    'commands-spec.md', 'loop-status-spec.md', 'large-project-guide.md'
)
foreach ($doc in $DRIVER_DOCS) {
    if (-not (Test-Path "$SRC\docs\$doc" -PathType Leaf)) {
        Fail "缺驱动文档 docs\$doc —— 套件不完整，重新下载"
    }
}

# ── 安装 ──
New-Item -ItemType Directory -Force -Path "$DST\skills" | Out-Null
New-Item -ItemType Directory -Force -Path "$DST\agents" | Out-Null

# skill：先删旧版再拷（避免残留过期文件）
if (Test-Path "$DST\skills\loopforge") {
    Remove-Item "$DST\skills\loopforge" -Recurse -Force
}
Copy-Item "$SRC\skills\loopforge" "$DST\skills\" -Recurse -Force

# 驱动文档带进 skill 目录的 docs\ 子目录 ——
# SKILL.md 与 agents 里写的是相对路径 docs/xxx.md，装到 skill 根会对不上
New-Item -ItemType Directory -Force -Path "$DST\skills\loopforge\docs" | Out-Null
foreach ($doc in $DRIVER_DOCS) {
    Copy-Item "$SRC\docs\$doc" "$DST\skills\loopforge\docs\" -Force
}

# agents：逐个覆盖
Copy-Item "$SRC\agents\*.md" "$DST\agents\" -Force

# ── 验证 ──
if (-not (Test-Path "$DST\skills\loopforge\SKILL.md" -PathType Leaf)) {
    Fail "SKILL.md 未装上"
}
# 只数本套件的 9 个，不数目标目录里的全部 agent ——
# 用户 .claude\agents\ 里可能已有别的 agent，全量计数会把装漏也撑成"看着对"
$installedAgents = 0
foreach ($f in Get-ChildItem "$SRC\agents\*.md") {
    if (Test-Path (Join-Path "$DST\agents" $f.Name) -PathType Leaf) { $installedAgents++ }
}
if ($installedAgents -ne 9) {
    Fail "agent 装漏: $installedAgents/9"
}
# 驱动文档逐个确认——少一份，运行时 agent 读不到就会自己编
foreach ($doc in $DRIVER_DOCS) {
    if (-not (Test-Path "$DST\skills\loopforge\docs\$doc" -PathType Leaf)) {
        Fail "驱动文档未装上: $doc"
    }
}

Write-Host "[OK] 全局层已装到 $DST" -ForegroundColor Green
Write-Host "     skill : $DST\skills\loopforge\"
Write-Host "     docs  : $DST\skills\loopforge\docs\ ($($DRIVER_DOCS.Count) 份驱动文档)"
Write-Host "     agents: $DST\agents\ (本套件 $installedAgents 个)"
Write-Host ""
Write-Host "下一步：到每个项目目录跑 loopforge-init.ps1 注册 /loopforge 命令族"
exit 0
