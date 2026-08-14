# OpenSpec 官方优先工作流重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除仓库内官方 Cursor skills/commands 副本，以 OpenSpec 1.9.0 官方 `spec-driven` 为基线重建 schema-only 的 `evidence-driven`，并同步文档。

**Architecture:** 官方 Cursor 产物由目标项目运行 `openspec init --tools cursor` 获取，本仓库只维护自定义 schema。`evidence-driven` 相对官方基线仅保留中文化、新增 `verification`、`apply.requires: [verification]` 与 apply 记录真实验证结果四类差异。

**Tech Stack:** OpenSpec CLI 1.9.0、YAML、Markdown、Git、ripgrep。

## Global Constraints

- 本次基线版本：`openspec --version` 与 `npm view @fission-ai/openspec version` 均为 `1.9.0`。
- 官方 explore/propose/update/apply/verify/archive/sync skills 与 commands 不得被 Git 跟踪。
- 不创建 Cursor rule 或 wrapper skill 承载流程门禁。
- 不保留独立 Agent verify、Code Review 归档硬门禁、自动派发 verify 或 finishing。
- `evidence-driven` schema、模板与 OpenSpec 文档使用简体中文。
- 保留 `.cursor/rules/openspec-chinese.mdc`、`openspec-update-change-from-code` 与 `docs/graphify-integration.md`。
- 未获用户明确要求时不得执行 git commit。

---

## 文件地图

- `.gitignore`：精确忽略 7 组官方 Cursor skills/commands。
- `.cursor/skills/openspec-{explore,propose,update-change,apply-change,verify-change,archive-change,sync-specs}/`：删除已跟踪副本。
- `.cursor/commands/opsx-{explore,propose,update,apply,verify,archive,sync}.md`：删除已跟踪副本。
- `openspec/schemas/evidence-driven/schema.yaml`：按官方 1.9.0 `spec-driven` 重建并新增 verification。
- `openspec/schemas/evidence-driven/templates/{proposal,spec,design,tasks}.md`：从官方模板重新建立中文版本。
- `openspec/schemas/evidence-driven/templates/verification.md`：重建为 schema-only 验证计划与结果模板。
- `README.md`：改为官方初始化 + 自定义 schema 的安装说明。
- `docs/ai-sdd-workflow.md`：删除本地 verify/archive 硬门禁承诺，改为官方行为。
- `spec/spec-architecture-openspec-workflow-refactor.md`：已批准的 2.0 规格，只做最终一致性核对。

### Task 1: 建立官方生成物所有权边界

**Files:**
- Modify: `.gitignore`
- Delete: `.cursor/skills/openspec-explore/SKILL.md`
- Delete: `.cursor/skills/openspec-propose/SKILL.md`
- Delete: `.cursor/skills/openspec-update-change/SKILL.md`
- Delete: `.cursor/skills/openspec-apply-change/SKILL.md`
- Delete: `.cursor/skills/openspec-verify-change/SKILL.md`
- Delete: `.cursor/skills/openspec-archive-change/SKILL.md`
- Delete: `.cursor/skills/openspec-sync-specs/SKILL.md`
- Delete: `.cursor/commands/opsx-explore.md`
- Delete: `.cursor/commands/opsx-propose.md`
- Delete: `.cursor/commands/opsx-update.md`
- Delete: `.cursor/commands/opsx-apply.md`
- Delete: `.cursor/commands/opsx-verify.md`
- Delete: `.cursor/commands/opsx-archive.md`
- Delete: `.cursor/commands/opsx-sync.md`

**Interfaces:**
- Consumes: 规格 §3.2 的官方生成路径清单。
- Produces: Git 不再跟踪且默认忽略官方生成物；from-code 旁路仍可跟踪。

- [ ] **Step 1: 写入精确忽略规则**

将 `.gitignore` 更新为：

```gitignore
.DS_Store

# OpenSpec 官方 Cursor 生成物：由目标项目运行 openspec init/update 管理
/.cursor/skills/openspec-explore/
/.cursor/skills/openspec-propose/
/.cursor/skills/openspec-update-change/
/.cursor/skills/openspec-apply-change/
/.cursor/skills/openspec-verify-change/
/.cursor/skills/openspec-archive-change/
/.cursor/skills/openspec-sync-specs/
/.cursor/commands/opsx-explore.md
/.cursor/commands/opsx-propose.md
/.cursor/commands/opsx-update.md
/.cursor/commands/opsx-apply.md
/.cursor/commands/opsx-verify.md
/.cursor/commands/opsx-archive.md
/.cursor/commands/opsx-sync.md
```

- [ ] **Step 2: 确认官方副本均处于删除状态**

运行：

```bash
git status --short
```

预期：上述 14 个 tracked 文件均显示 `D`；不得新增同名替代文件。

- [ ] **Step 3: 验证忽略边界**

运行：

```bash
git check-ignore --no-index -v .cursor/skills/openspec-apply-change/SKILL.md
git check-ignore --no-index -v .cursor/commands/opsx-apply.md
git check-ignore -q .cursor/skills/openspec-update-change-from-code/SKILL.md; test "$?" -eq 1
git check-ignore -q .cursor/commands/opsx-update-change-from-code.md; test "$?" -eq 1
```

预期：前两条在官方文件仍处于 tracked-but-deleted 状态时也显示 `.gitignore` 命中；后两条退出码检查通过，证明 from-code 未被忽略。用户未来提交删除后，再以 Task 4 的 `git ls-files` 闭合“不再跟踪”验收。

- [ ] **Step 4: 暂不提交**

保留工作区修改，等待用户明确要求后再 commit。

### Task 2: 从官方 1.9.0 基线重建 `evidence-driven`

**Files:**
- Replace: `openspec/schemas/evidence-driven/schema.yaml`
- Replace: `openspec/schemas/evidence-driven/templates/proposal.md`
- Replace: `openspec/schemas/evidence-driven/templates/spec.md`
- Replace: `openspec/schemas/evidence-driven/templates/design.md`
- Replace: `openspec/schemas/evidence-driven/templates/tasks.md`
- Replace: `openspec/schemas/evidence-driven/templates/verification.md`
- Verify: `openspec/config.yaml`

**Interfaces:**
- Consumes: `openspec schema which spec-driven` 解析出的官方 `schema.yaml` 与 4 个模板。
- Produces: 可由 OpenSpec 1.9.0 加载的 `evidence-driven`，apply 前置为 verification。

- [ ] **Step 1: 再次锁定官方基线**

运行：

```bash
test "$(openspec --version)" = "$(npm view @fission-ai/openspec version)"
openspec schema which spec-driven
```

预期：版本比较退出码为 0，输出路径指向当前 OpenSpec 包内 `schemas/spec-driven`。

- [ ] **Step 2: 重建 proposal/spec/design/tasks instruction**

以官方 `spec-driven/schema.yaml` 为逐段基线翻译为简体中文，必须保留：

```text
proposal:
  skip_specs: true、完整 capability-path、不得捏造 requirement
specs:
  行为契约边界、Purpose 规则、完整 MODIFIED requirement、四级 Scenario 标题
design:
  Context/Goals/Decisions/Risks、会影响任务的问题必须先解决
tasks:
  - [ ] 格式、依赖顺序、单会话粒度、可验证
```

不得保留旧 schema 中的 `Superpowers 对接`、brainstorming、writing-plans、Task 派发、Code Review 或 finishing 文案。

- [ ] **Step 3: 重建 4 个官方派生模板**

模板结构应分别为：

```markdown
proposal.md: 为什么 / 变更内容 / 能力（新增、修改）/ 影响
spec.md: Purpose / ADDED Requirements / Requirement / Scenario
design.md: 背景 / 目标与非目标 / 设计决策 / 风险与权衡
tasks.md: 两个编号任务组，每项使用 - [ ] X.Y
```

仅做忠实中文化，不加入 Superpowers 注释、文件地图或本地流程门禁。

- [ ] **Step 4: 新建 schema-only verification 模板**

`verification.md` 必须包含以下一级或二级章节：

```markdown
## 验证范围
## 需求与验证对应关系
## 自动化验证
## 人工验证
## 非功能验证
## 实际执行结果
## 未执行项与剩余风险
## 发布后验证与回滚
```

表格状态只使用 `待执行`、`通过`、`失败`、`不适用`。删除 `代码审查（归档硬门禁）`、`独立验证结论`、自动派发说明与 Finishing。
规划期填写的命令必须来自仓库中已确认的脚本或工具配置；尚未确认时写明确认方式，
不得伪造可执行命令。

- [ ] **Step 5: 设置制品图与 apply instruction**

`schema.yaml` 尾部必须等价于：

```yaml
  - id: verification
    generates: verification.md
    description: 验证计划与实际执行结果
    template: verification.md
    instruction: |
      创建验证计划，将需求和场景映射到真实、可执行的检查。
      规划阶段保持“待执行”，不得捏造结果。
      命令必须来自仓库中已确认的脚本或工具配置；尚未确认命令时，写明确认方式，不得伪造可执行命令。
      执行阶段仅在实际运行检查并阅读输出后记录“通过”。
      失败、不适用和未执行项必须记录原因与剩余风险。
    requires:
      - tasks

apply:
  requires: [verification]
  tracks: tasks.md
  instruction: |
    阅读上下文文件，逐项完成待办任务，完成后立即勾选。
    执行 verification.md 中适用的检查，并记录真实命令、结果、失败原因与剩余风险。
    遇到阻塞或需要澄清时暂停。
```

- [ ] **Step 6: 验证 schema**

运行：

```bash
test "$(awk '/^schema:/ {print $2}' openspec/config.yaml)" = "evidence-driven"
openspec schema validate evidence-driven
```

预期：配置断言通过；schema 校验退出码为 0。

- [ ] **Step 7: 验证禁止内容已移除**

运行：

```bash
if rg -n 'Superpowers|Task 派发|归档硬门禁|独立验证结论|Finishing|brainstorming|writing-plans' \
  openspec/schemas/evidence-driven; then
  exit 1
fi
```

预期：无匹配，脚本退出码为 0。

- [ ] **Step 8: 暂不提交**

保留工作区修改，等待用户明确要求后再 commit。

### Task 3: 更新安装说明与场景工作流

**Files:**
- Modify: `README.md`
- Replace: `docs/ai-sdd-workflow.md`

**Interfaces:**
- Consumes: Task 1 的官方所有权边界、Task 2 的 schema-only 行为。
- Produces: 不再承诺本地官方模板或硬门禁的用户文档。

- [ ] **Step 1: 重写 README 的仓库内容与安装步骤**

README 必须明确：

```text
1. 安装 npm 最新稳定版 OpenSpec。
2. 新目标项目运行 openspec init --tools cursor；已初始化目标项目使用 CLI openspec update 升级官方生成物。
3. 从 ai-tools 复制/安装 evidence-driven schema、配置、可选中文 rule 及可选旁路。
4. 在目标项目运行 openspec schema validate evidence-driven。
```

所有操作目标项目的执行块都必须显式包含 `cd "$TARGET_PROJECT"`，不能依赖前一个
可选步骤遗留的当前目录。中文 rule 的可选安装说明必须给出从
`$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc` 到
`$TARGET_PROJECT/.cursor/rules/openspec-chinese.mdc` 的完整复制命令。

删除“仓库包含 8 个 OpenSpec 工作流 skills 与对应 commands”的表述。Skills 表只保留非官方 `openspec-update-change-from-code`，官方命令以“由 OpenSpec 生成”说明，不逐项声称由本仓维护。

- [ ] **Step 2: 重写 schema 能力说明**

README 中 `evidence-driven` 只描述：

- 官方 proposal/spec/design/tasks 语义的中文派生；
- verification 计划与结果；
- apply 依赖 verification；
- schema-only 不扩展官方 verify/archive。

删除独立验证门禁、自动派发、Code Review、finishing，以及旧的“为保护本地定制而
禁止 `openspec update`”警告。必须保留新的所有权边界：`ai-tools` 仓库自身不运行
`openspec init` 或 `openspec update` 生成官方文件；目标项目可以运行官方初始化和
更新命令。

- [ ] **Step 3: 精简工作流文档**

`docs/ai-sdd-workflow.md` 保留：

- 官方命令的场景选择；
- schema 制品图；
- `skip_specs`、嵌套 capability path、Purpose、完整 MODIFIED requirement；
- apply 记录 verification 真实结果；
- from-code 独立旁路说明；
- 官方初始化、已初始化目标项目的 CLI `openspec update` 升级路径、状态与校验命令；
- 所有操作目标项目的执行块显式包含 `cd "$TARGET_PROJECT"`；
- 中文 rule 的可选源/目标复制命令；
- `ai-tools` 仓库自身不运行 init/update、目标项目可以运行官方命令的所有权边界。

删除：

- apply 自动 Task 派发 verify；
- 独立 Agent 持久化结论；
- CRITICAL/WARNING/SUGGESTION 本地门禁；
- archive 不可确认覆盖；
- 本地 sync/archive 实现细节；
- 所有 Superpowers 挂点。

verify/archive 章节必须明确“具体行为以当前 OpenSpec 官方生成物为准”。

- [ ] **Step 4: 静态检查文档**

运行：

```bash
rg -n 'openspec init --tools cursor|openspec update|schema validate evidence-driven|cd "\$TARGET_PROJECT"|openspec-chinese\.mdc' \
  README.md docs/ai-sdd-workflow.md
if rg -n '自动派发|独立 Agent|归档硬门禁|Finishing|Superpowers' README.md docs/ai-sdd-workflow.md; then
  exit 1
fi
```

预期：初始化、升级、显式目标目录、中文 rule 复制与校验文案存在；禁止内容无匹配。

- [ ] **Step 5: 暂不提交**

保留工作区修改，等待用户明确要求后再 commit。

### Task 4: 执行最终规格覆盖检查

**Files:**
- Verify: `spec/spec-architecture-openspec-workflow-refactor.md`
- Verify: 本计划全部变更路径

**Interfaces:**
- Consumes: Task 1–3 的完整工作区。
- Produces: 对规格 2.0 验收标准的可复核证据。

- [ ] **Step 1: 运行版本与 schema 检查**

运行：

```bash
openspec --version
npm view @fission-ai/openspec version
openspec schema which spec-driven
openspec schema validate evidence-driven
```

预期：两个版本均为 `1.9.0`；schema 来源为 package；validate 成功。

- [ ] **Step 2: 检查 tracked 官方路径**

运行：

```bash
git ls-files '.cursor/skills/openspec-*' '.cursor/commands/opsx-*'
```

预期最终提交后的 tracked 列表只包含：

```text
.cursor/commands/opsx-update-change-from-code.md
.cursor/skills/openspec-update-change-from-code/SKILL.md
```

在提交前，结合 `git status --short` 确认其余 tracked 文件均已标记删除。

- [ ] **Step 3: 检查保留项**

运行：

```bash
test -f .cursor/rules/openspec-chinese.mdc
test -f .cursor/skills/openspec-update-change-from-code/SKILL.md
test -f .cursor/commands/opsx-update-change-from-code.md
test -f docs/graphify-integration.md
```

预期：全部退出码为 0。

- [ ] **Step 4: 检查 schema-only 边界**

运行：

```bash
rg -n 'id: verification|requires: \[verification\]|tracks: tasks.md' \
  openspec/schemas/evidence-driven/schema.yaml
if rg -n 'Superpowers|Task 派发|归档硬门禁|独立验证结论|Finishing' \
  openspec/schemas/evidence-driven README.md docs/ai-sdd-workflow.md; then
  exit 1
fi
```

预期：三个 schema 契约均命中；禁止内容无匹配。

- [ ] **Step 5: 检查工作区与 lint**

运行：

```bash
git status --short
git diff --check
```

并读取编辑文件的 IDE lint。预期：`git diff --check` 退出码为 0，无新增 lint 错误。

- [ ] **Step 6: 对照规格人工复核**

逐项核对规格中的 `AC-OWN-*`、`AC-BASE-*`、`AC-SCH-*`、`AC-VER-*`、`AC-DOC-*` 与 `AC-SCOPE-*`，记录每项对应的命令输出或文件位置。发现缺口时回到对应任务修复，不得以口头说明替代。

- [ ] **Step 7: 停止在提交前**

向用户汇报变更与验证结果；仅当用户明确要求时再执行 git commit。
