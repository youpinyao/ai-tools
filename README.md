# ai-tools：OpenSpec / AI-SDD 工作流工具包

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
| 可选 Skill | `.cursor/skills/openspec-update-change-from-code/` | 非官方的从代码回写旁路：优先 active change，否则回写已有 main spec |
| 可选 Command | `.cursor/commands/opsx-update-change-from-code.md` | 在 Cursor 中暴露 `/opsx-update-change-from-code` |
| 工作流文档 | [docs/ai-sdd-workflow.md](docs/ai-sdd-workflow.md) | 官方命令场景选择与推荐路径 |
| 接入与迁移 | [docs/ai-tools-integration.md](docs/ai-tools-integration.md) | 其它项目从官方 OpenSpec 或旧版 ai-tools 接入/升级 |
| 升级维护 | [docs/openspec-upgrade-plan.md](docs/openspec-upgrade-plan.md) | OpenSpec 版本升级与语义复核清单 |
| 可选 Graphify 方案 | [docs/graphify-integration.md](docs/graphify-integration.md) | 用知识图谱增强 AI-SDD / OpenSpec 工作流 |

## 安装到目标项目

其它业务仓的完整接入、从旧版 ai-tools 迁移、以及日常升级步骤见
[docs/ai-tools-integration.md](docs/ai-tools-integration.md)。下文只完成官方生成层、自定义
schema 与可选旁路的基础安装；完整的 propose worktree 选择、隔离 worktree 收尾、verify 修复闭环及
sync/archive 流转门禁还须按
[接入文档 5.1 节](docs/ai-tools-integration.md#51-补充-verify-修复闭环与流转门禁)
安装 `AI_TOOLS_VERIFY_GATE_V2`、`AI_TOOLS_PROPOSE_WORKTREE_V1` 与
`AI_TOOLS_WORKTREE_FINISH_V1` 增强规则。

前置条件：

- Node.js ≥ 20.19.0，并可使用 npm 安装 OpenSpec CLI。
- 支持 [Agent Skills](https://agentskills.io) 的 AI 编程助手（本仓库以 Cursor 为主）。
- 若安装完整验证闭环，还需 Python 3.8+ 计算确定性 V2 范围指纹。

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
   npx skills add "$AI_TOOLS_DIR" \
     --skill openspec-update-change-from-code \
     --agent cursor

   # 如需在 Cursor 中使用同名 slash command，同时安装 command 文件
   mkdir -p "$TARGET_PROJECT/.cursor/commands"
   cp \
     "$AI_TOOLS_DIR/.cursor/commands/opsx-update-change-from-code.md" \
     "$TARGET_PROJECT/.cursor/commands/opsx-update-change-from-code.md"
   ```

4. 在目标项目校验自定义 schema：

   ```bash
   cd "$TARGET_PROJECT"
   openspec schema validate evidence-driven
   ```

5. 要完成当前 ai-tools 接入，必须继续执行
   [接入文档 5.1 节](docs/ai-tools-integration.md#51-补充-verify-修复闭环与流转门禁)：
   从本仓库复制 `.cursor/scripts/openspec-verification-fingerprint.py`，向 apply、
   verify、sync、archive 的 8 个官方 command/skill 文件幂等追加
   `AI_TOOLS_VERIFY_GATE_V2` 规则，并向 propose 的 2 个
   官方 command/skill 文件幂等追加 `AI_TOOLS_PROPOSE_WORKTREE_V1` 规则，并向上述 10 个
   官方 command/skill 文件幂等追加 `AI_TOOLS_WORKTREE_FINISH_V1` 收尾规则。增强规则同时提供
   apply 子 Agent 派发、独立 verify 子 Agent 派发、防递归标记（
   `AI_TOOLS_DELEGATED_APPLY_V1`、`AI_TOOLS_DELEGATED_VERIFY_V1`）与阶段内并行开关
   （`AI_TOOLS_PARALLEL_DISPATCH_V1`）：apply 时入口 Agent 先派发 apply 子 Agent，
   成功后再派发 verify 子 Agent；用户单独运行 `/opsx-verify` 时，入口 Agent 同样
   派发 verify 子 Agent。阶段子 Agent 每次运行时仅当本会话可用 skills 列表含
   `dispatching-parallel-agents` 时，才对独立域并行派发带工作者身份标记的实施者 /
   调查者；列表中没有则按官方默认串行。不得因磁盘上能读到 `SKILL.md` 而启用并行。
   后续安装该 skill 无需再次替换注入。未安装增强规则时，这些派发行为不成立。仅复制
   schema 不会自动获得这些流转门禁与子 Agent 编排。
   也必须注入 propose worktree 选择，否则 `/opsx-propose` 会跳过起始询问，直接在当前
   工作区创建 change。也必须注入隔离 worktree 按需收尾，否则用户事后明确要求合并或
   清理时没有同一套安全步骤；注入后各阶段结束时不得主动询问怎么处理。

官方 `/opsx-*` 命令及对应 skills 归 OpenSpec 管理；升级后的具体行为应以目标项目
中当前 OpenSpec 官方生成物为准，不要从本仓库寻找或复制官方模板。当前 CLI 1.10.0
已确认的命令（以 `openspec --help` 为准，不要猜测未列出的参数）：

- 新项目：`openspec init --tools cursor`
- 已初始化：`openspec update`（`--force` 可在工具已是最新时仍刷新）
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

安装 `AI_TOOLS_VERIFY_GATE_V2`、`AI_TOOLS_PROPOSE_WORKTREE_V1` 与
`AI_TOOLS_WORKTREE_FINISH_V1` 后的增强主线：

```text
官方 explore（可选）
  → 官方 propose（先询问隔离 worktree 或当前工作区）
  → evidence-driven 制品（含 verification 计划）
  → apply 子 Agent（实施并记录真实结果）
  → 独立 verify 子 Agent
  → 官方 archive
  → 隔离 worktree 默认留下；仅当用户明确要求时才合并或清理
```

apply 与 verify 两个阶段始终串行。阶段内并行不是接入时开关：仅当本会话可用
skills 列表含 `dispatching-parallel-agents` 时，阶段子 Agent 才按该 skill 派发
带独立身份标记的工作者；否则与现网串行路径相同。

单独运行 `/opsx-verify` 时，入口 Agent 也按同一规则派发独立 verify 子 Agent 执行验证
闭环。未安装增强规则时，propose 起始 worktree 询问、隔离 worktree 按需收尾、apply/verify 子 Agent 派发及 sync/archive 门禁均不成立；
具体行为仍以目标项目当前 OpenSpec 官方生成物为准。

常见旁路：

- 已有 change，只调整规划不改代码 → 使用官方 `/opsx-update`。
- 代码已先于规划变化 → `/opsx-update-change-from-code`（有唯一匹配的 active
  change 回写 change；无 change 且只有一份对应 spec 则回写该 spec；有歧义先问）。
- 只合并 delta specs 到 main specs、不归档 → 使用官方 `/opsx-sync`。
- 无规范层行为变化 → 在 change 的 `.openspec.yaml` 设置 `skip_specs: true`，不要
  捏造空 capability。

verify、archive 与 sync 的具体行为以当前 OpenSpec 官方生成物为准。场景选择与推荐路径见
[AI-SDD 场景化工作流](docs/ai-sdd-workflow.md)。

## Schema：`evidence-driven`

`evidence-driven` 以 OpenSpec 1.10.0 官方 `spec-driven` 为本次语义基线：

- `proposal`、`specs`、`design`、`tasks` 是官方语义的简体中文派生。
- 新增紧凑的 `verification.md` 账本，以范围、检查、代码审查、风险与回滚四节保存
  当前权威验证状态；复验更新原检查行，不追加完整历史。
- `verification` 依赖 `tasks`，`apply` 依赖 `verification` 并跟踪 `tasks.md`。
- apply 应执行 `verification.md` 中适用的检查，包括必做的代码审查，如实记录命令、
  结果、失败原因和未执行项；schema 不把这些记录扩展成额外的官方 verify 或
  archive 行为。

兼容的官方 1.10.0 语义包括：

- 用 `planningHome.root` 定位主规范，不要写死仓库相对路径。
- 每项任务必须在 `- [ ]` 说明中写明如何验证完成。
- 无规范层行为变化时在 `.openspec.yaml` 设置 `skip_specs: true`。
- capability 使用完整 `<capability-path>`，支持 `identity/user-auth` 等嵌套路径。
- 新增 capability 的 delta spec 以 `## Purpose` 开头（50 个以上字符，否则
  `openspec validate --strict` 会报过短）；修改已有 capability 时不添加
  delta `## Purpose`。
- `MODIFIED` requirement 必须复制并修改完整 requirement 块及其全部
  `#### Scenario`。
- 官方 `/opsx-verify` 只在会话中输出 Completeness / Correctness / Coherence
  记分卡，不写 `verification.md`。官方 `/opsx-archive` 对未完成制品或任务仅警告
  并允许确认继续。项目级 `AI_TOOLS_VERIFY_GATE_V2` 是额外门禁，不是 OpenSpec
  官方行为。V2 以声明范围计算摘要与内容指纹：范围内变化使门禁失效并阻断流转，
  范围外变化只告警；若范围外路径实际属于 change，必须扩展范围并复验。正常
  `/opsx-sync` 生成的 main spec 未纳入声明范围时，不强制重复实现验证。

后续升级 OpenSpec 时，应从当前官方 `spec-driven` 基线重新核对这些语义，而不是
永久假定 1.10.0 的实现细节。

## 许可证

[MIT](./LICENSE)
