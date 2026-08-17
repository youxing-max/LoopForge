#!/usr/bin/env python3
"""
loopforge 套件自校验器

对套件自身跑"全量测试"——套件是规格集不是代码，所以测的是：
  L1 结构完整性   文件存在、frontmatter 合法
  L2 权限不变式   职责隔离的硬约束是否真的成立
  L3 引用一致性   跨文档引用能否解析
  L4 闭环完整性   每个门有回退、每个回退有落点、无死路
  L5 契约一致性   role-permission-matrix 的声明 vs agent 实际 frontmatter

用法：python scripts/validate_suite.py [套件根目录]
退出码：0 全绿 / 1 有 FAIL
"""

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)

results = []  # (level, gate_id, name, status, detail)


def check(level, gate_id, name, passed, detail=""):
    results.append((level, gate_id, name, "PASS" if passed else "FAIL", detail))
    return passed


def warn(level, gate_id, name, detail):
    results.append((level, gate_id, name, "WARN", detail))


def parse_frontmatter(path):
    """返回 (frontmatter dict, body)。无 frontmatter 返回 ({}, 全文)"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw, body = text[3:end], text[end + 4:]
    fm = {}
    for line in fm_raw.strip().splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


# ─────────────────────────────────────────────────────────────
# L1 结构完整性
# ─────────────────────────────────────────────────────────────
EXPECTED_AGENTS = {
    "req-interrogator", "srs-drafter", "design-author",
    "impl-coder", "test-author", "test-runner",
    "gate-checker", "goal-auditor",
    "goal-architect",
}

agents_dir = ROOT / "agents"
skill_path = ROOT / "skills" / "loopforge" / "SKILL.md"
goal_tpl = ROOT / "docs" / "goal-template.md"
role_matrix = ROOT / "docs" / "role-permission-matrix.md"
settings_json = ROOT / "docs" / "settings-permissions.json"

check("L1", "S1.1", "agents/ 目录存在", agents_dir.is_dir())
check("L1", "S1.2", "主 SKILL.md 存在", skill_path.is_file())
check("L1", "S1.3", "goal-template.md 存在", goal_tpl.is_file())
check("L1", "S1.4", "role-permission-matrix.md 存在", role_matrix.is_file())
check("L1", "S1.5", "settings-permissions.json 存在", settings_json.is_file())

# ── S1.11~S1.15 v2.3 命令层 + 安装层 ──
# commands/ 是 /loopforge 命令族（loopforge-init.sh 校验 5 个，这里独立校验防两边一起坏）
commands_dir = ROOT / "commands"
EXPECTED_COMMANDS = {"loopforge", "loopforge-status", "loopforge-resume", "loopforge-cancel", "loopforge-help"}
found_commands = {p.stem for p in commands_dir.glob("loopforge*.md")} if commands_dir.is_dir() else set()
missing_cmds = EXPECTED_COMMANDS - found_commands
check("L1", "S1.11", "commands/ 目录存在", commands_dir.is_dir())
check("L1", "S1.12", "5 个 /loopforge 命令齐", not missing_cmds,
      f"缺失: {sorted(missing_cmds)}" if missing_cmds else "")
for cname in sorted(found_commands):
    cfm, _ = parse_frontmatter(commands_dir / f"{cname}.md")
    check("L1", f"S1.13[{cname}]", "命令 frontmatter 有 name/description",
          "name" in cfm and "description" in cfm,
          f"缺: {[k for k in ('name','description') if k not in cfm]}")
# 命令文件正确引用编排链关键 agent（拼写错误 = /loopforge 派不动人）
cmd_text_all = "\n".join(
    (commands_dir / f"{c}.md").read_text(encoding="utf-8")
    for c in found_commands if (commands_dir / f"{c}.md").is_file()
)
for a in ("goal-architect", "gate-checker"):
    check("L1", f"S1.14[{a}]", f"命令文件正确引用 {a}", a in cmd_text_all,
          f"/loopforge 编排链需要 {a}，commands/ 里没提到")
install_sh = ROOT / "scripts" / "install.sh"
loopforge_init_sh = ROOT / "scripts" / "loopforge-init.sh"
install_ps1 = ROOT / "scripts" / "install.ps1"
loopforge_init_ps1 = ROOT / "scripts" / "loopforge-init.ps1"
check("L1", "S1.15a", "install.sh 存在", install_sh.is_file())
check("L1", "S1.15b", "loopforge-init.sh 存在", loopforge_init_sh.is_file())
check("L1", "S1.15c", "install.sh 仍拷贝驱动文档",
      install_sh.is_file() and "role-permission-matrix.md" in install_sh.read_text(encoding="utf-8"),
      "install.sh 缺少 role-permission-matrix.md 拷贝逻辑，/loopforge 运行时会断" if install_sh.is_file() else "")

# ── S1.16 Windows 无 bash 时的等价安装路径 ──
# 只有 .sh 的话，纯 Windows（无 Git Bash）用户装不上。两套脚本必须行为等价，
# 否则一边改了另一边没改 = 平台间静默不一致。
check("L1", "S1.16a", "install.ps1 存在（Windows 无 bash 时用）", install_ps1.is_file())
check("L1", "S1.16b", "loopforge-init.ps1 存在（Windows 无 bash 时用）", loopforge_init_ps1.is_file())
_PS_PARITY = [
    (install_ps1, "install.ps1", ["role-permission-matrix.md", "goal-template.md",
                                  "goal-doc-template.md", "skills\\loopforge"]),
    (loopforge_init_ps1, "loopforge-init.ps1", ["commands", "SKILL.md", "name:"]),
]
for _p, _label, _needles in _PS_PARITY:
    if not _p.is_file():
        continue
    _txt = _p.read_text(encoding="utf-8")
    _miss = [n for n in _needles if n not in _txt]
    check("L1", f"S1.16c[{_label}]", "ps1 与 sh 关键逻辑对齐", not _miss,
          f"{_label} 缺少 {_miss} —— 与 .sh 版行为不等价，Windows 用户会装出残缺环境")

# ── S1.17 全局安装必须带齐运行时要读的套件文档 ──
# SKILL.md / agents 运行时会读这些模板与规范。装漏一份，全局模式下 agent
# 读不到就会自己编（模板内容全走样且没人发现）——不是报错，是静默降级。
_RUNTIME_DOCS = ["goal-template.md", "goal-doc-template.md", "role-permission-matrix.md",
                 "commands-spec.md", "loop-status-spec.md", "large-project-guide.md"]
for _script, _lbl in ((install_sh, "install.sh"), (install_ps1, "install.ps1")):
    if not _script.is_file():
        continue
    _t = _script.read_text(encoding="utf-8")
    _absent = [d for d in _RUNTIME_DOCS if d not in _t]
    check("L1", f"S1.17[{_lbl}]", "安装脚本带齐 6 份运行时文档", not _absent,
          f"{_lbl} 未拷贝 {_absent} —— 全局模式下 agent 读不到，会自己编内容")

# ── S1.18 本地模式（--local）必须真存在 ──
# SKILL.md 的部署模式表声称支持"整套装进项目"。若 loopforge-init 不支持，
# 文档说有、脚本做不到 —— 用户按文档操作会撞墙。
for _script, _lbl, _flag in ((loopforge_init_sh, "loopforge-init.sh", "--local"),
                             (loopforge_init_ps1, "loopforge-init.ps1", "Local")):
    if not _script.is_file():
        continue
    _t = _script.read_text(encoding="utf-8")
    _has_flag = _flag in _t
    # 本地模式必须同时装 skill、agents、6 份文档，缺一样就是残缺环境
    _local_ok = _has_flag and all(k in _t for k in ("agents", "skills", "docs"))
    check("L1", f"S1.18[{_lbl}]", "支持本地模式且装齐三类文件", _local_ok,
          f"{_lbl} 缺 {_flag} 模式或未装齐 skill/agents/docs —— "
          f"SKILL.md 声称支持本地部署，脚本做不到")


found_agents = {p.stem for p in agents_dir.glob("*.md")} if agents_dir.is_dir() else set()
missing = EXPECTED_AGENTS - found_agents
extra = found_agents - EXPECTED_AGENTS
check("L1", "S1.6", "9 个 agent 齐全", not missing, f"缺失: {sorted(missing)}" if missing else "")
check("L1", "S1.7", "无残留旧 agent", "loop-driver" not in found_agents,
      "loop-driver 仍存在——它违反职责隔离，应删除" if "loop-driver" in found_agents else "")
if extra - {"loop-driver"}:
    warn("L1", "S1.8", "存在计划外 agent", f"{sorted(extra - {'loop-driver'})}")

agent_fm = {}
for name in sorted(found_agents):
    fm, body = parse_frontmatter(agents_dir / f"{name}.md")
    agent_fm[name] = (fm, body)
    check("L1", f"S1.9[{name}]", "frontmatter 有 name/description/tools",
          all(k in fm for k in ("name", "description", "tools")),
          f"缺: {[k for k in ('name','description','tools') if k not in fm]}")
    if "name" in fm:
        check("L1", f"S1.10[{name}]", "frontmatter name 与文件名一致",
              fm["name"] == name, f"frontmatter={fm.get('name')} 文件名={name}")

# ── S1.19 套件文档引用必须带 <SKILL_DOCS> 前缀 ──
# 全局模式下 skill 在 ~/.claude/，而项目 docs/ 在用户项目里。写裸
# `docs/goal-template.md` 会去项目目录找模板 —— 找不到，agent 就自己编一份，
# 门判据全走样且没人发现（静默降级，不报错）。
# 只查"套件文档"（只读模板/规范）；项目产物（goal.md / goal-doc.md /
# loop-status.md）在 <项目>/docs/loopforge/ 下，不在此列（此检查只盯套件模板）。
_SUITE_DOCS = ["goal-template.md", "goal-doc-template.md", "role-permission-matrix.md",
               "commands-spec.md", "loop-status-spec.md", "large-project-guide.md"]
# 扫描范围必须覆盖"会被 agent/命令在运行时读到"的全部文件。
# 早期版本只扫 SKILL.md + agents，漏掉 commands/ 与套件文档自身之间的互引 ——
# 而 goal-template.md 会被 cp 成 <项目>/docs/loopforge/goal.md，是全流程读得最多的文件，
# 它写错路径的影响比 SKILL.md 还大。
_PATH_TARGETS = [(skill_path, "SKILL.md")] + \
                [(agents_dir / f"{a}.md", a) for a in sorted(found_agents)] + \
                [(commands_dir / f"{c}.md", f"cmd:{c}") for c in sorted(found_commands)] + \
                [(ROOT / "docs" / d, f"doc:{d}") for d in _SUITE_DOCS]
for _f, _lbl in _PATH_TARGETS:
    if not _f.is_file():
        continue
    _bad = set()
    for _ln in _f.read_text(encoding="utf-8").splitlines():
        # 已带解析占位符的行：<SKILL_DOCS>/x.md 或 <SKILL>/docs/x.md 都算正确
        if "SKILL_DOCS" in _ln or "<SKILL>/docs/" in _ln:
            continue
        # 举反例的行放行：路径被中文引号包住（如 只写"读 docs/xxx.md"）
        # —— 说明"为什么不能这么写"是合法的，扫它会误报
        _quoted = re.findall(r'“[^”]*”|"[^"]*"', _ln)
        for _d in _SUITE_DOCS:
            if f"docs/{_d}" not in _ln:
                continue
            if any(f"docs/{_d}" in _q for _q in _quoted):
                continue             # 在引号内 = 举例，不是指令
            _bad.add(_d)
    check("L1", f"S1.19[{_lbl}]", "套件文档引用带 <SKILL_DOCS> 前缀", not _bad,
          f"{_lbl} 写了裸 docs/{sorted(_bad)} —— 全局模式下会去项目目录找，"
          f"找不到就自己编内容")

# ── S1.20 声明解析顺序的地方必须同时给 Windows 等价路径 ──
# `$HOME` 在 Git Bash 下正常，但 PowerShell/cmd 不认。只写 $HOME 的话，
# Windows 用 .ps1 装完的用户按文档找不到目录 —— 不是报错，是找错地方。
for _f, _lbl in _PATH_TARGETS:
    if not _f.is_file():
        continue
    _txt = _f.read_text(encoding="utf-8")
    if "$HOME/.claude/skills/loopforge" not in _txt:
        continue                     # 没声明解析顺序的文件不适用
    check("L1", f"S1.20[{_lbl}]", "解析顺序含 Windows 等价路径",
          "USERPROFILE" in _txt,
          f"{_lbl} 只写了 $HOME —— PowerShell/cmd 不展开它，"
          f"Windows 用户按文档找不到 skill 目录")


# ─────────────────────────────────────────────────────────────
# L2 权限不变式（职责隔离的核心）
# ─────────────────────────────────────────────────────────────
def tools_of(name):
    fm, _ = agent_fm.get(name, ({}, ""))
    return {t.strip() for t in fm.get("tools", "").split(",") if t.strip()}


MUTATE = {"Edit", "Write", "NotebookEdit"}

# ── P2.1 核心不变式：写代码的角色不能同时能跑命令 ──
# 注意约束的是"写实现/写测试"这三个角色。test-runner/gate-checker 有 Bash
# 是设计使然（要跑测试/判定命令），它们的隔离靠 G5.x 事后检测，不靠 tools。
WRITER_ROLES = {"impl-coder", "test-author"}
for name in sorted(found_agents & WRITER_ROLES):
    t = tools_of(name)
    check("L2", f"P2.1[{name}]", "写者不得持有 Bash",
          "Bash" not in t,
          f"tools={sorted(t)} —— 写代码+跑测试同体，可改断言凑绿")

# 逐角色断言
INVARIANTS = [
    ("impl-coder",      "Bash",  False, "实现者有 Bash → 能看测试红绿 → 有改断言动机"),
    ("test-author",     "Bash",  False, "测试作者有 Bash → 能看红绿 → 有调容差凑绿动机"),
    ("goal-auditor",    "Bash",  False, "审计员有 Bash → 在做验证而非审计"),
    ("goal-auditor",    "Edit",  False, "审计员能改代码 → 自证自洽"),
    ("goal-auditor",    "Write", False, "审计员能写文件 → 可越权改产物"),
    ("test-runner",     "Edit",  False, "执行者能改代码 → 报告不可信"),
    ("test-runner",     "Write", False, "执行者能写文件 → 报告不可信"),
    ("test-runner",     "Bash",  True,  "执行者无 Bash → 跑不了测试"),
    ("gate-checker",    "Bash",  True,  "门判定无 Bash → 跑不了判定命令"),
    ("gate-checker",    "Edit",  False, "门判定能改文件 → 可改判据放水"),
    ("impl-coder",      "Edit",  True,  "实现者无 Edit → 写不了代码"),
    ("test-author",     "Write", True,  "测试作者无 Write → 写不了测试"),
    ("req-interrogator","Bash",  False, "拷问官有 Bash → 越界"),
    ("srs-drafter",     "Bash",  False, "SRS 起草有 Bash → 越界"),
    ("design-author",   "Bash",  False, "设计作者有 Bash → 越界"),
    ("goal-architect",  "Bash",  False, "目标架构有 Bash → 越界"),
    ("goal-architect",  "Edit",  False, "目标架构有 Edit → 可改代码越界"),
]
for agent, tool, should_have, why in INVARIANTS:
    if agent not in found_agents:
        continue
    actual = tool in tools_of(agent)
    check("L2", f"P2.2[{agent}:{tool}]",
          f"{agent} {'应有' if should_have else '禁有'} {tool}",
          actual == should_have, why if actual != should_have else "")

# ── P2.3 三角色两两不同体（取代原"三集合互不相交"）──
#
# 原判据把角色按 tools 分成 writer/runner/auditor 三个集合再查互斥。那是
# 恒真式：按 {有MUTATE且无Bash}/{有Bash}/{无MUTATE且无Bash} 的定义，穷举
# 7 种工具的全部 128 个子集，没有任何组合能落进两个桶 —— 不管 frontmatter
# 怎么写都 PASS，零证据价值。
#
# 真正要断言的是具体角色不重合：写实现的、跑测试的、做审计的必须是三个
# 不同 agent，且各自的能力边界正确。
ROLE_TRIAD = [
    ("impl-coder", "test-runner", "写实现者 与 跑测试者"),
    ("impl-coder", "goal-auditor", "写实现者 与 审计者"),
    ("test-author", "test-runner", "写测试者 与 跑测试者"),
    ("test-runner", "goal-auditor", "跑测试者 与 审计者"),
    ("gate-checker", "goal-auditor", "门判定者 与 审计者"),
]
for a, b, desc in ROLE_TRIAD:
    check("L2", f"P2.3[{a}|{b}]", f"{desc} 是不同 agent",
          a != b and a in found_agents and b in found_agents,
          f"缺 {a if a not in found_agents else b}")

# P2.4 审计者是全套件唯一"既不能写也不能跑"的角色 —— 这条有判别力：
# 给 goal-auditor 加任何写/执行工具都会 FAIL
pure_readers = {a for a in found_agents
                if not (tools_of(a) & MUTATE) and "Bash" not in tools_of(a)}
check("L2", "P2.4", "goal-auditor 在纯只读集合内",
      "goal-auditor" in pure_readers,
      f"goal-auditor tools={sorted(tools_of('goal-auditor'))} —— 审计者不该能写或能跑")

# P2.5 有 Bash 的角色必须被 G5.x 事后检测覆盖（因为 Bash ⊇ Write，
# tools 白名单对它们不起作用，事后检测是唯一防线）
bash_holders = {a for a in found_agents if "Bash" in tools_of(a)}
goal_text_early = goal_tpl.read_text(encoding="utf-8") if goal_tpl.is_file() else ""
for a in sorted(bash_holders):
    covered = a in goal_text_early or "G5.6" in goal_text_early
    check("L2", f"P2.5[{a}]", "持 Bash 者被 G5.x 事后检测覆盖", covered,
          f"{a} 有 Bash 但 goal 门里没有对应越权检测 —— 它能用 > 重定向写任意文件")


# ─────────────────────────────────────────────────────────────
# L3 引用一致性
# ─────────────────────────────────────────────────────────────
skill_text = skill_path.read_text(encoding="utf-8") if skill_path.is_file() else ""
matrix_text = role_matrix.read_text(encoding="utf-8") if role_matrix.is_file() else ""
goal_text = goal_tpl.read_text(encoding="utf-8") if goal_tpl.is_file() else ""

# SKILL.md 里 subagent_type= 引用的 agent 必须存在
referenced = set(re.findall(r'subagent_type="([\w-]+)"', skill_text))
unknown_refs = referenced - found_agents
check("L3", "R3.1", "SKILL.md 引用的 agent 都存在",
      not unknown_refs, f"未定义: {sorted(unknown_refs)}")

# 每个 agent 都被 SKILL.md 提到（无孤岛）
mentioned = {a for a in found_agents if a in skill_text}
orphan = found_agents - mentioned
check("L3", "R3.2", "无孤岛 agent（都在 SKILL.md 出现）",
      not orphan, f"孤岛: {sorted(orphan)}")

# 权限矩阵覆盖全部 agent
matrix_missing = {a for a in found_agents if a not in matrix_text}
check("L3", "R3.3", "权限矩阵覆盖全部 agent",
      not matrix_missing, f"矩阵未收录: {sorted(matrix_missing)}")

# 已删除的 loop-driver 不应作为【活跃组件】存在。
# 只认两个真信号：agent 文件仍在（S1.7 已查）、或仍有 subagent_type 调用。
# 散文里讨论"为什么删它"是合法的——迁移文档就该写这个，不扫描 prose。
active_calls = []
for p in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.json")):
    if re.search(r'subagent_type="loop-driver"', p.read_text(encoding="utf-8")):
        active_calls.append(str(p.relative_to(ROOT)))
check("L3", "R3.4", "无文档仍把 loop-driver 当活跃组件调用",
      not active_calls, f"仍有 subagent_type 调用: {active_calls}")

# ── R3.5 门判定命令不得引用套件外的 agent/skill ──
#
# 覆盖盲区修复：原 L3 只扫 SKILL.md 的 subagent_type=，完全不扫
# goal-template.md 里"调 X agent"这种写法。结果 G2.1~G2.3 引用不存在的
# doc-consistency-checker、G3.3 引用不自带的 phase-verify，四条阻断门
# 恒 [无法判定]（视同 FAIL）→ Stage 3/4 结构性无法退出，而自校验全绿。
#
# 只扫门定义表格行（以 | 开头且含 G<数字>.<数字>），不扫散文——
# 说明"为什么删掉某组件"是合法的，扫散文会误报。
gate_rows = [ln for ln in goal_text.splitlines()
             if ln.lstrip().startswith("|") and re.search(r'G\d+\.\d+', ln)]
gate_agent_refs = set()
for ln in gate_rows:
    gate_agent_refs |= set(re.findall(r'调\s*[`"]?([a-z][\w-]+)[`"]?\s*(?:agent|skill)', ln))
unknown_gate_refs = gate_agent_refs - found_agents
check("L3", "R3.5", "门判定命令不引用套件外组件",
      not unknown_gate_refs,
      f"引用了不存在的组件 {sorted(unknown_gate_refs)} —— 这些门恒[无法判定]，"
      f"按 gate-checker 规则视同 FAIL，对应 Stage 无法退出")

# ── R3.6 gate-checker 没有 Agent 工具，门判定不能要求它调 agent ──
gc_tools = tools_of("gate-checker")
if "Agent" not in gc_tools:
    check("L3", "R3.6", "门判定命令不要求 gate-checker 调 agent",
          not gate_agent_refs,
          f"gate-checker tools={sorted(gc_tools)} 无 Agent 工具，"
          f"却有门要求它调 {sorted(gate_agent_refs)}")

# ── R3.7 README 不写死自校验项数（项数随检查项增减变化，写死必失真）──
readme_text = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
hardcoded = re.findall(r'(\d+)\s*项检查|(\d+)\s*PASS\s*/\s*\d+\s*FAIL', readme_text)
hardcoded_nums = {int(n) for pair in hardcoded for n in pair if n}
check("L3", "R3.7", "README 不写死自校验项数",
      not hardcoded_nums,
      f"写死了 {sorted(hardcoded_nums)} —— 加减检查项后必失真，改为'跑 validate_suite.py 应全绿'")


# ─────────────────────────────────────────────────────────────
# L4 闭环完整性
# ─────────────────────────────────────────────────────────────
gate_ids = set(re.findall(r'\*\*(G\d+\.\d+)\*\*', goal_text))
check("L4", "C4.1", "Goal 门已定义（≥15 条）", len(gate_ids) >= 15, f"实际 {len(gate_ids)} 条")

# G5.x 越权检测门必须存在——这是唯一不依赖自觉的关卡
g5 = {g for g in gate_ids if g.startswith("G5.")}
check("L4", "C4.2", "G5.x 角色越权检测门存在", len(g5) >= 6,
      f"实际 {sorted(g5)} —— 缺了它，职责隔离只剩自觉")

# 每个门族都要在回退映射表里有落点
families = sorted({g.split(".")[0] for g in gate_ids})
fallback_section = goal_text[goal_text.find("回退映射"):] if "回退映射" in goal_text else ""
for fam in families:
    check("L4", f"C4.3[{fam}]", f"{fam}.x 在回退映射表有落点",
          fam in fallback_section, "该门族不过时不知道回哪个阶段")

# 防死循环规则必须存在
for kw, desc in [("连续 3 轮", "同门 3 轮上限"),
                 ("> 10", "累计回退上限"),
                 ("门冲突", "门互相拉扯处置")]:
    check("L4", f"C4.4[{desc}]", f"防死循环规则: {desc}",
          kw in skill_text, "缺此规则 → 可能无限循环烧 token")

# 双轮审计的独立性纪律
check("L4", "C4.5", "Round 2 禁读 Round 1 已写死",
      "禁读" in skill_text or "禁止读" in skill_text,
      "缺此纪律 → 双轮退化为单轮复读")

# 无法判定不得当 PASS
gc_body = agent_fm.get("gate-checker", ({}, ""))[1]
check("L4", "C4.6", "gate-checker 明确'无法判定≠PASS'",
      "无法判定" in gc_body and ("不算 PASS" in gc_body or "视同 FAIL" in gc_body),
      "缺此规则 → 检查失败会被当成通过混过去")


# ─────────────────────────────────────────────────────────────
# L5 契约一致性（矩阵声明 vs 实际 frontmatter）
# ─────────────────────────────────────────────────────────────
# 从矩阵的工具白名单表抽取声明，与 frontmatter 比对
for name in sorted(found_agents):
    declared = re.search(rf'`{name}`\s*\|\s*`([^`]+)`', matrix_text)
    if not declared:
        warn("L5", f"M5.1[{name}]", "矩阵未声明 tools", "无法交叉验证")
        continue
    decl_set = {t.strip() for t in declared.group(1).split(",") if t.strip()}
    actual_set = tools_of(name)
    check("L5", f"M5.1[{name}]", "矩阵声明 == frontmatter 实际",
          decl_set == actual_set,
          f"矩阵={sorted(decl_set)} 实际={sorted(actual_set)}")

# settings.json 合法性
if settings_json.is_file():
    import json
    try:
        cfg = json.loads(settings_json.read_text(encoding="utf-8"))
        check("L5", "M5.2", "settings-permissions.json 是合法 JSON", True)
        check("L5", "M5.3", "含 permissions.deny 块",
              "permissions" in cfg and "deny" in cfg.get("permissions", {}))
    except json.JSONDecodeError as e:
        check("L5", "M5.2", "settings-permissions.json 是合法 JSON", False, str(e))


# ─────────────────────────────────────────────────────────────
# L6 门判定命令实跑（覆盖盲区：L1~L5 只查文档结构，不执行门命令）
#
# 背景：2026-08-09 实跑发现三个只有执行才能暴露的 bug——
#   G1.2↔G1.4 互斥死锁 / G1.3 恒真假绿 / G0.1 数量当覆盖度。
# 本层造最小样例，实际执行门命令，并对已修 bug 做回归。
# ─────────────────────────────────────────────────────────────
import subprocess
import tempfile
import shutil

FIXTURE_SRS = """# Demo SRS

## 2. 需求编号索引
| R-XX | 描述 | 类别 | 优先级 |
|:--|:--|:--|:--|
| R-01 | 上传 | 功能 | P0 |

## 3. 功能需求

### R-01 上传
**优先级**：P0
**正常路径**：传合法文件 → 成功
**边界条件**：空文件 → 报错
**异常路径**：格式错 → 报错
**验收口径**：
```bash
python src/cli.py upload ok.csv
```

## 6. 验收矩阵
| R-XX | 方式 | TC | 自动化 |
|:--|:--|:--|:--|
| R-01 | 单测 | TC-R01-001 | 是 |
"""

FIXTURE_INTERROGATION = """# Demo 拷问清单
> 状态：全部回填
## 维度 1：5W2H
- Q1: 谁用？
  - 用户的回答：分析师
- **[推荐默认值]**：分析师
## 维度 2：边界条件
- Q2: 空文件？
  - 用户的回答：报错
- **[推荐默认值]**：报错
## 维度 3：异常路径
- Q3: 网络断？
  - 用户的回答：不涉及
- **[推荐默认值]**：不涉及
## 维度 4：非功能需求
- Q4: 性能？
  - 用户的回答：P99 < 2s
- **[推荐默认值]**：P99 < 200ms
## 维度 5：隐性需求
- Q5: 迁移？
  - 用户的回答：暂不考虑
- **[推荐默认值]**：暂不考虑
## 维度 6：冲突点
- Q6: 快 vs 准？
  - 用户的回答：优先准
- **[推荐默认值]**：优先准
"""

# G0.4 反例：草稿未回填，含"（待填）"和"待用户答卷" → 必须 FAIL
FIXTURE_INTERROGATION_UNFILLED = """# Demo 拷问清单
> 状态：待用户答卷
## 维度 1：5W2H
- Q1: 谁用？
  - 用户的回答：（待填）
- **[推荐默认值]**：分析师
## 维度 2：边界条件
- Q2: 空文件？
  - 用户的回答：（待填）
- **[推荐默认值]**：报错
## 维度 3：异常路径
- Q3: 网络断？
  - 用户的回答：（待填）
- **[推荐默认值]**：不涉及
## 维度 4：非功能需求
- Q4: 性能？
  - 用户的回答：（待填）
- **[推荐默认值]**：P99 < 200ms
## 维度 5：隐性需求
- Q5: 迁移？
  - 用户的回答：（待填）
- **[推荐默认值]**：暂不考虑
## 维度 6：冲突点
- Q6: 快 vs 准？
  - 用户的回答：（待填）
- **[推荐默认值]**：优先准
"""


def run_gate(cmd, cwd):
    """执行门判定命令，返回 (stdout, exit_code)。

    必须走 bash——门判定命令用了单引号包裹的 awk 程序，而 Windows 的
    cmd.exe 不把单引号当引号字符，awk 会收到带引号的乱参数、静默输出空。
    这正是 Goal 门在 Windows 上"看起来跑了但什么都没判"的隐患。
    """
    if _BASH:
        r = subprocess.run([_BASH, "-c", cmd], cwd=cwd, capture_output=True, text=True)
    else:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode


_BASH = shutil.which("bash")
if not _BASH:
    warn("L6", "E6.0", "未找到 bash", "门判定命令含 awk 单引号语法，非 bash 环境可能静默失效")

# ── E6.8 门判定命令不得依赖非标工具 ──
# 实跑发现 G4.3 原判据用了 `bc`，而 Windows Git Bash 不带 bc → command not found。
# 白名单只放 POSIX 常备 + git。
ALLOWED_TOOLS = {"grep", "awk", "sed", "git", "ls", "wc", "cut", "sort", "uniq",
                 "comm", "echo", "cat", "find", "xargs", "tr", "head", "tail",
                 "test", "printf", "sha1sum", "shasum", "diff"}
BANNED_TOOLS = {"bc", "jq", "python", "python3", "perl", "rg", "fd", "yq", "paste"}
# 只扫门定义表格行（以 | 开头且含 G<数字>.<数字>），不扫散文——
# 说明"为什么不用 bc"是合法的，扫散文会误报。
suspicious = set()
for ln in goal_text.splitlines():
    if not (ln.lstrip().startswith("|") and re.search(r'G\d+\.\d+', ln)):
        continue
    for cell in re.findall(r'`([^`]+)`', ln):
        for tok in re.findall(r'(?:^|\||;|\$\()\s*([a-z][a-z0-9_-]{1,12})\b', cell):
            if tok in BANNED_TOOLS:
                suspicious.add(tok)
check("L6", "E6.8", "门判定命令不依赖非常备工具",
      not suspicious,
      f"用到了 {sorted(suspicious)} —— Windows Git Bash 可能没有，门会报 command not found")


probe = Path(tempfile.mkdtemp(prefix="gate_probe_"))
try:
    (probe / "docs" / "loopforge" / "srs").mkdir(parents=True)
    (probe / "docs" / "loopforge" / "srs-raw").mkdir(parents=True)
    (probe / "docs" / "loopforge" / "srs" / "demo.md").write_text(FIXTURE_SRS, encoding="utf-8")
    (probe / "docs" / "loopforge" / "srs-raw" / "demo-interrogation.md").write_text(
        FIXTURE_INTERROGATION, encoding="utf-8")

    # G0.1 六维度标题齐全（应 =6）——不数问题数
    out, _ = run_gate(r"""grep -cE "^## 维度 [1-6]" docs/loopforge/srs-raw/demo-interrogation.md""", probe)
    check("L6", "E6.1", "G0.1 六维度判据可执行且判准", out == "6",
          f"期望 6 实际 {out!r}")

    # G0.2 模糊度（"暂不考虑"是合法答案，不该命中）
    out, _ = run_gate(
        r"""grep -icE "待定|大概|可能|差不多|tbd|todo" docs/loopforge/srs-raw/demo-interrogation.md""", probe)
    check("L6", "E6.2", "G0.2 模糊度判据不误伤'暂不考虑'", out in ("0", ""),
          f"'暂不考虑'被误判为模糊词，实际命中 {out!r}")

    # G0.4 答卷已回填（已回填样例应 PASS）
    out, _ = run_gate(
        r"""grep -cE "（待填）|待用户答卷" docs/loopforge/srs-raw/demo-interrogation.md""", probe)
    check("L6", "E6.2a", "G0.4 已回填答卷应 PASS", out == "0",
          f"已回填样例仍命中待填残留 {out!r} → G0.4 误 FAIL")

    # G0.4 反例：草稿未回填（含"（待填）"和"待用户答卷"）必须 FAIL
    (probe / "docs" / "loopforge" / "srs-raw" / "demo-interrogation.md").write_text(
        FIXTURE_INTERROGATION_UNFILLED, encoding="utf-8")
    out, _ = run_gate(
        r"""grep -cE "（待填）|待用户答卷" docs/loopforge/srs-raw/demo-interrogation.md""", probe)
    check("L6", "E6.2b", "【回归】G0.4 未回填草稿必须 FAIL（防跳过用户答卷）",
          out != "0" and int(out) > 0,
          f"草稿含'（待填）'+'待用户答卷'却判 PASS → 跳过用户答卷漏洞复发（命中 {out!r}）")
    # 还原已回填样例供后续测试用
    (probe / "docs" / "loopforge" / "srs-raw" / "demo-interrogation.md").write_text(
        FIXTURE_INTERROGATION, encoding="utf-8")

    # G1.1 三层级（1 需求 × 3 关键词 = 3）
    out, _ = run_gate(
        r"""awk '/^### R-/{r++} /正常路径|边界条件|异常路径/{k++} END{print r, k}' docs/loopforge/srs/demo.md""",
        probe)
    parts = out.split()
    ok = len(parts) == 2 and int(parts[1]) >= 3 * int(parts[0])
    check("L6", "E6.3", "G1.1 三层级判据可执行且判准", ok, f"输出 {out!r}（需 k>=3r）")

    # G1.2 + G1.4 互斥回归 —— 这两条曾经死锁
    out_g12, _ = run_gate(r"""grep -c '^```' docs/loopforge/srs/demo.md""", probe)
    out_g14, _ = run_gate(
        r"""awk '/^```/{c=!c;next} !c' docs/loopforge/srs/demo.md | grep -cE "已实现|已完成|待定|已确认|讨论中" """,
        probe)
    check("L6", "E6.4", "G1.2 验收口径判据可执行", out_g12 == "2",
          f"期望 2（一个命令块开+闭）实际 {out_g12!r}")
    check("L6", "E6.5", "【回归】G1.2 与 G1.4 不再互斥死锁",
          out_g12 == "2" and out_g14 in ("0", ""),
          f"验收口径含 src/cli.py 却被 G1.4 判为污染 → 死锁复发（G1.2={out_g12} G1.4={out_g14}）")

    # G1.3 恒真假绿回归 —— 清空验收矩阵必须 FAIL
    g13_cmd = (r"""awk '/^## .*验收矩阵/{m=1;next} /^## /{m=0} m&&/^\| R-[0-9]/{n++} """
               r"""/^### R-/{r++} END{print r, n+0}' docs/loopforge/srs/demo.md""")
    out, _ = run_gate(g13_cmd, probe)
    parts = out.split()
    check("L6", "E6.6", "G1.3 完整矩阵应 PASS",
          len(parts) == 2 and int(parts[1]) >= int(parts[0]), f"输出 {out!r}")

    empty = FIXTURE_SRS.replace("| R-01 | 单测 | TC-R01-001 | 是 |\n", "")
    (probe / "docs" / "loopforge" / "srs" / "demo.md").write_text(empty, encoding="utf-8")
    out, _ = run_gate(g13_cmd, probe)
    parts = out.split()
    caught = len(parts) == 2 and int(parts[1]) < int(parts[0])
    check("L6", "E6.7", "【回归】G1.3 空验收矩阵必须 FAIL（防恒真假绿）", caught,
          f"验收矩阵已清空却仍判 PASS → 恒真假绿复发（输出 {out!r}）")
finally:
    shutil.rmtree(probe, ignore_errors=True)


# ─────────────────────────────────────────────────────────────
# 报告
# ─────────────────────────────────────────────────────────────
LEVEL_NAME = {
    "L1": "结构完整性", "L2": "权限不变式", "L3": "引用一致性",
    "L4": "闭环完整性", "L5": "契约一致性", "L6": "门命令实跑",
}
ICON = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ "}

print(f"\nloopforge 套件自校验 —— {ROOT}\n" + "=" * 72)

for lvl in ["L1", "L2", "L3", "L4", "L5", "L6"]:
    rows = [r for r in results if r[0] == lvl]
    if not rows:
        continue
    p = sum(1 for r in rows if r[3] == "PASS")
    f = sum(1 for r in rows if r[3] == "FAIL")
    w = sum(1 for r in rows if r[3] == "WARN")
    print(f"\n{lvl} {LEVEL_NAME[lvl]}  —  {p} PASS / {f} FAIL / {w} WARN")
    print("-" * 72)
    for _, gid, nm, st, dt in rows:
        if st == "PASS":
            continue
        print(f"  {ICON[st]} {gid:26} {nm}")
        if dt:
            print(f"       └─ {dt}")
    if f == 0 and w == 0:
        print("  ✅ 全部通过")

total_p = sum(1 for r in results if r[3] == "PASS")
total_f = sum(1 for r in results if r[3] == "FAIL")
total_w = sum(1 for r in results if r[3] == "WARN")

print("\n" + "=" * 72)
print(f"合计: {total_p} PASS / {total_f} FAIL / {total_w} WARN")
print("判决: " + ("✅ 全绿" if total_f == 0 else f"❌ 未通过 —— {total_f} 项 FAIL"))
sys.exit(1 if total_f else 0)
