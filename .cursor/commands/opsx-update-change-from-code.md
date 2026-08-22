---
name: /opsx-update-change-from-code
id: opsx-update-change-from-code
category: Workflow
description: Sync an OpenSpec change or matching main spec from implemented code
---

Sync OpenSpec artifacts from implemented code. Prefer an active change; if none
exists and exactly one matching main spec already exists, write that spec.
Ambiguous targets (archived change, change vs spec, multiple specs) must be
chosen by the user.

Follow the project skill **openspec-update-change-from-code** exactly:
`.cursor/skills/openspec-update-change-from-code/SKILL.md`.

**Input:** An optional change name or spec id, for example:

```text
/opsx-update-change-from-code add-auth      # change name
/opsx-update-change-from-code user-auth     # spec id
```

If omitted, infer an active change first, then exactly one existing main spec,
only when repository evidence is unambiguous; otherwise prompt the user to
select. The Skill owns store handling, evidence discovery, confirmation,
editing boundaries, validation, and reporting.
