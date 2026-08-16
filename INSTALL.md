# 安装指南（INSTALL）

> 两种装法，选一种。装完任何项目里 `/loopforge <需求>` 直接启动 7 阶段闭环。

## 选哪种

| 模式 | 命令数 | 文件装在哪 | 选它当 |
|:--|:--:|:--|:--|
| **全局**（推荐） | 2 步 | `~/.claude/` + 项目的 `.claude/commands/` | 多项目共用，装一次 |
| **本地** | 1 步 | 全在 `<项目>/.claude/` | 不想动 `~/.claude`、各项目用不同版本、要把套件随项目提交 |

两种都把 `/loopforge` 命令装在项目里，**不碰** `~/.claude/commands/` —— 不覆盖 Claude Code 原生命令。

---

## 前置条件

| 工具 | 必须 | 检查命令 |
|:--|:--:|:--|
| git | ✅ | `git --version` |
| bash **或** PowerShell | ✅ | 见下方「选哪套脚本」 |
| awk / grep / sed | ⚠️ 门判定需要 | `awk --version` |
| Python 3 | ⚠️ 仅自校验需要 | `python --version` |

### 选哪套脚本

| 你的环境 | 用 | 说明 |
|:--|:--|:--|
| macOS / Linux | `.sh` | 原生 bash |
| Windows + Git Bash | `.sh` | 推荐 —— Goal 门判定命令本来就要 bash |
| **Windows 无 Git Bash** | `.ps1` | 装得上，但**跑 Loop 时门判定仍需 bash** |

> 🔴 **Windows 用户注意**：`.ps1` 只解决**安装**。Goal 门的判定命令用了单引号包裹的 awk，
> cmd.exe / PowerShell 下会**静默输出空且退出码 0** —— 门看起来跑了，实际什么都没判。
> 真跑 Loop 前请装 Git Bash（Git for Windows 自带）。

Windows 额外要求：

```bash
git config core.autocrlf false   # 否则 G5.x 越权检测被换行符干扰
```

---

## 方式 A · 全局（推荐）

### 第一步：全局层（所有项目共用，装一次）

**bash（macOS / Linux / Git Bash）**：

```bash
cd <loopforge 套件目录>
bash scripts/install.sh
```

**PowerShell（Windows 无 bash）**：

```powershell
cd <loopforge 套件目录>
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\install.ps1
```

成功输出：

```
✅ 全局层已装到 ~/.claude
   skill : ~/.claude/skills/loopforge/
   docs  : ~/.claude/skills/loopforge/docs/ (6 份驱动文档)
   agents: ~/.claude/agents/ (本套件 9 个)
```

装了什么：

| 目标 | 内容 |
|:--|:--|
| `~/.claude/skills/loopforge/SKILL.md` | 主编排手册 |
| `~/.claude/skills/loopforge/docs/` | **6 份运行时驱动文档**（goal-template · goal-doc-template · role-permission-matrix · commands-spec · loop-status-spec · large-project-guide） |
| `~/.claude/agents/*.md` | 9 个单一职责 agent |

> 🔴 那 6 份文档必须跟着走：SKILL.md 和 agents 运行时要读它们。少一份，agent 读不到就会**自己编内容**——不报错，静默降级。

**不装什么**（避免覆盖 Claude Code 原生）：
- ❌ 不动 `~/.claude/commands/`（/loopforge 是项目级命令）
- ❌ 不动 `~/.claude/CLAUDE.md`
- ❌ 不动 `~/.claude/settings.json`

重复执行安全（幂等）：先删旧 skill 目录再拷贝。

---

### 第二步：项目级注册（每个项目，一次）

**bash**：

```bash
cd <你的项目>
bash <loopforge 套件目录>/scripts/loopforge-init.sh
```

**PowerShell**：

```powershell
cd <你的项目>
powershell -NoProfile -ExecutionPolicy Bypass -File <loopforge 套件目录>\scripts\loopforge-init.ps1
```

成功输出：

```
✅ /loopforge 命令族已注册（用全局层的 skill 与 agents）
   skill : ~/.claude/skills/loopforge/
   命令  : <你的项目>/.claude/commands/

可用命令：
   /loopforge-cancel
   /loopforge-help
   /loopforge-resume
   /loopforge-status
   /loopforge
```

装了什么：`<项目>/.claude/commands/loopforge*.md`（5 个命令文件）。

前置：全局层必须先装（脚本会检查，未装时报错并给两个选项）。

---

## 方式 B · 本地（整套装进项目，不碰 `~/.claude`）

**一步搞定**，不需要先装全局层：

**bash**：

```bash
cd <你的项目>
bash <loopforge 套件目录>/scripts/loopforge-init.sh --local
```

**PowerShell**：

```powershell
cd <你的项目>
powershell -NoProfile -ExecutionPolicy Bypass -File <loopforge 套件目录>\scripts\loopforge-init.ps1 -Local
```

成功输出：

```
✅ 整套已装进本项目（本地模式，不依赖全局层）
   skill : <项目>/.claude/skills/loopforge/
   docs  : <项目>/.claude/skills/loopforge/docs/ (6 份)
   agents: <项目>/.claude/agents/ (9 个)
   命令  : <项目>/.claude/commands/
```

装完项目结构：

```
<你的项目>/
└── .claude/
    ├── skills/loopforge/
    │   ├── SKILL.md
    │   └── docs/            ← 6 份驱动文档
    ├── agents/              ← 9 个 agent
    └── commands/            ← 5 个 /loopforge 命令
```

**什么时候选这个**：
- 不想动 `~/.claude`
- 不同项目要用不同版本的 loopforge
- 想把套件随项目一起提交给团队（`git add .claude/`）

**代价**：每个项目一份拷贝，套件升级要逐个项目重跑。

---

前置：全局层必须先装（脚本会检查，未装时报错并指引）。

---

## 验证安装（6 步）

```bash
# 1. skill 在
test -f ~/.claude/skills/loopforge/SKILL.md && echo ok

# 2. 9 个 agent 在
ls ~/.claude/agents/*.md | wc -l        # 应 9

# 3. 项目命令在
ls <项目>/.claude/commands/loopforge*.md | wc -l   # 应 5

# 4. agent frontmatter 有 tools 白名单
grep -l "^tools:" ~/.claude/agents/*.md | wc -l   # 应 9

# 5. 套件自校验（可选）
cd <loopforge 套件目录> && python scripts/validate_suite.py

# 6. 端到端冒烟
#    在 Claude Code 里: /loopforge 我要做一个 TODO CLI
#    预期: goal-architect 开始问问题
```

---

## 使用

```bash
# 在你的项目目录，Claude Code 里：
/loopforge 我要做一个微信这样的聊天 App
/loopforge-status        # 看进度
/loopforge-resume        # 会话断了恢复
/loopforge-help          # 列命令
/loopforge-cancel        # 不做了
```

命令完整规范：`docs/commands-spec.md`。

---

## 卸载

### 项目级（删命令）

```bash
rm <项目>/.claude/commands/loopforge*.md
```

### 全局层（删 skill + agents）

```bash
rm -rf ~/.claude/skills/loopforge
rm ~/.claude/agents/{goal-architect,req-interrogator,srs-drafter,design-author,impl-coder,test-author,test-runner,gate-checker,goal-auditor}.md
```

项目里的 `docs/`（goal.md / goal-doc.md / loop-status.md 等）**不会被卸载触碰**——那是你的项目数据。

---

## 常见安装问题

| 现象 | 原因 | 解决 |
|:--|:--|:--|
| `install.sh` 报 "找不到 agents" | 不在套件目录跑 | `cd <套件目录>` 再跑 |
| `loopforge-init.sh` 报 "全局层未安装" | 没先跑 install.sh | 先跑第一步 |
| `/loopforge` 无反应 | 项目级命令没装 / Claude Code 未重启加载 | 重跑 loopforge-init.sh，重启会话 |
| Windows 下 `install.sh` 乱码 | 非 Git Bash | 用 Git Bash 跑 |
| agent 数不对 | 套件文件缺 | 重下套件，`install.sh` 自带 9 个校验会拦截 |
