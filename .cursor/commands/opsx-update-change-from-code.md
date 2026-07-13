---
name: /opsx-update-change-from-code
id: opsx-update-change-from-code
category: Workflow
description: Sync an OpenSpec change and related repository docs from implemented code
---

Sync an active OpenSpec change and its related repository documentation from implemented code.

Follow the project skill **openspec-update-change-from-code** exactly:
`.cursor/skills/openspec-update-change-from-code/SKILL.md`.

**Input:** An optional change name, for example:

```text
/opsx-update-change-from-code add-auth
```

If omitted, infer the change only when repository evidence is unambiguous; otherwise prompt the
user to select an active change. The Skill owns store handling, evidence discovery, confirmation,
editing boundaries, validation, and reporting.
