# OpenSpec 可重复升级实施计划

> **执行要求：** 逐项执行本计划。每次执行前复制本计划作为当次运行记录，只在副本中勾选任务，不要修改本计划模板的复选框。OpenSpec 相关对话、制品与总结必须使用简体中文。

**目标：** 在每次执行时，将 OpenSpec CLI 从当前已安装版本升级到指定目标版本（默认取 npm 发布的最新稳定版），使 `evidence-driven` 与目标版本官方 `spec-driven` 重新对齐，并验证本仓库扩展和目标项目仍可正常工作。

**方案：** 先记录源版本并解析 npm 最新稳定版，再从新 CLI 动态取得官方 schema 和 Cursor 生成物作为唯一基线。官方派生部分从新基线重建，只保留项目允许的自定义差异；随后验证 CLI JSON 契约、文档、目标项目更新流程和回滚路径。

**技术栈：** Node.js/npm、`@fission-ai/openspec` CLI、YAML、Markdown、Agent Skills、Git、`jq`、`rg`

## 全局约束

- 本文件是可重复执行的计划模板，不记录某次运行的完成状态或结论。
- 源版本取执行时 `openspec --version`；目标版本由执行者指定，未指定时才查询 npm，并固定精确版本。
- `ai-tools` 根目录不得执行 `openspec init` 或 `openspec update`；官方生成物对照必须在临时目录完成。
- 不得从目标项目反向复制官方生成物，也不得恢复 Cursor 专属 OpenSpec 副本。
- 官方 `spec-driven` 语义优先；本地只保留中文化、`evidence-driven`、`verification`、验证门禁和 from-code 等批准差异。
- 当前版本不再提供旧 worktree 增强；目标项目升级时必须确定性移除 `AI_TOOLS_PROPOSE_WORKTREE_V1`、`AI_TOOLS_WORKTREE_FINISH_V1` 与 `AI_TOOLS_VERIFY_GATE_NO_FINISH_ASK_V1`，不得让结果取决于生成器是否保留追加正文。
- 已有配置只合并 `schema`、`AGENTS.md` 的对话规则标记块与 `config.yaml` 的制品规则标记块；不覆盖无关设置或工作区修改。
- 不自动创建 commit。

## 每次运行的输入与记录

执行前设置：

```bash
AI_TOOLS_DIR="$(git rev-parse --show-toplevel)"
SOURCE_VERSION="$(openspec --version)"
TARGET_VERSION="${TARGET_VERSION:-$(npm view @fission-ai/openspec version)}"
VERSION_RE='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$'
[[ "$SOURCE_VERSION" =~ $VERSION_RE ]]
[[ "$TARGET_VERSION" =~ $VERSION_RE ]]
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-${SOURCE_VERSION}-to-${TARGET_VERSION}"
UPGRADE_TMP="$(mktemp -d "${TMPDIR:-/tmp}/ai-tools-openspec-upgrade.${RUN_ID}.XXXXXX")"
RUN_LOG_ROOT="${RUN_LOG_ROOT:-${XDG_STATE_HOME:-$HOME/.local/state}/ai-tools/openspec-upgrades}"
RUN_DIR="$RUN_LOG_ROOT/$RUN_ID"
RUN_LOG="$RUN_DIR/run.md"
RUN_CHECKLIST="$RUN_DIR/checklist.md"
mkdir -p "$RUN_DIR"
cp "$AI_TOOLS_DIR/.agents/skills/upgrading-openspec/reference.md" "$RUN_CHECKLIST"
export AI_TOOLS_DIR SOURCE_VERSION TARGET_VERSION RUN_ID UPGRADE_TMP
export RUN_LOG_ROOT RUN_DIR RUN_LOG RUN_CHECKLIST
printf '# OpenSpec 升级运行记录\n\n- run: `%s`\n- source: `%s`\n- target: `%s`\n- temp: `%s`\n' \
  "$RUN_ID" "$SOURCE_VERSION" "$TARGET_VERSION" "$UPGRADE_TMP" > "$RUN_LOG"
```

要求：

- `SOURCE_VERSION`、`TARGET_VERSION` 必须是非空语义版本，且本次运行后不再重新解析。
- 若两者相同，本次运行定义为兼容性复核，不得声称发生了版本升级。
- 每一步都把关键命令、退出码和结论追加到 `$RUN_LOG`，并只在 `$RUN_CHECKLIST` 中勾选任务。
- `$RUN_DIR` 是仓库外的持久运行记录，不随临时目录清理；成功或失败后都必须保留。`$UPGRADE_TMP` 中的临时样本可在证据汇总完成后删除。

---

## 1. 建立升级基线与隔离环境

**文件：**
- 读取：`README.md`
- 读取：`spec/spec-architecture-openspec-workflow-refactor.md`
- 读取：`openspec/schemas/evidence-driven/schema.yaml`
- 读取：`openspec/schemas/evidence-driven/templates/*.md`
- 读取：`.agents/skills/openspec-update-change-from-code/SKILL.md`

- [ ] **1.1 确认工作区和执行边界**

运行：

```bash
git status --short
git branch --show-current
```

预期：记录当前分支和已有修改；升级不得覆盖或混入无关变更。工作区不干净时暂停并让用户选择处理方式。

- [ ] **1.2 固定源版本与目标版本**

运行：

```bash
printf 'source=%s\ntarget=%s\n' "$SOURCE_VERSION" "$TARGET_VERSION"
test -n "$SOURCE_VERSION"
test -n "$TARGET_VERSION"
```

预期：两个变量均为非空语义版本。若版本相同，仍可继续执行兼容性复核，但不得声称发生了版本升级。

- [ ] **1.3 建立仓库外的临时对照目录**

运行：

```bash
printf '%s\n' "$UPGRADE_TMP"
test "${UPGRADE_TMP#"$AI_TOOLS_DIR"/}" = "$UPGRADE_TMP"
```

预期：目录位于仓库外，后续官方 schema 和生成物都保存在该目录。

- [ ] **1.4 记录旧 CLI 可见的官方基线位置**

运行：

```bash
SOURCE_SCHEMA_DIR="$(openspec schema which spec-driven)"
printf '%s\n' "$SOURCE_SCHEMA_DIR"
cp -R "$SOURCE_SCHEMA_DIR" "$UPGRADE_TMP/source-spec-driven-$SOURCE_VERSION"
```

预期：旧版官方 `schema.yaml` 和 `templates/` 已复制到临时目录，用于区分上游变化与本地定制。

## 2. 安装精确目标版本并采集新版官方基线

**文件：**
- 临时读取：`$UPGRADE_TMP/source-spec-driven-$SOURCE_VERSION/`
- 临时创建：`$UPGRADE_TMP/target-spec-driven-$TARGET_VERSION/`
- 临时创建：`$UPGRADE_TMP/tools-generated-$TARGET_VERSION/`

- [ ] **2.1 安装已固定的精确目标版本**

运行：

```bash
npm install --global "@fission-ai/openspec@$TARGET_VERSION"
test "$(openspec --version)" = "$TARGET_VERSION"
```

预期：安装成功，版本断言退出码为 0。

- [ ] **2.2 复制新版官方 `spec-driven` 基线**

运行：

```bash
TARGET_SCHEMA_DIR="$(openspec schema which spec-driven)"
printf '%s\n' "$TARGET_SCHEMA_DIR"
cp -R "$TARGET_SCHEMA_DIR" "$UPGRADE_TMP/target-spec-driven-$TARGET_VERSION"
```

预期：新版目录包含 `schema.yaml` 和官方模板；该目录是本次升级的唯一上游语义来源。

- [ ] **2.3 生成新版共享 Skill 样本**

运行：

```bash
mkdir -p "$UPGRADE_TMP/tools-generated-$TARGET_VERSION"
cd "$UPGRADE_TMP/tools-generated-$TARGET_VERSION"
openspec init --tools codex
```

预期：初始化成功，只记录 `.agents/skills/openspec-*` 路径；不得生成 Cursor command 或重复 skill。

- [ ] **2.4 比较新旧官方基线**

运行：

```bash
diff -ru \
  "$UPGRADE_TMP/source-spec-driven-$SOURCE_VERSION" \
  "$UPGRADE_TMP/target-spec-driven-$TARGET_VERSION" \
  > "$UPGRADE_TMP/spec-driven-upstream.diff" || test "$?" -eq 1
```

预期：无差异时 diff 文件为空；有差异时退出码 1 被接受，并逐项分类为 schema 格式、制品依赖、模板结构、校验规则或 instruction 语义变化。

## 3. 重建 `evidence-driven` 官方派生部分

**文件：**
- 修改：`openspec/schemas/evidence-driven/schema.yaml`
- 修改：`openspec/schemas/evidence-driven/templates/proposal.md`
- 修改：`openspec/schemas/evidence-driven/templates/spec.md`
- 修改：`openspec/schemas/evidence-driven/templates/design.md`
- 修改：`openspec/schemas/evidence-driven/templates/tasks.md`
- 检查或修改：`openspec/schemas/evidence-driven/templates/verification.md`
- 检查：`openspec/config.yaml`

- [ ] **3.1 对照新版 artifact 图和 schema 格式**

逐项比较新版官方 `schema.yaml` 与本地 `schema.yaml`。将 proposal、specs、design、tasks 及 apply 的新版结构和行为同步到本地，不复制旧版已经删除的字段。

预期保留的本地契约：

```yaml
name: evidence-driven
artifacts:
  # proposal、specs、design、tasks：新版官方语义的简体中文派生
  - id: verification
    generates: verification.md
    template: verification.md
    requires:
      - tasks
apply:
  requires: [verification]
  tracks: tasks.md
```

- [ ] **3.2 从新版模板重建四个官方派生模板**

以新版官方 `proposal.md`、`spec.md`、`design.md`、`tasks.md` 为源逐个重建中文版本。保持标题级别、关键字、路径格式、复选框和解析敏感标记不变，只翻译面向使用者的正文。

预期：每一处相对新版官方模板的行为差异都能归入以下白名单：

1. 简体中文化；
2. schema 名称和描述改为 `evidence-driven`；
3. 新增 `verification`；
4. apply 前置改为 `verification`；
5. apply 执行并如实记录验证；
6. verification 中代码审查为必做检查，但不虚构官方 archive 能力。

- [ ] **3.3 复核新版校验和归档语义**

重点检查新版是否改变：

- `skip_specs`
- `retire_capabilities`
- `<capability-path>` 与嵌套目录
- 新增 capability 的 `## Purpose`
- `MODIFIED Requirements` 完整块要求
- `#### Scenario` 标题层级
- tasks 的 `- [ ]` 跟踪格式

预期：只保留新版本实际支持的行为；删除失效说明，新增上游要求必须同步到中文 instruction 和模板。

- [ ] **3.4 适配 `verification` 与 apply instruction**

若新版 schema 格式、artifact 依赖或 apply instruction 结构变化，按新版格式迁移 `verification`，同时保留：

- 规划阶段不得预填成功；
- 命令必须来自真实仓库配置；
- 代码审查必须读取明确范围的完整 diff；
- 未处理的 Critical 或 Important 不得记为通过；
- 失败、不适用和未执行项必须记录原因与剩余风险；
- `verification.md` 只保留“范围、检查、代码审查、风险与回滚”四个二级章节，
  总行数不超过 30 行；复验更新原检查行，不追加完整历史。

预期：不增加新版 OpenSpec 无法强制执行的声明。

- [ ] **3.5 校验 schema 配置**

运行：

```bash
test "$(awk '/^schema:/ {print $2}' openspec/config.yaml)" = "evidence-driven"
openspec schema validate evidence-driven
```

预期：两个命令退出码均为 0。

## 4. 验证 CLI 命令和 JSON 契约

**文件：**
- 检查或修改：`.agents/skills/openspec-update-change-from-code/SKILL.md`

- [ ] **4.1 在临时项目创建 `evidence-driven` 冒烟 change**

将本仓库 `openspec/schemas/evidence-driven/` 和规范配置复制到临时项目，然后运行：

```bash
cd "$UPGRADE_TMP/tools-generated-$TARGET_VERSION"
mkdir -p openspec/schemas
cp -R "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" openspec/schemas/
cp "$AI_TOOLS_DIR/openspec/config.yaml" openspec/config.yaml
openspec schema validate evidence-driven
openspec new change "upgrade-contract-smoke" --schema evidence-driven
openspec instructions proposal --change "upgrade-contract-smoke" --json |
  jq -e '.context | contains("AI_TOOLS_OPENSPEC_CHINESE_V1_START")'
```

预期：schema 校验和 change 创建均成功。执行前必须设置 `AI_TOOLS_DIR` 为本仓库绝对路径。

- [ ] **4.2 验证 from-code 依赖的命令仍存在**

运行：

```bash
openspec store list --json
openspec list --json
openspec list --specs --json
openspec status --change "upgrade-contract-smoke" --json
openspec context --json
openspec validate "upgrade-contract-smoke" --type change --strict --json
openspec validate --specs --strict --json
```

```bash
openspec list --specs --json | jq -e 'has("specs") and has("root") and (.root | has("path"))'
openspec context --json | jq -e '.root | has("path")'
```

若临时项目里已有样例 spec，再跑 skill 实际使用的那条（把 `<spec-id>` 换成列出的 `id`）：

```bash
openspec validate "<spec-id>" --type spec --strict --json
```

预期：命令可执行；change 严格校验可因尚未填写制品而失败，但必须仍支持 `--json` 并返回可解释的结构化结果。`list --specs --json` 顶层含 `specs` 与带 `path` 的 `root`；无 spec 时 `specs` 可为 `[]`。有样例 spec 时，每项含 `id`，且 `--type spec` 可解析。

- [ ] **4.3 核对 `status --json` 字段**

运行并检查：

```bash
openspec status --change "upgrade-contract-smoke" --json |
  jq -e '
    has("changeRoot") and
    has("artifactPaths") and
    has("actionContext") and
    has("schemaName")
  '
```

预期：断言通过。若字段改名、嵌套或含义变化，更新 from-code skill 的读取方式、路径边界和错误处理，再用实际 JSON 重跑断言；不得用猜测补写字段。

- [ ] **4.4 验证 archive 定位假设**

检查 `openspec context --json` 的 root/store 结构，以及新版归档目录是否仍为 `openspec/changes/archive/`。

预期：若目录或 context 字段变化，同步更新 from-code skill 中 archived change 的定位说明。

## 5. 核对共享官方 Skill 和本地追加规则

**文件：**
- 检查或修改：`.gitignore`
- 检查或修改：`AGENTS.md`
- 检查或修改：`openspec/config.yaml`
- 检查或修改：`.agents/skills/integrating-ai-tools/reference.md`

- [ ] **5.1 比较新版生成的共享 Skill 清单**

运行：

```bash
cd "$UPGRADE_TMP/tools-generated-$TARGET_VERSION"
printf '%s\n' \
  .agents/skills/openspec-* .agents/skills/.openspec-target

# 5.1 注入目标必须存在（explore/propose/update 不注入）
for file in \
  .agents/skills/openspec-{apply-change,verify-change,sync-specs,archive-change}/SKILL.md
do
  test -f "$file" || { echo "missing injection target: $file" >&2; exit 1; }
done
```

预期：得到新版实际文件清单，且上述 4 个注入目标都存在。若官方新增、删除或重命名路径，精确更新 `.gitignore` 与 `.agents/skills/integrating-ai-tools/reference.md` 5.1 检查器；不得忽略本仓库唯一的 `.agents/skills/openspec-update-change-from-code/`。

- [ ] **5.2 核对中文规则覆盖范围**

确认 `AGENTS.md` 的对话级规则覆盖所有 OpenSpec 相关交互；再比较
`openspec/config.yaml` 的制品级规则与新版 artifact 清单，确认正文、状态及机器敏感结构均有明确约束。

预期：对话规则不依赖逐项枚举入口，制品规则覆盖新版 artifact；两层规则同时适用于官方共享 skills 与共用 `openspec-update-change-from-code` skill。

- [ ] **5.3 复核 `AI_TOOLS_VERIFY_GATE_V2` 追加点**

阅读新版 apply、verify、sync、archive skills，确认 A/B/C 块仍有有效插入点且不与官方行为冲突。apply 块必须包含 `AI_TOOLS_DIRECT_APPLY_V1` 与 `AI_TOOLS_APPLY_SKILL_RULE_DISCOVERY_V1`，verify 块必须包含 `AI_TOOLS_DIRECT_VERIFY_V1`；当前 Agent 须串行执行对应阶段，并在 apply 开始实现前按 description/适用范围发现匹配的 skill 与 rule。旧 V1 块标为 `STALE` 并由唯一 V2 完整块替换，不得重复追加。V1-only active change 必须先执行一次 verify，再生成新的结果块。

## 6. 同步当前维护文档

**文件：**
- 修改：`README.md`
- 修改：`docs/ai-sdd-workflow.md`
- 修改：`.agents/skills/integrating-ai-tools/reference.md`
- 按需修改：`spec/spec-architecture-openspec-workflow-refactor.md`（文件存在且属于当前维护范围时）
- 按需修改：`.agents/skills/integrating-graphify/reference.md`

- [ ] **6.1 更新当前基线版本和官方语义说明**

将当前维护文档中的源版本更新为本次 `TARGET_VERSION`，并按目标版本真实行为修订相关章节。搜索范围和替换内容必须由 `$SOURCE_VERSION` 动态确定；历史日期计划保留原版本记录，不把历史事实改写成新版本。

- [ ] **6.2 统一安装命令的可复现策略**

升级实施记录使用：

```bash
npm install --global "@fission-ai/openspec@$TARGET_VERSION"
test "$(openspec --version)" = "$TARGET_VERSION"
```

面向普通使用者的文档可以保留 `@latest` 快捷安装，但必须紧邻版本核对命令，并说明团队执行升级时应记录和固定解析出的精确版本。

- [ ] **6.3 更新工作流命令和目录说明**

以新版 CLI help、官方 schema 和临时生成物为证据更新 init/update、propose/apply/verify/sync/archive、schema validate 和 JSON 示例。删除新版不再支持的参数或行为。

- [ ] **6.4 同步验证门禁语言**

当前维护文档必须统一说明 sync/archive 只检查状态为通过、阻塞项为无。搜索
`README.md`、`docs/ai-sdd-workflow.md`、`.agents/skills/integrating-ai-tools/reference.md` 与本计划，
不得残留旧版 Verify 门禁标记或已删除的变化复核表述。历史记录允许保留当时的 V1
事实，不做批量改写。

- [ ] **6.5 更新架构规格验收基线**

若架构规格存在且属于当前维护范围，更新其验收基线；若不存在，搜索已跟踪路径确认无等价规格，并将缺口记入当次 `$RUN_LOG`，不得在计划模板中写入某次运行的检查结论。

## 7. 本仓库完整验证

**文件：**
- 验证：本计划列出的全部修改文件

- [ ] **7.1 运行版本与 schema 校验**

```bash
test "$(openspec --version)" = "$TARGET_VERSION"
openspec schema which spec-driven
openspec schema validate evidence-driven
```

预期：版本断言和 schema 校验退出码为 0，schema 路径来自目标版本安装包。

- [ ] **7.2 运行静态契约检查**

```bash
rg -n 'id: verification|requires: \[verification\]|tracks: tasks\.md' \
  openspec/schemas/evidence-driven/schema.yaml
python3 -m unittest tests.test_openspec_verification_contract -v
python3 -m unittest tests.test_openspec_verification_state_gate -v
python3 - <<'PY'
from pathlib import Path

text = Path("openspec/schemas/evidence-driven/templates/verification.md").read_text()
headings = [line for line in text.splitlines() if line.startswith("## ")]
expected = ["## 范围", "## 检查", "## 代码审查", "## 风险与回滚"]
if headings != expected:
    raise SystemExit("verification.md headings must be exactly: {}".format(expected))
if len(text.splitlines()) > 30:
    raise SystemExit("verification.md must not exceed 30 lines")
PY
if [ "$SOURCE_VERSION" != "$TARGET_VERSION" ]; then
  if rg -n -F "OpenSpec $SOURCE_VERSION" \
    README.md docs/ai-sdd-workflow.md .agents/skills/integrating-ai-tools/reference.md; then
    echo "错误：当前维护文档仍包含源版本 $SOURCE_VERSION" >&2
    exit 1
  else
    status=$?
    test "$status" -eq 1
  fi
else
  rg -n -F "OpenSpec $SOURCE_VERSION" \
    README.md docs/ai-sdd-workflow.md .agents/skills/integrating-ai-tools/reference.md
fi
```

预期：schema 与契约测试全部通过；紧凑模板严格为四个章节且不超过
30 行；当前维护文档无旧版 Verify 门禁标记或已删除的变化复核表述。若 `SOURCE_VERSION` 与
`TARGET_VERSION` 不同，最后一组在当前维护文档中无命中；若版本相同，则人工核对
命中上下文是否准确。

- [ ] **7.3 验证官方生成物所有权边界**

```bash
git ls-files '.cursor/skills/openspec-*' '.cursor/commands/opsx-*' \
  '.agents/skills/openspec-*'
git check-ignore .agents/skills/openspec-apply-change/SKILL.md
test -f .agents/skills/openspec-update-change-from-code/SKILL.md
test -f AGENTS.md
grep -q 'AI_TOOLS_OPENSPEC_CONVERSATION_CHINESE_V1_START' AGENTS.md
test -f openspec/config.yaml
grep -q 'AI_TOOLS_OPENSPEC_CHINESE_V1_START' openspec/config.yaml
test ! -e .cursor/commands/opsx-update-change-from-code.md
test ! -e .cursor/rules/openspec-chinese.mdc
test ! -e .cursor/skills/openspec-update-change-from-code
if git check-ignore -q .agents/skills/openspec-update-change-from-code/SKILL.md; then
  echo "错误：from-code skill 不应被忽略" >&2
  exit 1
fi
```

预期：不存在 OpenSpec Cursor command/skill；`git ls-files` 只包含 `.agents/skills/` 下的共用 from-code skill，官方生成 skills 被忽略。

- [ ] **7.4 人工执行差异审查**

审查三个差异集合：

1. 旧官方基线与新官方基线；
2. 新官方 `spec-driven` 与升级后 `evidence-driven`；
3. 本次 Git 完整 diff。

预期：第二组差异全部属于批准白名单；第三组不包含临时生成物、无关改动或未经解释的行为变化。未处理的 Critical 或 Important 发现项必须修复后重审。

## 8. 目标项目升级与冒烟验证

**文件：**
- 目标项目官方生成物：由 `openspec update` 刷新已配置工具；统一再跑 `openspec init --tools codex`
- 目标项目自定义 schema：`openspec/schemas/evidence-driven/`
- 目标项目配置：`openspec/config.yaml`
- 目标项目验证门禁文件：以新版实际生成清单和 `.agents/skills/integrating-ai-tools/reference.md` 为准

- [ ] **8.1 选择一个可回滚的代表性目标项目**

确认目标项目工作区干净或已隔离，并记录其升级前 OpenSpec 版本、官方生成物和自定义追加块状态。不得直接在有未提交业务改动的目录执行升级。

- [ ] **8.2 刷新目标项目官方层**

在目标项目运行：

```bash
openspec --version
openspec update
# 旧 worktree 增强没有可靠的结束边界，不能安全地原位裁剪。删除承载它们的
# 官方 skills 后再重建；只删除当前明确的官方目标，不删除自定义 from-code skill。
# AI_TOOLS_REMOVE_LEGACY_WORKTREE_SKILLS_V1_START
for skill_name in \
  openspec-propose \
  openspec-apply-change \
  openspec-verify-change \
  openspec-sync-specs \
  openspec-archive-change
do
  rm -rf -- "$TARGET_PROJECT/.agents/skills/$skill_name"
done
# AI_TOOLS_REMOVE_LEGACY_WORKTREE_SKILLS_V1_END
# 用 codex 重建唯一共享 Skill 层并清理 Cursor OpenSpec 生成物
openspec init --tools codex
rm -rf "$TARGET_PROJECT/.cursor/commands/opsx-"*
rm -rf "$TARGET_PROJECT/.cursor/skills/openspec-"*

LEGACY_WORKTREE_PATTERN='AI_TOOLS_(PROPOSE_WORKTREE|WORKTREE_FINISH|VERIFY_GATE_NO_FINISH_ASK)'
for file in \
  .agents/skills/openspec-{propose,apply-change,verify-change,sync-specs,archive-change}/SKILL.md
do
  test -f "$file" || continue
  if rg -q "$LEGACY_WORKTREE_PATTERN" "$file"; then
    echo "仍有旧 worktree 增强：$file" >&2
    exit 1
  fi
done
```

预期：官方生成物与目标 CLI 版本一致；`.agents/skills/openspec-*` 是唯一 Skill 源，OpenSpec Cursor command/skill 不存在，旧 worktree 增强不再残留。

- [ ] **8.3 安装升级后的自定义层**

只覆盖目标项目的 `openspec/schemas/evidence-driven/`，合并 `openspec/config.yaml`
中的 `schema: evidence-driven`，再按更新后的接入文档补齐缺失的规则。先运行接入文档
5.1 节检查器；对所有 `STALE` 文件，用对应 A/B/C 节的当前 V2 完整块原位替换旧块，
包括 V1-only 门禁和缺少 `AI_TOOLS_STATE_GATE_V1` 的旧 V2 指纹块；禁止在旧块后追加。
替换后直接运行以下断言：

```bash
set -euo pipefail

: "${REPRESENTATIVE_TARGET_PROJECT:?设置为 8.1 已选代表性目标项目的绝对路径}"
: "${RUN_DIR:?先执行“每次运行的输入与记录”初始化}"
case "$REPRESENTATIVE_TARGET_PROJECT" in
  /*) ;;
  *) echo "REPRESENTATIVE_TARGET_PROJECT 必须是绝对路径" >&2; exit 1 ;;
esac
case "$RUN_DIR" in
  /*) ;;
  *) echo "RUN_DIR 必须是绝对路径" >&2; exit 1 ;;
esac
TARGET_PROJECT="$REPRESENTATIVE_TARGET_PROJECT"
TARGET_PROJECT="$(cd "$TARGET_PROJECT" && pwd -P)"
RUN_DIR="$(cd "$RUN_DIR" && pwd -P)"
cd "$TARGET_PROJECT"

# 删除旧版本曾安装的两个指纹脚本位置；不影响 scripts/ 中其它工具。
rm -f -- \
  "$TARGET_PROJECT/scripts/openspec-verification-fingerprint.py" \
  "$TARGET_PROJECT/.cursor/scripts/openspec-verification-fingerprint.py"

# 检查 `.agents/skills/` 中这 4 个 Verify 门禁文件。
GATE_FILES=(
  .agents/skills/openspec-{apply-change,verify-change,sync-specs,archive-change}/SKILL.md
)

python3 - "${GATE_FILES[@]}" <<'PY'
from pathlib import Path
import re
import sys

legacy = re.compile(r"(?m)^<!-- AI_TOOLS_VERIFY_GATE_V[01] -->[ \t]*$")
start = "<!-- AI_TOOLS_VERIFY_GATE_V2 -->"
end = "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->"
required_by_name = {
    "openspec-apply-change": (
        "AI_TOOLS_DIRECT_APPLY_V1",
        "AI_TOOLS_APPLY_SKILL_RULE_DISCOVERY_V1",
    ),
    "openspec-verify-change": ("AI_TOOLS_DIRECT_VERIFY_V1",),
    "openspec-sync-specs": ("AI_TOOLS_VERIFY_FLOW_GATE_V1",),
    "openspec-archive-change": ("AI_TOOLS_VERIFY_FLOW_GATE_V1",),
}
removed_dispatch_markers = (
    "AI_TOOLS_DELEGATED_",
    "AI_TOOLS_STANDALONE_",
    "AI_TOOLS_DISPATCH_FALLBACK_V1",
    "AI_TOOLS_PARALLEL_",
    "AI_TOOLS_WORKER_",
    "AI_TOOLS_MULTI_IDE_V1",
)
for name in sys.argv[1:]:
    text = Path(name).read_text()
    if legacy.search(text):
        raise SystemExit("{} still contains a legacy gate".format(name))
    if text.count(start) != 1:
        raise SystemExit("{} must contain one V2 start".format(name))
    if text.count(end) != 1:
        raise SystemExit("{} must contain one V2 end".format(name))
    block = text.split(start, 1)[1].split(end, 1)[0]
    if "AI_TOOLS_STATE_GATE_V1" not in block:
        raise SystemExit("{} still contains a legacy fingerprint gate".format(name))
    skill_name = Path(name).parent.name
    required = required_by_name.get(skill_name)
    if required is None:
        raise SystemExit("{} missing required marker".format(name))
    missing = [marker for marker in required if marker not in block]
    if missing:
        raise SystemExit(
            "{} missing required marker: {}".format(name, missing[0])
        )
    present_removed = [
        marker for marker in removed_dispatch_markers if marker in block
    ]
    if present_removed:
        raise SystemExit("{} still contains removed dispatch marker".format(name))
PY

LEGACY_VERIFICATION_REPORT="$RUN_DIR/legacy-verification-changes.txt"
LEGACY_VERIFICATION_PATTERN='AI_TOOLS_VERIFICATION_SCOPE_V[12]_(START|END)|范围摘要：|内容指纹：|AI_TOOLS_VERIFICATION_RESULT_V1_(START|END)'
: > "$LEGACY_VERIFICATION_REPORT"
for verification in openspec/changes/*/verification.md; do
  test -f "$verification" || continue
  if rg -q "$LEGACY_VERIFICATION_PATTERN" "$verification"; then
    printf '%s\n' "$verification" >> "$LEGACY_VERIFICATION_REPORT"
  fi
done
test ! -s "$LEGACY_VERIFICATION_REPORT" || {
  echo '以下 active change 含旧验证结构，必须逐个运行 $openspec-verify 后才能继续：'
  command cat "$LEGACY_VERIFICATION_REPORT"
  exit 1
}
```

预期：目标项目自有配置未被整文件覆盖；每个目标文件中
`AI_TOOLS_VERIFY_GATE_V2` 完整块恰好一个。旧 V1 块必须替换而不是
重复追加；若 active change 含 V1 结果、V1/V2 范围块或旧摘要字段，先执行一次 verify
清理并生成当前结果块，不得自动沿用旧通过状态。第一次运行可能因
`$LEGACY_VERIFICATION_REPORT` 非空而退出 1；逐个完成 verify
后重跑必须退出 0，报告为空。该独立片段全程启用 `set -euo pipefail`；目标项目、
运行记录目录、任一目标文件或 V2 块断言失败都会立即以非零退出，不得继续执行并被
末尾命令掩盖。

- [ ] **8.4 运行目标项目 schema 和 change 冒烟测试**

```bash
openspec schema validate evidence-driven
openspec new change "openspec-upgrade-smoke" --schema evidence-driven
openspec status --change "openspec-upgrade-smoke"
openspec status --change "openspec-upgrade-smoke" --json
openspec instructions apply --change "openspec-upgrade-smoke" --json
openspec validate "openspec-upgrade-smoke" --type change --strict
```

预期：

- schema 校验通过；
- change 可创建并产生新版预期的制品图；
- status 和 apply instructions 能解析；
- 未填写制品时 strict validate 应返回明确的未完成错误，而不是崩溃或 schema 解析错误。

- [ ] **8.5 清理冒烟 change**

只删除本步骤创建且尚未包含业务内容的 `openspec-upgrade-smoke`。删除前确认其路径来自 `openspec status --json`，不要按猜测硬编码其它 change 路径。

## 9. 回滚与交付

**文件：**
- 检查：本次升级的全部 Git diff

- [ ] **9.1 验证 CLI 回滚命令**

若升级阻塞且需要回滚 CLI：

```bash
npm install --global "@fission-ai/openspec@$SOURCE_VERSION"
test "$(openspec --version)" = "$SOURCE_VERSION"
```

预期：CLI 恢复到源版本。仓库文件使用当前分支的 Git diff 人工撤销，不使用 `git reset --hard`。

- [ ] **9.2 汇总升级证据**

交付说明必须包含：

- 源版本与目标版本；
- 新版官方基线路径；
- 上游关键变化；
- `evidence-driven` 保留的自定义差异；
- CLI JSON 契约检查结果；
- schema 校验和目标项目冒烟结果；
- 未执行项、失败项和剩余风险。

- [ ] **9.3 最终状态检查**

运行：

```bash
git status --short
git diff --check
git diff -- README.md docs/ openspec/ .cursor/ .agents/skills/ spec/
```

预期：无空白错误；修改范围与本计划一致；没有提交临时目录、官方生成物或无关文件。只有在用户明确要求时，才按逻辑变更组创建 commit。

## 完成标准

- [ ] OpenSpec CLI 与本次固定的 `TARGET_VERSION` 完全一致。
- [ ] `evidence-driven` 已基于该版本官方 `spec-driven` 重建，所有额外差异均可解释。
- [ ] `openspec schema validate evidence-driven` 通过。
- [ ] from-code skill 依赖的 CLI 命令、JSON 字段和 archive 定位已验证或完成适配。
- [ ] `.gitignore`、中文规则和接入门禁与新版官方生成物一致。
- [ ] 结构化验证门禁、单元测试及紧凑模板四章节/30 行预算全部通过。
- [ ] 当前维护文档已统一为状态/阻塞项门禁且无 V1 Verify 门禁；历史计划仍保留其原始版本事实。
- [ ] 至少一个隔离的目标项目完成 update、schema 校验、旧验证结构清理及状态门禁冒烟测试。
- [ ] 完整 diff 已审查，未处理的 Critical 或 Important 为零。
- [ ] `$RUN_LOG` 包含真实执行证据、未执行项和剩余风险。
