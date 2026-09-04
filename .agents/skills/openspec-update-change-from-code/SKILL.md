---
name: openspec-update-change-from-code
description: Use when implemented code has drifted from an active OpenSpec change, or when there is no active change but an existing main spec matches the implementation, or the user asks to sync OpenSpec from code, update change artifacts after implementation, or 从代码回写 OpenSpec.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: youpinyao
  version: "1.3.1"
---

# Update OpenSpec from Code

Synchronize OpenSpec artifacts from implemented code. Code and explicit user
decisions are the source of truth.

Prefer an active change. When no identifiable active change exists and exactly
one existing main spec matches, write that spec. This is the reverse of
`openspec-apply-change` and is distinct from `openspec-sync-specs`, which merges
change delta specs into main specs.

## Input and store

The optional input is a change name or a spec id. If the work uses a registered
OpenSpec store, run `openspec store list --json` and retain `--store <id>` on
every supported follow-up command, including `list`, `status`, `context`, and
`validate`. Otherwise, use the nearest repository-local OpenSpec root.

## Workflow

### 1. Select the target

Do not create a change, a spec, or a capability. Follow this order. Stop and
ask whenever more than one path is possible; do not auto-pick.

1. **Explicit name is an active change** → `Using change: <name>`.
2. **Explicit name is not active** → run `openspec status --change "<name>"
   --json` (or compare `openspec list --json`) and inspect
   `<root.path>/openspec/changes/archive/`. If an archived match exists, stop
   and ask: follow-up active change, separately approved manual edit of the
   archive, or spec fallback when a matching main spec exists. Do not continue
   against the archive and do not silently switch to a spec.
3. **No explicit change, or the name is not a change** → infer an active
   change only when conversation, referenced files, and Git identify one
   change that clearly matches the implementation. Auto-select that sole
   change. If several active changes could match, run `openspec list --json`
   and ask; do not fall back to a spec while this is unresolved.
4. **An active change covers the same capability as a candidate spec** → stop
   and ask: update that change, or write the main spec. Do not write the spec
   while that change exists.
5. **No identifiable active change** → run `openspec list --specs --json`.
   Use an explicit name only when it equals one listed spec `id`. Otherwise
   infer a spec only when evidence identifies exactly one existing spec.
   Auto-select that sole spec. If several specs could match, ask the user to
   choose one listed `id` (or to propose a change). Write more than one spec
   only when the user names those existing ids.
6. **Nothing matches** → stop and suggest proposing a change.

If an explicit name matches both an active change and a spec, use the change
(step 1). After the user chooses, announce `Using change: <name>` or
`Using spec: <id>` and explain how to override it.

### 2. Resolve schema and edit boundaries

**Change target**

Run:

```bash
openspec status --change "<name>" --json
```

Include `--store <id>` when applicable. Use `changeRoot`, `artifactPaths`,
`actionContext`, and `schemaName` from the response. Read and edit only the
concrete files in `artifactPaths.<id>.existingOutputPaths`. Do not read or
write `outputPath` or `resolvedOutputPath` as concrete files: either value may
be a schema-relative path or an unresolved glob. Do not create an artifact or
a new file under a glob artifact through this workflow. Do not assume artifact
names such as `proposal.md`, `design.md`, `tasks.md`, or `specs/**`; those are
only common in the spec-driven schema.

If `status` reports that the selected change does not exist, return to step 1
(archived or missing). Do not treat that failure as an automatic spec
fallback.

**Spec target**

Run `openspec context --json` if `openspec list --specs --json` did not already
provide `root.path`. Include `--store <id>` when applicable. The only editable
spec file for the selected spec `id` is:

```text
<root.path>/openspec/specs/<id>/spec.md
```

`<id>` must appear in `openspec list --specs --json`. It may contain slashes
for nested capabilities (for example `identity/user-auth`) but must not
contain `..` segments. Confirm the file exists. The resolved realpath must
stay under `<root.path>/openspec/specs/`. Do not create `spec.md`, a
capability directory, or any other file under `specs/`. Do not use deprecated
`openspec spec ...` noun-form commands; prefer `openspec list --specs` and
`openspec validate --type spec`.

### 3. Discover implementation evidence

Build the evidence set from the current repository:

1. Git status and diffs related to the target.
2. Paths referenced by the selected change artifacts or main spec, and by the
   conversation.
3. Implemented code, tests, configuration, migrations, schemas, generated
   contracts, and assets in the affected dependency or call graph.
4. Related documentation discovered through artifact or spec links, code
   references, nearby documentation, and repository naming conventions.
5. Explicit user decisions in the current conversation.

Repository-specific paths such as a page-level `index.md`, API directory, or
model directory may be evidence when present, but none is mandatory. Generated
files may be read as contracts but must not be hand-edited.

Do not infer requirements from naming alone or invent missing behavior.

### 4. Build a behavioral drift list

Compare implementation with each editable file according to that file's purpose,
and compare related repository docs even when they are unchanged in Git.

- **Simple drift:** factual wording, task checkbox, field or option alignment,
  one scenario, one permission, or a small documentation correction with
  unambiguous evidence.
- **Complex drift:** added or removed requirement, scope change, architecture
  reversal, cross-capability impact, compatibility or migration policy change,
  or conflicting evidence.

Group drift by target file and record: documented intent → code reality →
proposed edit.

On the spec path, a new capability, a deleted capability, or a main-spec file
that does not yet exist is not spec-fallback work: stop and suggest proposing a
change.

### 5. Apply the confirmation policy

After the target is uniquely selected (or the user has chosen it):

- If all drift is simple, briefly state the intended updates and apply them.
- If any drift is complex, stop before applying those items and ask the user to
  approve all, a subset, or none.
- In a mixed set, simple items that depend on a complex item must remain pending
  with it. Apply only simple items that are demonstrably independent.

On the change path, a simple item must not make change artifacts or
`actionContext` docs inconsistent while complex items await a decision. On the
spec path, related repository docs are not part of the edit set; their drift
must not block applying independent spec edits.

### 6. Update surgically

**Change target**

- Modify only concrete artifact files listed in
  `artifactPaths.<id>.existingOutputPaths` and directly related repository
  documentation allowed by `actionContext`.
- Preserve each schema's existing structure and terminology.
- Keep unrelated requirements and prose unchanged.
- Mark work complete only when implementation or verification evidence exists.
- Update scope-level artifacts only when scope actually changed.
- Keep `actionContext` docs consistent with the resulting change artifacts.
- Do not update main specs on the change path.

**Spec target**

- Modify only the one selected existing main spec file, or the existing files
  the user explicitly named.
- Preserve main-spec structure (`Purpose`, `Requirements`, scenarios). Do not
  rewrite the file as a change delta (`ADDED` / `MODIFIED` / `REMOVED` /
  `RENAMED` headers).
- Keep unrelated requirements and prose unchanged.
- Do not implement features, refactor business logic, create a change, or
  archive.
- Do not update related repository docs unless the user explicitly asked.
  Record stale related docs under `Unchanged` or `Pending`; they do not block
  claiming the spec sync is complete.

Do not implement features or refactor business logic on either path. Do not
write incorrect implementation into a change or a spec; fix the code instead.

### 7. Validate and report

**Change target**

```bash
openspec validate "<name>" --type change --strict --json
```

**Spec target**

```bash
openspec validate "<id>" --type spec --strict --json
```

Validate every selected spec id. Include `--store <id>` when applicable. Fix
validation issues introduced by the edits and rerun until clean. If validation
cannot run or pre-existing failures remain, report them without claiming full
success.

Summarize:

```text
OpenSpec synced from code: <change-name or spec <id>>
Evidence: <key implementation and documentation paths>
Updated: <artifact, spec, or related-doc changes>
Unchanged: <checked files with no drift>
Pending: <user choice, complex drift, ambiguity, or validation blockers>
Next: <change path: optionally use openspec-sync-specs or openspec-archive-change; spec path: no sync or archive>
```

## Guardrails

- On the change path, stay within `changeRoot`, concrete
  `artifactPaths.<id>.existingOutputPaths`, and `actionContext`. Never write to
  main specs. Never leave an `actionContext` document stale while claiming
  synchronization is complete.
- On the spec path, stay within the selected existing
  `<root.path>/openspec/specs/<id>/spec.md` files. Never create, rename, or
  delete a spec or capability. Related docs are evidence only unless the user
  asked to update them.
- Prefer idempotent edits that produce no wording churn when rerun.
- Keep the language and style of each existing artifact or spec.
