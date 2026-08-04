---
name: /opsx-apply
id: opsx-apply
category: Workflow
description: Implement tasks from an OpenSpec change (Experimental)
---

Implement tasks from an OpenSpec change.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name (e.g., `/opsx:apply add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

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
   - `contextFiles`: artifact ID -> array of concrete file paths (varies by schema)
   - Progress (total, complete, remaining)
   - Task list with status
   - Dynamic instruction based on current state

   **Handle states:**
   - If `state: "blocked"` (missing artifacts): show message, suggest using `/opsx:propose <change-name>` to finish the existing change artifacts
   - If `state: "all_done"`: skip implementation and continue to the verification evidence gate below; do not suggest archive
   - Otherwise: proceed to implementation

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

6. **Implement tasks (loop until done or blocked)**

   For each pending task:
   - Show which task is being worked on
   - Make the code changes required
   - Keep changes minimal and focused
   - Mark task complete in the tasks file: `- [ ]` → `- [x]`
   - Continue to next task

   **Pause if:**
   - Task is unclear → ask for clarification
   - Implementation reveals a design issue → suggest updating artifacts
   - Error or blocker encountered → report and wait for guidance
   - User interrupts

7. **Complete the verification evidence gate**

   When all implementation tasks are complete:
   - Locate the `verification` artifact from `contextFiles`; do not assume a path.
   - Execute every applicable command or manual check defined in `verification.md`.
   - Update each applicable item to `通过` or `失败`; mark genuinely irrelevant items `不适用` with a reason.
   - Record the actual command or step, result, and concise evidence. Never fabricate execution.
   - List skipped checks, failures, and residual risks.
   - Do **not** fill or change `独立验证结论`; the implementer cannot verify itself.
   - Do **not** mark「代码审查」三轨为通过或填写审查台账结论；代码审查由独立 verify Agent 编排.
   - If any required check fails or remains `待执行`, pause and report the blocker.
   - If evidence is complete, **automatically dispatch** an independent verify Agent (preferred), then report its conclusion:
     1. Use the **Task** tool with a **fresh/isolated** subagent (do not `resume` the implementer; do not pass implementation chat history).
     2. Instruct it to follow `.cursor/skills/openspec-verify-change/SKILL.md` / `/opsx-verify` for this change (pass `--store` when applicable), re-run applicable checks, **orchestrate code-review tracks (Code Review / Bugbot / Security Review)**, update `## 代码审查（归档硬门禁）`, and write `## 独立验证结论` only.
     3. After it returns, summarize 通过/阻塞 for the user. Do **not** rewrite the conclusion yourself.
     4. **Fallback only** if Task/dispatch is unavailable: ask the user to open a fresh Agent conversation and run `/opsx:verify <change-name>`.

   A completed task list is not archive-ready until independent verification records `验证结论：通过`（含代码审查门禁通过）.

8. **On completion or pause, show status**

   Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - If all tasks and implementation checks are done: state that independent `/opsx:verify` was auto-dispatched (or fallback: user must open a fresh session)
   - If paused: explain why and wait for guidance

**Output During Implementation**

```
## Implementing: <change-name> (schema: <schema-name>)

Working on task 3/7: <task description>
[...implementation happening...]
✓ Task complete

Working on task 4/7: <task description>
[...implementation happening...]
✓ Task complete
```

**Output On Completion**

```
## Implementation Complete — Independent Verification Required

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 7/7 tasks complete ✓

### Completed This Session
- [x] Task 1
- [x] Task 2
...

Implementation checks are recorded in verification.md.
Independent `/opsx:verify` was auto-dispatched via Task (or fallback: open a fresh Agent conversation and run `/opsx:verify <change-name>`).
Do not archive until it records `验证结论：通过`.
```

**Output On Pause (Issue Encountered)**

```
## Implementation Paused

**Change:** <change-name>
**Schema:** <schema-name>
**Progress:** 4/7 tasks complete

### Issue Encountered
<description of the issue>

**Options:**
1. <option 1>
2. <option 2>
3. Other approach

What would you like to do?
```

**Guardrails**
- Keep going through tasks until done or blocked
- Always read context files before starting (from the apply instructions output)
- If task is ambiguous, pause and ask before implementing
- If implementation reveals issues, pause and suggest artifact updates
- Keep code changes minimal and scoped to each task
- Update task checkbox immediately after completing each task
- Pause on errors, blockers, or unclear requirements - don't guess
- Use contextFiles from CLI output, don't assume specific file names
- Never treat completed task checkboxes as sufficient evidence for archive
- Never fill the independent verification conclusion from the implementation session
- Never self-pass「代码审查」三轨 or invent review findings from the implementation session
- Prefer Task-dispatch of an independent `/opsx:verify` subagent after the evidence gate; only fall back to asking the user to open a fresh session
- Never suggest archive before independent verification passes（含代码审查门禁）

**Fluid Workflow Integration**

This skill supports the "actions on a change" model:

- **Can be invoked anytime**: Before all artifacts are done (if tasks exist), after partial implementation, interleaved with other actions
- **Allows artifact updates**: If implementation reveals design issues, suggest updating artifacts - not phase-locked, work fluidly
