# ai-tools

面向 AI 编程助手的 **OpenSpec / AI-SDD 工作流工具包**：Cursor skills、`/opsx-*` 命令、`evidence-driven` schema，以及场景化团队工作流说明。

默认约定：OpenSpec 相关对话与规划产物使用**简体中文**（见 `.cursor/rules/openspec-chinese.mdc`）。

## 仓库包含什么

| 内容 | 路径 | 说明 |
|------|------|------|
| Skills | `.cursor/skills/` | 8 个 OpenSpec 工作流 skills |
| Commands | `.cursor/commands/` | 对应的 `/opsx-*` Cursor 命令 |
| 中文规则 | `.cursor/rules/openspec-chinese.mdc` | OpenSpec 相关输出强制简体中文 |
| Schema | `openspec/schemas/evidence-driven/` | 带验证门禁的默认 schema |
| 配置 | `openspec/config.yaml` | `schema: evidence-driven` |
| 工作流文档 | [ai-sdd-workflow.md](ai-sdd-workflow.md) | 按场景选择命令与主线流程 |
| Graphify 接入方案 | [graphify-integration.md](graphify-integration.md) | 在目标项目中用知识图谱增强 AI-SDD / OpenSpec 工作流 |

## 前置条件

- 支持 [Agent Skills](https://agentskills.io) 的 AI 编程助手（本仓库以 Cursor 为主）
- [OpenSpec CLI](https://github.com/Fission-AI/OpenSpec)（`openspec` 需在 `PATH` 中）

## 如何使用

将本仓库内容放到目标项目根目录（或复制 `.cursor/` 与 `openspec/`），使 Cursor 能加载 skills / commands / rules，并用 OpenSpec 读取 `evidence-driven` schema：

```bash
git clone https://github.com/youpinyao/ai-tools.git
# 或按需复制 .cursor/、openspec/、ai-sdd-workflow.md 到业务仓库
```

也可通过 skills.sh 安装其中已发布的单个 skill（例如从代码回写变更）：

```bash
npx skills add youpinyao/ai-tools --skill openspec-update-change-from-code
```

## 标准主线

```text
[可选] explore
    ↓
propose
    ↓
apply（实现 tasks，并记录实现侧验证证据）
    ↓
verify（未参与实现的 Agent 独立复验；优先由 apply 自动派发子 Agent）
    ↓
archive（可在归档时同步 delta specs）
```

旁路场景：

- 已有 change，只改规划不改代码 → `/opsx-update`
- 代码已先于规划变化 → `/opsx-update-change-from-code`
- 只合并 delta specs 到 main specs、不归档 → `/opsx-sync`
- 纯重构 / 工具链 / 文档、无规范层行为变化 → 在 change 的 `.openspec.yaml` 设置 `skip_specs: true`（OpenSpec 1.7+），不要捏造空 specs

完整场景说明见 [AI-SDD 团队工作流](ai-sdd-workflow.md)。

## Skills 与命令

| Skill | 命令 | 用途 |
|-------|------|------|
| `openspec-explore` | `/opsx-explore` | 探索想法、调研问题、澄清需求 |
| `openspec-propose` | `/opsx-propose` | 新建 change，并一次生成规划产物 |
| `openspec-update-change` | `/opsx-update` | 修订已有规划产物并保持一致（不改代码） |
| `openspec-apply-change` | `/opsx-apply` | 按 tasks 开始或继续实现 |
| `openspec-update-change-from-code` | `/opsx-update-change-from-code` | 以代码为准回写活跃 change |
| `openspec-sync-specs` | `/opsx-sync` | 将 delta specs 同步到 main specs |
| `openspec-verify-change` | `/opsx-verify` | 独立复验实现是否匹配变更产物 |
| `openspec-archive-change` | `/opsx-archive` | 归档已完成的 change |

`evidence-driven` 产物链路大致为：

```text
proposal → specs / design → tasks → verification → apply → verify → archive
```

## Schema：`evidence-driven`

在 OpenSpec 常见的提案、规范、设计、任务之上，增加验证计划、实现证据与独立验证门禁。项目通过 `openspec/config.yaml` 默认启用该 schema。

模板位于 `openspec/schemas/evidence-driven/templates/`（`proposal`、`spec`、`design`、`tasks`、`verification` 等）。

兼容 OpenSpec CLI **1.7+**：零增量变更须声明 `skip_specs: true`；新增能力的 delta spec 建议以 `## Purpose` 开头。Skills 与 commands 为定向同步，勿对本仓库直接跑 `openspec update`（会覆盖定制门禁与扩展 skill）。

## 许可证

[MIT](./LICENSE)
