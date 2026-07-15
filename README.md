# ai-tools

OpenSpec workflow skills for AI coding agents — including **syncing active OpenSpec changes from implemented code**.

## Install (skills.sh)

```bash
npx skills add youpinyao/ai-tools
```

Install only this skill:

```bash
npx skills add youpinyao/ai-tools --skill openspec-update-change-from-code
```

Browse: [skills.sh/youpinyao/ai-tools/openspec-update-change-from-code](https://skills.sh/youpinyao/ai-tools/openspec-update-change-from-code)

## About

This package provides an agent skill that helps when implementation code has drifted from an
active OpenSpec change. **Code and explicit user decisions are the source of truth**; the skill
updates change artifacts and related repository docs accordingly.

It is the reverse of `openspec-apply-change`, and is distinct from `openspec-sync-specs`
(which updates main specs).

## Prerequisites

- An AI coding agent that supports [Agent Skills](https://agentskills.io)
- [OpenSpec CLI](https://github.com/Fission-AI/OpenSpec) (`openspec` on your `PATH`)

## Skill: `openspec-update-change-from-code`

| | |
|---|---|
| Path | `skills/openspec-update-change-from-code/SKILL.md` |
| When to use | Code drifted from an active change; need to 从代码回写 OpenSpec; `/opsx-update-change-from-code` |

**Does:**

- Select an active change (by name or evidence)
- Diff implementation against change artifacts
- Apply simple drift updates; ask before complex scope changes
- Validate with `openspec validate --type change --strict`

**Does not:**

- Update main specs (`openspec-sync-specs`)
- Implement features or archive changes

### Workflow overview

1. Select change  
2. Resolve schema / edit boundaries via `openspec status --change "<name>" --json`  
3. Gather implementation evidence (git, code, tests, related docs)  
4. Build a simple vs complex drift list  
5. Confirm complex items with the user  
6. Update only allowed artifacts surgically  
7. Validate and report

## Cursor extras

This repo also keeps Cursor-specific helpers:

| Type | Path |
|------|------|
| Cursor skill mirror | `.cursor/skills/openspec-update-change-from-code/SKILL.md` |
| Cursor command | `.cursor/commands/opsx-update-change-from-code.md` |

Clone into a project root if you want the Cursor command as well as the skill:

```bash
git clone https://github.com/youpinyao/ai-tools.git
```

## License

[MIT](./LICENSE)
