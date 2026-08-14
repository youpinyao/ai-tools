# OpenSpec 场景化工作流

本文帮助使用 `evidence-driven` schema 的团队选择 OpenSpec 官方命令，并说明本仓库
增加的 schema 制品语义。官方 Cursor skills 与 `/opsx-*` commands 不由本仓库维护：
先在目标项目运行 `openspec init --tools cursor`，后续命令的具体行为以目标项目中
当前 OpenSpec 官方生成物为准。

从官方 OpenSpec 或旧版 ai-tools 接入/升级本工具包，见
[ai-tools-integration.md](./ai-tools-integration.md)。

`ai-tools` 仓库自身不得运行 `openspec init` 或 `openspec update` 生成官方文件；
这些命令只在使用本工具包的目标项目中运行。

## 初始化

```bash
# 安装 npm 最新稳定版 OpenSpec
npm install --global @fission-ai/openspec@latest

# 设置并进入目标项目
TARGET_PROJECT="/absolute/path/to/target-project"
cd "$TARGET_PROJECT"

# 新目标项目：生成官方 Cursor skills 与 commands
openspec init --tools cursor

# 将 evidence-driven schema 复制到目标项目并合并设置 schema: evidence-driven 后校验
openspec schema validate evidence-driven
```

若目标项目已经初始化，升级 OpenSpec 后应在该目标项目根目录使用官方更新路径，
而不是再次初始化或从本仓库复制官方生成物：

```bash
cd "$TARGET_PROJECT"
openspec update
openspec schema validate evidence-driven
```

安装 schema 时，只复制本仓库的 `openspec/schemas/evidence-driven/` 到目标项目的
`openspec/schemas/evidence-driven/`。对于目标项目已有的 `openspec/config.yaml`，
只合并或设置 `schema: evidence-driven`，保留其他配置，不要用本仓库的完整配置文件
覆盖它。可执行的路径变量与复制命令见项目 README。

中文规则与 `/opsx-update-change-from-code` 是按需安装的本仓库扩展；其余
`/opsx-*` 命令由 OpenSpec 生成。

## 按场景选择命令

```text
需求或方案仍需探索？
  └─ 官方 /opsx-explore

准备为新工作建立 change？
  └─ 官方 /opsx-propose

已有 change，需要调整规划？
  └─ 官方 /opsx-update

准备开始或继续实现 tasks？
  └─ 官方 /opsx-apply

代码已先于规划变化，需要按代码事实回写 active change？
  └─ 本仓库 /opsx-update-change-from-code

需要使用规格同步、实现核验或结束 change？
  ├─ 官方 /opsx-sync
  ├─ 官方 /opsx-verify
  └─ 官方 /opsx-archive
```

explore、propose、update 与 apply 也应以当前官方生成物的说明为准。尤其是 verify、
archive 与 sync，本仓库不覆盖其条件、交互或执行步骤，也不推断未来版本的行为。

常见主线可以概括为：

```text
官方 explore（可选）
  → 官方 propose
  → evidence-driven 制品（含 verification 计划）
  → 官方 apply（实现 tasks 并记录真实验证结果）
  → 官方 verify（如使用）
  → 官方 archive
```

这只是场景导航，不是额外的流程约束。实现中发现规划有误时，可按官方命令说明返回
explore 或 update，再继续 apply。

## `evidence-driven` 制品图

```text
proposal
  ├─→ specs ─┐
  └─→ design ─┴─→ tasks → verification

apply.requires = [verification]
apply.tracks   = tasks.md
```

`proposal`、`specs`、`design` 与 `tasks` 派生自 OpenSpec 1.9.0 官方
`spec-driven` 语义。相对于该基线，自定义差异严格限定为四类：

1. 将面向使用者的正文翻译为简体中文。
2. 将 schema 名称和描述改为 `evidence-driven`。
3. 新增 `verification` 制品。
4. 将 `apply.requires` 从 `[tasks]` 改为 `[verification]`，并在 apply instruction
   中增加执行适用检查、记录真实命令、结果、失败原因与剩余风险的要求。

其中 `verification` 与 apply 的记录语义如下：

- `verification.md` 在 apply 前规划验证范围、需求对应关系、自动化与人工检查、
  非功能检查、发布后验证和回滚。
- 规划阶段的检查保持“待执行”，不得预填成功结果或捏造仓库中不存在的命令。
- apply 执行其中适用的检查，并记录真实命令、步骤、通过或失败结果、不适用原因、
  未执行项和剩余风险。
- 只有实际执行并读取输出后才能记录“通过”。

schema 只定义这些制品及依赖，不扩展官方 verify、archive 或 sync 的行为。

## OpenSpec 1.9.0 规格语义

### 无 specs 的 change

纯重构、工具链或文档变更若没有规范层行为变化，应在 change 的
`.openspec.yaml` 中保留 `schema:` 并设置：

```yaml
skip_specs: true
```

不要为了生成 specs 而捏造空 capability。

### capability 路径与 Purpose

- delta spec 位于 `specs/<capability-path>/spec.md`。
- `<capability-path>` 是完整 capability 路径，支持
  `identity/user-auth` 之类的嵌套目录。
- 新增 capability 的 delta spec 以 `## Purpose` 开头。
- 修改已有 capability 时不添加 delta `## Purpose`。

### 完整的 MODIFIED requirement

修改现有 requirement 时，`## MODIFIED Requirements` 中必须复制并修改完整的
requirement 块，包括该 requirement 的全部 scenarios。不要只写变化的句子或省略
未变化的 scenarios，否则未包含的内容可能在同步时丢失。

### 退役 capability

若 change 会移除某 capability 的最后一条 requirement 并删除其 main spec，应按
OpenSpec 1.9.0 语义在 `.openspec.yaml` 设置：

```yaml
retire_capabilities: true
```

涉及 sync 或 archive 时，实际处理方式仍以当前 OpenSpec 官方生成物为准。

## apply 与验证记录

使用官方 `/opsx-apply <change-name>` 开始或继续实现。除遵循当前官方生成物外，
`evidence-driven` 的 apply instruction 还要求：

1. 按 `tasks.md` 实施，完成任务后更新复选框。
2. 执行 `verification.md` 中适用的自动化、人工和非功能检查。
3. 如实记录实际命令、步骤、结果与失败原因。
4. 对不适用项说明原因；把未执行项和失败项保留为剩余风险。
5. 遇到阻塞或发现规划不一致时暂停，不伪造完成状态。

`verification.md` 是验证计划与结果记录，不代表对官方 verify 或 archive 增加了本地
裁决条件。

## from-code 独立旁路

```text
/opsx-update-change-from-code <change-name>
```

该命令是本仓库保留的非官方旁路，适用于实现已经发生且确认应保留，但 active
change 落后于代码事实的情况。它以代码证据和用户明确决策为依据，比较并回写
proposal、specs、design、tasks、verification 及允许范围内的相关文档。

它不实现新功能、不修改 main specs，也不结束 change。若代码偏离规划属于缺陷，
应修复代码，而不是用该旁路把缺陷写进规划。

## 状态与校验

```bash
# 查看 active changes
openspec list --json

# 查看 change 的产物状态
openspec status --change "<change-name>"
openspec status --change "<change-name>" --json

# 查看 apply 的动态上下文与指令
openspec instructions apply --change "<change-name>" --json

# 严格校验 change
openspec validate "<change-name>" --type change --strict

# 校验自定义 schema
openspec schema validate evidence-driven
```

应通过 OpenSpec 状态和指令输出取得实际上下文，不要在工具或文档中硬编码 change
产物路径。OpenSpec 升级后，应重新核对官方 `spec-driven` 基线和目标项目中的官方
生成物。
