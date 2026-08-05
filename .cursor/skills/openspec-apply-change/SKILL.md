---
name: openspec-apply-change
description: Implement tasks from an OpenSpec change. Use when the user wants to start implementing, continue implementation, or work through tasks.
allowed-tools: Bash(openspec:*)
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.6.0"
---

Implement tasks from an OpenSpec change.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

---

## Superpowers 对接：worktree / TDD / debugging / 证据门禁（薄适配）

在开始改代码与派发实现子 Agent 之前，以及实现失败、证据门禁声称完成时，MUST 遵循下方写死的门禁。本节与 Spec / schema `apply.instruction` 为权威；skill 可更严，不得更松；冲突时以更严门禁为准。MAY Read 上游 `using-git-worktrees` / `test-driven-development` / `systematic-debugging` / `verification-before-completion` 作话术补充；**上游全文 checklist / 终态仅参考，本节下列步骤为权威**（含已写死的 worktree 检测顺序），避免与本节冲突。

### 开工：Git worktree 评估与询问（决策 4）

在**首次改代码 / 首次派发实现子 Agent 之前**，按 `using-git-worktrees` 检测顺序评估隔离状态：

1. 检测是否已在隔离 worktree（注意 submodule 与 linked worktree 的区分；已在隔离则宣布路径/分支并继续）
2. 若在普通 checkout：向用户简短说明利弊并询问是否创建/切换隔离工作区；大变更或主工作树已有无关脏改动时，措辞偏「推荐隔离」
3. 用户同意 → 用原生 worktree 工具（若有）或 `git worktree` 回退完成准备后，再派发实现子 Agent
4. 用户明确要求在当前工作树继续 → **MAY 跳过**，不得静默强制；MUST 在状态汇报中注明「未隔离 / 用户拒绝 worktree」

同一时刻仍只跑一个实现子 Agent。用户本会话已声明过 worktree 偏好时，可遵从该声明而不重复追问。

### Implementer 提示：默认 TDD（决策 5）

派发给实现子 Agent 的提示 MUST 要求遵循 `test-driven-development`：

- 行为变更：先失败测试（或仓库约定的等价红灯信号），再最小实现，再交任务级审查
- 行为变更的任务汇报 MUST 附上红灯证据（失败测试命令与输出，或仓库约定的等价红灯信号），供任务级审查执法
- 纯文档 / 纯配置 / 无行为断言的生成物、或用户明确豁免：MAY 跳过 TDD，但 MUST 在任务汇报写明跳过理由
- 任务级 reviewer 可将「行为变更却无红灯证据」列为 Critical / Important，并据此要求修复后复审

`executing-plans` SHALL NOT 替代 SDD 成为默认主路径。

### 阻塞与失败：systematic-debugging

当实现、任务级审查或证据门禁出现测试失败、异常行为或不明根因时：

- MUST 先遵循 `systematic-debugging` 收集证据并定位根因，禁止连续盲改
- 下一动作是系统化调试（或派发调试取向的修复子 Agent），而不是堆叠无关改动
- 若根因在 design / specs / tasks：MUST 暂停实现（含暂停勾选后续任务），建议更新 OpenSpec 制品，而不是用代码绕过

### 证据声称：verification-before-completion

执行与记录 `verification.md` 检查、以及任务完成汇报中的自动化证据时，MUST 遵循 `verification-before-completion`：

- 本回合实际执行适用命令并阅读输出后，才可将检查标为「通过」或宣称完成
- **无新鲜命令输出不得标通过**；禁止沿用旧会话口头记忆作为唯一证据

### Finishing 不在 apply（决策 7）

**不要**在 apply 内执行 `finishing-a-development-branch` 或整分支终审。finishing 挂在独立 verify 通过后（及 archive 成功后若尚未集成）。apply 仅可提醒「verify/archive 会提示收尾」，不得在未询问时强制推送或删分支。

---

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context if the user mentioned a change
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` to get available changes and use the **AskUserQuestion tool** to let the user select

   Always announce: "Using change: <name>" and how to override (e.g., `/opsx:apply <other>`).

2. **Check status to understand the schema**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to understand:
   - `schemaName`: The workflow being used (e.g., "spec-driven")
   - `planningHome`, `changeRoot`, and `actionContext`: planning scope and edit constraints
   - Which artifact contains the tasks (typically "tasks" for spec-driven, check status for others)

3. **Get apply instructions**

   ```bash
   openspec instructions apply --change "<name>" --json
   ```

   This returns:
   - `contextFiles`: artifact ID -> array of concrete file paths (varies by schema - could be proposal/specs/design/tasks or spec/tests/implementation/docs)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest using `/opsx:propose <change-name>` to finish the existing change artifacts
   - If `state: "all_done"`: **跳过**步骤 6（worktree 评估与询问）与步骤 7（实现段）；读完 context 并展示进度后，**直接**进入步骤 8 证据门禁；do not suggest archive
   - Otherwise: proceed to implementation（含步骤 6–7）

   CLI `apply.instruction` 与本 skill 双写关键约束；冲突时以**更严门禁**为准（决策 8）。

4. **Read context files**

   Read every file path listed under `contextFiles` from the apply instructions output.
   The files depend on the schema being used:
   - **spec-driven**: proposal, specs, design, tasks
   - Other schemas: follow the contextFiles from CLI output

5. **Show current progress**

   Display:
   - Schema being used
   - Progress: "N/M tasks complete"
   - Remaining tasks overview
   - Dynamic instruction from CLI
   - Worktree：尚未评估时写「待评估 / 见下一步」（`all_done` 时可写「跳过（all_done → 证据门禁）」）；**禁止**在步骤 6 完成前预填「已隔离 / 用户已拒绝」等未评估结论。仅当本会话已完成评估或用户已声明偏好时，才填写真实状态。

   若 `state: "all_done"`：展示进度后跳到步骤 8，不要进入步骤 6–7。

6. **开工前：worktree 评估与询问**（`all_done` 时跳过）

   按上方「开工：Git worktree 评估与询问」执行。未完成评估（或用户选择未记录）前，不要派发实现子 Agent、不要改业务代码。

7. **Implement tasks（默认：superpowers 子 Agent 驱动）**（`all_done` 时跳过）

   实现阶段**默认**遵循 superpowers `subagent-driven-development`：编排器（本会话）只做协调，不亲自写业务代码。

   **编排约定：**
   - 以 `tasks.md` 复选框为进度真源（`- [ ]` / `- [x]`）；可选用 `.superpowers/sdd/progress.md` 作恢复台账，但勾选 tasks 仍必须同步。
   - **逐项**处理待办：对每个 pending 任务用 **Task** 派发**全新** implementer 子 Agent（不 `resume` 上一任务；不把本会话实现历史整段灌入）。
   - 同一时刻**只跑一个**实现子 Agent（禁止并行改同一工作树，避免冲突）。
   - 子 Agent 提示须包含：任务原文、相关 proposal/specs/design 要点或路径、全局约束、最小必要接口上下文、**默认 TDD 要求**（行为变更须附红灯命令与输出；文档/配置可跳过并记原因）；不要让子 Agent 通读整份无关历史。
   - 实现子 Agent 完成后：派发**任务级** reviewer（spec 合规 + 代码质量；可将「行为变更却无红灯证据」升为 Important/Critical）。Critical / Important 须再派 fix 子 Agent 并复审，通过后才勾选任务。
   - 失败或不明根因：先走 `systematic-debugging`（见上方），再决定修复或暂停改制品。
   - 勾选：`- [ ]` → `- [x]`，再进入下一项。
   - **不要**在 apply 内做 SDD 的「整分支终审」或 `finishing-a-development-branch`；整分支审查与归档门禁由后续独立 `/opsx:verify` 负责。
   - **不要**擅自 `git commit`，除非用户在本会话明确要求提交。

   **回退（仅当 Task / 子 Agent 不可用）：**
   - 在本会话内直接实现该任务，仍保持最小改动、TDD（可跳过记原因）、即时勾选；并在状态汇报中注明已回退。

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - 调试表明根因在 design/specs/tasks → 暂停并建议更新制品
   - Error or blocker encountered → report and wait for guidance
   - Implementer 报告 `BLOCKED` / 无法消解的歧义 → escalate to user
   - User interrupts

8. **Complete the verification evidence gate**

   When all implementation tasks are complete（含进入本步时 `state` 已为 `all_done`）：
   - Locate the `verification` artifact from `contextFiles`; do not assume a path.
   - Execute every applicable command or manual check defined in `verification.md`（遵循 `verification-before-completion`：本回合新鲜输出）。
   - Update each applicable item to `通过` or `失败`; mark genuinely irrelevant items `不适用` with a reason.
   - Record the actual command or step, result, and concise evidence. Never fabricate execution.
   - **无新鲜命令输出不得标「通过」**；禁止仅用旧会话口头记忆作为唯一证据。
   - List skipped checks, failures, and residual risks.
   - Do **not** fill or change `独立验证结论`; the implementer cannot verify itself.
   - Do **not** mark「代码审查」为通过或填写审查台账结论；代码审查由独立 verify Agent 编排.
   - If any required check fails or remains `待执行`, pause and report the blocker（失败原因不明时先 `systematic-debugging`）。
   - If evidence is complete, **automatically dispatch** an independent verify Agent (preferred), then report its conclusion:
     1. Use the **Task** tool with a **fresh/isolated** subagent (do not `resume` the implementer; do not pass implementation chat history).
     2. Instruct it to follow `.cursor/skills/openspec-verify-change/SKILL.md` / `/opsx-verify` for this change (pass `--store` when applicable), re-run applicable checks, **orchestrate Code Review**, update `## 代码审查（归档硬门禁）`, and write `## 独立验证结论` only.
     3. After it returns, summarize 通过/阻塞 for the user. Do **not** rewrite the conclusion yourself.
     4. **Fallback only** if Task/dispatch is unavailable: ask the user to open a fresh Agent conversation and run `/opsx:verify <change-name>`.

   A completed task list is not archive-ready until independent verification records `验证结论：通过`（含代码审查门禁通过）.
   apply 不执行 finishing；可提醒用户 verify/archive 阶段会提示分支收尾选项。

9. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - Worktree：仅当本会话已完成步骤 6 评估（或用户已声明偏好）时填写真实结果（已隔离路径，或「用户拒绝隔离，在当前工作树继续」）。**若因 `all_done` 跳过步骤 6 而未评估** → 写「跳过（all_done）」或「待评估已跳过」，**禁止**编造「已隔离 / 用户拒绝」。
   - If all tasks and implementation checks are done: state that independent `/opsx:verify` was auto-dispatched (or fallback: user must open a fresh session)
   - If paused: explain why and wait for guidance

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)
Mode: subagent-driven-development（Task 逐任务实现 + 任务级审查）
Worktree: <已隔离 path | 用户拒绝，当前工作树 | 跳过（all_done）| 待评估已跳过>

Working on task 3/7: <task description>
→ Task: implementer …（提示含 TDD 或跳过理由要求）
→ Task: task-reviewer …
✓ Task complete（已勾选 tasks.md）

Working on task 4/7: <task description>
→ Task: implementer …
→ Task: task-reviewer …
✓ Task complete（已勾选 tasks.md）
```

**Output On Completion**

```
## Implementation Complete — Independent Verification Required

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓
**Worktree:** <已隔离 path | 用户拒绝，当前工作树 | 跳过（all_done）| 待评估已跳过>

### Completed This Session
- [x] Task 1
- [x] Task 2
...

Implementation checks are recorded in verification.md（证据为本回合新鲜命令输出）.
Independent `/opsx:verify` was auto-dispatched via Task (or fallback: open a fresh Agent conversation and run `/opsx:verify <change-name>`).
Do not archive until it records `验证结论：通过`.
（finishing 不在 apply；verify/archive 会提示收尾选项。）
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete
**Worktree:** <status>

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**
- Default to superpowers `subagent-driven-development` for implementation; orchestrator coordinates, does not implement application code unless Task is unavailable
- `executing-plans` SHALL NOT 替代 SDD 成为默认主路径
- 开工前 MUST 做 worktree 评估与询问（`state: all_done` 时跳过评估与实现，直接证据门禁）；禁止静默强制；用户拒绝 MUST 记录；Show progress / 完成态不得预填或编造未评估的 Worktree 结论（`all_done` 未评估时用「跳过（all_done）」或「待评估已跳过」）
- Implementer 提示默认 TDD；行为变更汇报须附红灯证据；文档/配置可跳过并记原因；审查可将无红灯升 Important/Critical
- 失败/不明根因 MUST 先 `systematic-debugging`；根因在设计则暂停并建议改制品
- 证据门禁 MUST 遵循 `verification-before-completion`：无新鲜命令输出不得标通过
- Keep going through tasks until done or blocked; do not pause for "should I continue?"
- Always read context files before starting (from the apply instructions output)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task; one implementer subagent at a time
- Do not mark a task complete until task-level review approves (or fallback in-session work is done)
- Update task checkbox immediately after a task is approved complete
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names
- Never treat completed task checkboxes as sufficient evidence for archive
- Never fill the independent verification conclusion from the implementation session
- Never self-pass「代码审查」 or invent review findings from the implementation session
- Prefer Task-dispatch of an independent `/opsx:verify` subagent after the evidence gate; only fall back to asking the user to open a fresh session
- Never suggest archive before independent verification passes（含代码审查门禁）
- Do not run `finishing-a-development-branch` or whole-branch final review inside apply
- Do not commit unless the user explicitly asks
- 薄适配权威：本节 / Spec / schema 为准；MAY Read 上游 skill 仅参考

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
