---
name: /opsx-archive
id: opsx-archive
category: Workflow
description: Archive a completed change in the experimental workflow
---

Archive a completed change in the experimental workflow.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`, `view`). Once selected, treat `--store <id>` as sticky for the rest of the workflow. Every unscoped example of those commands below is shorthand: before running it, append the flag. For example, run `openspec status --change "<name>" --json --store "<id>"`, not the unscoped form shown below. Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

`<capability-path>` is the spec directory relative to `specs/` (for example, `user-auth` or `identity/user-auth`). Preserve the full path from each delta spec when resolving its main spec.

**Input**: Optionally specify a change name after `/opsx:archive` (e.g., `/opsx:archive add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

---

## Superpowers 对接：finishing（薄适配）

在归档门禁全部通过并完成归档移动之后，若尚未完成分支集成，MUST 遵循下方写死的门禁。本节与 Spec「Verify 通过后须提供分支收尾选项」中 archive 场景 / Design 决策 7 为权威；skill/command 可更严，不得更松；冲突时以更严门禁为准。MAY Read 上游 `finishing-a-development-branch` 作话术补充；**上游全文 checklist / 终态仅参考，本节下列步骤为权威**，避免与本节冲突。

### Finishing：归档成功后若未集成则再提示（决策 7）

当归档门禁通过且 `changeRoot` 已成功移至 archive 后：

- 若分支尚未完成集成（未合并到目标分支、未创建/合并 PR、用户此前推迟了收尾等）→ MUST 遵循 `finishing-a-development-branch` 核心步骤：确认归档门禁已通过 → 检测工作区环境 → 向用户呈现结构化选项（合并 / 创建 PR / 保留分支 / 清理 worktree 等，按环境裁剪）
- **仅在用户选择后**执行集成或清理动作
- MUST NOT 在未询问的情况下默认强制推送或删除分支
- 用户可推迟收尾；不得静默结束而不提及集成/清理选项
- 若用户在 verify 阶段（或此前）已完成集成 → 可跳过 finishing 菜单，并在摘要中注明「分支已集成」
- finishing **不在** apply 中执行；verify 负责通过后的首次提示，本 command 负责归档成功后的再次提示（若尚未集成）
- 本约定 MUST NOT 削弱既有归档硬门禁（制品完成、任务完成、独立验证通过、代码审查门禁、delta sync 评估等）

---

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show only active changes (not already archived).
   Include the schema used for each change if available.

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

   **Load archive instructions (advisory, OpenSpec 1.7+):**

   After resolving the change, run:
   ```bash
   openspec instructions archive --change "<name>" --json
   ```
   Keep the same selected-root / `--store` flags. This lookup is optional: if it fails or returns invalid JSON (older CLI), continue with no extra context. Do not block archiving.

   On success, treat `context` as required prompt-level input (apply relevant project facts). Treat `operationGuidance` as optional additive advice. Do not copy either field verbatim into artifacts or summaries unless the user asks. If either conflicts with built-in gates, CLI checks, or explicit user choices, preserve the controlling value and explain.

2. **Check artifact completion status**

   Run `openspec status --change "<name>" --json` to check artifact completion.

   Parse the JSON to understand:
   - `schemaName`: The workflow being used
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context
   - `artifacts`: List of artifacts with their status (`done`, `skipped`, or other)

   **If any artifacts are neither `done` nor `skipped`** (skipped satisfies the requirement when the change declares `skip_specs`):
   - Stop and list the incomplete artifacts
   - Do not offer an override; complete the artifacts first

3. **Check task completion status**

   Read the tasks file (typically `tasks.md`) to check for incomplete tasks.

   Count tasks marked with `- [ ]` (incomplete) vs `- [x]` (complete).

   **If incomplete tasks found:**
   - Stop and show the incomplete task count and descriptions
   - Do not offer an override; complete or explicitly remove invalid tasks first

   **If no tasks file exists:** Proceed without task-related warning.

4. **Enforce independent verification**

   For schemas that include a `verification` artifact:
   - Resolve and read the verification artifact from status/instruction context; do not assume its path.
   - Require the exact conclusion `验证结论：通过` in `## 独立验证结论`.
   - Require `验证者` to identify an independent Agent/new conversation.
   - Block archive if the conclusion is missing, `待执行`, or `阻塞`.
   - Block archive if any applicable check is `待执行` or `失败`.
   - Block archive if any CRITICAL issue is unresolved.
   - **Code review gate（档位 1）:** when `## 代码审查（归档硬门禁）` exists:
     - Block if any applicable 审查轨 is `待执行` or `失败`.
     - Block if Finding 处置台账 has unresolved Critical.
     - Block if any Important finding is still `待执行` / 未关闭，且未在「未执行项与剩余风险」中写明技术反驳并接受.
     - Minor-only open items may proceed when recorded as accepted residual risk.
     - Missing「代码审查」section on evidence-driven changes: block（须先补跑 verify）.

   Verification failures are hard gates. Do not offer a confirmation override.

5. **Assess delta spec sync state**

   Use `artifactPaths.specs.existingOutputPaths` from status JSON as the only delta-spec source. If the `specs` entry is missing or `existingOutputPaths` is empty (including `skip_specs` changes), proceed without sync prompt and do not infer deltas elsewhere.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `<planningHome.root>/openspec/specs/<capability-path>/spec.md` (use store-aware `planningHome.root`, not a hardcoded repo path)
   - Determine what changes would be applied (adds, modifications, removals, renames)
   - Show a combined summary before prompting

   **Prompt options:**
   - If changes needed: "Sync now (recommended)", "Archive without syncing"
   - If already synced: "Archive now", "Sync anyway", "Cancel"

   Route on the answer:
   - "Cancel" — stop, do not archive
   - "Archive without syncing" or "Archive now" — proceed to archive
   - "Sync now" or "Sync anyway" — sync inline, then verify (below)
   - Anything else — ask again rather than archiving

   Before a selected sync writes any main spec, run `openspec instructions specs --change "<name>" --json` once with the same selected-root flags. If the lookup fails or returns invalid JSON, report the error and stop before writing main specs or moving the change. Apply returned `rules` only to the content/form of main specs produced by this merge.

   Then run the `openspec-sync-specs` workflow **inline** (agent-driven intelligent merge) for change '<name>' and wait for it to finish. Do not delegate to a background task — the next step would move `changeRoot` out from under an in-flight sync. If you must delegate, do it synchronously and wait.

   Then re-compare every capability that has a delta in `artifactPaths.specs.existingOutputPaths`. A successful sync leaves nothing left to apply. If the sync failed or any capability still differs, report and stop — do not archive. Each capability must now read as already synced:
   - ADDED requirements present
   - MODIFIED requirements carrying the scenario and description changes named in the delta, with their other scenarios intact
   - REMOVED requirements gone — and where this sync retired a capability (removed its last requirement, leaving `## Requirements` empty), its main spec deleted rather than left empty; a spec the sync deliberately kept and reported is also a match
   - RENAMED requirements present under the new name and absent under the old one

6. **Perform the archive**

   Create an `archive` directory under `planningHome.changesDir` if it doesn't exist:
   ```bash
   mkdir -p "<planningHome.changesDir>/archive"
   ```

   Generate the target name: use the change name as-is when it already starts with a `YYYY-MM-DD-` prefix; otherwise prepend the current date as `YYYY-MM-DD-<change-name>`. Never stack a second date (same rule as `openspec archive`).

   **Check if target already exists:**
   - If yes: Fail with error, suggest renaming existing archive or using different date
   - If no: Move `changeRoot` to the archive directory

   ```bash
   mv "<changeRoot>" "<planningHome.changesDir>/archive/<target-name>"
   ```

7. **Display summary**

   Show archive completion summary including:
   - Change name
   - Schema that was used
   - Archive location
   - Spec sync status (synced / sync skipped / no delta specs)
   - Independent verification status, code-review gate status, and any explicitly accepted warnings or residual risks

8. **Finishing 菜单（归档成功后若尚未集成）**

   归档移动成功后，按上方「Finishing」薄适配检测分支是否已集成：
   - 尚未集成 → MUST 立即向用户呈现 `finishing-a-development-branch` 选项菜单（按环境裁剪），并等待用户选择后再执行；用户可推迟
   - 已集成 → 跳过菜单，在摘要中注明「分支已集成」
   - MUST NOT 未询问即 force push、强制合并或删除分支
   - 归档门禁失败或未完成移动 → **不进入**本步（既有硬门禁不变，不得用 finishing 绕过）

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/<target-name>/
**Specs:** ✓ Synced to main specs
**Verification:** ✓ Independent verification passed（含代码审查门禁）

All artifacts and tasks complete. Archive gate passed.

**Finishing:** 分支尚未集成 → 呈现收尾选项菜单（或「分支已集成」/「用户推迟」）
```

**Output On Success (No Delta Specs)**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/<target-name>/
**Specs:** No delta specs
**Verification:** ✓ Independent verification passed（含代码审查门禁）

All artifacts and tasks complete. Archive gate passed.

**Finishing:** 分支尚未集成 → 呈现收尾选项菜单（或「分支已集成」/「用户推迟」）
```

**Output On Success With Warnings**

```
## Archive Complete (with warnings)

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/<target-name>/
**Specs:** Sync skipped (user chose to skip)

**Warnings:**
- Independent verification passed with accepted non-critical warnings
- Residual risks were explicitly accepted
- Delta spec sync was skipped (user chose to skip)

**Finishing:** 分支尚未集成 → 呈现收尾选项菜单（或「分支已集成」/「用户推迟」）

Review the archive if this was not intentional.
```

**Output On Error (Archive Exists)**

```
## Archive Failed

**Change:** <change-name>
**Target:** the archive path derived from `planningHome.changesDir`/<target-name>/

Target archive directory already exists.

**Options:**
1. Rename the existing archive
2. Delete the existing archive if it's a duplicate
3. Wait until a different date to archive
```

**Guardrails**
- Always prompt for change selection if not provided
- Use artifact graph (openspec status --json) for completion checking
- Treat `skipped` artifacts as satisfied when `skip_specs` is declared
- Incomplete artifacts (neither done nor skipped), incomplete tasks, missing independent verification, pending/failed checks, CRITICAL issues, and code-review gate failures（未跑完适用轨 / 未关闭 Critical / 未处置 Important）are hard blockers
- Warnings and Minor review findings may proceed only when residual risks are explicitly documented and accepted
- Accepted Important 技术反驳 must appear in residual risks with verifier acknowledgment
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- If sync is requested, run the Skill tool to invoke `openspec-sync-specs` inline and verify before moving `changeRoot`
- If delta specs exist, always run the sync assessment and show the combined summary before prompting
- Never archive while a spec sync is still in flight
- Apply relevant runtime context from `instructions archive`; operation guidance remains advisory
- 归档成功后若尚未集成 MUST 呈现 finishing 菜单；不得静默结束；不得未询问即 force push/删分支
- 薄适配权威：本节 / Spec archive 场景 / Design 决策 7 为准；MAY Read 上游 skill 仅参考
- MUST NOT 因 finishing 约定削弱既有归档硬门禁
