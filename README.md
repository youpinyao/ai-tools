# ai-tools

面向 AI 编程助手的 **OpenSpec / AI-SDD 工作流工具包**。本仓库维护
`evidence-driven` 自定义 schema、简体中文规则、可选的 from-code 旁路及场景文档；
OpenSpec 官方 Cursor skills 与 `/opsx-*` commands 由 OpenSpec 在目标项目生成，本仓库
不跟踪、不复制也不定制这些官方生成物。

默认约定：OpenSpec 相关对话与规划产物使用**简体中文**（见
`.cursor/rules/openspec-chinese.mdc`）。

## 仓库包含什么

| 内容 | 路径 | 说明 |
|------|------|------|
| Schema | `openspec/schemas/evidence-driven/` | 官方 `spec-driven` 的中文派生，增加 `verification` 制品 |
| 配置 | `openspec/config.yaml` | 默认使用 `schema: evidence-driven` |
| 中文规则 | `.cursor/rules/openspec-chinese.mdc` | OpenSpec 相关输出强制简体中文 |
| 可选 Skill | `.cursor/skills/openspec-update-change-from-code/` | 非官方的从代码回写 active change 旁路 |
| 工作流文档 | [docs/ai-sdd-workflow.md](docs/ai-sdd-workflow.md) | 官方命令场景选择与 schema 制品说明 |
| 接入与迁移 | [docs/ai-tools-integration.md](docs/ai-tools-integration.md) | 其它项目从官方 OpenSpec 或旧版 ai-tools 接入/升级 |
| Graphify 接入方案 | [docs/graphify-integration.md](docs/graphify-integration.md) | 用知识图谱增强 AI-SDD / OpenSpec 工作流 |

## 安装到目标项目

其它业务仓的完整接入、从旧版 ai-tools 迁移、以及日常升级步骤见
[docs/ai-tools-integration.md](docs/ai-tools-integration.md)。下文是最短安装路径。

前置条件是支持 [Agent Skills](https://agentskills.io) 的 AI 编程助手（本仓库以
Cursor 为主）和 npm。以下命令中的 `AI_TOOLS_DIR` 是本仓库的绝对路径，
`TARGET_PROJECT` 是目标项目的绝对路径：

```bash
AI_TOOLS_DIR="/absolute/path/to/ai-tools"
TARGET_PROJECT="/absolute/path/to/target-project"
```

重要：本仓库自身不得运行 `openspec init` 或 `openspec update` 生成官方文件；
这两个命令只在目标项目中运行。按以下顺序安装：

1. 安装 npm 最新稳定版 OpenSpec：

   ```bash
   npm install --global @fission-ai/openspec@latest
   ```

2. 在目标项目根目录生成或升级 OpenSpec 官方 Cursor skills 与 commands。新项目
   使用 `init`：

   ```bash
   cd "$TARGET_PROJECT"
   openspec init --tools cursor
   ```

   已初始化的目标项目使用官方 `update` 升级生成物：

   ```bash
   cd "$TARGET_PROJECT"
   openspec update
   ```

3. 将本仓库的 schema 复制到目标项目，并在目标配置中启用：

   ```bash
   mkdir -p "$TARGET_PROJECT/openspec/schemas"
   cp -R \
     "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
     "$TARGET_PROJECT/openspec/schemas/"
   ```

   然后编辑目标项目的 `openspec/config.yaml`：若文件已存在，只合并或设置下面的
   字段，保留项目原有的其他配置；若文件不存在，再创建它。不要用本仓库的完整
   `openspec/config.yaml` 盲目覆盖目标配置。

   ```yaml
   schema: evidence-driven
   ```

   中文规则可按需从本仓库明确复制到目标项目：

   ```bash
   mkdir -p "$TARGET_PROJECT/.cursor/rules"
   cp \
     "$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc" \
     "$TARGET_PROJECT/.cursor/rules/openspec-chinese.mdc"
   ```

   from-code 旁路可选安装：

   ```bash
   cd "$TARGET_PROJECT"
   npx skills add youpinyao/ai-tools --skill openspec-update-change-from-code
   ```

4. 在目标项目校验自定义 schema：

   ```bash
   cd "$TARGET_PROJECT"
   openspec schema validate evidence-driven
   ```

官方 `/opsx-*` 命令及对应 skills 归 OpenSpec 管理；升级后的具体行为应以目标项目
中当前 OpenSpec 官方生成物为准，不要从本仓库寻找或复制官方模板。

## 标准主线

```text
官方 explore（可选）
  → 官方 propose
  → evidence-driven 制品（含 verification 计划）
  → 官方 apply（执行适用检查并记录真实结果）
  → 官方 verify（如使用）
  → 官方 archive
```

常见旁路：

- 已有 change，只调整规划不改代码 → 使用官方 `/opsx-update`。
- 代码已先于规划变化 → `/opsx-update-change-from-code`。
- 只合并 delta specs 到 main specs、不归档 → 使用官方 `/opsx-sync`。
- 无规范层行为变化 → 在 change 的 `.openspec.yaml` 设置 `skip_specs: true`，不要
  捏造空 capability。

verify、archive 与 sync 的具体行为以当前 OpenSpec 官方生成物为准。完整说明见
[AI-SDD 场景化工作流](docs/ai-sdd-workflow.md)。

## Schema：`evidence-driven`

`evidence-driven` 以 OpenSpec 1.9.0 官方 `spec-driven` 为本次语义基线：

- `proposal`、`specs`、`design`、`tasks` 是官方语义的简体中文派生。
- 新增 `verification.md`，用于规划验证并记录实际执行结果与剩余风险。
- `verification` 依赖 `tasks`，`apply` 依赖 `verification` 并跟踪 `tasks.md`。
- apply 应执行 `verification.md` 中适用的检查，如实记录命令、结果、失败原因和
  未执行项；schema 不把这些记录扩展成额外的官方 verify 或 archive 行为。

兼容的官方 1.9.0 语义包括：

- 无规范层行为变化时在 `.openspec.yaml` 设置 `skip_specs: true`。
- capability 使用完整 `<capability-path>`，支持 `identity/user-auth` 等嵌套路径。
- 新增 capability 的 delta spec 以 `## Purpose` 开头；修改已有 capability 时不添加
  delta `## Purpose`。
- `MODIFIED` requirement 必须复制并修改完整 requirement 块及其全部 scenarios。
- 退役整项能力时使用 `retire_capabilities: true`。

后续升级 OpenSpec 时，应从当前官方 `spec-driven` 基线重新核对这些语义，而不是
永久假定 1.9.0 的实现细节。

## 许可证

[MIT](./LICENSE)
