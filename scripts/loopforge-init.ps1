# loopforge 项目级注册（Windows PowerShell 版）
# 把 /loopforge 命令族装到 <当前项目>\.claude\commands\
#
# 用法:
#   cd <你的项目>
#   powershell -NoProfile -ExecutionPolicy Bypass -File <路径>\scripts\loopforge-init.ps1
#       只装命令，依赖已装好的全局层（$HOME\.claude\skills\loopforge）
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File <路径>\scripts\loopforge-init.ps1 -Local
#       整套装进本项目（skill + agents + 套件文档 + 命令），不依赖全局层
#       适合：不想污染 $HOME\.claude、或每个项目要用不同版本
#
# 退出码: 0 成功 / 1 失败
#
# 与 loopforge-init.sh 行为等价。

param([switch]$Local)

$ErrorActionPreference = 'Stop'

$SRC  = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PROJ = (Get-Location).Path

$DRIVER_DOCS = @(
    'goal-template.md', 'goal-doc-template.md', 'role-permission-matrix.md',
    'commands-spec.md', 'loop-status-spec.md', 'large-project-guide.md'
)

function Fail([string]$msg) {
    Write-Host "[X] $msg" -ForegroundColor Red
    exit 1
}

# ── 前置检查 ──
if (-not (Test-Path "$SRC\commands" -PathType Container)) {
    Fail "找不到 $SRC\commands"
}

$cmdFiles = @(Get-ChildItem "$SRC\commands\loopforge*.md" -ErrorAction SilentlyContinue)
if ($cmdFiles.Count -ne 5) {
    Fail "commands/ 应有 5 个 loopforge*.md，实际 $($cmdFiles.Count)"
}

# 逐文件校验 frontmatter：首个非空行必须是 ---，且含 name: 行
# 用 -Raw + 手工切行，避免 Get-Content 对 CRLF/编码的差异
foreach ($f in $cmdFiles) {
    $lines = (Get-Content $f.FullName -Raw -Encoding UTF8) -split "`r?`n"
    $firstLine = $null
    foreach ($ln in $lines) {
        if ($ln.Trim() -ne '') { $firstLine = $ln.Trim(); break }
    }
    if ($firstLine -ne '---') {
        Fail "$($f.FullName) 首个非空行不是 ---（frontmatter 损坏）"
    }
    if (-not ($lines | Where-Object { $_ -match '^name:' })) {
        Fail "$($f.FullName) 缺少 name: 行（frontmatter 损坏）"
    }
}

if ($Local) {
    # ── 本地模式：整套装进项目 ──
    $agentFiles = @(Get-ChildItem "$SRC\agents\*.md" -ErrorAction SilentlyContinue)
    if ($agentFiles.Count -ne 9) {
        Fail "agents/ 应有 9 个文件，实际 $($agentFiles.Count)"
    }
    foreach ($doc in $DRIVER_DOCS) {
        if (-not (Test-Path "$SRC\docs\$doc" -PathType Leaf)) {
            Fail "缺驱动文档 docs\$doc —— 套件不完整"
        }
    }

    New-Item -ItemType Directory -Force -Path "$PROJ\.claude\skills" | Out-Null
    New-Item -ItemType Directory -Force -Path "$PROJ\.claude\agents" | Out-Null
    if (Test-Path "$PROJ\.claude\skills\loopforge") {
        Remove-Item "$PROJ\.claude\skills\loopforge" -Recurse -Force
    }
    Copy-Item "$SRC\skills\loopforge" "$PROJ\.claude\skills\" -Recurse -Force
    New-Item -ItemType Directory -Force -Path "$PROJ\.claude\skills\loopforge\docs" | Out-Null
    foreach ($doc in $DRIVER_DOCS) {
        Copy-Item "$SRC\docs\$doc" "$PROJ\.claude\skills\loopforge\docs\" -Force
    }
    Copy-Item "$SRC\agents\*.md" "$PROJ\.claude\agents\" -Force
    $skillLoc = "$PROJ\.claude\skills\loopforge"
}
else {
    # ── 默认模式：依赖全局层 ──
    $skillLoc = Join-Path $HOME '.claude\skills\loopforge'
    if (-not (Test-Path "$skillLoc\SKILL.md" -PathType Leaf)) {
        Write-Host "[X] 全局层未安装（$skillLoc\SKILL.md 不存在）" -ForegroundColor Red
        Write-Host ""
        Write-Host "    两个选择："
        Write-Host "    1) 装全局层（推荐，所有项目共用）:"
        Write-Host "       powershell -NoProfile -ExecutionPolicy Bypass -File $SRC\scripts\install.ps1"
        Write-Host "    2) 整套装进本项目（不碰 `$HOME\.claude）:"
        Write-Host "       powershell -NoProfile -ExecutionPolicy Bypass -File $SRC\scripts\loopforge-init.ps1 -Local"
        exit 1
    }
}

# ── 注册命令 ──
New-Item -ItemType Directory -Force -Path "$PROJ\.claude\commands" | Out-Null
Copy-Item "$SRC\commands\loopforge*.md" "$PROJ\.claude\commands\" -Force

# ── 验证 ──
# 逐个确认本套件的 5 个都到位，不数目标目录的 loopforge*.md 总数 ——
# 用户可能已有自己的命令，全量计数会误报失败
$installed = 0
foreach ($f in $cmdFiles) {
    if (Test-Path (Join-Path "$PROJ\.claude\commands" $f.Name) -PathType Leaf) { $installed++ }
}
if ($installed -ne 5) {
    Fail "注册不完整: $installed/5"
}

if ($Local) {
    foreach ($doc in $DRIVER_DOCS) {
        if (-not (Test-Path "$skillLoc\docs\$doc" -PathType Leaf)) {
            Fail "驱动文档未装上: $doc"
        }
    }
    $localAgents = 0
    foreach ($f in Get-ChildItem "$SRC\agents\*.md") {
        if (Test-Path (Join-Path "$PROJ\.claude\agents" $f.Name) -PathType Leaf) { $localAgents++ }
    }
    if ($localAgents -ne 9) {
        Fail "agent 装漏: $localAgents/9"
    }
    Write-Host "[OK] 整套已装进本项目（本地模式，不依赖全局层）" -ForegroundColor Green
    Write-Host "     skill : $PROJ\.claude\skills\loopforge\"
    Write-Host "     docs  : $PROJ\.claude\skills\loopforge\docs\ (6 份)"
    Write-Host "     agents: $PROJ\.claude\agents\ (9 个)"
}
else {
    Write-Host "[OK] /loopforge 命令族已注册（用全局层的 skill 与 agents）" -ForegroundColor Green
    Write-Host "     skill : $skillLoc\"
}
Write-Host "     命令  : $PROJ\.claude\commands\"
Write-Host ""
Write-Host "可用命令："
foreach ($f in $cmdFiles) {
    Write-Host "   /$($f.BaseName)"
}
Write-Host ""
Write-Host "开始: /loopforge <你的模糊需求>"
exit 0
