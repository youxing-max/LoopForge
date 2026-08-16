# Goal 门清单（Goal Gates）

> 这是 loopforge Loop 的**唯一交付判据**——5 阶段退出时都跑这份清单，全绿才算交付。
> 文件位置：`<项目>/docs/goal.md`
> 生成时机：Stage 0（Loop 启动时由主 Claude + 用户协作填写一次）

---

## 使用方法

1. **Stage 0 启动时**，主 Claude 会和你一起填这份清单——把项目专属的"什么叫完成"显式化
2. **每阶段退出时**，`gate-checker` 按本清单逐条跑判定命令
3. **不通过哪条 → 主 Skill 自动回退到能补该门的最小阶段**
4. **G0.1~G5.6 全绿 = 唯一交付条件**

---

## ⚠️ 执行环境要求（Windows 用户必读）

**判定命令必须在 bash 下执行**，不能用 cmd.exe / PowerShell。

原因：多条门用了单引号包裹的 awk 程序（如 G1.1、G1.3、G1.4）。cmd.exe **不把单引号当引号字符**，awk 会收到带引号的乱参数，**静默输出空字符串且退出码为 0**——门看起来"跑过了"，实际什么都没判。

这是最危险的失效模式：不报错，只是永远判不出问题。

```bash
# 验证你的环境
awk '/^x/{print "ok"}' /dev/null && echo "bash 正常"

# gate-checker 调用判定命令时应显式走 bash
bash -c '<判定命令>'
```

`scripts/validate_suite.py` 的 L6 层会实际执行这些命令做回归——若你改了判据，跑一次它。

---

## Stage 0 必填变量

门判定命令引用这些变量。**不填就等于沿用 Python/单体布局假设，换栈后静默失效。**

```bash
# ── 路径（G5.x 角色越权检测全族引用）──
IMPL_ROOT="src/"              # Maven: src/main/  Gradle: src/main/  Go: internal/  Node: src/
TEST_ROOT="tests/"            # Maven: src/test/  Gradle: src/test/  Go: 同包*_test.go  Node: tests/

# ── 命令（G3.x 引用）──
TEST_CMD="python tests/run_<组>.py"      # Maven: mvn -q test   Go: go test ./...   Node: npx jest --ci
RUNNER="tests/run_<组>.py"               # runner 文件路径，G3.6 读它的 KNOWN_FAILURES
TYPE_CMD="mypy src/"                     # Java: mvn -q compile  Go: go vet ./...   TS: tsc --noEmit

# ── 多批次项目追加变量（单批次项目留空）──
# G0.4 契约门：批次 0 交付后冻结，每次验收前跑
CONTRACT_CMD="python tests/run_contract.py"   # 与你项目的 run_contract 路径一致
# G3.7 跨批回归门：本批次改动没破坏已完成批次
FULL_TEST_CMD="for r in tests/run_*.py; do \$r || exit 1; done"   # 跑全部 runner
# 当前批次标识（用于 loop-status 路径与 G5.6 白名单）
BATCH="batch-X"   # 例如 batch-A
```

### 换栈适配表

| 栈 | IMPL_ROOT | TEST_ROOT | TEST_CMD | TYPE_CMD |
|:--|:--|:--|:--|:--|
| Python/pytest | `src/` | `tests/` | `python tests/run_<组>.py` | `mypy src/` |
| **Java/Maven** | **`src/main/`** | **`src/test/`** | `mvn -q -Dgroups=<组> test` | `mvn -q compile` |
| Go | `internal/` `cmd/` | `*_test.go`（同包） | `go test ./... -tags=<组>` | `go vet ./...` |
| Node/Jest | `src/` | `tests/` | `npx jest --selectProjects <组>` | `tsc --noEmit` |

> 🔴 **Java/Go 用户必读**：
> - **Maven/Gradle**：实现在 `src/main/java`、测试在 `src/test/java`，**都在 `src/` 下**。沿用默认值 → `impl-coder` 改测试凑绿时 G5.1 恒为 0 → **永远绿灯**。失效方式是静默放行不是报错。
> - **Go**：测试文件与实现同包同目录（`foo.go` / `foo_test.go`），**路径前缀无法区分**。G5.1/G5.2 需改为按文件名后缀判：`grep -c '_test\.go$'`。
> - 这两种布局下，路径前缀式隔离检测**从原理上就不成立**，必须改判据而非改路径。

### 前置检查（Stage 0 退出前跑）

```bash
git rev-parse --git-dir >/dev/null 2>&1 || echo "🔴 非 git 仓库 → G5.x 全族失效"
test -f .gitignore || echo "🔴 无 .gitignore → 跑一次测试即触发 G5.3 活锁"
grep -qE '__pycache__|target/|node_modules|\.pytest_cache' .gitignore || echo "🔴 .gitignore 未覆盖测试产物"
command -v bash >/dev/null || echo "🔴 无 bash → awk 判据静默失效"
test -f docs/type-baseline.txt || echo "⚠️  无类型基线 → G3.5 无法判'不劣化'"
```

---

## Goal 门清单（统一集合）

> 填空式：每条 Goal 门有 4 个字段——**自动判定命令 / 通过判据 / 失败回退到 / 严重级**

### Stage 0.5 Goal 门（项目目标书阶段）

| Goal | 内容 | 自动判定命令 | 通过判据 | 失败回退到 | 严重 |
|:-----|:-----|:--------------|:---------|:-----------|:-----|
| **G0.5** | goal-doc 七大章节齐 | `for s in "## 0" "## 1" "## 2" "## 3" "## 4" "## 5" "## 6" "## 7"; do grep -qE "^$s\\." docs/goal-doc.md && echo ok || echo MISSING:$s; done \| grep -c MISSING` | = 0（七大章节标题都在） | Stage 0.5 补章节 | 阻断 |
| **G0.6** | 范围外 ≥ 1 条 | `grep -cE "P[0-9]\|未来\|暂不\|不做" docs/goal-doc.md` | ≥ 1 | Stage 0.5 加范围外声明 | 警告 |
| **G0.7** | 用户已确认 | `grep -cE "\[待用户拍板\]\|\[待确认\]\|\[待澄清\]" docs/goal-doc.md` | ≤ 3 | Stage 0.5 重审循环 | 警告 |

> **为什么 G0.5~G0.7 是必加的**：没有 goal-doc 七章节全章检查，主 Claude 容易让 agent 跳过任一章（如漏画系统边界、漏写范围外）—— 漏一章 = 项目分解有盲点，Stage 1 拷问会一直撞同一面墙。
>
> **G0.5 模板**：把 `<SKILL_DOCS>/goal-doc-template.md` 的 §0~§7 标题固定为编号样式（`## 0. 一句话定义`），避免漂移。若你的项目用了别的编号习惯，替换这七行为你的标题前缀再扫。
>
> `<SKILL_DOCS>` = skill 安装目录下的 `docs/`：全局 `$HOME/.claude/skills/loopforge/docs/`（Windows PowerShell 下同一目录写作 `%USERPROFILE%\.claude\skills\loopforge\docs\`）；本地 `<项目>/.claude/skills/loopforge/docs/`。——**不是**本文件所在的项目 `docs/`。

### Stage 1 Goal 门（拷问阶段）

| Goal | 内容 | 自动判定命令（示例） | 通过判据 | 失败回退到 | 严重 |
|:-----|:-----|:---------------------|:---------|:-----------|:-----|
| **G0.1** | 6 维度全拷问且非空壳 | `awk '/^## 维度 [1-6]/{d++;q[d]=0;next} /^- *Q[0-9]/{q[d]++} /^\| *[A-Z][0-9]/{q[d]++} END{for(i=1;i<=d;i++) if(q[i]==0) bad++; print d, bad+0}'` | 输出 `6 0`（六维度齐 **且每维度非空**） | Stage 1 补拷问 | 阻断 |
| **G0.2** | 无未决项 | `grep -icE "待定\|待确认\|TBD\|TODO\|回头再说\|再说吧" docs/srs-raw/<需求>-interrogation.md` | 命中 = 0 | Stage 1 重拷问 | 阻断 |
| **G0.3** | 冲突已裁决 | `awk '/^\| *C[0-9]/{t++; if($NF ~ /^ *\|? *$/ \|\| $0 ~ /（待填）/) bad++} END{print t+0, bad+0}'` | 第二个数 = 0（冲突表每行裁决列非空） | Stage 1 重拷问 | 阻断 |
| **G0.4** | 答卷已回填 | `grep -cE "（待填）\|待用户答卷" docs/srs-raw/<需求>-interrogation.md` | 命中 = 0（无待填残留 + 回填状态非"待用户答卷"） | Stage 1 回用户答卷 | 阻断 |

> **G0.4 是 v2.4 新增门，堵的是流程意图与判据的缺口**：
> 原 G0.1~G0.3 只查问卷**结构**（6 维度齐/无未决词/冲突裁决列非空），**从不查答卷列填没填**。实测：req-interrogator 产出草稿后，主 Claude 跳过用户答卷直接判 G0.1~G0.3 全绿冲进 Stage 2——把所有需求假设压在 agent 推荐默认值上，而流程意图（NEWBIE-GUIDE §2「回答问题 / 你答 Q1=A」）明确要用户答卷。
>
> 这是**判据比流程意图松**导致的漏洞：流程要问你答卷，判据没卡这一步。G0.4 补上——草稿产出"回填状态=待用户答卷"且含"（待填）"时命中，必须走完修订轮回填才过。
>
> **与推荐默认值的关系**：v2.4 给每维度加 `[推荐默认值]`，用户可选"接受推荐默认值"跳过逐 Q 答——但**仍必须显式回填**（答卷列填"接受推荐默认值"，回填状态改"全部回填"），不能留"（待填）"。默认值省的是用户体力，不省"用户拍板"这个动作。

> **三条判据都被实跑推翻过，这是修正版**：
> - **G0.1** 旧判据 `grep -c "Q[0-9]" ≥29` 把**数量当覆盖度**——简单需求 7 问覆盖 6 维度会被误判不过，逼 agent 凑无意义问题。中间版本改为只查标题齐全，但实测**六个空标题、零问题零答卷也判 PASS**（空壳过门）。现版本同时查"每维度至少 1 问"。
> - **G0.2** 旧词表含「可能/大概/差不多」。实测「重试 3 次…极端情况下**可能**丢失最后一批数据，接受」——这是已裁决的完整答案，却被判模糊。中文异常路径与风险描述天然用这些词，而维度 3、6 强制要写 → **近乎恒 FAIL**。现词表只留真正的未决词。
> - **G0.3** 旧判据 `grep -c "用户裁决"` 会命中**表头那一行**（永久虚高 +1），而真正的裁决内容「选 A，极简优先」一个都不命中；且"冲突点数"这个分母无命令产出。现版本改为结构化查冲突表的裁决列是否留空。

### Stage 2 Goal 门（SRS 起草）

| Goal | 内容 | 自动判定命令（示例） | 通过判据 | 失败回退到 | 严重 |
|:-----|:-----|:---------------------|:---------|:-----------|:-----|
| **G1.1** | 每条 R-XX 三层级 | `awk '/^### R-/{if(n)printf "%s:%d ",n,c; n=$2;c=0} /\*\*(正常路径\|边界条件\|异常路径)\*\*/{c++} END{if(n)printf "%s:%d\n",n,c}' docs/srs/<需求>.md` | **每个** `R-XX:N` 的 N ≥ 3 | Stage 2 补起草 | 阻断 |
| **G1.2** | 每条 R-XX 验收口径含命令 | `awk '/^### R-/{if(n)printf "%s:%d ",n,c; n=$2;c=0} /^```/{c++} END{if(n)printf "%s:%d\n",n,c}' docs/srs/<需求>.md` | **每个** `R-XX:N` 的 N ≥ 2（开+闭） | Stage 2 补起草 | 阻断 |
| **G1.3** | 验收矩阵无遗漏 | 见下方脚本（**去重 R 编号**比对） | 未覆盖集合为空 | Stage 2 补起草 | 阻断 |
| **G1.4** | 纯度达标 | `awk '/^```/{c=!c;next} !c' docs/srs/<需求>.md \| sed 's/`[^`]*`//g' \| grep -cE "已实现\|已完成\|待定\|已确认\|讨论中"` | 命中 = 0 | Stage 2 重起草 | 阻断 |
| **G1.5** | 每条 R-XX 标优先级 | `awk '/^### R-/{if(n)printf "%s:%d ",n,c; n=$2;c=0} /优先级/&&/P[012]/{c++} END{if(n)printf "%s:%d\n",n,c}' docs/srs/<需求>.md` | **每个** `R-XX:N` 的 N ≥ 1 | Stage 2 补起草 | 警告 |

**G1.3 判定脚本**（`grep -c` 数行数会被"一条需求占多行"蒙混，必须去重编号）：

```bash
R=$(grep -oE '^### (R-[0-9]+)' docs/srs/<需求>.md | awk '{print $2}' | sort -u)
M=$(awk '/^## .*验收矩阵/{f=1;next} /^## /{f=0} f' docs/srs/<需求>.md | grep -oE 'R-[0-9]+' | sort -u)
comm -23 <(echo "$R") <(echo "$M")     # 有输出 = 这些需求没进验收矩阵
```

> **Stage 2 五条门全部重写过，原因**：
> - **G1.1/G1.2/G1.5 旧判据是全文计数，与"每条需求齐不齐"无关**。实测双向误判：三层级写在一行 → r=1,k=1 → 误 FAIL；R-01 重复写 6 次「正常路径」而 R-02 一个层级都没有 → r=2,k=6 → **误 PASS**。G1.2 同理——两条需求验收口径一个字没写，靠附录两个无关代码块凑到 4 就过。现版本全部改为**逐需求分段计数**。
> - **G1.3 换位置的恒真假绿**：中间版本改为锁验收矩阵章节内计数行数，但实测 R-01 占 3 行、R-02 零覆盖 → n=3 ≥ r=2 → 仍 PASS。**数行数不等于数覆盖**，现改为去重编号求差集。
> - **G1.2 ↔ G1.4 曾是无解死锁**：G1.2 要求验收口径写命令块，G1.4 禁止出现 `src/*.py`——但验收命令必然是 `python src/cli.py`。已修：G1.4 跳过代码块 + 从词表移除代码路径，并加 `sed` 去行内反引号。
> - **G1.5 旧判据要求精确字面量 `**优先级**：P0`（含全角冒号）**，而 `srs-drafter` 自带的约束模板 R-30/31/32 根本没有优先级字段 → 照自家模板写必 FAIL。现版本放宽为"同段内出现优先级与 P0/P1/P2"。

### Stage 3 Goal 门（设计文档）

> ⚠️ **本族原有 3 条门调用 `doc-consistency-checker` agent —— 该 agent 不在套件内，且 `gate-checker` 没有 Agent 工具（`tools: Read, Bash, Grep, Glob`），物理上调不动任何 agent**。按 gate-checker 自身规则「无法判定 ≠ PASS」，三条阻断门恒 FAIL → **Stage 3 结构性无法退出**。已全部改写为 bash 可直接执行，或移交 `goal-auditor`。

| Goal | 内容 | 自动判定命令 | 通过判据 | 失败回退到 | 严重 |
|:-----|:-----|:--------------|:---------|:-----------|:-----|
| **G2.1** | 引用单向性 | `grep -oE '\(\.{0,2}/?docs/[a-z-]+/' docs/design/<需求>.md \| grep -cvE 'docs/(srs\|design\|physics)/'` | =0（设计只可引用 SRS/同层/推导书，不引用下游 verification/test/audit） | Stage 3 重写 | 阻断 |
| **G2.2** | 内部一致 | **移交 `goal-auditor` 维度 F**（价值判断，非机械可判） | 审计无 🔴 | Stage 3 重写 | 阻断 |
| **G2.3** | 纯度 | `awk '/^```/{c=!c;next} !c' docs/design/<需求>.md \| sed 's/`[^`]*`//g' \| grep -cE "已实现\|已完成\|待定\|已确认\|讨论中\|✅\|❌"` | =0 | Stage 3 重写 | 阻断 |
| **G2.4** | R-XX 全覆盖设计 | 同 G1.3 脚本，比对 SRS 需求编号 vs 设计文档出现的编号 | 未覆盖集合为空 | Stage 3 补设计 | 阻断 |
| **G2.5** | 接口签名明确 | **移交 `goal-auditor` 维度 F**（跨语言签名正则不可能统一） | 审计确认关键接口有类型 | Stage 3 补设计 | 警告 |

> **G2.4 旧判据 `awk '...{c++}/^## /&&!/^### /'` 没有 END 块，r/c 算完从不输出** —— 实际打印的是被 awk 默认规则输出的 `## 1. 架构`、`## 2. 数据流` 两行，与判据毫无关系，阻断门退化成人肉判断。
>
> **G2.5 旧正则 `def [a-z_]+\(.*\):` 判反了**：它要求 `)` 紧跟 `:`。实测 `def upload(path: str) -> int:` → 命中 **0**；`def upload(path, mode):` → 命中 **1**。门名叫"接口签名有类型"，结果**带类型注解的漏检、裸签名算通过**。而且 Java/Go/TS 的签名形态完全不同，单一正则无解 → 移交审计。

### Stage 4 Goal 门（Loop 验证）

| Goal | 内容 | 自动判定命令 | 通过判据 | 失败回退到 | 严重 |
|:-----|:-----|:--------------|:---------|:-----------|:-----|
| **G3.1** | 测试全 PASS | `$TEST_CMD; echo $?`（`TEST_CMD` 见 Stage 0 变量） | exit = 0 | Stage 4 修复代码 | 阻断 |
| **G3.2** | 零可疑 skip | `grep -rE '@pytest\.mark\.skip\|@Disabled\|t\.Skip\|it\.skip' $TEST_ROOT \| grep -cE '未实现\|待定\|未明确\|暂不\|TODO\|not implemented'` | =0 | Stage 4 重写测试 | 阻断 |
| **G3.3** | 零弱断言 | **移交 `goal-auditor` 维度 C**（断言强不强是价值判断） | 审计无弱断言 P1 | Stage 4 补断言 | 阻断 |
| **G3.4** | ~~回归全绿~~ | **已并入 G3.1**（原判据 `pytest tests/test_R*.py -v` 与 G3.1 重复，且 glob 无匹配时 pytest 退 4、零用例退 5，判据没说看什么） | — | — | — |
| **G3.5** | 类型不劣化 | `$TYPE_CMD 2>&1 \| grep -c "error:"` 与 `docs/type-baseline.txt` 比对 | ≤ 基线值 | Stage 4 修复类型 | 警告 |
| **G3.6** | **KNOWN_FAILURES 为空** | `awk '/KNOWN_FAILURES *=/{f=1} f&&/\]/{f=0} f&&/["'"'"']/{n++} END{print n+0}' $RUNNER` | =0 | Stage 4 修复代码 | 阻断 |

> **G3.6 是新增门，堵的是套件最大的绿化通道**：`KNOWN_FAILURES` 里的测试标 `[WARN]` 不阻止验收，而 `test-author` 独占 runner 写权 —— 它把红测试登记进去就能合法变绿。原设计中 G3.1 只看 exit code、G3.2 只 grep skip、`goal-auditor` 红线**只查 KNOWN_GAPS 从不查 KNOWN_FAILURES**，全链路无一处覆盖。铁律 1「失败可见」被架空。
>
> **G3.2 旧正则 `skip\(reason="未实现` 要求关键词紧跟 `reason="`**。实测 3 个可疑 skip 只抓到 1 个：漏 `skip(reason="分页功能未实现")`（关键词不在开头）、漏 `skip("未实现")`（位置参数）。现改为**先取 skip 行、再查可疑词**，且覆盖 JUnit/Go/Jest 的等价物。实测 3/3 抓全，合法 skip（人工判断类、依赖已删类）未误伤。
>
> **G3.5 需要基线文件**。原判据写"新增 = 0"但套件里没有任何地方存基线 → 无法判定。Stage 0 须生成 `docs/type-baseline.txt`。工具未装时按 `[无法判定]` 处理（回 Stage 0 决定是否删除此门），不要让一条警告级门变成阻塞噪音。

### Stage 5 Goal 门（独立审计）

| Goal | 内容 | 自动判定命令 | 通过判据 | 失败回退到 | 严重 |
|:-----|:-----|:--------------|:---------|:-----------|:-----|
| **G4.1** | Round 1 审计完成 | `ls docs/audit/goal-audit-round1-*.md 2>/dev/null \| wc -l` | ≥1 | Stage 5 跑 Round 1 | 阻断 |
| **G4.2** | Round 1 P0/P1 全修复 | 见下方脚本（逐条比对 Round 1 的 P0/P1 编号 vs fixes 记录） | 未修复集合为空 | Stage 4 修复 | 阻断 |
| **G4.3** | Round 2 无 P0/P1 | `awk '/\[AUDIT VERDICT\]/{f=1} f&&match($0,/P0: *[0-9]+/){p0=substr($0,RSTART+4,RLENGTH-4)+0;got=1} f&&match($0,/P1: *[0-9]+/){p1=substr($0,RSTART+4,RLENGTH-4)+0} END{if(!got) print "NOBLOCK"; else print p0+p1}' docs/audit/goal-audit-round2-*.md` | 输出 `0`（`NOBLOCK`=无法判定，非 PASS） | Stage 4 修复后重 Round 2 | 阻断 |

**G4.2 判定脚本**（`ls` 只能判文件在不在，"修复记录完整"原本是人工判断）：

```bash
ISSUES=$(grep -oE '\*\*(P0|P1)-[0-9]+' docs/audit/goal-audit-round1-*.md | grep -oE '(P0|P1)-[0-9]+' | sort -u)
FIXED=$(grep -oE '(P0|P1)-[0-9]+' docs/audit/round1-fixes.md | sort -u)
comm -23 <(echo "$ISSUES") <(echo "$FIXED")     # 有输出 = 这些问题没有修复记录
```

> **G4.3 三个 bug 一起修的**（实跑发现）：
> 1. 原判据末尾 `| bc` —— **Windows Git Bash 不带 `bc`**，直接 `command not found`
> 2. 改 awk 求和后仍错：正则同时命中总评表格行 `| P0（阻断） | 0 |` 和结构化块，**P1 的值被数两次**
> 3. 最阴的一条：报告若缺 `[AUDIT VERDICT]` 块，求和输出 `0` → **判 PASS**。但 0 的含义是"没找到数据"不是"零缺陷" —— 审计报告格式写错反而放行交付。现改为输出 `NOBLOCK`，按"无法判定"处理。
>
> **依赖提醒**：判定命令只用 `grep/awk/sed/git`，不用 `bc`/`paste`/`comm` 之外的工具。`comm` 用在 G1.3/G2.4/G4.2，Git Bash 自带。
>
> **G4.x 回退落点原本三处矛盾**：`SKILL.md` 说回 Stage 4、本文件映射表说回 Stage 5、逐门字段又混着写。已统一为 **Stage 4**（问题都要靠改代码/改测试修，Stage 5 只是重跑审计）。

### 多批次项目追加门（大型项目必加，单需求项目跳过）

> 完整用法见 `<SKILL_DOCS>/large-project-guide.md`。单个需求走一遍 Loop 不需要这两条。

| Goal | 内容 | 自动判定命令 | 通过判据 | 失败回退到 | 严重 |
|:-----|:-----|:--------------|:---------|:-----------|:-----|
| **G0.4** | 契约未破坏 | `$CONTRACT_CMD; echo $?` | =0 | **停止，回批次 0 评审** | 阻断 |
| **G3.7** | 跨批回归 | `$FULL_TEST_CMD; echo $?` | =0 | 回退本批 Stage 4 | 阻断 |

> **G0.4 单列一条门的原因**：契约破坏与普通测试失败性质不同。普通失败是"这批没做好"，契约失败是"地基被改了，所有已完成批次的验收全部作废"。它每个批次每一轮都要跑，秒级无 I/O。
>
> **G3.7 是多批次的必需品**：没有它就会出现"A 批次绿了，做 B 的时候把 A 改挂了，没人发现"。单批次项目它和 G3.1 重复，可以不要。

---

### 全阶段 Goal 门（G5.x 角色越权检测）

> **每个阶段退出时都跑**。这是职责隔离的**事后硬关卡**——不依赖 agent 自觉。
> 契约定义见 `<SKILL_DOCS>/role-permission-matrix.md`。

#### 前提：派工基线协议（不做这步，G5.x 全族失效）

每次派 agent 干活前，主 Claude 必须：

```bash
# 1. 先更新状态表（把编排自身的改动并入基线，不算到 agent 头上）
#    写 docs/loop-status.md 的派工记录块
# 2. 打基线
git add -A && git commit -q -m "pre-dispatch: <agent> round <N>"
# 3. 再派 agent
```

派工后 `gate-checker` 用**工作区状态**判定：

```bash
git status --porcelain | cut -c4-     # 列出该 agent 的全部改动
```

**三条硬要求**：

| # | 要求 | 不满足的后果 |
|:--|:--|:--|
| 1 | 项目是 git 仓库 | G5.x 全族无法判定 |
| 2 | **有 `.gitignore` 覆盖测试产物**（`__pycache__/` `*.pyc` `target/` `node_modules/` `.pytest_cache/`） | 跑一次测试即产生未忽略文件 → G5.3 恒判越权 → **活锁** |
| 3 | **先记状态再打基线，最后派工**（顺序不可颠倒） | 主 Claude 的 loop-status 改动被算进 agent 越权 → **活锁** |

> 用 `git status --porcelain` 而**不是** `git diff --name-only HEAD`：后者**看不见新建文件**（untracked），而"新建一个测试文件"恰是越权最自然的形态。实测：agent 新建 `tests/test_injected.py` 后 `git diff` 只列 `src/app.py`，G5.1 判 PASS 放行。

#### 路径变量（Stage 0 必填）

不同技术栈的实现/测试目录不同，**必须在此声明**，G5.x 全族引用这两个变量：

```bash
IMPL_ROOT="src/"           # Maven: src/main/   Go: internal/,cmd/   Node: src/
TEST_ROOT="tests/"         # Maven: src/test/   Go: *_test.go        Node: tests/
```

> 🔴 **Maven/Gradle 用户必看**：Java 实现在 `src/main/java`、测试在 `src/test/java`，**都在 `src/` 下**。若沿用默认值，`impl-coder` 改测试断言凑绿时 `grep -c '^tests/'` 恒为 0 → **G5.1 永远绿灯**。失效方式是**静默放行，不是报错**——套件最核心的关卡变成摆设，而自校验照样全绿。

#### 门定义

| Goal | 内容 | 自动判定命令 | 通过判据 | 失败处置 | 严重 |
|:-----|:-----|:--------------|:---------|:---------|:-----|
| **G5.1** | impl-coder 未越权 | `git status --porcelain \| cut -c4- \| awk -v ok="$TEST_ROOT" 'index($0,ok)==1{print}' \| wc -l` | =0（派 impl-coder 时） | 回滚该 agent 改动 + 重派 test-author | 阻断 |
| **G5.2** | test-author 未越权 | `git status --porcelain \| cut -c4- \| awk -v ok="$IMPL_ROOT" 'index($0,ok)==1{print}' \| wc -l` | =0（派 test-author 时） | 回滚 + 重派 impl-coder | 阻断 |
| **G5.3** | test-runner 零改动 | `git status --porcelain \| wc -l` | =0（要求 .gitignore 已覆盖测试产物） | 回滚 + 排查 Bash 写入路径 | 阻断 |
| **G5.4** | goal-auditor 只写 audit/ | `git status --porcelain \| cut -c4- \| grep -v '^docs/audit/' \| grep -v '^docs/loop-status.md$' \| wc -l` | =0（派 goal-auditor 时） | 回滚 + 审计作废重审 | 阻断 |
| **G5.5** | design-author 只写 design/ | `git status --porcelain \| cut -c4- \| grep -v '^docs/design/' \| grep -v '^docs/loop-status.md$' \| wc -l` | =0（派 design-author 时） | 回滚 + 重派 | 阻断 |
| **G5.6** | 改动落在派工允许范围内（**覆盖主 Claude 与 gate-checker 自身**） | 见下方脚本 | 无越界路径 | 记越权事件 + 作废本轮 | 阻断 |

> **G5.1/G5.2 都用 awk 边界检查，不用 `grep -c "^$ROOT"`** —— 实跑发现 `grep -c "^src/"` 会把 `src_evil/x.py` 也算成 `src/` 下的合规路径（前缀重叠）。awk 版要求 `src/` 之后必须是路径分隔符 `/` 或行尾才算子路径。G5.4/G5.5 是白名单路径（保留路径之外都判越权），前缀重叠反倒是符合预期的行为 —— 不动它们。

#### G5.6 自动判定（取代原"人工核对"）

原判据字面写的是"人工核对"，却是阻断级、每阶段都跑 —— 等于每个阶段退出都卡一个人工门。改为读 `docs/loop-status.md` 的机读派工块自动判：

`docs/loop-status.md` 必须含（主 Claude 在打基线**之前**写）：

```
<!-- DISPATCH -->
round: 4-3
agent: impl-coder
allowed: src/
<!-- /DISPATCH -->
```

判定命令（注意 `grep -v "^${ALLOWED}"` 漏判前缀重叠，**改用 awk 边界检查**）：

```bash
ALLOWED="src/"
git status --porcelain | cut -c4- | awk -v ok="${ALLOWED}" '
{
  p = $0
  if (p ~ "^" ok) {
    rest = substr(p, length(ok)+1)
    if (rest != "" && rest !~ "/") print p " <-- PREFIX OVERLAP"
  } else { print p }
}' | grep -v '^docs/loop-status.md$'
# 有输出 = 越权，输出即越界路径清单
```

> **为什么不用 `grep -v "^src/"`**：实跑发现 `grep -v "^src/"` 会把 `src_evil/file.py`、`src-backup/x.py` 算合规 —— 因为它们以 `src` 开头，不是以 `src/` 开头。**前缀重叠路径静默漏抓**。awk 修法要求 `src/` 之后必须是路径分隔符 `/` 或行尾才算合规子路径。

这条同时覆盖**主 Claude 自己**——若它绕过 agent 直接改 `src/`，而当轮 `allowed:` 不含 `src/`，一样被抓。原表六条只查五个 agent，能力最强的主 Claude 和 gate-checker 自身反而不在检测范围。

#### 非 git 仓库的替代方案

```bash
# 派工前
find "$IMPL_ROOT" "$TEST_ROOT" -type f | sort | xargs -r sha1sum > /tmp/snap.pre
# 派工后比对
find "$IMPL_ROOT" "$TEST_ROOT" -type f | sort | xargs -r sha1sum > /tmp/snap.post
diff /tmp/snap.pre /tmp/snap.post | grep '^[<>]' | awk '{print $NF}' | sort -u
```

> 原方案硬编码 `-name '*.py' -o -name '*.ts'`，Java/Go 项目采集为空集 → 比对恒等 → **静默失效**。上面改为不限扩展名。`md5sum` 在 macOS 不存在，改用 `sha1sum`（或 `shasum`）。

---


## Goal 门回退映射表（关键）

> 当某条 Goal 门不通过时，主 Skill 自动查这张表回到能补的最小阶段。

### 按门号回退

| Goal 门 | 不通过 → 回退到 | 修复行动 |
|:--------|:---------------|:---------|
| **G0.5 ~ G0.7** | Stage 0.5（修目标书） | 重跑 `goal-architect` 补章节/范围外/待确认 |
| G0.1 ~ G0.4 | Stage 1（重拷问） | 重跑 `req-interrogator`，针对缺口补拷问；G0.4 不过=回填用户答卷
| G1.1 ~ G1.5 | Stage 2（重起草） | 重跑 `srs-drafter`，针对缺口补起草 |
| G2.1 ~ G2.5 | Stage 3（重写设计） | 重跑 `design-author` → 再判 |
| G3.1 ~ G3.5 | Stage 4（修代码/重跑 Loop） | 缺实现 → `impl-coder`；弱断言/可疑 skip → `test-author` |
| **G5.1 ~ G5.6** | **当前阶段（结果作废）** | **回滚越权 agent 的改动 → 重派正确角色** |
| G4.1 ~ G4.3 | **Stage 4**（修代码后重跑审计轮次） | Round 1 失败→修→Round 2；Round 2 失败→修→Round 3 |

### 按失败类型回退（非门号类，原表缺失）

门判定除 PASS/FAIL 外还有三类结果，它们**不对应任何门号**，原回退表查不到落点 —— 而"判定命令跑不动"恰恰必然发生：

| 失败类型 | 含义 | 回退到 | 修复行动 |
|:--|:--|:--|:--|
| `[无法判定]` | 命令报错 / 文件缺失 / 输出为空但判据要求数值 | **Stage 0** | 修 `docs/goal.md` 该条判定命令；修完重跑本阶段判定 |
| `[门定义错误]` | 判定命令语法错、引用不存在的组件 | **Stage 0** | 同上。**这类必须修门，不是修产物**——重跑一万次 agent 也改变不了命令跑不动 |
| `[需人工]` | 判据本身是价值判断（gate-checker 被禁止做判断） | **主 Claude 裁决** | 主 Claude 判定通过/不通过并记入 loop-status；连续 2 次拿不准 → 升级给人 |

> **为什么必须有这三行**：`gate-checker` 遇到跑不动的命令会报 `[无法判定]`，按其自身规则「无法判定 ≠ PASS」视同 FAIL。若回退表查不到落点，Loop 就卡死在该阶段——反复重跑同一个 agent，而问题根本不在 agent 身上。

**回退原则**：回到能补该门的**最小**阶段，不一定回到 Stage 1。

---

## Goal 门自动化

> 每阶段退出时由主 Skill 调 **`gate-checker` agent**（不是 `goal-auditor`）跑本阶段的门。
> `gate-checker` 只机械执行判定命令，不做价值判断；`goal-auditor` 只在 Stage 5 做双轮独立审计。两者分属不同 agent —— 自检形成的宽松印象不能污染终审。

### 判定规则（`gate-checker` 遵守）

| 结果 | 条件 |
|:--|:--|
| ✅ PASS | 命令跑通 + 输出满足通过判据 |
| ❌ FAIL | 命令跑通 + 输出不满足判据 |
| ⚠️ 无法判定 | 命令报错 / 文件缺失 / 依赖缺失 / **输出为空但判据要求数值** → **不算 PASS**，回 Stage 0 修判据 |

**三条执行纪律**：

1. **必须走 `bash -c`** —— 多条门用单引号包裹的 awk，cmd.exe 下会静默输出空且退出码 0
2. **比数值不比退出码** —— `grep -c` 只要命中 ≥1 行就退 0，而多数门的判据是"命中数 = N"或"每条需求 ≥3"。只看退出码会让这些门恒真
3. **零命中的退出码是 1，不是错误** —— `grep -c` 无匹配时退 1。对"命中 = 0"类判据（G0.2/G1.4/G3.2/G5.1/G5.2），**退 1 且输出 0 就是 PASS**，不要判成"无法判定"

> 第 2、3 条是参考实现最容易写错的地方：若按 `returncode == expected` 判，G0.2 这类"命中=0 才过"的门会整体反向。

### 参考实现骨架

```python
# scripts/check_goal_gates.py —— 按你项目的 docs/goal.md 填 GATES
import subprocess, sys, shutil

BASH = shutil.which("bash")   # 必须走 bash，见纪律 1

def run(cmd):
    r = subprocess.run([BASH, "-c", cmd], capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

def check(gate_id, cmd, predicate, desc):
    """predicate: 拿 stdout 判 True/False。不看 returncode —— 见纪律 2/3"""
    out, _ = run(cmd)
    if out == "" and predicate is not None:
        print(f"  ⚠️  {gate_id} 无法判定（输出为空）"); return None
    ok = predicate(out)
    print(f"  {'✅' if ok else '❌'} {gate_id} {desc}  [{out}]")
    return ok

# 判据全部对照 docs/goal.md 的「通过判据」列，不要另写一套
GATES = [
    ("G0.1", """awk '/^## 维度 [1-6]/{d++;q[d]=0;next} /^- *Q[0-9]/{q[d]++} """
              """END{for(i=1;i<=d;i++) if(q[i]==0) bad++; print d, bad+0}' docs/srs-raw/*-interrogation.md""",
     lambda o: o.split() == ["6", "0"], "6 维度齐且非空壳"),

    ("G0.2", """grep -icE "待定|待确认|TBD|TODO|回头再说" docs/srs-raw/*-interrogation.md""",
     lambda o: o == "0", "无未决项"),

    ("G1.1", """awk '/^### R-/{if(n)printf "%s:%d ",n,c; n=$2;c=0} """
              """/\\*\\*(正常路径|边界条件|异常路径)\\*\\*/{c++} END{if(n)printf "%s:%d\\n",n,c}' docs/srs/*.md""",
     lambda o: all(int(x.split(":")[1]) >= 3 for x in o.split()), "每条需求三层级齐"),

    ("G3.6", """awk '/KNOWN_FAILURES *=/{f=1} f&&/\\]/{f=0} f&&/["'"'"']/{n++} END{print n+0}' $RUNNER""",
     lambda o: o == "0", "KNOWN_FAILURES 为空"),
]

failed = [g for g, c, p, d in GATES if check(g, c, p, d) is not True]
if failed:
    print(f"\n❌ {len(failed)} 门未通过: {failed} → 查回退映射表")
    sys.exit(1)
print("\n✅ 全部通过")
```

> Stage 3 的 G2.2/G2.5 与 Stage 4 的 G3.3 **不在这个脚本里** —— 它们是价值判断（内部一致性、接口签名跨语言形态、断言强不强），已移交 `goal-auditor`。原版本让 `gate-checker` "调 `doc-consistency-checker` agent"，但那个 agent 不在套件内，且 `gate-checker` 的 `tools:` 没有 Agent —— 物理上调不动，四条阻断门恒 [无法判定]，Stage 3/4 结构性无法退出。

---

## 项目定制指南

每个项目的 Goal 门都不一样，按你的项目改：

### 必改项

| 字段 | 改什么 |
|:-----|:-------|
| **自动判定命令** | 改为你项目的实际路径和命令 |
| **Goal 门内容** | 删去不适用的（如非物理项目无 G6 物理可信度）；加上项目专属的（如合规、隐私） |
| **回退映射** | 改阶段映射关系 |

### 建议加的项目专属门

| 项目类型 | 建议加的 Goal 门 |
|:---------|:-----------------|
| **Web 后端** | API 契约冻结、SLA 指标压测、SQL 注入扫描 |
| **数据处理** | 数据血缘、Schema 演进、幂等性验证 |
| **嵌入式** | 资源占用（ROM/RAM）、中断延迟、掉电恢复 |
| **桌面应用** | 跨平台兼容性、安装包大小、冷启动时间 |
| **AI/ML** | 模型版本冻结、推理延迟、偏差检测 |

---

## 修订记录

| 版本 | 日期 | 变更 |
|:-----|:-----|:-----|
| v1.0 | 2026-08-09 | 初版（基于 KH OFDR 套件通用化） |
