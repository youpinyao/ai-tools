---
name: openspec-update-change-from-code
description: Use when implemented code has drifted from an active OpenSpec change, or the user asks to sync OpenSpec from code, update change artifacts after implementation, 从代码回写 OpenSpec, or runs /opsx-update-change-from-code.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: youpinyao
  version: "1.2.0"
---

# Update an OpenSpec Change from Code

Synchronize an active OpenSpec change and its related repository documentation from implemented
code. Code and explicit user decisions are the source of truth.

This is the reverse of `openspec-apply-change` and is distinct from
`openspec-sync-specs`, which updates main specs.

## Input and store

The optional input is a change name. If the work uses a registered OpenSpec store, run
`openspec store list --json` and retain `--store <id>` on every supported follow-up command.
Otherwise, use the nearest repository-local OpenSpec root.

## Workflow

### 1. Select the change

- Use an explicitly supplied change name.
- Otherwise infer it only when conversation, referenced files, and Git changes identify one change.
- Auto-select a sole active change only when it clearly matches the implementation.
- If selection is ambiguous, run `openspec list --json` and ask the user to choose.
- If no identifiable active change exists, stop and suggest proposing or selecting one.

Announce `Using change: <name>` and explain how to override it.

### 2. Resolve schema and edit boundaries

Run:

```bash
openspec status --change "<name>" --json
```

Use `changeRoot`, `artifactPaths`, `actionContext`, and `schemaName` from the response. Read every
existing artifact path returned by the CLI. Do not assume artifact names such as `proposal.md`,
`design.md`, `tasks.md`, or `specs/**`; those are only common in the spec-driven schema.

If the change is archived, do not edit it silently. Ask whether to document the drift in a follow-up
change or intentionally edit the archived copy.

### 3. Discover implementation evidence

Build the evidence set from the current repository:

1. Git status and diffs related to the change.
2. Paths referenced by change artifacts and conversation.
3. Implemented code, tests, configuration, migrations, schemas, generated contracts, and assets in
   the affected dependency or call graph.
4. Related documentation discovered through artifact links, code references, nearby documentation,
   and repository naming conventions.
5. Explicit user decisions in the current conversation.

Repository-specific paths such as a page-level `index.md`, API directory, or model directory may be
evidence when present, but none is mandatory. Generated files may be read as contracts but must not
be hand-edited.

Do not infer requirements from naming alone or invent missing behavior.

### 4. Build a behavioral drift list

Compare implementation with each artifact according to that artifact's purpose, and compare related
repository docs even when they are unchanged in Git.

- **Simple drift:** factual wording, task checkbox, field or option alignment, one scenario, one
  permission, or a small documentation correction with unambiguous evidence.
- **Complex drift:** added or removed requirement, scope change, architecture reversal,
  cross-capability impact, compatibility or migration policy change, or conflicting evidence.

Group drift by target file and record: documented intent → code reality → proposed edit.

### 5. Apply the confirmation policy

- If all drift is simple, briefly state the intended updates and apply them.
- If any drift is complex, stop before applying those items and ask the user to approve all, a
  subset, or none.
- In a mixed set, simple items may be applied while complex items remain pending.

### 6. Update surgically

- Modify only artifacts returned by the resolved change context and directly related repository
  documentation allowed by `actionContext`.
- Preserve each schema's existing structure and terminology.
- Keep unrelated requirements and prose unchanged.
- Mark work complete only when implementation or verification evidence exists.
- Update scope-level artifacts only when scope actually changed.
- Keep related docs consistent with the resulting change artifacts.

Do not implement features, refactor business logic, update main specs, or archive the change.

### 7. Validate and report

Run:

```bash
openspec validate "<name>" --type change --strict --json
```

Include `--store <id>` when applicable. Fix validation issues introduced by the edits and rerun until
clean. If validation cannot run or pre-existing failures remain, report them without claiming full
success.

Summarize:

```text
OpenSpec synced from code: <change-name>
Evidence: <key implementation and documentation paths>
Updated: <artifact or related-doc changes>
Unchanged: <checked artifacts with no drift>
Pending: <complex drift, ambiguity, or validation blockers>
Next: optionally use openspec-sync-specs or openspec-archive-change
```

## Guardrails

- Stay within `changeRoot`, `artifactPaths`, and `actionContext`.
- Never write to main specs through this workflow.
- Never leave a discovered related document stale while claiming synchronization is complete.
- Prefer idempotent edits that produce no wording churn when rerun.
- Keep the language and style of each existing artifact.
