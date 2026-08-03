---
name: /opsx-archive
id: opsx-archive
category: Workflow
description: Archive a completed change in the experimental workflow
---

Archive a completed change in the experimental workflow.

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`, `view`). Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: Optionally specify a change name after `/opsx:archive` (e.g., `/opsx:archive add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

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

   Verification failures are hard gates. Do not offer a confirmation override.

5. **Assess delta spec sync state**

   Use `artifactPaths.specs.existingOutputPaths` from status JSON as the only delta-spec source. If the `specs` entry is missing or `existingOutputPaths` is empty (including `skip_specs` changes), proceed without sync prompt and do not infer deltas elsewhere.

   **If delta specs exist:**
   - Compare each delta spec with its corresponding main spec at `<planningHome.root>/openspec/specs/<capability>/spec.md` (use store-aware `planningHome.root`, not a hardcoded repo path)
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

   Then re-compare every capability that has a delta in `artifactPaths.specs.existingOutputPaths`. A successful sync leaves nothing left to apply. If the sync failed or any capability still differs, report and stop — do not archive.

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
   - Independent verification status and any explicitly accepted warnings or residual risks

**Output On Success**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/<target-name>/
**Specs:** ✓ Synced to main specs
**Verification:** ✓ Independent verification passed

All artifacts and tasks complete. Archive gate passed.
```

**Output On Success (No Delta Specs)**

```
## Archive Complete

**Change:** <change-name>
**Schema:** <schema-name>
**Archived to:** the archive path derived from `planningHome.changesDir`/<target-name>/
**Specs:** No delta specs
**Verification:** ✓ Independent verification passed

All artifacts and tasks complete. Archive gate passed.
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
- Incomplete artifacts (neither done nor skipped), incomplete tasks, missing independent verification, pending/failed checks, and CRITICAL issues are hard blockers
- Warnings may proceed only when residual risks are explicitly documented and accepted
- Preserve .openspec.yaml when moving to archive (it moves with the directory)
- Show clear summary of what happened
- If sync is requested, run the Skill tool to invoke `openspec-sync-specs` inline and verify before moving `changeRoot`
- If delta specs exist, always run the sync assessment and show the combined summary before prompting
- Never archive while a spec sync is still in flight
- Apply relevant runtime context from `instructions archive`; operation guidance remains advisory
