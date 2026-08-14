---
title: OpenSpec 官方优先工作流重构规格（官方 skills/commands 外置 + evidence-driven schema-only）
version: 2.1
date_created: 2026-08-14
last_updated: 2026-08-14
owner: ai-tools
tags:
  - architecture
  - openspec
  - official-first
  - schema
---

# 1. 背景

本仓库原先跟踪并定制 OpenSpec 为 Cursor 生成的 skills 与 commands。该模式会复制上游模板，并在 OpenSpec 升级后产生语义漂移。

本次重构改为“官方能力外置、自定义 schema 内聚”：

1. 官方已有的 Cursor skills/commands 完全由目标项目执行 `openspec init --tools cursor` 或官方更新流程获得。
2. `ai-tools` 不再生成、复制、翻译或定制这些官方文件，也不将其纳入版本控制。
3. 本仓库只维护 OpenSpec CLI 本身不能替代的 `evidence-driven` 自定义 schema。
4. `evidence-driven` 以重构时最新官方 `spec-driven` schema 为语义基线，增加 `verification` 制品，并令 apply 依赖该制品。

截至 2026-08-14，本机安装版本与 npm 最新版本均为 OpenSpec **1.9.0**。本规格以 1.9.0 为本次实现基线；后续重构必须重新查询最新版，不得永久假定 1.9.0。

# 2. 目标与非目标

## 2.1 目标

- 官方 Cursor skills/commands 零本地分叉。
- 删除仓库中原有官方模板副本，避免再次误提交。
- 从最新官方 `spec-driven` 重新构建 `evidence-driven`，而不是继续修补旧模板。
- 保留“先规划验证、再进入 apply”的制品依赖。
- 将代码审查定为 verification 必做检查，但不把它做成官方 archive 条件。
- 保留 OpenSpec 1.9.0 的 `skip_specs`、嵌套 `<capability-path>`、新增能力 `## Purpose` 与完整 MODIFIED requirement 语义。
- OpenSpec 自定义 schema、模板、规格和工作流文档使用简体中文。
- 提供可重复执行的基线核对和 schema 校验方法。

## 2.2 非目标

- 不修改 OpenSpec CLI 安装包源码。
- 不在本仓库重新实现官方 explore/propose/update/apply/verify/archive/sync。
- 不通过 Cursor rule 或 wrapper skill 扩展官方流程。
- 不保证独立 Agent verify、Code Review 归档硬门禁、自动派发 verify 或 finishing 菜单。
- 不修改 `.cursor/rules/openspec-chinese.mdc` 的策略。
- 不删除或重构本地旁路 `openspec-update-change-from-code`。
- 不修改 Graphify 接入设计。
- 不自动创建 git commit。

# 3. 架构

## 3.1 分层

```text
目标项目
├── OpenSpec 官方生成层
│   └── openspec init --tools cursor
│       ├── 官方 .cursor/skills/openspec-*
│       └── 官方 .cursor/commands/opsx-*
│
└── ai-tools 自定义层
    ├── openspec/config.yaml
    ├── openspec/schemas/evidence-driven/
    │   ├── schema.yaml
    │   └── templates/
    ├── .cursor/rules/openspec-chinese.mdc
    └── openspec-update-change-from-code（独立旁路）
```

两层不得通过覆盖同一路径进行合并。官方层归 OpenSpec CLI 管理；自定义层只提供项目 schema 与明确列出的非官方旁路。

## 3.2 官方文件所有权

以下路径属于官方生成物，本仓库 MUST NOT 跟踪：

- `.cursor/skills/openspec-explore/`
- `.cursor/skills/openspec-propose/`
- `.cursor/skills/openspec-update-change/`
- `.cursor/skills/openspec-apply-change/`
- `.cursor/skills/openspec-verify-change/`
- `.cursor/skills/openspec-archive-change/`
- `.cursor/skills/openspec-sync-specs/`
- `.cursor/commands/opsx-explore.md`
- `.cursor/commands/opsx-propose.md`
- `.cursor/commands/opsx-update.md`
- `.cursor/commands/opsx-apply.md`
- `.cursor/commands/opsx-verify.md`
- `.cursor/commands/opsx-archive.md`
- `.cursor/commands/opsx-sync.md`

仓库 SHOULD 使用精确 `.gitignore` 条目忽略这些路径。忽略规则不得覆盖：

- `.cursor/skills/openspec-update-change-from-code/`
- `.cursor/commands/opsx-update-change-from-code.md`

## 3.3 最新官方基线解析

重建或升级 schema 前 MUST：

1. 执行 `npm view @fission-ai/openspec version` 获取 npm 最新稳定版本。
2. 执行 `openspec --version` 获取当前 CLI 版本。
3. 若版本不同，先由维护者升级 CLI；不得混用不同版本的模板与行为说明。
4. 执行 `openspec schema which spec-driven` 获取官方 schema 的实际路径。
5. 从该路径读取 `schema.yaml` 和 `templates/`，作为唯一官方基线。

不得以本仓库旧副本、聊天记忆或手工保存的历史快照代替上述基线。

# 4. `evidence-driven` schema 契约

## 4.1 制品图

```text
proposal
  ├─→ specs ─┐
  └─→ design ─┴─→ tasks → verification

apply.requires = [verification]
apply.tracks   = tasks.md
```

`schema.yaml` MUST 满足：

- `name: evidence-driven`
- `artifacts` 至少包含 `proposal`、`specs`、`design`、`tasks`、`verification`
- `verification.generates: verification.md`
- `verification.requires: [tasks]`
- `apply.requires: [verification]`
- `apply.tracks: tasks.md`

## 4.2 官方语义继承

`proposal`、`specs`、`design`、`tasks` 的 instruction 与模板 MUST 从第 3.3 节解析出的官方 `spec-driven` 基线重新建立。

允许的差异只有：

1. 将面向使用者的正文翻译为简体中文。
2. 将 schema 名称和描述改为 `evidence-driven`。
3. 新增 `verification` 制品。
4. 将 `apply.requires` 从 `[tasks]` 改为 `[verification]`。
5. 在 apply instruction 中增加“执行 `verification.md` 中适用检查并记录真实结果”的 schema-only 要求。
6. 将代码审查定为 verification 必做检查（规划写入模板、apply 时实际阅读实现 diff 并记录结论），不构成官方 archive 裁决。

不得加入或恢复以下旧定制：

- brainstorming 或 writing-plans 门禁；
- Superpowers skill 调度；
- 独立 Agent verify；
- Task 子 Agent 自动派发；
- Code Review 归档硬门禁；
- finishing 菜单；
- 对官方 archive/verify 行为的本地覆盖。

## 4.3 兼容语义

重建后的 instruction MUST 保留官方基线中的以下能力：

- 无规范层行为变化时使用 `.openspec.yaml` 的 `skip_specs: true`，不得捏造空 capability。
- capability 使用完整 `<capability-path>`，支持嵌套目录。
- 新增 capability 的 delta spec 以 `## Purpose` 开头。
- 修改已有 capability 时不得添加会被忽略的 delta `## Purpose`。
- MODIFIED requirement 必须复制并修改完整 requirement 块及其全部 scenarios。
- design 中会影响规格、方案或任务拆分的问题必须在生成 tasks 前解决。
- tasks 必须使用 `- [ ]` 复选框格式，并按依赖顺序组织。

若未来官方基线新增或修改这些语义，本地中文版本 MUST 随基线更新，不得以本清单限制上游新增能力。

## 4.4 `verification` 制品

`verification.md` 用于规划和记录验证，不承担独立归档裁决。

模板 MUST 包含：

- 验证范围；
- 需求与验证对应关系；
- 自动化验证；
- 人工验证；
- 非功能验证；
- 代码审查（必做检查：范围、标准、发现项、结论）；
- 实际执行结果；
- 未执行项与剩余风险；
- 发布后验证与回滚。

规划阶段：

- 检查状态使用 `待执行`。
- 命令必须来自仓库中已确认的真实脚本或工具配置。
- 未确认命令时应说明确认方式，不得伪造可执行命令。
- 不得填写未经实际执行的成功结果。

执行阶段：

- 仅在本回合实际执行命令并阅读输出后记录 `通过`。
- 失败项记录 `失败` 与简洁原因。
- 不适用项记录 `不适用` 与具体原因。
- 未执行项不得伪装为通过，必须进入剩余风险。

代码审查 MUST：

- 作为 verification 必做检查出现在模板中，并纳入需求对应关系与实际执行结果。
- 规划阶段保持「待执行」，不得预填通过。
- apply 时实际阅读本次变更的实现 diff 后再改状态。
- 存在未处理的 Critical 或 Important 时记「失败」，并进入剩余风险。
- Minor 可记后续项，不单独导致失败。
- 仅当工作区相对本变更无实现 diff（纯规划、尚未编码）时可记「不适用」，并写明原因；文档、schema 与配置变更仍须审查。
- 由当前 apply 会话执行；不得绑定独立 reviewer、自动派发或官方 archive 条件。

模板 MUST NOT 包含：

- `## 代码审查（归档硬门禁）`
- `## 独立验证结论`
- `/opsx-verify` 自动派发说明
- Finishing 状态

## 4.5 apply instruction

apply instruction MUST：

- 沿用官方“读取上下文、逐项完成待办、完成即勾选、阻塞时暂停”的语义；
- 要求执行 `verification.md` 中适用检查，包括必做的代码审查；
- 要求记录真实命令、结果、失败原因与剩余风险；
- 要求代码审查实际阅读实现 diff；未处理的 Critical 或 Important 不得记为通过。

apply instruction MUST NOT：

- 声称会自动启动独立 verify；
- 声称 archive 会检查独立验证结论或 Code Review；
- 调用或依赖 Superpowers；
- 承诺 schema 无法强制执行的归档硬门禁。

# 5. 工作流

## 5.1 安装与初始化

目标项目使用本工具包时：

1. 安装或升级至 npm 最新稳定版 OpenSpec。
2. 在目标项目运行 `openspec init --tools cursor`，生成官方 Cursor skills/commands。
3. 复制或安装本仓库的 `openspec/config.yaml` 与 `openspec/schemas/evidence-driven/`。
4. 按需安装中文规则和 `openspec-update-change-from-code` 旁路。
5. 运行 `openspec schema validate evidence-driven`。

本仓库不得提供脚本代替第 2 步生成官方文件。

## 5.2 主线

```text
官方 explore（可选）
  → 官方 propose
  → evidence-driven artifacts（含 verification 计划）
  → 官方 apply（按 schema instruction 记录验证结果）
  → 官方 verify（如使用）
  → 官方 archive
```

verify 与 archive 的具体行为以当前 OpenSpec 官方生成物为准。本仓库文档不得继续描述已删除的本地硬门禁。

## 5.3 更新

- 官方 skills/commands：由目标项目使用 OpenSpec 官方更新机制维护。
- `evidence-driven`：按第 3.3 节重新解析基线、对照差异、更新中文版本并校验。
- 不得从目标项目反向复制官方生成物回本仓库。
- 不得用旧本地文件覆盖新官方模板。

# 6. 文件变更范围

## 6.1 删除

- 第 3.2 节列出的官方生成 skills/commands。
- `openspec/schemas/evidence-driven/templates/` 中现有模板内容；随后从官方基线重新建立。

## 6.2 新建或重建

- `.gitignore` 中官方生成路径的精确忽略规则。
- `openspec/schemas/evidence-driven/schema.yaml`
- `openspec/schemas/evidence-driven/templates/proposal.md`
- `openspec/schemas/evidence-driven/templates/spec.md`
- `openspec/schemas/evidence-driven/templates/design.md`
- `openspec/schemas/evidence-driven/templates/tasks.md`
- `openspec/schemas/evidence-driven/templates/verification.md`

## 6.3 更新

- `README.md`
- `docs/ai-sdd-workflow.md`
- 本规格文件

## 6.4 保持不变

- `.cursor/rules/openspec-chinese.mdc`
- `.cursor/skills/openspec-update-change-from-code/SKILL.md`
- `.cursor/commands/opsx-update-change-from-code.md`
- `docs/graphify-integration.md`

# 7. 验收标准

- **AC-OWN-001**：Git 不再跟踪第 3.2 节列出的官方生成路径。
- **AC-OWN-002**：`.gitignore` 精确忽略官方路径，但不忽略 `openspec-update-change-from-code`。
- **AC-OWN-003**：README 明确要求使用者运行 `openspec init --tools cursor`，且不再声称仓库自带官方 skills/commands。
- **AC-BASE-001**：本次实现记录显示 `openspec --version` 与 npm 最新稳定版一致，均为 1.9.0。
- **AC-BASE-002**：proposal/spec/design/tasks 的结构与 instruction 语义覆盖官方 1.9.0 `spec-driven`，差异符合第 4.2 节白名单。
- **AC-SCH-001**：`openspec/config.yaml` 的默认 schema 为 `evidence-driven`。
- **AC-SCH-002**：`verification` 依赖 `tasks`，apply 依赖 `verification` 并跟踪 `tasks.md`。
- **AC-SCH-003**：`openspec schema validate evidence-driven` 退出码为 0。
- **AC-SCH-004**：模板与 schema instruction 使用简体中文，并保留代码标识符、路径和 CLI 名称。
- **AC-VER-001**：verification 模板包含第 4.4 节规定的九类内容，其中包括独立「代码审查」章节。
- **AC-VER-002**：verification 模板不含 `## 代码审查（归档硬门禁）`、独立验证结论、自动派发 verify 或 finishing；代码审查是 verification 必做检查，不是官方 archive 条件。
- **AC-VER-003**：schema 的 verification 与 apply instruction 要求执行代码审查，未处理 Critical/Important 不得记通过。
- **AC-DOC-001**：README 与工作流文档不再宣称本仓库定制官方 verify/archive/apply skill。
- **AC-SCOPE-001**：from-code 旁路、中文规则与 Graphify 文档未被误删。

# 8. 验证策略

## 8.1 自动检查

```bash
openspec --version
npm view @fission-ai/openspec version
openspec schema which spec-driven
openspec schema validate evidence-driven
git status --short
git ls-files '.cursor/skills/openspec-*' '.cursor/commands/opsx-*'
```

`git ls-files` 的结果只允许包含：

- `.cursor/skills/openspec-update-change-from-code/SKILL.md`
- `.cursor/commands/opsx-update-change-from-code.md`

## 8.2 静态契约检查

检查项：

1. `schema.yaml` 含 `id: verification`。
2. `verification` 的 `requires` 为 `tasks`。
3. `apply.requires` 为 `[verification]`。
4. proposal/spec/design/tasks 保留官方基线关键语义。
5. schema 与 verification 模板不含 `Superpowers`、`Task 派发`、`归档硬门禁`、`独立验证结论` 或 `Finishing`。
6. verification 模板含 `## 代码审查`，且 schema instruction 要求该检查为必做。
7. README 与工作流文档指向官方初始化流程。

## 8.3 人工核对

将官方 `spec-driven` 与 `evidence-driven` 并排核对。除中文化、新增 verification、修改 apply 前置、记录验证结果及 verification 必做代码审查外，不应存在无法解释的行为差异。

# 9. 风险与取舍

- **失去本地 verify/archive 硬门禁**：这是 schema-only 的明确取舍。缓解方式是如实删除相关承诺，并以官方行为为准。
- **官方升级导致中文版本漂移**：通过每次从 `schema which spec-driven` 解析基线并执行差异核对缓解。
- **使用者忘记初始化官方工具**：通过 README 的安装顺序和 schema 校验步骤缓解。
- **忽略规则误伤本地旁路**：使用精确路径，并以 AC-OWN-002 验证。
- **schema 实验性接口变化**：OpenSpec schema 命令仍标记为 experimental；升级时必须先校验结构与模板。

# 10. 迁移顺序

1. 确认本机 CLI 与 npm 最新稳定版一致。
2. 读取官方 `spec-driven` 基线。
3. 删除仓库内官方生成 skills/commands，并加入精确忽略规则。
4. 删除现有 `evidence-driven` 模板内容。
5. 从官方基线重建中文 proposal/spec/design/tasks。
6. 新建简化 verification 模板，并更新制品图与 apply instruction。
7. 更新 README 与工作流文档。
8. 执行第 8 节全部检查。
9. 核对 from-code 旁路、中文规则与 Graphify 文档保持存在。

# 11. 决策记录

- 选择“官方生成物不入库”，拒绝固定官方副本。
- 选择“schema-only”，拒绝 Cursor rule 与 wrapper skills/commands。
- 选择删除并从官方基线重建 schema templates，而不是继续增量修补旧模板。
- 接受 schema-only 无法维持独立 verify、Code Review 作为 archive 条件与 finishing 的能力边界。
- 选择把代码审查放在 verification 必做检查中，由 apply 会话阅读 diff 并记账，而不是恢复 archive 拦截。
- 本规格取代 1.0 中与本决策冲突的 `APP-*`、`VER-*`、`CR-*`、`ARC-*` 与 Superpowers 薄适配要求。
