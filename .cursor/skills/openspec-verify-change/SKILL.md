---
name: openspec-verify-change
description: Verify implementation matches change artifacts. Use when the user wants to validate that implementation is complete, correct, and coherent before archiving.
allowed-tools: Bash(openspec:*)
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.6.0"
---

Verify that an implementation matches the change artifacts (specs, tasks, design).

**Independence gate:** The verifier must **not** have implemented the change. Allowed runners:
1. **Preferred:** A Task-dispatched subagent started by `/opsx:apply` after the implementation evidence gate (isolated context; no implementer history).
2. A user-opened fresh Agent conversation that runs `/opsx-verify`.

If **this** conversation participated in implementation (wrote application code / marked implementation tasks done for this change), **stop**: do not fill `独立验证结论` yourself—dispatch a Task subagent for verify, or ask the user to open a fresh conversation. The implementer cannot approve its own work.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

---

## Superpowers 对接：代码审查 / 新鲜证据 / finishing（薄适配）

在复跑检查、编排代码审查、以及写入「验证结论：通过」之后，MUST 遵循下方写死的门禁。本节与 Spec / schema `verification.instruction` 为权威；skill/command 可更严，不得更松；冲突时以更严门禁为准。MAY Read 上游 `verification-before-completion` / `finishing-a-development-branch` / `receiving-code-review` / `requesting-code-review` 作话术补充；**上游全文 checklist / 终态仅参考，本节下列步骤为权威**，避免与本节冲突。

### 复跑检查：verification-before-completion

复跑 `verification.md` 中适用的自动化/人工检查时，MUST 遵循 `verification-before-completion`：

- 本回合实际重新执行适用命令并阅读输出后，才可将该项标为「通过」或写入通过证据
- **无新鲜命令输出不得标通过**；禁止仅复制实现会话的旧结论、口头记忆或未复跑的历史摘要作为唯一证据
- 本回合未执行该命令 → MUST NOT 将该项状态改为「通过」

### 代码审查：派发 Code Review（决策 6）

编排 Code Review 时（Task 可用且轨适用）：

- MUST 按 `requesting-code-review` 派发 reviewer（Task 可用时用 Task 子 Agent + `code-reviewer` 模板）
- Task 不可用时回退为本会话审查并注明；不得假造通过结果
- 轨不适用（如纯文档 / 无代码 diff）→ MUST 标明具体原因，不得假造通过结果
- **判定「不适用」前 MUST 检查脏工作区**（见步骤 8「适用性与 Diff 范围」）：存在未提交变更时须纳入 Diff 或阻塞；**禁止**仅因 BASE==HEAD 空 commit diff 将审查标为不适用
- Finding 处置遵循 `receiving-code-review`（核实 → 修复或技术反驳；禁止表演式同意）
- apply 仍禁止并行多实现子 Agent；本约定**仅限** verify 审查段

### Finishing：验证通过后必提示（决策 7）

当 `## 独立验证结论` 写入「验证结论：通过」（含代码审查门禁已满足）后：

- MUST 遵循 `finishing-a-development-branch` 核心步骤：确认门禁已通过 → 检测工作区环境 → 向用户呈现结构化选项（合并 / 创建 PR / 保留分支 / 清理 worktree 等，按环境裁剪）
- **仅在用户选择后**执行集成或清理动作
- MUST NOT 在未询问的情况下默认强制推送或删除分支
- finishing **不在** apply 中执行；用户可推迟收尾。archive 成功后若尚未集成，由 archive 阶段再次提示（本 skill 负责 verify 通过后的首次提示）

---

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show changes that have implementation tasks (tasks artifact exists).
   Include the schema used for each change if available.
   Mark changes with incomplete tasks as "(In Progress)".

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context
   - Which artifacts exist for this change

3. **Get planning context and load artifacts**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   This returns the change directory and `contextFiles` (artifact ID -> array of concrete file paths). Read all available artifacts from `contextFiles`.

   If `contextFiles.verification` exists:
   - Read `verification.md` before assessing the implementation.
   - Treat any applicable `待执行` or `失败` item as a CRITICAL issue.
   - Treat an item marked `不适用` without a concrete reason as a WARNING.
   - Re-run every applicable recorded automated check independently, including contract, migration, security, E2E, and non-functional checks when listed（遵循上方 `verification-before-completion`：本回合新鲜输出）。
   - Re-perform applicable manual checks, or record a CRITICAL blocker when the required environment or authority is unavailable.
   - Never trust a recorded success result without fresh command evidence；不得仅复制实现会话旧结论。

4. **Initialize verification report structure**

   Create a report structure with three dimensions:
   - **Completeness**: Track tasks and spec coverage
   - **Correctness**: Track requirement implementation and scenario coverage
   - **Coherence**: Track design adherence and pattern consistency

   Each dimension can have CRITICAL, WARNING, or SUGGESTION issues.

5. **Verify Completeness**

   **Task Completion**:
   - If `contextFiles.tasks` exists, read every file path in it
   - Parse checkboxes: `- [ ]` (incomplete) vs `- [x]` (complete)
   - Count complete vs total tasks
   - If incomplete tasks exist:
     - Add CRITICAL issue for each incomplete task
     - Recommendation: "Complete task: <description>" or "Mark as done if already implemented"

   **Spec Coverage**:
   - If delta specs exist in `contextFiles.specs`:
     - Extract all requirements (marked with "### Requirement:")
     - For each requirement:
       - Search codebase for keywords related to the requirement
       - Assess if implementation likely exists
     - If requirements appear unimplemented:
       - Add CRITICAL issue: "Requirement not found: <requirement name>"
       - Recommendation: "Implement requirement X: <description>"

6. **Verify Correctness**

   **Requirement Implementation Mapping**:
   - For each requirement from delta specs:
     - Search codebase for implementation evidence
     - If found, note file paths and line ranges
     - Assess if implementation matches requirement intent
     - If divergence detected:
       - Add WARNING: "Implementation may diverge from spec: <details>"
       - Recommendation: "Review <file>:<lines> against requirement X"

   **Scenario Coverage**:
   - For each scenario in delta specs (marked with "#### Scenario:"):
     - Check if conditions are handled in code
     - Check if tests exist covering the scenario
     - If scenario appears uncovered:
       - Add WARNING: "Scenario not covered: <scenario name>"
       - Recommendation: "Add test or implementation for scenario: <description>"

7. **Verify Coherence**

   **Design Adherence**:
   - If `contextFiles.design` exists:
     - Extract key decisions (look for sections like "Decision:", "Approach:", "Architecture:")
     - Verify implementation follows those decisions
     - If contradiction detected:
       - Add WARNING: "Design decision not followed: <decision>"
       - Recommendation: "Update implementation or revise design.md to match reality"
   - If no design.md: Skip design adherence check, note "No design.md to verify against"

   **Code Pattern Consistency**:
   - Review new code for consistency with project patterns
   - Check file naming, directory structure, coding style
   - If significant deviations found:
     - Add SUGGESTION: "Code pattern deviation: <details>"
     - Recommendation: "Consider following project pattern: <example>"

8. **Orchestrate code review (archive hard gate)**

   When `verification.md` includes `## 代码审查（归档硬门禁）` (evidence-driven schema):

   **Metadata first:**
   - Fill Diff 范围、BASE_SHA、HEAD_SHA（默认相对仓库默认 base 的 branch changes；可用 `git merge-base` / `git rev-parse`）。
   - Fill 变更摘要与需求依据（from proposal / tasks / specs / design）。

   **适用性与 Diff 范围（判定「不适用」前的硬门禁）：**
   - MUST 先检查脏工作区：`git status`、`git diff HEAD`（含 unstaged）、以及 staged（`git diff --cached` / status 中 staged 列表）。
   - 存在未提交变更（含 untracked 且属于本 change 范围）时：MUST 将未提交变更纳入 Diff 范围审查（例如 `Diff: uncommitted changes`，或明确列出路径），**或**阻塞并要求用户明确审查范围——不得继续标「不适用」。
   - **禁止**仅因 `BASE_SHA == HEAD_SHA`（相对 base 无超前提交 / commit range 为空）就把审查标为「不适用」并旁路归档硬门禁；空 commit diff ≠ 无变更。
   - 仅当确认工作区干净 **且** 无待审 commit/路径 diff、确属纯文档/无代码变更时，才可将适用性标为「不适用」并写明具体原因；不得假造通过。

   **Dispatch Code Review**（Task 可用时派发；verifier 只编排，不自审通过）：
   - **Code Review** — follow superpowers `requesting-code-review`: dispatch a general-purpose reviewer with the `code-reviewer.md` prompt template (`DESCRIPTION`, `PLAN_OR_REQUIREMENTS`, `BASE_SHA`, `HEAD_SHA`)。默认相对 base 的 branch changes；**脏树时按上方规则改用 `Diff: uncommitted changes`（或明确列出路径）或阻塞**，勿只传 BASE/HEAD 空 commit range。Expect Critical / Important / Minor。
   - Task 不可用 → 回退为本会话审查并注明。轨不适用 → 标明原因，不得仅因「未派发」而假造失败，但仍须满足 schema 对「不适用」说明的要求。

   **Record results into verification.md:**
   - Update 审查轨 row: 状态、Critical、Important、Minor counts、证据摘要.
   - Append every finding to Finding 处置台账（ID、轨、严重级、位置、摘要；处置/状态 initially 待执行 unless already fixed before this verify）.

   **Gate mapping (档位 1):**
   - Applicable track still `待执行`, or dispatch failed without a compensated re-run → CRITICAL（阻塞）
   - Unresolved Critical → CRITICAL（阻塞）
   - Unresolved Important without 修复 or 技术反驳并接受（须写入「未执行项与剩余风险」且验证者确认）→ CRITICAL（阻塞）
   - Minor → 可记入剩余风险；单独存在时不阻塞 `验证结论：通过`
   - Finding 处置遵循 `receiving-code-review`（核实 → 修复或技术反驳；禁止表演式同意）. If fixes are still needed, set conclusion to `阻塞` and list required fixes—do not silently pass.

9. **Persist the independent verification conclusion**

   If a `verification` artifact exists, update its `## 独立验证结论` section:
   - Set `验证结论` to `通过` only when there are no CRITICAL issues, no failed required checks, no applicable pending checks, **and** code-review gate (step 8) has no blocking open findings.
   - Otherwise set `验证结论` to `阻塞`.
   - Set `验证者` to `独立 Agent（子 Agent）` when Task-dispatched, or `独立 Agent（新会话）` when user-opened.
   - Record the verification scope, CRITICAL issues, WARNING issues, **代码审查**摘要, and whether residual risks were explicitly accepted.
   - Add concise fresh command evidence to the relevant result rows（本回合复跑输出，非实现会话拷贝）.

   Do not erase implementation evidence or silently downgrade failures.

10. **Generate Verification Report**

   **Summary Scorecard**:
   ```
   ## Verification Report: <change-name>

   ### Summary
   | Dimension    | Status           |
   |--------------|------------------|
   | Completeness | X/Y tasks, N reqs|
   | Correctness  | M/N reqs covered |
   | Coherence    | Followed/Issues  |
   | Code Review  | 审查状态 / 阻塞 finding |
   ```

   **Issues by Priority**:

   1. **CRITICAL** (Must fix before archive):
      - Incomplete tasks
      - Missing requirement implementations
      - Code-review：未跑完的适用轨、未关闭 Critical、未处置 Important
      - Each with specific, actionable recommendation

   2. **WARNING** (Should fix):
      - Spec/design divergences
      - Missing scenario coverage
      - Accepted Important 技术反驳（须已写入剩余风险）
      - Each with specific recommendation

   3. **SUGGESTION** (Nice to fix):
      - Pattern inconsistencies
      - Minor code-review findings
      - Each with specific recommendation

   **Final Assessment**:
   - If CRITICAL issues: "X critical issue(s) found. Fix before archiving."
   - If only warnings and residual risks are explicitly accepted: "No critical issues. Y accepted warning(s). Independent verification passed."
   - If all clear: "All checks passed. Independent verification passed and the change is ready for archive."

11. **Finishing 菜单（仅当验证结论为通过）**

   当步骤 9 已将「验证结论」写为 `通过` 后，MUST 立即按上方「Finishing」薄适配向用户呈现 `finishing-a-development-branch` 选项菜单（按环境裁剪），并等待用户选择后再执行。更新 `verification.md` 中 Finishing 相关状态为已提示/用户选择（若模板有该字段）。

   - 结论为 `阻塞` → **跳过** finishing，列出须修复项
   - MUST NOT 未询问即 push、强制合并或删除分支
   - 用户可选择推迟（保留分支）；不得静默结束而不提及收尾选项

**Verification Heuristics**

- **Completeness**: Focus on objective checklist items (checkboxes, requirements list)
- **Correctness**: Use keyword search, file path analysis, reasonable inference - don't require perfect certainty
- **Coherence**: Look for glaring inconsistencies, don't nitpick style
- **Code Review**: Orchestrate real subagent review；never invent findings or mark track passed without dispatch evidence
- **Fresh Evidence**: 复跑遵循 `verification-before-completion`；无本回合命令输出不得标通过
- **False Positives**: When uncertain, prefer SUGGESTION over WARNING, WARNING over CRITICAL（但未关闭的 Critical 与未处置 Important 仍为 CRITICAL）
- **Actionability**: Every issue must have a specific recommendation with file/line references where applicable

**Graceful Degradation**

- If only tasks.md exists: verify task completion only, skip spec/design checks
- If tasks + specs exist: verify completeness and correctness, skip design
- If full artifacts: verify all three dimensions
- If verification.md lacks「代码审查」节（旧产物）: add the section from the current template before concluding, or treat missing applicable review as CRITICAL
- Always note which checks were skipped and why
- A completed task list is not proof of correctness
- Never mark independent verification as passed with applicable pending or failed checks
- Never mark passed with open Critical or undisposed Important from code review
- Persist the conclusion to verification.md; 仅聊天输出不满足归档门禁，须写入 verification.md
- 验证结论为通过后 MUST 呈现 finishing 菜单；不得未询问即 push/删分支
- 薄适配权威：本节 / Spec / schema 为准；MAY Read 上游 skill 仅参考
- 保留独立验证者门禁：实现会话不得自填「独立验证结论」或自审通过代码审查

**Output Format**

Use clear markdown with:
- Table for summary scorecard
- Grouped lists for issues (CRITICAL/WARNING/SUGGESTION)
- Code references in format: `file.ts:123`
- Specific, actionable recommendations
- No vague suggestions like "consider reviewing"
- 通过后附 finishing 选项菜单（等待用户选择）
