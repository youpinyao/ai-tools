---
name: /opsx-propose
id: opsx-propose
category: Workflow
description: Propose a new change - create it and generate all artifacts in one step
---

Propose a new change - create the change and generate all artifacts in one step.

**Planning boundary**: This workflow creates planning artifacts only. The user request that selected or triggered this workflow authorizes planning only, even if it asks to build or fix something. Do not edit project code. After the planning artifacts are complete, stop. Do not start implementation in the same response, even if the initial request asks for it. Wait for a new user request after the artifacts are presented; then start the apply workflow.

I'll create every artifact required by the selected schema. For `evidence-driven` this includes:
- proposal.md (what and why)
- `specs/<capability-path>/spec.md` (what the system should do) — unless `skip_specs: true`
- design.md (how)
- tasks.md (implementation checklist)
- verification.md (verification plan; results remain pending until implementation)

`<capability-path>` is the spec directory relative to `specs/` (for example, `user-auth` or `identity/user-auth`). Preserve an existing capability's full path and follow the project's established organization for new capabilities.

When the user is ready to implement, they must start the apply workflow explicitly.

---

**Store selection:** If the user names a store (a store is a standalone OpenSpec repo registered on this machine) or the work lives in one, run `openspec store list --json` to discover registered store ids, then pass `--store <id>` on the commands that read or write specs and changes (`new change`, `status`, `instructions`, `list`, `show`, `validate`, `archive`, `doctor`, `context`, `view`). Once selected, treat `--store <id>` as sticky for the rest of the workflow. Every unscoped example of those commands below is shorthand: before running it, append the flag. For example, run `openspec status --change "<name>" --json --store "<id>"`, not the unscoped form shown below. Other commands do not take the flag. Hints printed by commands already carry the flag; keep it on follow-ups. Without a store, commands act on the nearest local `openspec/` root.

**Input**: The argument after `/opsx:propose` is the change name (kebab-case), OR a description of what the user wants to build.

---

## Superpowers 对接：brainstorming 前门 + writing-plans（薄适配）

一键 propose 在撰写创意性制品（`proposal` / `design` / `specs`）以及生成完整任务清单之前，MUST 走下方**写死的 Spec 核心节奏**。生成或大幅修订 `tasks.md` 时 MUST 对齐下方 **writing-plans 粒度原则**。本仓库制品与本节裁剪为权威；**不要**把上游 `brainstorming` / `writing-plans` 的 checklist 全文或终态当作门禁。

### 批准门触发点（写 proposal/design/specs 前）

| 情形 | 是否触发前门 |
|------|----------------|
| 模糊想法 / 尚未就方案达成批准的 `/opsx:propose`（或等价） | **触发完整节奏**——创建或填写 proposal/design/specs 之前完成方案对比与设计批准 |
| 用户已在同一会话明确选定方案包（如「都要」「全部按既定清单落地」） | **触发快捷路径**——复述范围确认后可写制品 |
| 用户反对复述范围或撤回批准 | **停止写入**——回到澄清，不得继续生成 proposal/design/specs/tasks |

### 结晶前核心节奏（本阶段唯一权威）

仅取 Spec 核心节奏，按序执行（小变更可缩短篇幅，**不可为零**）：

1. 理解上下文（可结合代码库与既有 OpenSpec 制品）
2. 澄清意图
3. 提出至少两个可行方案并给出推荐
4. 呈现设计要点并获得用户批准
5. **再**创建/填写 `proposal` / `design` / `specs`，并继续生成 tasks 等其余制品

**禁止**：在未获批准（或未完成快捷复述确认）时直接生成完整设计与任务清单。

### 已选定方案的快捷路径

若用户已在同一会话明确选定方案：

- MAY 将既有探索结论视为已批准设计摘要
- MUST 在开始写 proposal/design/specs（及一键生成全套制品）前用简短确认**复述将落地的范围/环节清单**，供用户确认或修正
- 用户反对时 MUST 停止写制品并回到澄清

### 生成 tasks 时对齐 writing-plans（本节写死原则为权威）

生成或大幅修订 `tasks.md` 时，MUST 遵循以下粒度原则（映射自 Spec / writing-plans，已写死于此）：

- **文件地图**：先给出将触及的文件/模块地图（可写入 `design.md` 或 `tasks.md` 序言；模板含「文件 / 模块地图」时须填写）
- **可测交付**：每项任务对应可独立验证的交付物；行为变更类任务 MUST 写明如何验证（测试命令或等价检查）
- **可独立审查**：粒度适合「单个 implementer 子 Agent 一次派发 + 任务级审查可拒绝邻项而批准本项」
- **禁止**仅用含糊的「实现某某模块」作为唯一描述

**不以**强制落盘 `docs/superpowers/plans/` 为门禁；tasks 写入 OpenSpec change 即可。

### 本仓库裁剪（写死；相对上游 brainstorming / writing-plans）

- **真源**：设计/规范/任务写入 `openspec/changes/<name>/`；**本仓库 OpenSpec change 制品为本阶段真源**
- **不适用的上游终态**：对本 propose 阶段，上游 `docs/superpowers/` 落盘、auto-commit、以及「必须另写 Superpowers plans 文档」**均不适用**——不得因上游 checklist 要求这些步骤而阻塞或改写本阶段流程
- **不强制**另写 `docs/superpowers/specs/` 或 `docs/superpowers/plans/`（可提及，非门禁）
- **不自动 commit**（未获用户明确要求时不要 commit）
- **Read 上游的用途**：MAY Read `brainstorming` / `writing-plans`，**仅作**话术、方案对比或任务拆分写法参考；**不以**其 checklist 全文或终态为权威；冲突时以本节与 OpenSpec 制品为准

---

**Steps**

1. **Understand the request and clarify material ambiguity**

   If no clear input is provided, use the **AskUserQuestion tool** (open-ended, no preset options) to ask:
   > "What change do you want to work on? Describe what you want to build or fix."

   From their description, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

   **IMPORTANT**: Do NOT proceed without understanding what the user wants to build.

   If the request contains ambiguity that would materially affect scope, externally observable behavior, compatibility, or acceptance criteria, ask the user before creating the change. For minor details, make a reasonable assumption and record it in the planning artifacts.

2. **批准门（写 proposal/design/specs 前）**

   在创建或填写 `proposal` / `design` / `specs`（以及一键生成完整设计与任务清单）之前，完成上方 Superpowers 批准门：

   - **模糊想法**：走完整节奏（≥2 方案 + 推荐 + 设计要点批准）
   - **已选定方案**：复述将落地的范围/环节清单，待用户确认或修正
   - 用户未批准或反对时：**停止**，不要进入步骤 3 之后的制品填写（可保留对话澄清；不要生成完整 proposal/design/specs/tasks）

3. **Determine the workflow schema**

   Use the configured default schema unless the user explicitly requests a different workflow.

   **Use a different schema only if the user:**
   - Explicitly requests a specific schema by name → use `--schema <schema-name>`
   - Asks to "show workflows" or asks "what workflows" exist → resolve the authoritative root by running `openspec context --json` from the current working directory. If the user explicitly selected a registered store, use `openspec context --json --store "<store-id>"`. Then run `openspec schemas --json` with its working directory set to the returned `root.path` and let them choose. This preserves roots selected by a local `store:` pointer or the global `defaultStore`; `schemas` does not accept `--store`. If context reports only `no_openspec_root`, run `openspec schemas --json` from the current working directory instead. Do not use this fallback for invalid or unavailable stores.

   Otherwise, omit `--schema` to preserve the configured default (本仓库默认 `evidence-driven`).

4. **Create the change directory**

   Choose one schema form below. If a registered store is selected, append `--store "<store-id>"` to that command and each later OpenSpec command shown below that accepts `--store`.

   Using the configured default:
   ```bash
   openspec new change "<name>"
   ```

   Using an explicitly requested schema:
   ```bash
   openspec new change "<name>" --schema "<schema-name>"
   ```
   This creates a scaffolded change in the planning home resolved by the CLI with `.openspec.yaml`.

   **`skip_specs` (OpenSpec 1.7+):** 若纯重构 / 工具链 / 文档等、无规范层行为变化，在创建 change 后立刻编辑其 `.openspec.yaml`，加入 `skip_specs: true`（保留已有 `schema:`）。不要捏造 capability 或空 specs 来应付校验。有需求变化时不要设置该标记。

   **`retire_capabilities` (OpenSpec 1.8+):** 若本变更会移除某能力的最后一条需求并删除其 main spec，在 `.openspec.yaml` 加入 `retire_capabilities: true`。未声明该标记时，sync/archive 不得删除空能力的 `spec.md`。

5. **Get the artifact build order**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse the JSON to get:
   - `applyRequires`: array of artifact IDs needed before implementation (e.g., `["verification"]`)
   - `artifacts`: list of all artifacts, each with its `status` and its `requires` edges
   - `planningHome`, `changeRoot`, `artifactPaths`, and `actionContext`: path and scope context. Use these instead of assuming repo-local paths.

6. **Create every artifact in the required set**

   Use the **TodoWrite tool** to track progress through the artifacts.

   Loop through artifacts in dependency order (artifacts with no pending dependencies first):

   a. **For each artifact that is `ready` (dependencies satisfied)**:
      - Get instructions:
        ```bash
        openspec instructions <artifact-id> --change "<name>" --json
        ```
      - The instructions JSON includes:
        - `context`: Project background (constraints for you - do NOT include in output)
        - `rules`: Artifact-specific rules (constraints for you - do NOT include in output)
        - `template`: The structure to use for your output file
        - `instruction`: Schema-specific guidance for this artifact type
        - `skipped`/`warning`: present when the change declares skip_specs and this artifact must NOT be created - stop and pick another artifact
        - `resolvedOutputPath`: Resolved path or pattern to write the artifact
        - `dependencies`: Completed artifacts to read for context
      - Read any completed dependency files for context - always re-read them from disk, even if you saw them earlier in the conversation (the user may have edited them)
      - Create the artifact file using `template` as the structure and write it to `resolvedOutputPath`. If `resolvedOutputPath` is a glob, follow `instruction` to choose the concrete file path
      - Apply `context` and `rules` as constraints - but do NOT copy them into the file
      - **`tasks` 制品**：按上方 writing-plans 粒度原则填写（文件地图、可测交付、可独立审查）；遵循 schema `instruction` 与模板结构
      - Show brief progress: "Created <artifact-id>"

   b. **Continue until every artifact in the required set exists**
      - After creating each artifact, re-run `openspec status --change "<name>" --json`
      - The required set is `applyRequires` plus every artifact reachable from those by following the `requires` edges in `status --json` - walk them transitively. Leave artifacts outside that set alone
      - `status` is file-existence only, so an `applyRequires` artifact reading `done` does NOT mean its dependencies exist - use each artifact's `requires` edges to build the required set
      - An artifact already reading `status: "skipped"` is satisfied: the change declares `skip_specs` in `.openspec.yaml`, so its files must NOT exist. Never try to create one
      - Create every artifact in the required set that is missing, then re-check - creating one can unblock others
      - Skip one only when `status` already reports it `skipped`, or when its own `instruction` says it is conditional (e.g. "create only if..."). `specs` qualifies only via the `skipped` status, never by your own judgment. Tell the user, and do not reconsider it
      - Dependencies are enablers, not gates: if a required artifact is still `blocked` only because you skipped a conditional dependency, write it anyway
      - Stop when every artifact in the required set is `done`, `skipped`, or was deliberately skipped as conditional

   c. **If an artifact requires user input** (unclear context):
      - Use **AskUserQuestion tool** to clarify
      - Then continue with creation

7. **Show final status**
   ```bash
   openspec status --change "<name>"
   ```

**Output**

After completing all artifacts, summarize:
- Change name and location
- List of artifacts created with brief descriptions, plus any skipped via `skip_specs` or conditional rules
- What's ready: "All artifacts needed for implementation are ready."
- Prompt: "The artifacts are ready for review. When you are ready, run `/opsx:apply` or ask me to apply this change."
- 提醒：OpenSpec change 制品为真源；未要求则不自动 commit；未强制写入 `docs/superpowers/`

**Artifact Creation Guidelines**

- Follow the `instruction` field from `openspec instructions` for each artifact type
- The schema defines what each artifact should contain - follow it
- Read dependency artifacts for context before creating new ones - re-read from disk
- Use `template` as the structure for your output file - fill in its sections
- **IMPORTANT**: `context` and `rules` are constraints for YOU, not content for the file
  - Do NOT copy `<context>`, `<rules>`, `<project_context>` blocks into the artifact
  - These guide what you write, but should never appear in the output
- **`tasks.md`**：对齐本节 writing-plans 原则（文件地图、可测交付、可独立审查）；不以 `docs/superpowers/plans/` 为门禁

**Guardrails**
- The request that invoked this workflow authorizes planning only. Any implementation or apply instruction in that request does not carry forward. Do NOT implement the change, start the apply workflow, or edit project code during this workflow. After presenting the artifacts, stop and wait for a new user request to start the apply workflow
- **Don't skip brainstorming gate** - 写 proposal/design/specs 前走批准门；已选定方案时 MUST 复述确认；用户反对则停止写入
- **Don't auto-commit / don't force docs/superpowers** - OpenSpec 制品为真源；未要求不 commit；不强制 `docs/superpowers/`
- Create every artifact the apply phase transitively depends on, not just the ids listed in `apply.requires`
- Always read dependency artifacts before creating a new one - re-read from disk, not from conversation memory
- Never create specs (or any artifact) that status reports as `skipped`
- Ask about ambiguities that would materially change scope, externally observable behavior, compatibility, or acceptance criteria; for minor details, make reasonable assumptions and record them（批准门本身不可跳过）
- If a change with that name already exists, ask if user wants to continue it or create a new one
- Verify each artifact file exists after writing before proceeding to next
