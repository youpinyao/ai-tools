# 将 ai-tools 接入目标项目

本文面向**其它业务仓库**：说明如何从「仅有官方 OpenSpec」或「旧版 ai-tools（含 Cursor commands/重复 skills）」升级并接入当前 `ai-tools`。

当前语义基线为 OpenSpec **1.13.0** 官方 `spec-driven`（以 `openspec --version` 与 `npm view @fission-ai/openspec version` 为准）。后续升级须重新查询最新稳定版，不得永久假定该版本细节。

场景化日常用法见 [ai-sdd-workflow.md](../../../docs/ai-sdd-workflow.md)。Graphify 可选增强见 [integrating-graphify reference](../integrating-graphify/reference.md)。

## 1. 当前 ai-tools 是什么

当前仓库采用**官方优先（official-first）**分层：

```text
目标项目
├── OpenSpec 官方生成层（openspec init --tools codex / update 管理）
│   └── .agents/skills/openspec-*（Cursor / Codex 共用的唯一 Skill 源）
│
└── ai-tools 自定义层（从本仓库复制或安装）
    ├── openspec/schemas/evidence-driven/
    ├── openspec/config.yaml 中的 schema: evidence-driven
    ├── AGENTS.md 中的对话级中文标记片段
    ├── openspec/config.yaml 的 context 中的制品级中文标记片段
    ├── .agents/skills/openspec-update-change-from-code/ （可选；唯一 Skill 源）
```

| 层级 | 谁维护 | 内容 |
|------|--------|------|
| 官方生成层 | OpenSpec CLI | explore / propose / update / apply / verify / archive / sync |
| 自定义层 | ai-tools | `evidence-driven`、验证闭环与流转门禁、中文规则、from-code |

**不要**初始化或保留 `.cursor/commands/opsx-*` 与 `.cursor/skills/openspec-*`。应由 `openspec init --tools codex` / `openspec update` 在 `.agents/skills/` 生成唯一官方层，再按本文向 apply、verify、sync、archive skills 追加项目规则。

### 1.1 相对纯官方 OpenSpec，你多得到什么

- 默认 schema：`evidence-driven`，并增加持久化的 `verification.md`。
- `tasks → verification`，且 `apply` 依赖 `verification`。
- 当前 Agent 完成 apply、首次完整 diff 审查和后续 verify。
- sync/archive 入口强制复核 Verify 门禁。
- 当前不再提供 propose 起始 worktree 选择或隔离 worktree 收尾增强；旧项目升级时必须重建对应官方 skills，确定性移除旧增强块。
- `AGENTS.md` 约束对话语言，`openspec/config.yaml` 的 `context` 注入制品规则；可选 from-code skill。

### 1.2 相对旧版 ai-tools，你不再从本仓库获得什么

旧版曾跟踪并深度定制官方 skills/commands。当前版本不再分发整套分叉模板，只在官方生成物上追加验证闭环与流转门禁。

接入后：

- apply / verify / archive / sync 主体仍以当前官方生成物为准。
- 其它项目级硬门禁应另立规则或独立 skill。

## 2. 前置条件

- Node.js 满足 OpenSpec CLI 要求（官方要求 Node.js ≥ 20.19.0）。
- 支持从 `.agents/skills/` 发现 [Agent Skills](https://agentskills.io) 的 Cursor 或 Codex。统一运行 `openspec init --tools codex`，两种助手共享生成的 skills，不创建 Cursor command。
- 能在目标项目根目录执行 shell。

建议固定变量：

```bash
AI_TOOLS_DIR="/absolute/path/to/ai-tools"          # 本仓库克隆路径
TARGET_PROJECT="/absolute/path/to/target-project"  # 业务项目根目录
```

也可不克隆本仓库，仅用 GitHub / skills.sh 安装可选 skill；schema 仍需从本仓库（或发布物）复制。

```bash
npm install --global @fission-ai/openspec@latest
openspec --version
# 建议与 npm 最新稳定版一致后再接入
```

团队执行升级时应记录并固定解析出的精确版本，避免 `@latest` 在执行过程中再次漂移：

```bash
TARGET_VERSION="$(npm view @fission-ai/openspec version)"
npm install --global "@fission-ai/openspec@$TARGET_VERSION"
test "$(openspec --version)" = "$TARGET_VERSION"
```

## 3. 先判断你属于哪条路径

```text
目标项目里有没有 openspec/ ？
  ├─ 没有 → A. 全新接入（官方 OpenSpec + ai-tools）
  └─ 有
       ├─ 仅有官方 skills，schema 多为 spec-driven
       │     → B. 已有官方 OpenSpec，叠加 ai-tools
       └─ 曾复制旧 ai-tools（本地改过 opsx-* / openspec-* skill）
             → C. 从旧版 ai-tools 迁移到 official-first
```

可用快速探测：

```bash
cd "$TARGET_PROJECT"

# 是否已有 OpenSpec 根
test -f openspec/config.yaml && echo "has-openspec-config" || echo "no-config"

# 当前默认 schema
grep -E '^schema:' openspec/config.yaml 2>/dev/null || true

# 是否像「旧版本地定制」：存在 Cursor commands、重复 skills，或官方 skill 被 Git 跟踪
git ls-files '.cursor/commands/opsx-*' '.cursor/skills/openspec-*' \
  '.agents/skills/openspec-*' 2>/dev/null
rg -n "独立验证结论|代码审查（归档硬门禁）|Superpowers 对接" \
  .cursor/commands .cursor/skills \
  .agents/skills/openspec-apply-change \
  2>/dev/null || true
```

- 若官方路径被 Git **跟踪**，或文件中出现上述旧门禁文案 → 走 **路径 C**。
- 若只有 `openspec/` + 未被定制的官方生成物 → 走 **路径 B**。
- 若几乎没有 OpenSpec → 走 **路径 A**。

## 4. 路径 A：全新项目接入

在业务项目根目录：

```bash
cd "$TARGET_PROJECT"

# 1) 在唯一共享目录生成官方 skills，不生成 Cursor command
openspec init --tools codex

# 2) 清理既有 OpenSpec Cursor command 与重复 skill；不影响其它 Cursor 文件
rm -rf "$TARGET_PROJECT/.cursor/commands/opsx-"*
rm -rf "$TARGET_PROJECT/.cursor/skills/openspec-"*

# 3) 安装 evidence-driven schema
mkdir -p openspec/schemas
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 4) 启用 schema 并合并分层中文规则（新建或合并，勿盲目整文件覆盖）
# openspec/config.yaml 至少包含：
#   schema: evidence-driven
#   context 中的 AI_TOOLS_OPENSPEC_CHINESE_V1 标记块
# 已有 context 时只替换或插入该制品规则标记块。
# AGENTS.md 插入或替换 AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1 对话规则标记块；
# 若仍有旧 AI_TOOLS_OPENSPEC_CHINESE_V1 标记块，只删除旧片段，保留文件其余内容。

# 5) 校验
openspec schema validate evidence-driven
```

可选：

```bash
# from-code：Cursor / Codex 共用同一份项目 Skill。
mkdir -p .agents/skills
rm -rf .agents/skills/openspec-update-change-from-code
cp -R "$AI_TOOLS_DIR/.agents/skills/openspec-update-change-from-code" .agents/skills/
```

建议在目标项目 `.gitignore` 中**不要**忽略官方 skills（它们通常需要提交给团队共用）；本 `ai-tools` 仓库自身忽略它们，是因为工具包仓库不负责分发官方副本。业务仓按团队惯例选择是否提交官方生成物即可。

## 5. 路径 B：已有官方 OpenSpec，叠加 ai-tools

适用于：项目已 `openspec init`，默认 `spec-driven`，未深度分叉官方 skill。

`openspec update` 只刷新已经配置过的工具。无论项目原来配置了什么工具，都再运行 `openspec init --tools codex`，随后删除 OpenSpec Cursor commands 与重复 skills，确保 `.agents/skills/` 是唯一来源；最后重做 5.1 注入。

```bash
cd "$TARGET_PROJECT"

# 1) 先把已有官方生成物升到当前 CLI 对应版本
npm install --global @fission-ai/openspec@latest
openspec --version
# 团队升级请改用精确版本，见 7.1 节
openspec update

# 1b) 生成唯一共享 Skill 层并清理旧入口
openspec init --tools codex
rm -rf "$TARGET_PROJECT/.cursor/commands/opsx-"*
rm -rf "$TARGET_PROJECT/.cursor/skills/openspec-"*

# 2) 安装 / 覆盖自定义 schema（只覆盖 evidence-driven 目录）
mkdir -p openspec/schemas
rm -rf openspec/schemas/evidence-driven
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 3) 合并配置：只改 schema 与制品中文 context 标记块，保留其余 context / rules / operations
# schema: evidence-driven
# context 中插入或替换 AI_TOOLS_OPENSPEC_CHINESE_V1 标记块
# AGENTS.md 插入或替换 AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1 标记块
# 若仍有旧 AI_TOOLS_OPENSPEC_CHINESE_V1 标记块，只删除旧片段，不要删整份文件

# 4) 校验
openspec schema validate evidence-driven
```

### 5.1 补充 verify 修复闭环与流转门禁

安装或更新官方 skills 后，确保 apply、verify、sync、archive 各自只保留一个 `AI_TOOLS_VERIFY_GATE_V2` 增强块。

目标文件合计 **4** 个，全部位于 `.agents/skills/openspec-*`。Cursor 与 Codex 发现同一份 Skill，不存在 skill 双入口或跨目录副本。

apply、verify、sync、archive 先执行官方 Store selection 与 **Steps** 第 1 步以选定 change，再在第 2 步之前放置 A/B/C 块。

#### A. Apply：当前 Agent 直接实施并验证

向以下文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.agents/skills/openspec-apply-change/SKILL.md`

插入位置：官方 Store selection 和 **Steps** 第 1 步（Select the change）之后、第 2 步（Check status to understand the schema）之前。1.13.0 官方 apply 是串行任务循环；其 `context` 与 `operationGuidance` 明确只是 prompt-level behavior contracts，不能替代 CLI 状态或证明任务完成；在 `state: "all_done"` 与完成输出中仍会建议 `$openspec-archive`。以本块为准，门禁通过前不得按官方文案建议 sync 或 archive。

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V2 -->
## Apply 直接实施与强制验证

本块使用状态门禁（`AI_TOOLS_STATE_GATE_V1`）。

当前 Agent 必须按官方逐项循环串行执行 apply（`AI_TOOLS_DIRECT_APPLY_V1`）。

1. 开始实现前，当前 Agent 必须执行适用项发现（`AI_TOOLS_APPLY_SKILL_RULE_DISCOVERY_V1`）：阅读当前可用 skill 的 description 与 rule 的 description/适用范围，调用所有匹配的 skill 并遵循其工作流，同时遵循所有匹配的 rule。不得仅凭名称判断；执行期间任务性质变化时重新判断，指令冲突且无法按既定优先级消解时暂停澄清。
2. 当前 Agent 执行官方 apply 主体、更新 `tasks.md`，并对完整实现 diff 做首次代码审查。
3. apply 未成功或存在阻塞时不得启动 verify；change 保持 active，并向用户报告具体原因。
4. apply 成功后，当前 Agent 继续串行执行 `openspec-verify-change` 的完整验证闭环。
5. verify 完成后，当前 Agent 读取恰好一个 `AI_TOOLS_VERIFICATION_RESULT_V2_START` 结果块。
6. 仅当状态为“通过”、阻塞项为“无”时，当前 Agent 才可结束 apply 并建议 sync 或 archive。状态阻塞或 verify 执行失败均阻止完成；change 保持 active，必须报告具体原因，且不得建议 sync 或 archive。
<!-- AI_TOOLS_VERIFY_GATE_V2_END -->
```

#### B. Verify：修复、复验并持久化结论

向以下文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.agents/skills/openspec-verify-change/SKILL.md`

插入位置：官方 Store selection 和 **Steps** 第 1 步（Select the change）之后、第 2 步（Check status to understand the schema）之前。1.13.0 官方 verify 只在会话中输出 Completeness / Correctness / Coherence 记分卡，不写 `verification.md`、不修复；官方「Ready for archive」不是本项目持久化门禁，不得替代下方闭环。

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V2 -->
## Verify 直接执行与验证阻塞修复闭环

本块使用状态门禁（`AI_TOOLS_STATE_GATE_V1`）。

官方 verify 的会话记分卡（CRITICAL / WARNING / SUGGESTION）和「Ready for archive」文案不是本项目硬门禁，不得替代下方闭环；必须写入 `verification.md`。

当前 Agent 必须串行执行完整验证闭环（`AI_TOOLS_DIRECT_VERIFY_V1`）。需要停止时由当前 Agent 向用户报告。

### 验证闭环

1. 实际执行验证并检查代码、测试及 change 制品。发现可安全修复的阻塞项时，由当前 Agent 修复，并重新运行受影响的检查和完整 verify。
2. 最多执行 3 轮“验证—修复—重新验证”。同一阻塞连续两轮无进展时提前停止。
3. 遇到需要用户决策、缺少权限或凭据、外部服务故障、破坏性操作，或超出当前 change 范围的修改时，不得自行处理，停止并报告。
4. 根据当前 change 的实现 baseline 与完整 diff 确认验证范围。无法区分当前 change 与既有无关改动时停止并询问。
5. 将实际检查写回 `verification.md` 的统一检查表；复验时只更新统一表中的原行，不追加每轮历史。结果证据只保留退出码、摘要和报告路径。当前 Agent 每次修改代码后，必须针对修复后的完整 diff 重新执行代码审查并更新原审查行；存在未处理的 Critical/Important 时不得通过。
6. 最终写入恰好一个结果块，并删除旧 V1 结果块、所有
   `AI_TOOLS_VERIFICATION_SCOPE_V1/V2` 块以及旧结果块中的“范围摘要”“内容指纹”字段：

   <!-- AI_TOOLS_VERIFICATION_RESULT_V2_START -->
   ## Verify 门禁
   - 状态：通过
   - 阻塞项：无
   <!-- AI_TOOLS_VERIFICATION_RESULT_V2_END -->

7. 未通过时将结果状态写为“阻塞”并列出具体阻塞项，不得保留旧“通过”结果。

单独运行 `$openspec-verify` 时也执行以上步骤。

<!-- AI_TOOLS_VERIFY_GATE_V2_END -->
```

#### C. Sync / Archive：入口处强制检查

向以下文件追加或替换为以下内容（`STALE` 时替换旧块）：

- `.agents/skills/openspec-sync-specs/SKILL.md`
- `.agents/skills/openspec-archive-change/SKILL.md`

插入位置：官方 Store selection 和 **Steps** 第 1 步选定 change 之后、第 2 步之前。sync 在第 2 步 Resolve change context 前检查；archive 则在第 1 步选定 change 后、读取 advisory `openspec instructions archive --json` 前检查。1.13.0 官方 sync 已使用 `artifactPaths.specs.existingOutputPaths`、specs rules 快照和 `openspec validate --specs` 约束 main spec 合并，archive 也会在内联 sync 后复核 delta，但两者均不检查 `verification.md` 的结构化结论，因此 C 块不与这些官方行为重复。官方 archive 对未完成制品或任务仍仅警告并允许用户确认继续，且 archive instructions 仍是不得阻断归档的 advisory 输入；这些官方行为不能替代本项目 Verify 门禁规则。

```markdown
<!-- AI_TOOLS_VERIFY_GATE_V2 -->
## Verification 流转门禁（AI_TOOLS_VERIFY_FLOW_GATE_V1）

本块使用状态门禁（`AI_TOOLS_STATE_GATE_V1`）。

官方第 1 步选定 change 后、执行第 2 步及任何 sync 写入或 archive advisory 查询前，必须读取当前 change 的 `verification.md`，并要求恰好一个 V2 结果块。只有状态为“通过”、阻塞项为“无”时才可继续。

本门禁发生在官方 sync / archive 主体之前。官方 archive 对未完成制品或任务仅警告并允许用户确认继续，且 `openspec instructions archive --json` 被标明为不得阻断归档的 advisory 输入；上述官方行为不得用来绕过本门禁。

V1-only active change 必须先执行一次 verify，不得自动转换。V2 结果块缺失或重复、状态不是“通过”或阻塞项不是“无”时立即停止，不得通过用户确认绕过，也不得在 archive 前重复实现验证来代替已持久化门禁。sync / archive 不比较验证完成后的代码或证据变化；官方 spec validate 失败仍按官方主体处理，不能由本门禁改写成成功。

<!-- AI_TOOLS_VERIFY_GATE_V2_END -->
```

首次接入、追加或替换前，以及每次 `openspec update` 或 ai-tools 自定义层升级后，在目标项目根目录运行：

```bash
for file in \
  .agents/skills/openspec-{apply-change,verify-change,sync-specs,archive-change}/SKILL.md
do
  if [ ! -f "$file" ]; then
    echo "NOFILE    $file"
    continue
  fi

  case "$file" in
    *opsx-apply.md|*opsx/apply.md|*openspec-apply-change/SKILL.md) kind="apply" ;;
    *opsx-verify.md|*opsx/verify.md|*openspec-verify-change/SKILL.md) kind="verify" ;;
    *) kind="flow" ;;
  esac

  status="$(python3 - "$kind" "$file" <<'PY'
# AI_TOOLS_VERIFY_GATE_CHECKER_V2_START
from pathlib import Path
import re
import sys

kind, path = sys.argv[1:]
text = Path(path).read_text()
start_pattern = re.compile(
    r"(?m)^<!-- AI_TOOLS_VERIFY_GATE_V2 -->[ \t]*$"
)
end_pattern = re.compile(
    r"(?m)^<!-- AI_TOOLS_VERIFY_GATE_V2_END -->[ \t]*$"
)
old_gate = "<!-- AI_TOOLS_VERIFY_GATE_" + "V1 -->"
old_pattern = re.compile(r"(?m)^" + re.escape(old_gate) + r"[ \t]*$")

starts = list(start_pattern.finditer(text))
ends = list(end_pattern.finditer(text))
old_count = len(old_pattern.findall(text))

if not starts:
    if ends:
        print("STALE (malformed V2 block boundary)")
    elif old_count:
        print("STALE (V1-only gate)")
    else:
        print("MISSING")
    raise SystemExit(0)
if len(starts) > 1 or len(ends) > 1:
    print("DUPLICATE ({} starts, {} ends)".format(len(starts), len(ends)))
    raise SystemExit(0)
if old_count:
    print("STALE (mixed V1/V2 gates)")
    raise SystemExit(0)
if len(ends) != 1 or ends[0].start() < starts[0].end():
    print("STALE (malformed V2 block boundary)")
    raise SystemExit(0)

block = text[starts[0].end():ends[0].start()]
required_by_kind = {
    "apply": (
        "AI_TOOLS_STATE_GATE_V1",
        "AI_TOOLS_DIRECT_APPLY_V1",
        "AI_TOOLS_APPLY_SKILL_RULE_DISCOVERY_V1",
    ),
    "verify": (
        "AI_TOOLS_STATE_GATE_V1",
        "AI_TOOLS_DIRECT_VERIFY_V1",
    ),
    "flow": ("AI_TOOLS_STATE_GATE_V1", "AI_TOOLS_VERIFY_FLOW_GATE_V1"),
}
missing = [marker for marker in required_by_kind[kind] if marker not in block]
if missing:
    print("STALE (missing in V2 block: {})".format(missing[0]))
    raise SystemExit(0)

removed_dispatch_markers = (
    "AI_TOOLS_DELEGATED_",
    "AI_TOOLS_STANDALONE_",
    "AI_TOOLS_DISPATCH_FALLBACK_V1",
    "AI_TOOLS_PARALLEL_",
    "AI_TOOLS_WORKER_",
    "AI_TOOLS_MULTI_IDE_V1",
)
present_removed = [
    marker for marker in removed_dispatch_markers if marker in block
]
if present_removed:
    print("STALE (removed dispatch marker in V2 block: {})".format(
        present_removed[0]
    ))
    raise SystemExit(0)

print("OK")
# AI_TOOLS_VERIFY_GATE_CHECKER_V2_END
PY
)"
  echo "$status $file"
done
```

每个 V2 注入必须以独立注释行 `<!-- AI_TOOLS_VERIFY_GATE_V2 -->` 开始，以独立注释行 `<!-- AI_TOOLS_VERIFY_GATE_V2_END -->` 结束；检查器只读取这两个边界之间的正文，不接受行内伪标记，也不允许文档其它位置代打 required。`MISSING` 表示既没有 V2/V1 独立起始标记，也没有孤立 V2 结束标记；`DUPLICATE` 表示 V2 起止标记重复；`STALE` 包括 V1-only、V1/V2 混写、缺少 `AI_TOOLS_STATE_GATE_V1` 的旧 V2 指纹正文、孤立 start 或 end 等边界不完整或块内 required 缺失。出现 V1 或缺少状态门禁标记时标为 `STALE`，必须以当前 V2 完整块替换，不得再次追加。

apply 块内必须包含 `AI_TOOLS_DIRECT_APPLY_V1` 与 `AI_TOOLS_APPLY_SKILL_RULE_DISCOVERY_V1`，verify 块内必须包含 `AI_TOOLS_DIRECT_VERIFY_V1`；sync/archive 块内必须包含 `AI_TOOLS_VERIFY_FLOW_GATE_V1`，防止只有边界、没有流转检查正文的空块被误判为 `OK`。`NOFILE` 表示官方文件不存在，应先恢复官方生成层。

### 5.2 已有 active change 怎么办

| 情况 | 建议 |
|------|------|
| change 使用 `spec-driven`，且仍在规划/实现中 | 可继续用原 schema 做完并归档；新 change 再改用 `evidence-driven` |
| 希望中途切到 `evidence-driven` | 需补齐 `verification.md`，并确认 `.openspec.yaml` 的 `schema:`；有行为变化时再改 tasks/specs |
| 纯重构/文档、无规范层变化 | 可设 `skip_specs: true`，仍建议有 `verification` 计划 |

切换默认 schema **不会**自动改写历史 archived changes；只影响之后 `openspec new change` 的默认 schema（除非命令显式传 `--schema`）。

### 5.3 从 `spec-driven` 迁到 `evidence-driven` 的制品差异

```text
spec-driven:   proposal → specs/design → tasks → apply
evidence-driven: proposal → specs/design → tasks → verification → apply
```

官方 skills 以 CLI 生成物为基线，并按 5.1 节追加验证闭环与流转门禁。`verification` 的制品依赖通过 schema 的 `apply.requires` 与模板指导进入工作流；该依赖只保证制品存在。apply 与 verify 始终由当前 Agent 串行执行。最终由 verification 中持久化的 Verify 门禁决定能否继续 sync 或 archive。

## 6. 路径 C：从旧版 ai-tools 迁移

旧版特征通常包括：

- Git 跟踪了 `openspec-explore` … `openspec-sync-specs` 与对应 `opsx-*.md`；
- skill/command 内含「独立验证结论」「代码审查（归档硬门禁）」「Superpowers 对接」等本地段落；
- 可能还有本仓独有的 `openspec-update-change-from-code`（应保留）。

### 6.1 迁移原则

1. 官方层归还 OpenSpec CLI 管理，删除本地分叉的官方生成物。
2. 自定义层只保留 `evidence-driven`、验证闭环与流转门禁、中文规则和 from-code。
3. 不把旧分叉文件整体合并进新版官方模板；只追加带幂等标记的当前规则。
4. 删除前保留分支或补丁，以便核对旧定制。

### 6.2 推荐步骤

```bash
cd "$TARGET_PROJECT"
git checkout -b chore/migrate-to-ai-tools-official-first

# 0) 备份旧定制（可选但强烈建议）
mkdir -p /tmp/ai-tools-legacy-backup
cp -R .cursor/skills/openspec-apply-change /tmp/ai-tools-legacy-backup/ 2>/dev/null || true
cp .cursor/commands/opsx-apply.md /tmp/ai-tools-legacy-backup/ 2>/dev/null || true

# 1) 移除全部 OpenSpec Cursor command 与重复 skill；不影响其它 Cursor 文件
git rm -r --ignore-unmatch .cursor/commands/opsx-* .cursor/skills/openspec-*
rm -rf "$TARGET_PROJECT/.cursor/commands/opsx-"*
rm -rf "$TARGET_PROJECT/.cursor/skills/openspec-"*
git rm --ignore-unmatch .cursor/rules/openspec-chinese.mdc
rm -f -- \
  "$TARGET_PROJECT/scripts/openspec-verification-fingerprint.py" \
  "$TARGET_PROJECT/.cursor/scripts/openspec-verification-fingerprint.py"

# 2) 升级 CLI 并重新生成官方层
npm install --global @fission-ai/openspec@latest
openspec --version
# 团队升级请改用精确版本，见 7.1 节
openspec update
# 旧 worktree 增强没有可靠的结束边界，不能安全地原位裁剪；重建承载它们的
# 官方 skills，确保旧块不会残留。自定义 from-code skill 不在此清单。
for skill_name in \
  openspec-propose \
  openspec-apply-change \
  openspec-verify-change \
  openspec-sync-specs \
  openspec-archive-change
do
  rm -rf -- "$TARGET_PROJECT/.agents/skills/$skill_name"
done
# 用 codex 生成 `.agents/skills/` 唯一官方层
openspec init --tools codex
# 若项目尚不完整，也用上面的 init

# 3) 刷新自定义 schema
mkdir -p openspec/schemas
rm -rf openspec/schemas/evidence-driven
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 4) 确认 config
# schema: evidence-driven

# 5) 重装共用旁路；同步 AGENTS.md 对话规则与 config.yaml 制品规则（若仍需要）
# 勿整文件覆盖任一文件；旧 AI_TOOLS_OPENSPEC_CHINESE_V1 AGENTS 片段只删除该片段。
mkdir -p .agents/skills
rm -rf .agents/skills/openspec-update-change-from-code
cp -R "$AI_TOOLS_DIR/.agents/skills/openspec-update-change-from-code" .agents/skills/

# 6) 校验
openspec schema validate evidence-driven
openspec list --json
```

重新生成官方层后，还必须按 5.1 节向 `.agents/skills/` 中的 apply、verify、sync、archive skills 追加增强块。

### 6.3 迁移后行为变化清单（给团队的预期管理）

| 旧内容 | 迁移后 |
|--------|--------|
| 仓库内维护的官方 skill/command 分叉 | 删除，改由 OpenSpec CLI 生成 |
| Cursor 专属 commands/skills | 删除，统一使用 `.agents/skills/` |
| `evidence-driven`、`verification.md`、V2 门禁 | 保留 |
| 中文规则、from-code | 可保留 |
| propose 起始 worktree 选择、隔离 worktree 收尾 | 不再提供；升级时重建对应官方 skills，并移除 `AI_TOOLS_PROPOSE_WORKTREE_V1`、`AI_TOOLS_WORKTREE_FINISH_V1` 与 `AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1` 旧增强 |

当前 verification 已内置完整 diff 代码审查，未处理的 Critical/Important 会阻断流转。若业务还需要独立审批人、第二次审查或 archive 阶段的额外审批门禁，迁移完成后单独开 change，用项目自有 rule/skill 表达，避免再次深度分叉官方生成路径。

### 6.4 正在进行中的 change

1. 迁移前用旧流程尽量完成或归档关键 change，成本最低。
2. 若必须带着 active change 迁移：
   - 保留 change 目录与 `.openspec.yaml`；
   - 刷新 schema 后运行 `openspec status --change "<name>" --json` 与 `openspec validate "<name>" --type change --strict`；
   - 缺 `verification.md` 时按新模板补齐（规划阶段结果保持「待执行」，须含代码审查章节）；
   - 旧 verification 中「独立验证结论 / 代码审查硬门禁」章节可保留为项目约定；官方 archive 本身不一定检查它们，但 5.1 节追加的项目级门禁会阻止带有未处理 Critical/Important 的 change 流转。

## 7. 日常升级（接入之后）

### 7.1 升级 OpenSpec 官方层

普通使用者可用 `@latest` 快捷安装，但必须立刻核对版本：

```bash
cd "$TARGET_PROJECT"
npm install --global @fission-ai/openspec@latest
openspec --version
openspec update
# 重建 `.agents/skills/` 唯一官方层：
for skill_name in \
  openspec-propose \
  openspec-apply-change \
  openspec-verify-change \
  openspec-sync-specs \
  openspec-archive-change
do
  rm -rf -- "$TARGET_PROJECT/.agents/skills/$skill_name"
done
openspec init --tools codex
rm -rf "$TARGET_PROJECT/.cursor/commands/opsx-"*
rm -rf "$TARGET_PROJECT/.cursor/skills/openspec-"*
openspec schema validate evidence-driven
```

`openspec update` 可能刷新官方生成物。升级后重新运行 5.1 节检查器；对 `MISSING` 追加当前块，对 `STALE` 原位替换，对 `DUPLICATE` 先清理重复块。最终四个门禁文件均应为 `OK`。

团队执行升级时应记录并固定 `npm view` 解析出的精确版本，不要只依赖 `@latest` 的瞬时解析：

```bash
cd "$TARGET_PROJECT"
TARGET_VERSION="$(npm view @fission-ai/openspec version)"
npm install --global "@fission-ai/openspec@$TARGET_VERSION"
test "$(openspec --version)" = "$TARGET_VERSION"
openspec update
# 精确版本升级也重建这五个官方 skills；清单不含自定义
# openspec-update-change-from-code，后者必须保留。
for skill_name in \
  openspec-propose \
  openspec-apply-change \
  openspec-verify-change \
  openspec-sync-specs \
  openspec-archive-change
do
  rm -rf -- "$TARGET_PROJECT/.agents/skills/$skill_name"
done
openspec init --tools codex
LEGACY_WORKTREE_PATTERN='AI_TOOLS_(PROPOSE_WORKTREE|WORKTREE_FINISH|VERIFY_GATE_NO_FINISH_ASK)'
for file in \
  .agents/skills/openspec-{propose,apply-change,verify-change,sync-specs,archive-change}/SKILL.md
do
  test -f "$file" || continue
  ! rg -q "$LEGACY_WORKTREE_PATTERN" "$file" || {
    echo "仍有旧 worktree 增强：$file" >&2
    exit 1
  }
done
openspec schema validate evidence-driven
```

### 7.2 升级 ai-tools 自定义层

```bash
# 拉取最新 ai-tools 后
rm -rf "$TARGET_PROJECT/openspec/schemas/evidence-driven"
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  "$TARGET_PROJECT/openspec/schemas/"

# 把制品规则并入目标 config.yaml 的 context（AI_TOOLS_OPENSPEC_CHINESE_V1）。
# 把对话规则并入 AGENTS.md（AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1）。
# 已有标记块时只替换该块；旧 AGENTS 中文块只删除旧片段，保留其余内容。

# Cursor / Codex 共用唯一 from-code Skill。
mkdir -p "$TARGET_PROJECT/.agents/skills"
rm -rf "$TARGET_PROJECT/.agents/skills/openspec-update-change-from-code"
cp -R "$AI_TOOLS_DIR/.agents/skills/openspec-update-change-from-code" \
  "$TARGET_PROJECT/.agents/skills/"

# 删除旧版本曾安装的范围指纹脚本。
rm -f -- \
  "$TARGET_PROJECT/scripts/openspec-verification-fingerprint.py" \
  "$TARGET_PROJECT/.cursor/scripts/openspec-verification-fingerprint.py"

cd "$TARGET_PROJECT"
openspec schema validate evidence-driven
```

**禁止**用本仓库完整文件覆盖目标配置；`config.yaml` 只合并 `schema: evidence-driven` 与制品规则标记块，`AGENTS.md` 只合并对话规则标记块。

ai-tools 自定义层升级后必须重新运行 5.1 节检查器。旧 V1 或缺少 `AI_TOOLS_DIRECT_APPLY_V1`、`AI_TOOLS_APPLY_SKILL_RULE_DISCOVERY_V1`、`AI_TOOLS_DIRECT_VERIFY_V1` 的块均为 `STALE`，必须用当前 A/B/C 节完整块替换。

### 7.3 本仓库（ai-tools）自身注意事项

- 不要在 `ai-tools` 仓库根目录对官方路径跑 `openspec init` / `openspec update` 并提交生成物。
- 官方模板对照应在临时目录完成，再手工同步到 `evidence-driven`。

### 7.4 工作流命令、JSON 与目录（OpenSpec 1.13.0）

以下命令与字段均来自 1.13.0 的 `openspec --help`、子命令 help、官方 schema 和临时 `openspec init --tools codex` 生成物，不要猜测未列出的参数。

| 用途 | 命令 | 1.13.0 说明 |
|------|------|-------------|
| 新项目官方生成层 | `openspec init --tools codex` | `--tools` 用于非交互指定工具。Cursor 生成 7 组 skill + 7 个 command；Codex 生成 7 组 skill（skills-only，入口为 `$openspec-*`）。官方 apply 在制品缺失时可能提示未随 init 生成的 `$openspec-continue`，不要纳入本仓库忽略清单或 5.1 幂等清单。 |
| 已初始化刷新 | `openspec update` | 更新 instruction 文件；`--force` 可在工具已是最新时仍刷新。 |
| schema 校验 | `openspec schema validate evidence-driven` | schema 子命令仍标为 experimental；`--json` 返回 `name` / `path` / `valid` / `issues`。 |
| 新建 change | `openspec new change "<name>" --schema evidence-driven` | `--schema` 覆盖默认 schema。 |
| 列出 change | `openspec list --json` | 顶层含 `changes`、`root`。`openspec change list` 的 `--help` 标明 DEPRECATED。 |
| 列出 spec | `openspec list --specs --json` | 顶层含 `specs`（条目含 `id`、`requirementCount`）、`root`。`openspec spec list` 运行时打印 deprecated 警告，勿再作为主命令。 |
| 制品状态 | `openspec status --change "<name>" --json` | 顶层含 `changeRoot`、`artifactPaths`、`actionContext`、`schemaName`、`planningHome`。 |
| 严格校验 | `openspec validate "<name>" --type change --strict --json` | 未填制品时会失败但返回可解析 JSON。 |
| 校验 spec | `openspec validate "<id>" --type spec --strict --json` | from-code 无 change 回写 main spec 时使用。 |
| apply 指令 | `openspec instructions apply --change "<name>" --json` | 顶层含 `state`、`missingArtifacts`、`contextFiles`。`evidence-driven` 在缺少 `verification` 时 `state` 可为 `blocked`。 |
| archive 指令 | `openspec instructions archive --change "<name>" --json` | 官方 skill 标明该查询为 advisory，不得当作硬门禁；成功 JSON 可省略 `context` / `operationGuidance`。 |

以 `schemaName` / `--schema` 为准，不要用 `planningHome.defaultSchema`（该字段在 1.13.0 仍可能报 `spec-driven`）。

目录（用 JSON 里的 store-aware 路径，不要写死仓库相对路径）：

- 主规范：`<planningHome.root>/openspec/specs/<capability-path>/spec.md`；无 change 时
  `planningHome.root` 换成 `openspec list --specs --json` 或 `openspec context --json`
  的 `root.path`
- active change：`openspec/changes/<name>/`
- 归档：`<planningHome.changesDir>/archive/`（仓库内通常是 `openspec/changes/archive/`）

Cursor 与 Codex 共用的 `$openspec-propose` skill 由 `.agents/skills/` 中的官方生成物提供。1.13.0 的生成 workflow 除更新 `generatedBy` 外，`explore` 新增持久能力盘点：用 `openspec list --specs` 区分能力与在途 change，以 `openspec show "<spec-id>" --type spec --json --no-scenarios` 筛选后再完整读取相关规范及场景。`propose` 新增强制 context 根解析：先运行 `openspec context --json`，无 OpenSpec 根时停止并等待用户请求初始化；解析成功后，在探索与规划前读取配置中的项目 `context`。官方 schema 的 proposal/specs instruction 也要求先核对既有能力及准确路径。apply、update、verify、sync、archive 正文除 `generatedBy` 外没有语义变化。1.13.0 官方 verify 只输出 Completeness / Correctness / Coherence 会话记分卡，不写 `verification.md`。官方 sync 以 `artifactPaths.specs.existingOutputPaths` 为 delta 路径来源，合并后运行 `openspec validate --specs`；archive 在内联 sync 后复核 delta，对未完成制品或任务仅警告并允许确认继续。项目级 `AI_TOOLS_VERIFY_GATE_V2` 检查结构化验证结论，不是官方行为。

## 8. 验收清单

首次接入或任何升级后，必须运行 5.1 节检查器，直到四个门禁文件全部输出 `OK`，然后确认：

- [ ] OpenSpec 使用团队固定的精确稳定版本。
- [ ] `evidence-driven` schema 存在、启用且校验通过。
- [ ] `.agents/skills/` 是唯一官方 Skill 源。
- [ ] apply/verify/sync/archive 各有且只有一个完整的 `AI_TOOLS_VERIFY_GATE_V2` 块。
- [ ] apply 的适用 skill/rule 发现标记及 apply/verify 的直接串行执行标记完整。
- [ ] sync/archive 会复核通过状态与无阻塞。
- [ ] 中文规则和 from-code skill 按约定安装。

冒烟命令示例：

```bash
cd "$TARGET_PROJECT"
openspec schema validate evidence-driven
openspec new change "smoke-ai-tools-integration" --schema evidence-driven
openspec status --change "smoke-ai-tools-integration" --json
# 1.13.0 顶层应含 changeRoot、artifactPaths、actionContext、schemaName、planningHome
openspec instructions apply --change "smoke-ai-tools-integration" --json
# 未填 verification 时 evidence-driven 的 apply 可为 blocked
openspec validate "smoke-ai-tools-integration" --type change --strict --json
# 验证完毕后可删除该 smoke change 目录，勿归档到生产规格
```

## 9. 常见问题

### 为什么 README 说「不要从 ai-tools 复制官方 templates」？

因为官方层应以 CLI 生成物为准。复制会导致版本漂移，下一次 `openspec update` 也会冲突。`ai-tools` 只保证自定义 schema 目录可复制。

### 接入后官方 verify 变「弱」了？

verify 主体仍跟随官方生成物。OpenSpec 1.13.0 官方 verify 只在会话中输出 Completeness / Correctness / Coherence 记分卡，不写 `verification.md`。增强规则要求当前 Agent 串行执行完整 verify。verify 执行者仅对可安全、在当前 change 范围内且不需要用户决策的阻塞直接修复并重新验证（最多 3 轮）；其余情况停止并报告。结构化结论写回 verification，sync/archive 会在各自入口强制检查该结论（状态为通过、阻塞项为无）。当前 verification 已要求完整 diff 代码审查，并以未处理的 Critical/Important 阻断流转。若还需要独立审批人、第二次审查或 archive 阶段的额外审批门禁，应另加项目规则或独立 skill。

### 安装增强规则后还要再装 Superpowers 吗？注入要不要再替换？

不必。当前增强规则不依赖 Superpowers。只有注入文本过期（5.1 节脚本报 `STALE`，例如缺少直接执行标记）时，才需要用当前 A/B 节替换。

### `openspec update` 会不会删掉 `evidence-driven`？

一般不会删除 `openspec/schemas/` 下的自定义 schema。但升级后仍应再跑 `openspec schema validate evidence-driven`，并确认 `config.yaml` 的 `schema:` 未被改回 `spec-driven`。

### 可以继续用 `spec-driven` 吗？

可以。不改 `config.yaml` 即保持官方默认。只有需要 `verification` 制品与 apply 前置依赖时，才切换到 `evidence-driven`。

### from-code 与官方 sync 有何区别？

| 命令 | 真源 | 写入范围 |
|------|------|----------|
| `openspec-update-change-from-code` skill | 已实现代码 + 用户决策 | 优先唯一匹配的 active change（及 `actionContext` 文档）；无 change 且唯一匹配已有 spec 时只改该 main spec；目标有歧义时先请用户选择；不创建 change/spec |
| 官方 `$openspec-sync` | change 内 delta specs | main specs |

## 10. 相关文档

- 安装与仓库边界：[README.md](../../../README.md)
- 场景化工作流：[ai-sdd-workflow.md](../../../docs/ai-sdd-workflow.md)
- Graphify 可选增强：[integrating-graphify reference](../integrating-graphify/reference.md)
- 当前维护基线见 README 与本文。历史架构规格 `spec/spec-architecture-openspec-workflow-refactor.md` 已移出版本控制（`.gitignore` 含 `/spec`），本仓库不再跟踪等价文件。
- OpenSpec 上游：https://github.com/Fission-AI/OpenSpec
