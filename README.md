# ai-tools：OpenSpec / AI-SDD 工作流工具包

面向 AI 编程助手的 **OpenSpec / AI-SDD 工作流工具包**。本仓库维护
`evidence-driven` 自定义 schema、简体中文规则、可选的 from-code 旁路及场景文档；
OpenSpec 官方 skills 由 OpenSpec 在目标项目的 `.agents/skills/` 生成，作为 Cursor 与
Codex 共用的唯一来源；不初始化或保留 Cursor commands 与重复 skills。

默认约定：OpenSpec 相关对话与规划产物使用**简体中文**。根目录 `AGENTS.md`
提供对话级约束；`openspec/config.yaml` 的 `context` 由 OpenSpec 注入制品
instruction，负责制品正文与机器敏感结构。

## 仓库包含什么

| 内容 | 路径 | 说明 |
|------|------|------|
| Schema | `openspec/schemas/evidence-driven/` | 官方 `spec-driven` 的中文派生，增加 `verification` 制品 |
| 配置 | `openspec/config.yaml` | 默认 `schema: evidence-driven`，并以 `context` 注入制品中文规则 |
| 对话规则 | `AGENTS.md` | 覆盖对话、澄清、进度、总结及 Commit / PR；带独立幂等边界标记 |
| 制品规则 | `openspec/config.yaml` 的 `context` | 官方制品注入路径；带 `AI_TOOLS_OPENSPEC_CHINESE_V1` 幂等边界标记 |
| 可选 Skill | `.agents/skills/openspec-update-change-from-code/` | Cursor / Codex 共用的唯一 Agent Skill 源（从代码回写） |
| 工作流文档 | [docs/ai-sdd-workflow.md](docs/ai-sdd-workflow.md) | 官方命令场景选择与推荐路径 |
| 接入与迁移 | [integrating-ai-tools](.agents/skills/integrating-ai-tools/reference.md) | 其它项目从官方 OpenSpec 或旧版 ai-tools 接入/升级 |
| 升级维护 | [upgrading-openspec](.agents/skills/upgrading-openspec/reference.md) | OpenSpec 版本升级与语义复核清单 |
| 可选 Graphify 方案 | [integrating-graphify](.agents/skills/integrating-graphify/reference.md) | 用知识图谱增强 AI-SDD / OpenSpec 工作流 |

## 安装到目标项目

其它业务仓的完整接入、从旧版 ai-tools 迁移、以及日常升级步骤见
[integrating-ai-tools reference](.agents/skills/integrating-ai-tools/reference.md)。下文只完成官方生成层、自定义
schema 与可选旁路的基础安装；完整的 verify 修复闭环及 sync/archive 流转门禁还须按
[接入文档 5.1 节](.agents/skills/integrating-ai-tools/reference.md#51-补充-verify-修复闭环与流转门禁)
安装 `AI_TOOLS_VERIFY_GATE_V2` 增强规则。

前置条件：

- Node.js ≥ 20.19.0，并可使用 npm 安装 OpenSpec CLI。
- 支持 [Agent Skills](https://agentskills.io) 的 AI 编程助手（默认 Cursor、Codex）。

以下命令中的 `AI_TOOLS_DIR` 是本仓库的绝对路径，`TARGET_PROJECT` 是目标项目的
绝对路径：

```bash
AI_TOOLS_DIR="/absolute/path/to/ai-tools"
TARGET_PROJECT="/absolute/path/to/target-project"
```

重要：本仓库自身不得运行 `openspec init` 或 `openspec update` 生成官方文件；
这两个命令只在目标项目中运行。按以下顺序安装：

1. 安装 npm 最新稳定版 OpenSpec。普通使用者可用 `@latest` 快捷安装，但必须立刻核对版本：

   ```bash
   npm install --global @fission-ai/openspec@latest
   openspec --version
   ```

   团队执行升级时应记录并固定 `npm view` 解析出的精确版本，避免 `@latest` 在执行过程中再次漂移：

   ```bash
   TARGET_VERSION="$(npm view @fission-ai/openspec version)"
   npm install --global "@fission-ai/openspec@$TARGET_VERSION"
   test "$(openspec --version)" = "$TARGET_VERSION"
   ```

2. 在目标项目根目录生成或升级 OpenSpec 官方共享 skills。新项目
   使用 `init`：

   ```bash
   cd "$TARGET_PROJECT"
   openspec init --tools codex
   ```

   已初始化的目标项目先刷新，再生成 `.agents/skills/` 唯一来源，并清理旧 OpenSpec Cursor 生成物：

   ```bash
   cd "$TARGET_PROJECT"
   openspec update
   openspec init --tools codex
   rm -rf "$TARGET_PROJECT/.cursor/commands/opsx-"*
   rm -rf "$TARGET_PROJECT/.cursor/skills/openspec-"*
   ```

3. 将本仓库的 schema 复制到目标项目，并在目标配置中启用：

   ```bash
   mkdir -p "$TARGET_PROJECT/openspec/schemas"
   cp -R \
     "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
     "$TARGET_PROJECT/openspec/schemas/"
   ```

   然后编辑目标项目的 `openspec/config.yaml`：若文件已存在，只合并 `schema` 与
   `AI_TOOLS_OPENSPEC_CHINESE_V1` 标记块，保留项目原有的其他配置（含其余
   `context` / `rules` / `operations`）；若文件不存在，再创建它。不要用本仓库的完整
   `openspec/config.yaml` 盲目覆盖目标配置。制品规则正文以本仓库
   `openspec/config.yaml` 的标记块为准。

   ```yaml
   schema: evidence-driven

   context: |
     # AI_TOOLS_OPENSPEC_CHINESE_V1_START
     语言：中文（简体）
     ...
     # AI_TOOLS_OPENSPEC_CHINESE_V1_END
   ```

   已有 `context` 时，只替换或插入该标记块，不要清空其它上下文。若目标
   `AGENTS.md` 仍有旧 `AI_TOOLS_OPENSPEC_CHINESE_V1` 标记块，删除该旧片段；
   同时插入或替换本仓库 `AGENTS.md` 中的
   `AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1` 标记块。目标已有其它
   `AGENTS.md` 内容时必须保留，不得整文件覆盖。

   from-code Skill 只安装一份到通用 `.agents/skills/`，Cursor 与 Codex 都发现该路径：

   ```bash
   mkdir -p "$TARGET_PROJECT/.agents/skills"
   rm -rf "$TARGET_PROJECT/.agents/skills/openspec-update-change-from-code"
   cp -R \
     "$AI_TOOLS_DIR/.agents/skills/openspec-update-change-from-code" \
     "$TARGET_PROJECT/.agents/skills/"
   ```

4. 在目标项目校验自定义 schema：

   ```bash
   cd "$TARGET_PROJECT"
   openspec schema validate evidence-driven
   ```

5. 要完成当前 ai-tools 接入，必须继续执行
   [接入文档 5.1 节](.agents/skills/integrating-ai-tools/reference.md#51-补充-verify-修复闭环与流转门禁)：
   向 apply、verify、sync、archive 的官方 skills 幂等追加
   `AI_TOOLS_VERIFY_GATE_V2` 规则。增强规则要求当前 Agent 串行完成 apply 和 verify，
   并提供 sync/archive 的 Verify 门禁。apply 使用 `AI_TOOLS_DIRECT_APPLY_V1`，verify
   使用 `AI_TOOLS_DIRECT_VERIFY_V1`；仅复制 schema 不会自动获得这些流转门禁。

官方 `$openspec-*` skills 归 OpenSpec 管理；Cursor 与 Codex 共同从 `.agents/skills/` 发现它们。升级后的具体行为应以目标项目
中当前 OpenSpec 官方生成物为准，不要从本仓库寻找或复制官方模板。当前 CLI 1.13.0
已确认的命令（以 `openspec --help` 为准，不要猜测未列出的参数）：

- 新项目：`openspec init --tools codex`
- 已初始化：`openspec update` 后运行 `openspec init --tools codex`，清理 OpenSpec Cursor commands/重复 skills，随后重做 5.1 注入
- 校验 schema：`openspec schema validate evidence-driven`（schema 子命令仍标为 experimental）
- 新建 change：`openspec new change "<name>" --schema evidence-driven`
- JSON：`openspec list --json`、`openspec list --specs --json`、
  `openspec status --change "<name>" --json`、`openspec context --json`、
  `openspec validate "<name>" --type change --strict --json`、
  `openspec validate "<id>" --type spec --strict --json`、
  `openspec instructions apply --change "<name>" --json`

主规范位于 `<root>/openspec/specs/<capability-path>/spec.md`。有 change 时
`root` 来自 `planningHome.root`（`openspec instructions apply --change "<name>" --json`
或 `openspec status --change "<name>" --json`）；无 change 时来自
`openspec list --specs --json` 或 `openspec context --json` 的 `root.path`。
归档目录为 `<planningHome.changesDir>/archive/`（仓库内通常是 `openspec/changes/archive/`）。

## 标准主线

安装 `AI_TOOLS_VERIFY_GATE_V2` 后的增强主线：

```text
官方 explore（可选）
  → 官方 propose
  → evidence-driven 制品（含 verification 计划）
  → 当前 Agent 执行 apply
  → 当前 Agent 执行 verify
  → 官方 archive
```

apply 与 verify 两个阶段始终由当前 Agent 串行执行。单独运行 `$openspec-apply-change` 或
`$openspec-verify` 时同样由当前 Agent 执行对应阶段。未安装增强规则时，相关直接执行
约束及 sync/archive 门禁均不成立；
具体行为仍以目标项目当前 OpenSpec 官方生成物为准。

常见旁路：

- 已有 change，只调整规划不改代码 → 使用官方 `$openspec-update`。
- 代码已先于规划变化 → 共用 `openspec-update-change-from-code` skill（有唯一匹配的 active
  change 回写 change；无 change 且只有一份对应 spec 则回写该 spec；有歧义先问）。
- 只合并 delta specs 到 main specs、不归档 → 使用官方 `$openspec-sync`。
- 无规范层行为变化 → 在 change 的 `.openspec.yaml` 设置 `skip_specs: true`，不要
  捏造空 capability。

verify、archive 与 sync 的具体行为以当前 OpenSpec 官方生成物为准。场景选择与推荐路径见
[AI-SDD 场景化工作流](docs/ai-sdd-workflow.md)。

## Schema：`evidence-driven`

`evidence-driven` 以 OpenSpec 1.13.0 官方 `spec-driven` 为本次语义基线：

- `proposal`、`specs`、`design`、`tasks` 是官方语义的简体中文派生。
- 新增紧凑的 `verification.md` 账本，以范围、技能与规则、检查、代码审查、风险与回滚五节
  保存当前权威验证状态；复验更新原检查行，不追加完整历史。
- `verification` 依赖 `tasks`，`apply` 依赖 `verification` 并跟踪 `tasks.md`。
- `design` 记录预期适用的 skill / rule；apply 在实现前依据当前 description /
  适用范围重新发现并处理差异，将实际采用项和证据写入 `verification.md`；任务已为
  `all_done` 时也须在 verify 前复核，证据缺失会阻断后续流转。
- apply 应执行 `verification.md` 中适用的检查，包括必做的代码审查，如实记录命令、
  结果、失败原因和未执行项；schema 不把这些记录扩展成额外的官方 verify 或
  archive 行为。

兼容的官方 1.13.0 语义包括：

- `explore` 在提出事实性问题前先只读检查相关 OpenSpec 制品、源码、测试、文档与配置，
  同时用 `openspec list --specs` 与带 `--type spec` 的 `openspec show` 区分在途 change
  和持久能力；概览筛选后必须完整读取相关规范及场景。
- `propose` 先用 `openspec context --json` 解析权威根；无 OpenSpec 根时停止并等待用户
  明确请求初始化。解析成功后，在探索代码库和规划前读取配置中的项目 `context`，再按
  变更需要只读检查相关实现、测试、配置和文档；范围、方案与任务必须以实际发现为依据。
- proposal 与 delta spec 在复用既有能力前通过 `openspec list --specs` 核对准确路径，
  避免把近似名称或错误路径当成新能力。
- 用 `planningHome.root` 定位主规范，不要写死仓库相对路径。
- 每项任务必须在 `- [ ]` 说明中写明如何验证完成。
- 无规范层行为变化时在 `.openspec.yaml` 设置 `skip_specs: true`。
- capability 使用完整 `<capability-path>`，支持 `identity/user-auth` 等嵌套路径。
- 新增 capability 的 delta spec 以 `## Purpose` 开头（50 个以上字符，否则
  `openspec validate --strict` 会报过短）；修改已有 capability 时不添加
  delta `## Purpose`。
- `MODIFIED` requirement 必须复制并修改完整 requirement 块及其全部
  `#### Scenario`。
- 官方 `$openspec-verify` 只在会话中输出 Completeness / Correctness / Coherence
  记分卡，不写 `verification.md`。官方 `$openspec-archive` 对未完成制品或任务仅警告
  并允许确认继续。项目级 `AI_TOOLS_VERIFY_GATE_V2` 是额外门禁，不是 OpenSpec
  官方行为。该门禁只读取 `verification.md` 中当前的结构化结论：状态必须为“通过”，
  阻塞项必须为“无”。

后续升级 OpenSpec 时，应从当前官方 `spec-driven` 基线重新核对这些语义，而不是
永久假定 1.13.0 的实现细节。

## 许可证

[MIT](./LICENSE)
