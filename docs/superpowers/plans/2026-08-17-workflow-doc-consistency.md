# 工作流文档一致性调整实施计划

> **供智能体执行者使用：** 必须使用子技能 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，逐项实施本计划。任务使用复选框语法记录完成状态。

**目标：** 消除工作流文档对官方 OpenSpec 流转条件的过度约束，让 README 的入口说明与实际内容一致，并分层补充本仓库的 SDD 增强闭环。

**架构：** `docs/ai-sdd-workflow.md` 以官方命令场景导航和推荐路径为主，并用独立章节说明本仓库增强规则形成的 SDD 闭环；官方命令的实际条件继续由目标项目当前生成物决定。`README.md` 负责概述 `evidence-driven` schema 语义，不在工作流文档中重复维护。

**技术栈：** Markdown、Mermaid、ripgrep。

## 全局约束

- OpenSpec 相关正文使用简体中文。
- 不改变 OpenSpec 官方命令或本仓库 schema。
- 不把 `verify` 描述为 `sync` 或 `archive` 的官方硬前置。
- 未经用户明确要求不创建 Git 提交。

---

### 任务 1：修正场景导航语义

**文件：**
- 修改：`docs/ai-sdd-workflow.md`

**接口：**
- 输入：目标项目中当前 OpenSpec 官方生成物的行为。
- 输出：不附加官方硬门禁的场景导航文档。

- [x] **步骤 1：调整 Mermaid 流程**

将通过 `verify` 后的分支改为推荐归档路径，并从 `Start` 增加独立 `sync` 场景入口，
表达“只同步 delta specs、不归档”无需由本文强制经过 `verify`。

- [x] **步骤 2：调整正文**

将“归档前同步”改为“独立旁路”，删除 `verify → sync → archive` 的强制链路；把末尾
原则改为：实现完成后建议核验，具体 `verify`、`sync`、`archive` 条件遵循目标项目
当前官方生成物。

- [x] **步骤 3：检查过度约束已移除**

运行：

```bash
rg -n '每条路径都应进入|verify → sync → archive|已通过验证.*opsx-sync' docs/ai-sdd-workflow.md
```

预期：无输出，退出码为 1。

### 任务 2：同步 README 定位

**文件：**
- 修改：`README.md`

**接口：**
- 输入：README 现有 `Schema：evidence-driven` 章节。
- 输出：与工作流文档实际职责一致的入口说明。

- [x] **步骤 1：收窄文档说明**

将仓库内容表中工作流文档的说明从“官方命令场景选择与 schema 制品说明”改为
“官方命令场景选择与推荐路径”。

- [x] **步骤 2：保留 schema 语义入口**

确认 README 的 `Schema：evidence-driven` 章节仍包含 `verification`、
`apply.requires` 与官方行为边界说明，不复制到工作流文档。

- [x] **步骤 3：执行跨文档一致性检查**

运行：

```bash
rg -n '官方命令场景选择与推荐路径|场景选择与推荐路径见|schema 不把这些记录扩展成额外的官方 verify' README.md
rg -n '具体条件与行为遵循目标项目当前 OpenSpec 官方生成物' docs/ai-sdd-workflow.md
```

预期：两个命令均退出码为 0，并分别命中各自指定的文件；README 中保留 schema
边界说明，工作流文档中保留官方生成物免责声明。两个文件独立检查，任一文件缺少
目标内容时，其对应命令必须失败。

### 任务 3：审阅最终差异

**文件：**
- 核验：`docs/ai-sdd-workflow.md`
- 核验：`README.md`

**接口：**
- 输入：任务 1–2 的最终内容。
- 输出：无互相矛盾且未越出范围的文档差异。

- [x] **步骤 1：阅读目标差异**

运行：

```bash
git diff --check -- README.md docs/ai-sdd-workflow.md
git diff -- README.md docs/ai-sdd-workflow.md
```

预期：`git diff --check` 无输出且退出码为 0；差异仅包含已批准的一致性调整及
用户原有的工作流文档改写。

- [x] **步骤 2：确认没有附带修改**

运行：

```bash
git status --short
```

预期：除用户已有变更、两份目标文档及本次设计/计划记录外，没有其他文件变化。

### 任务 4：补充 SDD 增强闭环

**文件：**
- 修改：`docs/ai-sdd-workflow.md`

**接口：**
- 输入：`evidence-driven` 的制品依赖、验证记录，以及接入文档中的
  `AI_TOOLS_VERIFY_GATE_V1` 增强规则。
- 输出：与官方场景导航分层、包含发布后反馈路径的 SDD 闭环说明。

- [x] **步骤 1：新增独立闭环章节和 Mermaid 图**

在“各个场景工作量”之后新增“SDD 增强闭环”章节。图中必须包含：

- `proposal / specs / design / tasks / verification` 到 `apply` 的制品驱动链路。
- `verify` 先直接修复可安全处理的阻塞并复验；仍未解决时按实现缺陷、规划偏差、
  证据不足回流。
- Verify 门禁通过后按目标进入 `sync` 或 `archive`。
- `sync` 后如需归档，必须先重新验证并刷新已经失效的工作区指纹。
- 发布后发现问题时，active change 按问题类型回到 `update`、`apply` 或补充检查，
  已归档 change 建立新 change。

章节开头必须说明：这张图描述本仓库 `evidence-driven` 与验证增强规则组合后的闭环，
不改变前一张图所表达的官方命令默认语义。

- [x] **步骤 2：明确门禁生效条件和闭环退出条件**

正文必须区分：

- schema 自身保证 `verification` 制品存在并由 `apply` 跟踪。
- 只有按 `docs/ai-tools-integration.md` 安装 `AI_TOOLS_VERIFY_GATE_V1` 后，
  `sync` / `archive` 才受验证状态、阻塞项和工作区指纹约束。
- verify 直接修复、sync 后复验和 active change 问题分流必须与接入文档规则一致。
- 未安装增强规则时，`verify`、`sync`、`archive` 的实际条件仍以目标项目当前官方
  生成物为准。

- [x] **步骤 3：执行结构与语义检查**

运行：

```bash
rg -n 'SDD 增强闭环|AI_TOOLS_VERIFY_GATE_V1|发布后|active change|新 change' docs/ai-sdd-workflow.md
rg -n '具体条件与行为遵循目标项目当前 OpenSpec 官方生成物' docs/ai-sdd-workflow.md
git diff --check -- docs/ai-sdd-workflow.md
```

预期：前两个搜索均命中，`git diff --check` 无输出且退出码为 0。最终阅读 Mermaid，
确认没有把增强门禁写成官方默认行为，也没有把独立 `sync` 旁路改成官方强制
`verify → sync → archive` 链路。
