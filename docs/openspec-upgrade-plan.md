# OpenSpec 可重复升级实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: 使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐项执行本计划。每次执行前复制本计划作为当次运行记录，只在副本中勾选任务，不要修改本计划模板的复选框。OpenSpec 相关对话、制品与总结必须使用简体中文。

**目标：** 在每次执行时，将 OpenSpec CLI 从当前已安装版本升级到指定目标版本（默认取 npm 发布的最新稳定版），使 `evidence-driven` 与目标版本官方 `spec-driven` 重新对齐，并验证本仓库扩展和目标项目仍可正常工作。

**方案：** 先记录源版本并解析 npm 最新稳定版，再从新 CLI 动态取得官方 schema 和 Cursor 生成物作为唯一基线。官方派生部分从新基线重建，只保留项目允许的自定义差异；随后验证 CLI JSON 契约、文档、目标项目更新流程和回滚路径。

**技术栈：** Node.js/npm、`@fission-ai/openspec` CLI、YAML、Markdown、Cursor Agent Skills、Git、`jq`、`rg`

## 全局约束

- 本文件是可重复执行的计划模板，不记录某次运行的完成状态或结论。每次运行的版本、路径、命令输出、差异分类和验证结论写入独立运行记录。
- 不得永久假定任何源版本或目标版本；源版本取执行时 `openspec --version`，目标版本由执行者显式指定，未指定时才取 `npm view @fission-ai/openspec version`。
- 安装时使用查询得到的精确版本 `@${TARGET_VERSION}`，避免执行过程中 `@latest` 再次漂移。
- `ai-tools` 根目录不得执行 `openspec init` 或 `openspec update`；官方生成物对照必须在临时目录完成。
- 不得从目标项目反向复制官方生成物到本仓库，也不得提交官方 `.cursor/skills/openspec-*` 或 `.cursor/commands/opsx-*` 副本。
- `proposal`、`specs`、`design`、`tasks` 必须继承新版官方 `spec-driven`；本地只允许简体中文化、`evidence-driven` 命名、`verification` 制品、apply 前置和验证记录语义等已批准差异。
- `openspec/config.yaml` 必须继续使用 `schema: evidence-driven`。
- 目标项目已有 `openspec/config.yaml` 时只合并 `schema` 字段，不得整文件覆盖。
- 不修改与升级无关的工作区变更；开始前使用独立分支或 worktree，并确保基线可恢复。
- 不自动创建 commit；只有用户明确授权时才在任务检查点提交。

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
cp "$AI_TOOLS_DIR/docs/openspec-upgrade-plan.md" "$RUN_CHECKLIST"
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
- 读取：`.cursor/skills/openspec-update-change-from-code/SKILL.md`

- [ ] **1.1 确认工作区和执行边界**

运行：

```bash
git status --short
git branch --show-current
```

预期：明确记录执行前已有变更；升级不得覆盖或混入这些变更。若工作区不干净，先创建保留现状的独立 worktree，或暂停并让用户选择处理方式。

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
- 临时创建：`$UPGRADE_TMP/cursor-generated-$TARGET_VERSION/`

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

- [ ] **2.3 生成新版 Cursor 官方产物样本**

运行：

```bash
mkdir -p "$UPGRADE_TMP/cursor-generated-$TARGET_VERSION"
cd "$UPGRADE_TMP/cursor-generated-$TARGET_VERSION"
openspec init --tools cursor
```

预期：初始化成功。记录实际生成的 `.cursor/skills/openspec-*` 和 `.cursor/commands/opsx-*` 路径，不依赖旧版本名称推断。

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
- 检查或修改：`.cursor/skills/openspec-update-change-from-code/SKILL.md`
- 检查或修改：`.cursor/commands/opsx-update-change-from-code.md`

- [ ] **4.1 在临时项目创建 `evidence-driven` 冒烟 change**

将本仓库 `openspec/schemas/evidence-driven/` 复制到临时项目，只合并 `schema: evidence-driven`，然后运行：

```bash
cd "$UPGRADE_TMP/cursor-generated-$TARGET_VERSION"
mkdir -p openspec/schemas
cp -R "$AI_TOOLS_DIR/openspec/schemas/evidence-driven" openspec/schemas/
printf 'schema: evidence-driven\n' > openspec/config.yaml
openspec schema validate evidence-driven
openspec new change "upgrade-contract-smoke" --schema evidence-driven
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

## 5. 核对 Cursor 官方生成物和本地追加规则

**文件：**
- 检查或修改：`.gitignore`
- 检查或修改：`.cursor/rules/openspec-chinese.mdc`
- 检查或修改：`docs/ai-tools-integration.md`

- [ ] **5.1 比较新版生成的 skill/command 清单**

运行：

```bash
cd "$UPGRADE_TMP/cursor-generated-$TARGET_VERSION"
printf '%s\n' .cursor/skills/openspec-* .cursor/commands/opsx-*
```

预期：得到新版实际文件清单。若官方新增、删除或重命名路径，精确更新 `.gitignore`；不得忽略 `.cursor/skills/openspec-update-change-from-code/` 和 `.cursor/commands/opsx-update-change-from-code.md`。

- [ ] **5.2 核对中文规则覆盖范围**

比较 `.cursor/rules/openspec-chinese.mdc` 中列出的阶段、skill 和 `/opsx-*` 命令与新版清单。

预期：规则覆盖新版 OpenSpec 操作，同时保留 `/opsx-update-change-from-code`。

- [ ] **5.3 复核 `AI_TOOLS_VERIFY_GATE_V2`、`AI_TOOLS_PROPOSE_WORKTREE_V1` 与 `AI_TOOLS_WORKTREE_FINISH_V1` 追加点**

阅读新版 propose、apply、verify、sync、archive 的 command 和 skill，逐项判断 `docs/ai-tools-integration.md` 第 5.1 节 A/B/C、D 与 E 的追加内容是否仍有有效插入点、是否与新版官方行为冲突。

预期：

- 仍适用的规则更新文件名和措辞；
- 已由官方实现的重复规则删除或收敛；
- 无法由新版官方流程保证的规则不得继续宣称为硬门禁；
- 幂等检查以新版实际文件清单为准。
- propose 的 worktree 询问仍必须发生在官方 propose 主体与任何制品写入之前；
- 隔离 worktree 按需收尾仍不得在入口准备结束回复时主动询问（含官方主体失败但本次 worktree 已在）；只在用户明确要求时收尾本次相关路径，且不得自动合并或删除；
- V2 范围指纹脚本的命令行接口、输出字段和单元测试仍与注入块一致；
- 目标项目中旧 V1 Verify 块必须标为 `STALE` 并由唯一 V2 完整块替换，不得在旧块后重复追加；
- V1-only active change 不得自动迁移结果，必须先执行一次 verify，生成新的范围块、结果块与指纹。

## 6. 同步当前维护文档

**文件：**
- 修改：`README.md`
- 修改：`docs/ai-sdd-workflow.md`
- 修改：`docs/ai-tools-integration.md`
- 按需修改：`spec/spec-architecture-openspec-workflow-refactor.md`（文件存在且属于当前维护范围时）
- 按需修改：`docs/graphify-integration.md`
- 不修改：`docs/superpowers/plans/2026-08-14-openspec-official-first-refactor.md`

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

- [ ] **6.4 同步范围验证语言**

当前维护文档必须统一使用“V2 范围指纹”“范围内阻断”“范围外告警”，并说明正常
sync 生成的 main spec 未纳入声明范围时不强制重复实现验证。搜索
`README.md`、`docs/ai-sdd-workflow.md`、`docs/ai-tools-integration.md` 与本计划，
不得残留旧版 Verify 门禁标记或全工作区指纹表述；`docs/superpowers/plans/` 和
`docs/superpowers/specs/` 是历史记录，允许保留当时的 V1 事实，不做批量改写。

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
python3 -m unittest tests.test_openspec_verification_fingerprint -v
python3 -m unittest tests.test_openspec_verification_contract -v
python3 - <<'PY'
from pathlib import Path

text = Path("openspec/schemas/evidence-driven/templates/verification.md").read_text()
headings = [line for line in text.splitlines() if line.startswith("## ")]
assert headings == ["## 范围", "## 检查", "## 代码审查", "## 风险与回滚"]
assert len(text.splitlines()) <= 30
PY
if [ "$SOURCE_VERSION" != "$TARGET_VERSION" ]; then
  if rg -n -F "OpenSpec $SOURCE_VERSION" \
    README.md docs/ai-sdd-workflow.md docs/ai-tools-integration.md; then
    echo "错误：当前维护文档仍包含源版本 $SOURCE_VERSION" >&2
    exit 1
  else
    status=$?
    test "$status" -eq 1
  fi
else
  rg -n -F "OpenSpec $SOURCE_VERSION" \
    README.md docs/ai-sdd-workflow.md docs/ai-tools-integration.md
fi
```

预期：schema、V2 脚本接口与契约测试全部通过；紧凑模板严格为四个章节且不超过
30 行；当前维护文档无旧版 Verify 门禁标记或全工作区指纹表述。历史
`docs/superpowers/` 文档不在该静态搜索范围内。若 `SOURCE_VERSION` 与
`TARGET_VERSION` 不同，最后一组在当前维护文档中无命中；若版本相同，则人工核对
命中上下文是否准确。

- [ ] **7.3 验证官方生成物所有权边界**

```bash
git ls-files '.cursor/skills/openspec-*' '.cursor/commands/opsx-*'
git check-ignore .cursor/skills/openspec-apply-change/SKILL.md
if git check-ignore -q .cursor/skills/openspec-update-change-from-code/SKILL.md; then
  echo "错误：from-code skill 不应被忽略" >&2
  exit 1
fi
```

预期：`git ls-files` 只包含 from-code skill 和 command；官方 apply skill 被忽略；from-code skill 不被忽略。

- [ ] **7.4 人工执行差异审查**

审查三个差异集合：

1. 旧官方基线与新官方基线；
2. 新官方 `spec-driven` 与升级后 `evidence-driven`；
3. 本次 Git 完整 diff。

预期：第二组差异全部属于批准白名单；第三组不包含临时生成物、无关改动或未经解释的行为变化。未处理的 Critical 或 Important 发现项必须修复后重审。

## 8. 目标项目升级与冒烟验证

**文件：**
- 目标项目官方生成物：由 `openspec update` 管理
- 目标项目自定义 schema：`openspec/schemas/evidence-driven/`
- 目标项目配置：`openspec/config.yaml`
- 目标项目验证门禁文件：以新版实际生成清单和 `docs/ai-tools-integration.md` 为准

- [ ] **8.1 选择一个可回滚的代表性目标项目**

确认目标项目工作区干净或已隔离，并记录其升级前 OpenSpec 版本、官方生成物和自定义追加块状态。不得直接在有未提交业务改动的目录执行升级。

- [ ] **8.2 刷新目标项目官方层**

在目标项目运行：

```bash
openspec --version
openspec update
```

预期：更新成功，官方生成物与目标 CLI 版本一致。

- [ ] **8.3 安装升级后的自定义层**

只覆盖目标项目的 `openspec/schemas/evidence-driven/`，合并 `openspec/config.yaml`
中的 `schema: evidence-driven`，再按更新后的接入文档补齐缺失的规则。先运行接入文档
5.1 节检查器；对报告为 `STALE (V1-only gate)` 的文件，用对应 A/B/C 节的 V2 完整块
原位替换旧块，禁止在旧块后追加。替换后直接运行以下断言：

```bash
GATE_FILES=(
  .cursor/commands/opsx-{apply,verify,sync,archive}.md
  .cursor/skills/openspec-{apply-change,verify-change,sync-specs,archive-change}/SKILL.md
)

python3 - "${GATE_FILES[@]}" <<'PY'
from pathlib import Path
import re
import sys

legacy = re.compile(r"(?m)^<!-- AI_TOOLS_VERIFY_GATE_V[01] -->[ \t]*$")
start = "<!-- AI_TOOLS_VERIFY_GATE_V2 -->"
end = "<!-- AI_TOOLS_VERIFY_GATE_V2_END -->"
for name in sys.argv[1:]:
    text = Path(name).read_text()
    assert not legacy.search(text), "{} still contains a legacy gate".format(name)
    assert text.count(start) == 1, "{} must contain one V2 start".format(name)
    assert text.count(end) == 1, "{} must contain one V2 end".format(name)
PY

V1_ACTIVE_REPORT="$RUN_DIR/v1-active-changes.txt"
: > "$V1_ACTIVE_REPORT"
for verification in openspec/changes/*/verification.md; do
  test -f "$verification" || continue
  if rg -q 'AI_TOOLS_VERIFICATION_(SCOPE|RESULT)_V[[]1[]]_' "$verification"; then
    printf '%s\n' "$verification" >> "$V1_ACTIVE_REPORT"
  fi
done
test ! -s "$V1_ACTIVE_REPORT" || {
  echo "以下 active change 必须逐个运行 /opsx-verify 后才能继续："
  command cat "$V1_ACTIVE_REPORT"
  exit 1
}
```

预期：目标项目自有配置未被整文件覆盖；V2 范围指纹脚本已复制并通过语法检查；
每个目标文件中 `AI_TOOLS_VERIFY_GATE_V2` 完整块恰好一个。旧 V1 块必须替换而不是
重复追加；若 active change 只有 V1 结果，先执行一次 verify 迁移到 V2，不得自动
沿用旧通过状态。第一次运行可能因 `$V1_ACTIVE_REPORT` 非空而退出 1；逐个完成 verify
后重跑必须退出 0，报告为空。

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

然后执行以下可重复的范围指纹冒烟。目录由 `mktemp` 建在仓库外；脚本使用目标项目
8.3 已复制的版本，结束时由 `trap` 清理：

```bash
SCOPED_SMOKE="$(mktemp -d "${TMPDIR:-/tmp}/ai-tools-scoped-smoke.XXXXXX")"
trap 'rm -rf "$SCOPED_SMOKE"' EXIT
test "${SCOPED_SMOKE#"$AI_TOOLS_DIR"/}" = "$SCOPED_SMOKE"

git -C "$SCOPED_SMOKE" init -q
mkdir -p \
  "$SCOPED_SMOKE/src" \
  "$SCOPED_SMOKE/openspec/changes/scoped-smoke"
printf 'VALUE = 1\n' > "$SCOPED_SMOKE/src/app.py"
printf 'baseline\n' > "$SCOPED_SMOKE/notes.md"
git -C "$SCOPED_SMOKE" add src/app.py notes.md
git -C "$SCOPED_SMOKE" \
  -c user.name='OpenSpec Smoke' \
  -c user.email='openspec-smoke@example.invalid' \
  commit -qm 'baseline'
BASELINE="$(git -C "$SCOPED_SMOKE" rev-parse HEAD)"
VERIFICATION="$SCOPED_SMOKE/openspec/changes/scoped-smoke/verification.md"

cat > "$VERIFICATION" <<EOF
## 范围
<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_START -->
baseline: $BASELINE
include:
- src/
- openspec/changes/scoped-smoke/
exclude:
- none
<!-- AI_TOOLS_VERIFICATION_SCOPE_V2_END -->
## 检查
- smoke | command | PASS | 初始范围指纹
## 代码审查
- 范围：src/ 与当前 change
- 结论：PASS
## 风险与回滚
- 风险：无
- 回滚：删除临时目录
<!-- AI_TOOLS_VERIFICATION_RESULT_V2_START -->
## Verify 门禁
- 状态：通过
- 阻塞项：无
- 范围摘要：PENDING_SCOPE
- 内容指纹：PENDING_CONTENT
<!-- AI_TOOLS_VERIFICATION_RESULT_V2_END -->
EOF

run_fingerprint() {
  (
    cd "$SCOPED_SMOKE"
    python3 "$TARGET_PROJECT/.cursor/scripts/openspec-verification-fingerprint.py" "$VERIFICATION"
  )
}
value_of() {
  printf '%s\n' "$1" | awk -F= -v key="$2" '$1 == key {print $2; exit}'
}

baseline_output="$(run_fingerprint)"
baseline_exit=$?
test "$baseline_exit" -eq 0
scope_digest="$(value_of "$baseline_output" scope_digest)"
content_digest="$(value_of "$baseline_output" content_digest)"
test -n "$scope_digest"
test -n "$content_digest"

python3 - "$VERIFICATION" "$scope_digest" "$content_digest" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace("PENDING_SCOPE", sys.argv[2])
text = text.replace("PENDING_CONTENT", sys.argv[3])
path.write_text(text)
PY

check_gate() {
  output="$(run_fingerprint)" || return
  printf '%s\n' "$output"
  actual_scope="$(value_of "$output" scope_digest)"
  actual_content="$(value_of "$output" content_digest)"
  test "$actual_scope" = "$scope_digest"
  test "$actual_content" = "$content_digest"
}

printf 'outside\n' >> "$SCOPED_SMOKE/notes.md"
set +e
outside_output="$(check_gate 2>&1)"
outside_exit=$?
set -e
test "$outside_exit" -eq 0
outside_scope_digest="$(value_of "$outside_output" scope_digest)"
outside_content_digest="$(value_of "$outside_output" content_digest)"
test "$outside_scope_digest" = "$scope_digest"
test "$outside_content_digest" = "$content_digest"
test "$(value_of "$outside_output" outside_changes)" -eq 1
test "$(value_of "$outside_output" outside_path)" = "notes.md"

printf 'VALUE = 2\n' > "$SCOPED_SMOKE/src/app.py"
set +e
inside_output="$(check_gate 2>&1)"
inside_exit=$?
set -e
inside_content_digest="$(value_of "$inside_output" content_digest)"
test "$inside_content_digest" != "$content_digest"
test "$inside_exit" -ne 0

rm -rf "$SCOPED_SMOKE"
trap - EXIT
```

预期：初始化、baseline commit 和首次脚本调用均退出 0。只修改 `notes.md` 时
`outside_exit=0`，范围摘要与内容指纹均不变，并输出一个 `outside_path=notes.md`
告警；修改 `src/app.py` 后内容指纹变化，`check_gate` 因摘要不匹配而使
`inside_exit` 非 0，表示范围内阻断。最后只删除本步骤创建的仓库外临时目录。

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

预期：CLI 恢复到源版本。仓库文件使用本次独立分支/worktree 的 Git diff 人工撤销，不使用 `git reset --hard`。

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
git diff -- README.md docs/ openspec/ .cursor/ spec/
```

预期：无空白错误；修改范围与本计划一致；没有提交临时目录、官方生成物或无关文件。只有在用户明确要求时，才按逻辑变更组创建 commit。

## 完成标准

- [ ] OpenSpec CLI 与本次固定的 `TARGET_VERSION` 完全一致。
- [ ] `evidence-driven` 已基于该版本官方 `spec-driven` 重建，所有额外差异均可解释。
- [ ] `openspec schema validate evidence-driven` 通过。
- [ ] from-code skill 依赖的 CLI 命令、JSON 字段和 archive 定位已验证或完成适配。
- [ ] `.gitignore`、中文规则和接入门禁与新版官方生成物一致。
- [ ] V2 范围指纹脚本接口、单元测试及紧凑模板四章节/30 行预算全部通过。
- [ ] 当前维护文档已统一为范围内阻断、范围外告警且无 V1 Verify 门禁；历史计划仍保留其原始版本事实。
- [ ] 至少一个隔离的目标项目完成 update、schema 校验、V1 → V2 替换及范围内/范围外冒烟测试。
- [ ] 完整 diff 已审查，未处理的 Critical 或 Important 为零。
- [ ] `$RUN_LOG` 包含真实执行证据、未执行项和剩余风险。
