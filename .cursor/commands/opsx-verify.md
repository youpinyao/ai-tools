---
name: /opsx-verify
id: opsx-verify
category: Workflow
description: Verify implementation matches change artifacts before archiving
---

Verify that an implementation matches the change artifacts (specs, tasks, design).

**Independence gate:** The verifier must **not** have implemented the change. Allowed runners:
1. **Preferred:** A Task-dispatched subagent started by `/opsx:apply` after the implementation evidence gate (isolated context; no implementer history).
2. A user-opened fresh Agent conversation that runs `/opsx-verify`.

If **this** conversation participated in implementation (wrote application code / marked implementation tasks done for this change), **stop**: do not fill `独立验证结论` yourself—dispatch a Task subagent for verify, or ask the user to open a fresh conversation. The implementer cannot approve its own work.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name after `/opsx:verify` (e.g., `/opsx:verify add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

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
   - Re-run every applicable recorded automated check independently, including contract, migration, security, E2E, and non-functional checks when listed.
   - Re-perform applicable manual checks, or record a CRITICAL blocker when the required environment or authority is unavailable.
   - Never trust a recorded success result without fresh command evidence.

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

   **Dispatch three tracks** (prefer parallel Task subagents; verifier orchestrates, does not self-approve):
   1. **Code Review** — follow superpowers `requesting-code-review`: dispatch a general-purpose reviewer with the `code-reviewer.md` prompt template (`DESCRIPTION`, `PLAN_OR_REQUIREMENTS`, `BASE_SHA`, `HEAD_SHA`). Expect Critical / Important / Minor.
   2. **Bugbot** — follow `review-bugbot`: exactly one `bugbot` subagent; default `Diff: branch changes`.
   3. **Security Review** — follow `review-security`: exactly one `security-review` subagent; default `Diff: branch changes`.

   **Record results into verification.md:**
   - Update each 审查轨 row: 状态、Critical/高危、Important、Minor counts、证据摘要.
   - Append every finding to Finding 处置台账（ID、轨、严重级、位置、摘要；处置/状态 initially 待执行 unless already fixed before this verify）.
   - Pure docs / empty diff: mark track `不适用` with a concrete reason; do not fake a pass.

   **Gate mapping (档位 1):**
   - Applicable track still `待执行`, or dispatch failed without a compensated re-run → CRITICAL（阻塞）
   - Unresolved Critical（含安全高危）→ CRITICAL（阻塞）
   - Unresolved Important without 修复 or 技术反驳并接受（须写入「未执行项与剩余风险」且验证者确认）→ CRITICAL（阻塞）
   - Minor → 可记入剩余风险；alone does NOT block `验证结论：通过`
   - Implementer/response loop for findings should follow `receiving-code-review`（核实 → 修复或技术反驳；禁止表演式同意）. If fixes are still needed, set conclusion to `阻塞` and list required fixes—do not silently pass.

9. **Persist the independent verification conclusion**

   If a `verification` artifact exists, update its `## 独立验证结论` section:
   - Set `验证结论` to `通过` only when there are no CRITICAL issues, no failed required checks, no applicable pending checks, **and** code-review gate (step 8) has no blocking open findings.
   - Otherwise set `验证结论` to `阻塞`.
   - Set `验证者` to `独立 Agent（子 Agent）` when Task-dispatched, or `独立 Agent（新会话）` when user-opened.
   - Record the verification scope, CRITICAL issues, WARNING issues, **代码审查**三轨摘要, and whether residual risks were explicitly accepted.
   - Add concise fresh command evidence to the relevant result rows.

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
   | Code Review  | 三轨状态 / 阻塞 finding |
   ```

   **Issues by Priority**:

   1. **CRITICAL** (Must fix before archive):
      - Incomplete tasks
      - Missing requirement implementations
      - Code-review：未跑完的适用轨、未关闭 Critical/高危、未处置 Important
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

**Verification Heuristics**

- **Completeness**: Focus on objective checklist items (checkboxes, requirements list)
- **Correctness**: Use keyword search, file path analysis, reasonable inference - don't require perfect certainty
- **Coherence**: Look for glaring inconsistencies, don't nitpick style
- **Code Review**: Orchestrate real subagent reviews; never invent findings or mark tracks passed without dispatch evidence
- **False Positives**: When uncertain, prefer SUGGESTION over WARNING, WARNING over CRITICAL（但未关闭的 Critical/高危与未处置 Important 仍为 CRITICAL）
- **Actionability**: Every issue must have a specific recommendation with file/line references where applicable

**Graceful Degradation**

- If only tasks.md exists: verify task completion only, skip spec/design checks
- If tasks + specs exist: verify completeness and correctness, skip design
- If full artifacts: verify all three dimensions
- If verification.md lacks「代码审查」节（旧产物）: add the section from the current template before concluding, or treat missing applicable review as CRITICAL
- Always note which checks were skipped and why
- A completed task list is not proof of correctness
- Never mark independent verification as passed with applicable pending or failed checks
- Never mark passed with open Critical/高危 or undisposed Important from code review
- Persist the conclusion to verification.md; chat output alone does not satisfy the archive gate

**Output Format**

Use clear markdown with:
- Table for summary scorecard
- Grouped lists for issues (CRITICAL/WARNING/SUGGESTION)
- Code references in format: `file.ts:123`
- Specific, actionable recommendations
- No vague suggestions like "consider reviewing"
