# 将 ai-tools 接入目标项目

本文面向**其它业务仓库**：说明如何从「仅有官方 OpenSpec」或「旧版 ai-tools（本地定制 skills/commands）」升级并接入当前 `ai-tools`。

场景化日常用法见 [ai-sdd-workflow.md](./ai-sdd-workflow.md)。Graphify 可选增强见 [graphify-integration.md](./graphify-integration.md)。

## 1. 当前 ai-tools 是什么

当前仓库采用**官方优先（official-first）**分层：

```text
目标项目
├── OpenSpec 官方生成层（openspec init / update 管理）
│   ├── .cursor/skills/openspec-{explore,propose,update-change,apply-change,verify-change,archive-change,sync-specs}/
│   └── .cursor/commands/opsx-{explore,propose,update,apply,verify,archive,sync}.md
│
└── ai-tools 自定义层（从本仓库复制或安装）
    ├── openspec/schemas/evidence-driven/
    ├── openspec/config.yaml 中的 schema: evidence-driven
    ├── .cursor/rules/openspec-chinese.mdc          （可选）
    └── openspec-update-change-from-code             （可选旁路）
```

| 层级 | 谁维护 | 内容 |
|------|--------|------|
| 官方生成层 | OpenSpec CLI | explore / propose / update / apply / verify / archive / sync |
| 自定义层 | ai-tools | `evidence-driven` schema（含 `verification`）、中文规则、from-code 旁路 |

**不要**再把本仓库里的官方 skill/command 副本拷进业务仓覆盖官方文件。本仓库 `.gitignore` 已忽略那 7 组官方路径；业务仓也应让官方层只由 `openspec init` / `openspec update` 更新。

### 1.1 相对纯官方 OpenSpec，你多得到什么

- 默认 schema：`evidence-driven`（官方默认多为 `spec-driven`）。
- 额外制品：`verification.md`（验证计划 + 实现侧真实结果记录，含必做代码审查）。
- 制品依赖：`tasks → verification`，且 `apply` 依赖 `verification`。
- 代码审查在 verification 中必做，由 apply 会话阅读实现 diff 并记账；**不是**官方 archive 条件。
- 可选：简体中文强制规则、`/opsx-update-change-from-code`。

### 1.2 相对旧版 ai-tools，你不再从本仓库获得什么

旧版曾在仓库内跟踪并定制官方 skills/commands（含独立 verify、Code Review 归档硬门禁、apply 自动派发 verify、Superpowers finishing 等）。**当前版本不再分发这些定制**。

接入后：

- verify / archive / sync 的具体行为以目标项目中**当前官方生成物**为准。
- 若业务仍需要旧硬门禁，应另立项目内规则或独立 skill，而不是期待本仓库继续提供分叉模板。

## 2. 前置条件

- Node.js 满足 OpenSpec CLI 要求（官方要求 Node.js ≥ 20.19.0）。
- 支持 [Agent Skills](https://agentskills.io) 的助手（本文以 Cursor 为主）。
- 能在目标项目根目录执行 shell。

建议固定变量：

```bash
AI_TOOLS_DIR="/absolute/path/to/ai-tools"          # 本仓库克隆路径
TARGET_PROJECT="/absolute/path/to/target-project"  # 业务项目根目录
```

也可不克隆本仓库，仅用 GitHub / skills.sh 安装可选 skill；schema 仍需从本仓库（或发布物）复制。

```bash
npm install --global @fission-ai/openspec@latest
openspec --version
# 建议与 npm 最新稳定版一致后再接入
```

## 3. 先判断你属于哪条路径

```text
目标项目里有没有 openspec/ ？
  ├─ 没有 → A. 全新接入（官方 OpenSpec + ai-tools）
  └─ 有
       ├─ 仅有官方 skills/commands，schema 多为 spec-driven
       │     → B. 已有官方 OpenSpec，叠加 ai-tools
       └─ 曾复制旧 ai-tools（本地改过 opsx-* / openspec-* skill）
             → C. 从旧版 ai-tools 迁移到 official-first
```

可用快速探测：

```bash
cd "$TARGET_PROJECT"

# 是否已有 OpenSpec 根
test -f openspec/config.yaml && echo "has-openspec-config" || echo "no-config"

# 当前默认 schema
grep -E '^schema:' openspec/config.yaml 2>/dev/null || true

# 是否像「旧版本地定制」：官方 skill 被 Git 跟踪，或含本仓库旧门禁关键词
git ls-files '.cursor/skills/openspec-apply-change/*' '.cursor/commands/opsx-apply.md' 2>/dev/null
rg -n "独立验证结论|代码审查（归档硬门禁）|Superpowers 对接" \
  .cursor/skills/openspec-apply-change \
  .cursor/commands/opsx-apply.md 2>/dev/null || true
```

- 若官方路径被 Git **跟踪**，或文件中出现上述旧门禁文案 → 走 **路径 C**。
- 若只有 `openspec/` + 未被定制的官方生成物 → 走 **路径 B**。
- 若几乎没有 OpenSpec → 走 **路径 A**。

## 4. 路径 A：全新项目接入

在业务项目根目录：

```bash
cd "$TARGET_PROJECT"

# 1) 生成官方 Cursor skills / commands
openspec init --tools cursor

# 2) 安装 evidence-driven schema
mkdir -p openspec/schemas
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 3) 启用 schema（新建或合并，勿盲目整文件覆盖）
# openspec/config.yaml 至少包含：
#   schema: evidence-driven

# 4) 校验
openspec schema validate evidence-driven
```

可选：

```bash
# 中文规则
mkdir -p .cursor/rules
cp \
  "$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc" \
  .cursor/rules/openspec-chinese.mdc

# from-code 旁路
npx skills add youpinyao/ai-tools --skill openspec-update-change-from-code
```

建议在目标项目 `.gitignore` 中**不要**忽略官方 skills（它们通常需要提交给团队共用）；本 `ai-tools` 仓库自身忽略它们，是因为工具包仓库不负责分发官方副本。业务仓按团队惯例选择是否提交官方生成物即可。

## 5. 路径 B：已有官方 OpenSpec，叠加 ai-tools

适用于：项目已 `openspec init`，默认 `spec-driven`，未深度分叉官方 skill。

```bash
cd "$TARGET_PROJECT"

# 1) 先把官方生成物升到当前 CLI 对应版本
npm install --global @fission-ai/openspec@latest
openspec update

# 2) 安装 / 覆盖自定义 schema（只覆盖 evidence-driven 目录）
mkdir -p openspec/schemas
rm -rf openspec/schemas/evidence-driven
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 3) 合并配置：只改 schema 字段，保留 context / rules / operations 等项目配置
# schema: evidence-driven

# 4) 校验
openspec schema validate evidence-driven
```

### 5.1 已有 active change 怎么办

| 情况 | 建议 |
|------|------|
| change 使用 `spec-driven`，且仍在规划/实现中 | 可继续用原 schema 做完并归档；新 change 再改用 `evidence-driven` |
| 希望中途切到 `evidence-driven` | 需补齐 `verification.md`，并确认 `.openspec.yaml` 的 `schema:`；有行为变化时再改 tasks/specs |
| 纯重构/文档、无规范层变化 | 可设 `skip_specs: true`，仍建议有 `verification` 计划 |

切换默认 schema **不会**自动改写历史 archived changes；只影响之后 `openspec new change` 的默认 schema（除非命令显式传 `--schema`）。

### 5.2 从 `spec-driven` 迁到 `evidence-driven` 的制品差异

```text
spec-driven:   proposal → specs/design → tasks → apply
evidence-driven: proposal → specs/design → tasks → verification → apply
```

官方 apply/verify/archive **不会**被本仓库改写；`verification` 的约束主要通过 schema 的 `apply.requires` 与模板指导进入工作流。apply 阶段应按模板执行适用检查（含必做代码审查）并记录真实结果。

## 6. 路径 C：从旧版 ai-tools 迁移

旧版特征通常包括：

- Git 跟踪了 `openspec-explore` … `openspec-sync-specs` 与对应 `opsx-*.md`；
- skill/command 内含「独立验证结论」「代码审查（归档硬门禁）」「Superpowers 对接」等本地段落；
- 可能还有本仓独有的 `openspec-update-change-from-code`（应保留）。

### 6.1 迁移原则

1. **官方层归还官方**：删除本地分叉的官方 skill/command，再用 `openspec update`（或 `init`）重新生成。
2. **自定义层只留 ai-tools 明确分发的内容**：`evidence-driven`、中文规则、from-code。
3. **不要**把旧分叉文件「合并进」新官方模板；旧门禁若仍需要，迁到项目自有 rule/skill，与官方路径解耦。
4. **先备份再删**：至少保留分支或补丁，便于对照旧门禁文案。

### 6.2 推荐步骤

```bash
cd "$TARGET_PROJECT"
git checkout -b chore/migrate-to-ai-tools-official-first

# 0) 备份旧定制（可选但强烈建议）
mkdir -p /tmp/ai-tools-legacy-backup
cp -R .cursor/skills/openspec-apply-change /tmp/ai-tools-legacy-backup/ 2>/dev/null || true
cp .cursor/commands/opsx-apply.md /tmp/ai-tools-legacy-backup/ 2>/dev/null || true

# 1) 从版本控制中移除旧官方副本（路径按仓库实际调整）
git rm -r --ignore-unmatch \
  .cursor/skills/openspec-explore \
  .cursor/skills/openspec-propose \
  .cursor/skills/openspec-update-change \
  .cursor/skills/openspec-apply-change \
  .cursor/skills/openspec-verify-change \
  .cursor/skills/openspec-archive-change \
  .cursor/skills/openspec-sync-specs
git rm --ignore-unmatch \
  .cursor/commands/opsx-explore.md \
  .cursor/commands/opsx-propose.md \
  .cursor/commands/opsx-update.md \
  .cursor/commands/opsx-apply.md \
  .cursor/commands/opsx-verify.md \
  .cursor/commands/opsx-archive.md \
  .cursor/commands/opsx-sync.md

# 2) 升级 CLI 并重新生成官方层
npm install --global @fission-ai/openspec@latest
openspec update
# 若项目尚不完整，可用：openspec init --tools cursor

# 3) 刷新自定义 schema
mkdir -p openspec/schemas
rm -rf openspec/schemas/evidence-driven
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  openspec/schemas/

# 4) 确认 config
# schema: evidence-driven

# 5) 保留 / 重装旁路与中文规则（若仍需要）
mkdir -p .cursor/rules
cp \
  "$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc" \
  .cursor/rules/openspec-chinese.mdc
# from-code：若目录仍在可保留；否则
# npx skills add youpinyao/ai-tools --skill openspec-update-change-from-code

# 6) 校验
openspec schema validate evidence-driven
openspec list --json
```

### 6.3 迁移后行为变化清单（给团队的预期管理）

| 旧版 ai-tools 常见行为 | 迁移后 |
|------------------------|--------|
| apply 结束后强制独立子 Agent verify | 不再由本仓库保证；遵循官方 apply/verify |
| archive 要求 `验证结论：通过` 且不可确认绕过 | 不再由本仓库保证；遵循官方 archive |
| Code Review 作为归档硬门禁 | 不再由本仓库保证 |
| 代码审查作为 verification 必做检查 | **保留**（schema 层，apply 记账；非 archive 条件） |
| Superpowers brainstorming / finishing 写死在 skill | 不再由本仓库保证 |
| `verification.md` 制品 | **保留**（schema 层） |
| 中文规则、from-code | **可保留** |

若业务必须保留旧硬门禁，迁移完成后单独开 change，用项目自有 rule/skill 重新表达，避免再次分叉官方生成路径。

### 6.4 正在进行中的 change

1. 迁移前用旧流程尽量完成或归档关键 change，成本最低。
2. 若必须带着 active change 迁移：
   - 保留 change 目录与 `.openspec.yaml`；
   - 刷新 schema 后运行 `openspec status --change "<name>" --json` 与 `openspec validate "<name>" --type change --strict`；
   - 缺 `verification.md` 时按新模板补齐（规划阶段结果保持「待执行」，须含代码审查章节）；
   - 旧 verification 中「独立验证结论 / 代码审查硬门禁」章节可保留为项目约定，但**官方 archive 不一定再强制它们**；代码审查应改记为 verification 必做检查。

## 7. 日常升级（接入之后）

### 7.1 升级 OpenSpec 官方层

```bash
cd "$TARGET_PROJECT"
npm install --global @fission-ai/openspec@latest
openspec update
openspec schema validate evidence-driven
```

`openspec update` 可能刷新官方 skills/commands。只要没有再次手工改这些文件，升级通常是安全的。

### 7.2 升级 ai-tools 自定义层

```bash
# 拉取最新 ai-tools 后
rm -rf "$TARGET_PROJECT/openspec/schemas/evidence-driven"
cp -R \
  "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" \
  "$TARGET_PROJECT/openspec/schemas/"

# 按需更新中文规则、from-code skill
cp \
  "$AI_TOOLS_DIR/.cursor/rules/openspec-chinese.mdc" \
  "$TARGET_PROJECT/.cursor/rules/openspec-chinese.mdc"

cd "$TARGET_PROJECT"
openspec schema validate evidence-driven
```

**禁止**用本仓库完整 `openspec/config.yaml` 覆盖目标配置；只合并 `schema: evidence-driven`。

### 7.3 本仓库（ai-tools）自身注意事项

- 不要在 `ai-tools` 仓库根目录对官方路径跑 `openspec init` / `openspec update` 并提交生成物。
- 官方模板对照应在临时目录完成，再手工同步到 `evidence-driven`。

## 8. 验收清单

接入或迁移完成后，在目标项目确认：

- [ ] `openspec --version` 为团队约定的最新稳定版。
- [ ] 存在官方 `/opsx-propose`、`/opsx-apply` 等（Cursor 重启后可见）。
- [ ] `openspec/schemas/evidence-driven/schema.yaml` 存在。
- [ ] `openspec/config.yaml` 含 `schema: evidence-driven`，且项目原有 context/rules 未丢。
- [ ] `openspec schema validate evidence-driven` 通过。
- [ ] 旧分叉官方 skill/command 已从 Git 跟踪中移除（路径 C）。
- [ ] 仍需要时：中文规则、`openspec-update-change-from-code` 可用。
- [ ] 试跑：`/opsx-propose` 小 change，确认生成 `verification.md`，且 apply 前依赖满足。

冒烟命令示例：

```bash
cd "$TARGET_PROJECT"
openspec schema validate evidence-driven
openspec new change "smoke-ai-tools-integration" --schema evidence-driven
openspec status --change "smoke-ai-tools-integration"
# 验证完毕后可删除该 smoke change 目录，勿归档到生产规格
```

## 9. 常见问题

### 为什么 README 说「不要从 ai-tools 复制官方 templates」？

因为官方层应以 CLI 生成物为准。复制会导致版本漂移，下一次 `openspec update` 也会冲突。`ai-tools` 只保证自定义 schema 目录可复制。

### 接入后官方 verify 变「弱」了？

若你来自旧版硬门禁 ai-tools，这是预期差异。当前产品边界是 schema-only；更严的独立验证需项目自行加层。

### `openspec update` 会不会删掉 `evidence-driven`？

一般不会删除 `openspec/schemas/` 下的自定义 schema。但升级后仍应再跑 `openspec schema validate evidence-driven`，并确认 `config.yaml` 的 `schema:` 未被改回 `spec-driven`。

### 可以继续用 `spec-driven` 吗？

可以。不改 `config.yaml` 即保持官方默认。只有需要 `verification` 制品与 apply 前置依赖时，才切换到 `evidence-driven`。

### from-code 与官方 sync 有何区别？

| 命令 | 真源 | 写入范围 |
|------|------|----------|
| `/opsx-update-change-from-code` | 已实现代码 + 用户决策 | active change（及允许的相关文档），**不改** main specs |
| 官方 `/opsx-sync` | change 内 delta specs | main specs |

## 10. 相关文档

- 安装与仓库边界：[README.md](../README.md)
- 场景化工作流：[ai-sdd-workflow.md](./ai-sdd-workflow.md)
- Graphify 可选增强：[graphify-integration.md](./graphify-integration.md)
- 架构规格（官方优先）：[../spec/spec-architecture-openspec-workflow-refactor.md](../spec/spec-architecture-openspec-workflow-refactor.md)
- OpenSpec 上游：https://github.com/Fission-AI/OpenSpec
