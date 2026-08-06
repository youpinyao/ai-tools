---
name: openspec-sync-specs
description: Sync delta specs from a change to main specs. Use when the user wants to update main specs with changes from a delta spec, without archiving the change.
allowed-tools: Bash(openspec:*)
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.8.0"
---

Sync delta specs from a change to main specs.

This is an **agent-driven** operation - you will read delta specs and directly edit main specs to apply the changes. This allows intelligent merging (e.g., adding a scenario without copying the entire requirement).

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`, `view`). Once selected, treat `--store <id>` as sticky for the rest of the workflow. Every unscoped example of those commands below is shorthand: before running it, append the flag. For example, run `openspec status --change "<name>" --json --store "<id>"`, not the unscoped form shown below. Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

`<capability-path>` is the spec directory relative to `specs/` (for example, `user-auth` or `identity/user-auth`). Preserve the full path from each delta spec when resolving its main spec.

**Input**: Optionally specify a change name. If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **If no change name provided, prompt for selection**

   Run `openspec list --json` to get available changes. Use the **AskUserQuestion tool** to let the user select.

   Show changes that have delta specs (under `specs/` directory).

   **IMPORTANT**: Do NOT guess or auto-select a change. Always let the user choose.

2. **Resolve change context**

   Run:
   ```bash
   openspec status --change "<name>" --json
   ```

3. **Find delta specs**

   Use `artifactPaths.specs.existingOutputPaths` from the status JSON as the list of delta spec files.

   Each delta spec file contains sections like:
   - `## ADDED Requirements` - New requirements to add
   - `## MODIFIED Requirements` - Changes to existing requirements
   - `## REMOVED Requirements` - Requirements to remove
   - `## RENAMED Requirements` - Requirements to rename (FROM:/TO: format)

   If no delta specs found, inform user and stop.

4. **For each delta spec, apply changes to main specs**

   For each repo-local capability delta spec path returned by the CLI:

   a. **Read the delta spec** to understand the intended changes

   b. **Read the main spec** at `openspec/specs/<capability-path>/spec.md` (may not exist yet)

   c. **Apply changes intelligently**:

      **ADDED Requirements:**
      - If requirement doesn't exist in main spec → add it
      - If requirement already exists → update it to match (treat as implicit MODIFIED)

      **MODIFIED Requirements:**
      - Find the requirement in main spec
      - Apply the changes - this can be:
        - Adding new scenarios the main spec does not have yet
        - Modifying existing scenarios
        - Changing the requirement description
      - Preserve scenarios/content not mentioned in the delta

      **REMOVED Requirements:**
      - Remove the entire requirement block from main spec
      - Retiring the capability. Delete the whole `spec.md` - and the directory once
        nothing else is left in it - only when ALL of these hold:
        1. removing the requirements *this run* left no requirement blocks;
        2. the rest of the spec is well-formed (it still has a `## Purpose`);
        3. the main spec was not already empty before this sync - if you removed
           nothing, change nothing;
        4. every other nonblank line in the whole file is accounted for as the
           title, Purpose, Requirements header, or a canonical requirement's
           statement, scenarios, or fenced examples;
        5. the change's `.openspec.yaml` declares `retire_capabilities: true`;
        6. the `spec.md` resolves inside the real specs root (do not follow a
           capability-directory symlink to delete an external file).
        If removing the selected requirements would leave no requirement blocks and
        any retirement condition is not satisfied, do not modify the main spec. Stop
        the sync for that capability, report the blocking condition, and tell the user
        how to resolve it. Never write or leave an empty `## Requirements` section.
        When only the marker is missing, say that too - it is the one thing the user
        can add to make the retirement go through.
      - Deleting the file also deletes its `## Purpose`; any other section blocks
        retirement. Name Purpose when you report the retirement. Include a pasteable
        `git checkout` only when the spec lived in the caller's checkout;
        otherwise give checkout-scoped recovery guidance.

      **RENAMED Requirements:**
      - Find the FROM requirement, rename to TO

   d. **Create new main spec** if capability doesn't exist yet:
      - Create `<planningHome.root>/openspec/specs/<capability-path>/spec.md`
      - Add Purpose section: copy the delta's `## Purpose` body verbatim when it has one
        (this is what `openspec archive` does); only write a brief TBD placeholder when it does not
      - Add Requirements section with the ADDED requirements

5. **Validate updated main specs**

   Run `openspec validate --specs` with the same selected-root flags used earlier.
   If validation fails, report the problems and do not claim the sync succeeded.

6. **Show summary**

   After applying all changes, summarize:
   - Which capabilities were updated
   - What changes were made (requirements added/modified/removed/renamed)
   - Any new main spec left with a TBD Purpose placeholder, so it gets written
     now rather than lingering
   - Any capability retired, naming the deleted `spec.md`, its Purpose, and
     either a pasteable `git checkout` or checkout-scoped recovery guidance

**Delta Spec Format Reference**

```markdown
## ADDED Requirements

### Requirement: New Feature
The system SHALL do something new.

#### Scenario: Basic case
- **WHEN** user does X
- **THEN** system does Y

## MODIFIED Requirements

### Requirement: Existing Feature
The system SHALL keep doing the existing thing, now also handling A.

#### Scenario: Scenario the main spec already has
- **WHEN** user does X
- **THEN** system does Y

#### Scenario: New scenario to add
- **WHEN** user does A
- **THEN** system does B

## REMOVED Requirements

### Requirement: Deprecated Feature

## RENAMED Requirements

- FROM: `### Requirement: Old Name`
- TO: `### Requirement: New Name`
```

**Key Principle: Intelligent Merging**

Unlike programmatic merging, you can apply **partial updates**:
- To add a scenario, just include that scenario under MODIFIED - don't copy existing scenarios
- The delta represents *intent*, not a wholesale replacement
- Use your judgment to merge changes sensibly

**Output On Success**

```
## Specs Synced: <change-name>

Updated main specs:

**<capability-1>**:
- Added requirement: "New Feature"
- Modified requirement: "Existing Feature" (added 1 scenario)

**<capability-2>**:
- Created new spec file
- Added requirement: "Another Feature"

Main specs are now updated. The change remains active - archive when implementation is complete.
```

**Guardrails**
- Read both delta and main specs before making changes
- Preserve existing content not mentioned in delta
- Never delete a main spec unless `retire_capabilities: true` and all retirement conditions hold
- If something is unclear, ask for clarification
- Show what you're changing as you go
- The operation should be idempotent - running twice should give same result
- Do not claim success if `openspec validate --specs` fails
